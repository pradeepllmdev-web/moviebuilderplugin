"""Blender-only previs driver: build every actor of many activities or movie shots in parallel, merge them into one
low-poly scene (previs_merge.py) and optionally render a quick mp4.

  python quick_review.py gallery [names|all]          every activity side by side in one Blender window, all playing
  python quick_review.py previs --plan module:VAR     a movie plan as one Blender scene with a camera per shot (+ --render mp4)

Both write to quick_review/previs_<time>/ and print one line per piece."""
import json,math,os,subprocess,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
H=Path(__file__).resolve().parent
def _qr():
 import quick_review;return quick_review
def close_viewers():
 """Close Blender windows opened earlier by these tools (their command line carries view_setup.py); other Blender sessions are left alone."""
 command="Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | Where-Object { $_.CommandLine -like '*view_setup.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
 try:subprocess.run(['powershell','-NoProfile','-Command',command],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
 except Exception:pass
KEEP_OPEN=False   # set by quick_review --keep-open: leave earlier viewer windows alone
def open_viewer(blend,folder,mode):
 """Open a built scene in a Blender window framed for viewing, after closing the previous viewer windows."""
 qr=_qr()
 if not KEEP_OPEN:close_viewers();time.sleep(1)
 subprocess.Popen([qr.BLENDER,str(blend),'--python',str(H/'view_setup.py'),'--',str(folder),mode],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def build_actor(single,label,threads=2,activity=None):
 """Blender build of one per-actor plan; returns (folder, ok, one-line summary)."""
 qr=_qr();folder=qr.OUT/f'actor_{label}_{time.strftime("%H%M%S")}_{os.getpid()}_{abs(hash(label))%1000}';folder.mkdir(parents=True,exist_ok=True)
 (folder/'plan.json').write_text(json.dumps(single));log=folder/'build.log'
 with open(log,'w') as handle:code=subprocess.call([qr.BLENDER,'-b','-t',str(threads),'--python-exit-code','1','-P',str(H/'build_prompt_scene_blender.py'),'--',str(folder)],stdout=handle,stderr=subprocess.STDOUT)
 if code:
  text=log.read_text(errors='ignore').splitlines();error=next((l.strip() for l in reversed(text) if 'Error' in l and 'script failed' not in l),'see '+str(log))
  return folder,False,error[:140]
 import activities
 if activity in activities.GESTURES or activity=='phone':
  beats=activities.ACTIVITIES[activity]['test_beats'];start=sum(d for a,d in beats[:[a for a,d in beats].index(activity)])
  subprocess.call([qr.BLENDER,'-b',str(folder/'scene.blend'),'--python',str(H/'gesture_check.py'),'--',str(folder),str(start),str(start+dict(beats)[activity])],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 bad=[l.strip()[:120] for l in qr.summary(folder) if 'ok=False' in l]
 return folder,not bad,' | '.join(bad) if bad else 'ok'
def actor_inputs(shot,plan_extra=None):
 """Per-actor plan.json dicts for one validated shot, as the studio worker writes them (partner contact, facing)."""
 from scene_gaze import conversation_context
 import contact_actions
 from character_profiles import PROFILES
 heights={k:v['height_cm'] for k,v in PROFILES.items()}
 actors=shot.get('actors') or [dict(character=shot['character'],segments=shot['segments'],position_cm=[0,0])]
 out=[]
 for i,actor in enumerate(actors):
  single={k:v for k,v in shot.items() if k!='actors'}
  single.update(character=actor['character'],segments=actor['segments'],motion_heading=False,partner_gaze=conversation_context(shot,actor) if shot.get('actors') else None,
   facing_yaw_deg=actor.get('facing_yaw_deg',0),actor_position_cm=actor.get('position_cm',[0,0]),carry_pose=None,box_state=None,box_scene_stands=None)
  if shot.get('actors'):single.update(contact_actions.pair_inputs(actors,i,heights))
  out.append(single)
 return out
def camera_for(shot,actors_xy):
 """Camera like the Unreal builder places it (world cm), as a previs camera dict."""
 kind=shot.get('camera','full');close=kind in ('close','reaction');cx=sum(p[0] for p in actors_xy)/len(actors_xy);cy=sum(p[1] for p in actors_xy)/len(actors_xy)
 pair=len(actors_xy)>1
 pos=[cx+(230 if close else 520 if pair else 420),cy+(150 if close else 220),180 if close else 230];target=[cx,cy,145 if close else 105]
 return dict(pos_cm=pos,target_cm=target,lens=42 if close else 32 if kind=='full' else 40)
def shot_length(shot):
 actors=shot.get('actors') or [dict(segments=shot['segments'])]
 return round(sum(g['duration'] for g in actors[0]['segments'])*24)
def merge(spec,name,render=False,open_gui=False):
 """Write the spec, run the merge in background Blender, optionally render and open."""
 qr=_qr();folder=qr.OUT/f'previs_{time.strftime("%H%M%S")}_{name}';folder.mkdir(parents=True,exist_ok=True);spec['out']=str(folder/'previs');spec['render']=render
 (folder/'spec.json').write_text(json.dumps(spec));log=folder/'merge.log'
 with open(log,'w') as handle:code=subprocess.call([qr.BLENDER,'-b','--python-exit-code','1','-P',str(H/'previs_merge.py'),'--',str(folder/'spec.json')],stdout=handle,stderr=subprocess.STDOUT)
 if code:return folder,'merge FAILED: '+next((l.strip() for l in reversed(log.read_text(errors='ignore').splitlines()) if 'Error' in l),'see '+str(log))
 if open_gui:
  open_viewer(folder/'previs.blend',folder,spec['mode'])
 return folder,'ok'
def run_gallery(names,character='lion',open_gui=True,sequence=False,render=False):
 """Every named activity (pairs included) built in parallel, then all merged into one scene."""
 import activities
 from movie_prompt import validate
 qr=_qr();started=time.time();pieces=[]
 for name in names:
  a=activities.ACTIVITIES[name]
  if character not in a['characters']:pieces.append((name,None,'not calibrated for '+character));continue
  pieces.append((name,qr.activity_plan(name,character) if not a.get('pair') else pair_plan(name),None))
 jobs=[]
 for name,plan,skip in pieces:
  if skip:continue
  shot=validate(plan)['shots'][0] if not activities.ACTIVITIES[name].get('pair') else plan['shots'][0]
  jobs+=[(name,i,single) for i,single in enumerate(actor_inputs(shot))]
 with ThreadPoolExecutor(8) as pool:results=list(pool.map(lambda j:(j,build_actor(j[2],f'{j[0]}{j[1]}',1,j[0])),jobs))
 report=[];shots=[];by={}
 for (name,i,single),(folder,ok,detail) in results:by.setdefault(name,[]).append((folder,ok,detail,single))
 for name,plan,skip in pieces:
  if skip:report.append(f'SKIP {name}: {skip}');continue
  actors=by[name];ok=all(a[1] for a in actors)
  if ok and len(actors)==2:
   pair=_pair_check(actors[0][0],actors[1][0]);ok=pair['ok'];detail='pair '+json.dumps(pair)
  else:detail=' | '.join(a[2] for a in actors)
  report.append(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
  if all(a[1] or True for a in actors) and all((a[0]/'scene.blend').exists() for a in actors):
   length=sum(d for a,d in activities.ACTIVITIES[name]['test_beats'])*24
   shots.append(dict(start=1,length=length,label=name,actors=[dict(folder=str(f),position_cm=s['actor_position_cm'],yaw=s['facing_yaw_deg']) for f,ok_,d,s in actors]))
 if sequence:
  # One animation at a time, 5 seconds each, one fixed camera: the slot shows the activity's own beat (leading idle skipped).
  start=1;slot=120
  for s in shots:
   beats=activities.ACTIVITIES[s['label']]['test_beats'];lead=0
   for a,d in beats:
    if a=='idle':lead+=d
    else:break
   total=sum(d for a,d in beats);s['src_start']=lead*24+1;s['src_length']=min(slot,(total-lead)*24);s['start']=start;s['length']=slot;start+=slot
  library={s['label']:dict(slot_start_frame=s['start'],slot_end_frame=s['start']+slot-1,seconds=5,source_actor_folders=[a['folder'] for a in s['actors']]) for s in shots}
  folder,note=merge(dict(mode='movie',fps=24,shots=shots,width=640,height=360,trees=True,captions=True,camera=dict(pos_cm=[170,250,140],target_cm=[0,0,95],lens=35)),'reel',render,open_gui)
  (folder/'library.json').write_text(json.dumps(library,indent=1))
  report.append(f'reel: {note} -> {folder}/'+('previs.mp4' if render else 'previs.blend')+f'  ({start-1} frames, {time.time()-started:.0f}s)')
  return report
 folder,note=merge(dict(mode='gallery',fps=24,shots=shots,columns=8,gap_cm=300),'gallery',False,open_gui)
 report.append(f'gallery: {note} -> {folder}/previs.blend  ({time.time()-started:.0f}s)')
 return report
def pair_plan(name,left='lion',right='rowan',spacing=None,lateral=0.):
 """Two-actor test shot for a contact activity: both do the beat, spacing inside the reach limit."""
 import activities,contact_actions
 beats=activities.ACTIVITIES[name]['test_beats'];spacing=spacing or contact_actions.default_spacing(name,left,right)
 def actor(ch,x):
  extra=dict(position_cm=[x,0],facing_yaw_deg=0)   # handshake and hug are side by side, both facing the same way
  return dict(character=ch,segments=[dict(action=a,duration=d,dialogue='') for a,d in beats],**extra)
 shot=dict(version=1,title=name,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera='full',unsupported=[],notes=[],actors=[actor(left,-spacing/2),actor(right,spacing/2)])
 import scene_prompt
 return dict(version=1,title=name+' check',unsupported=[],shots=[scene_prompt.validate(shot)])
def _pair_check(a,b):
 import contact_actions
 try:return contact_actions.pair_check(a,b)
 except Exception as error:return dict(ok=False,reason=str(error)[:100])
def props_for(folder,single,style=None):
 """World-space proxies an actor's build needs: bench, table and cup (seat/drink), stairs. Cup, crate and door already live in the actor's scene."""
 import contact_actions as ca
 folder=Path(folder);props=[];pos=single['actor_position_cm']
 route=json.loads((folder/'route.json').read_text()) if (folder/'route.json').exists() else None
 def world(x,y,z,frame=0):
  r=route[frame];return ca.to_world((x,y,z),(pos[0]+r['location_cm'][0],pos[1]+r['location_cm'][1]),r['yaw'])
 if (folder/'seat.json').exists() and route:
  s=json.loads((folder/'seat.json').read_text());c=world(s['lateral_cm'],-(s['forward_cm']-3),s['top_cm']/2,s['frame']);props.append(dict(shape='box',center_cm=list(c),size_cm=[70,32,s['top_cm']],color=[.35,.22,.1],yaw=route[s['frame']]['yaw']+180,name='Bench'))
  if (folder/'drink.json').exists():
   d=json.loads((folder/'drink.json').read_text());tb=d['table'];tc=world(tb['center'][0],tb['center'][1],tb['top_cm']-tb['thickness_cm']/2,s['frame'])
   props.append(dict(shape='box',center_cm=list(tc),size_cm=[tb['size_cm'][0],tb['size_cm'][1],tb['thickness_cm']],color=[.5,.3,.15],yaw=route[s['frame']]['yaw']+180,name='DrinkTable'))
   for sx in (-1,1):
    for sy in (-1,1):
     lc=world(tb['center'][0]+sx*(tb['size_cm'][0]/2-4),tb['center'][1]+sy*(tb['size_cm'][1]/2-4),tb['top_cm']/2,s['frame']);props.append(dict(shape='box',center_cm=list(lc),size_cm=[5,5,tb['top_cm']],color=[.4,.25,.12],name='TableLeg'))
   cc=world(d['cup_cm'][0],d['cup_cm'][1],d['cup_cm'][2],s['frame']);props.append(dict(shape='cylinder',center_cm=list(cc),size_cm=[d['cup']['radius_cm'],d['cup']['height_cm']],color=[.85,.25,.2],name='Cup'))
 if (folder/'door.json').exists() and route:   # a door needs a wall, a room behind it and a lit window
  d=json.loads((folder/'door.json').read_text());hx,py,dr,w=d['hinge_cm'][0],d['plane_y_cm'],d['dir'],d['width_cm'];x1=hx+dr*w;mid=(hx+x1)/2;depth=440;R=280;out=R-w/2;yaw=route[0]['yaw']+180
  def part(name,cx,cy,cz,sx,sy,sz,color):props.append(dict(shape='box',center_cm=list(world(cx,cy,cz)),size_cm=[sx,sy,sz],color=color,yaw=yaw,name=name))
  cream=[.9,.84,.7];part('DoorWallL',hx-dr*out/2,py,130,out,15,260,cream);part('DoorWallR',x1+dr*out/2,py,130,out,15,260,cream);part('DoorWallTop',mid,py,230,w,15,60,cream)
  span=2*R;part('HutBack',mid,py-depth,130,span,15,260,cream);part('HutSideA',mid-span/2,py-depth/2,130,15,depth,260,cream);part('HutSideB',mid+span/2,py-depth/2,130,15,depth,260,cream)
  part('HutRoof',mid,py-depth/2,268,span+20,depth+30,16,[.55,.2,.15]);part('HutFloor',mid,py-depth/2,.5,span,depth,1,[.5,.36,.22]);part('WindowLit',x1+dr*out/2,py+9,150,70,3,60,[1,.93,.55])
  props.append(dict(shape='sphere',center_cm=list(world(mid,py-90,200)),size_cm=[9],color=[1,.9,.45],name='Lamp'))
  if style=='cafe':   # striped awning, sign and patio tables outside the door
   stripe=(w+80)/8
   for i in range(8):part('Awning',mid+dr*(-(w+80)/2+stripe*(i+.5))*-1,py+55,222,stripe,100,8,[.85,.15,.15] if i%2==0 else [.95,.92,.88])
   part('CafeSign',mid,py+10,246,w+60,6,34,[.3,.18,.08])
   for sx in (-1,1):
    cx=mid+sx*190;part('PatioTable',cx,py+150,72,70,70,5,[.8,.7,.55]);part('PatioLeg',cx,py+150,36,8,8,72,[.4,.3,.2])
    for dx,dy in ((50,0),(-50,0),(0,50)):part('PatioChair',cx+dx,py+150+dy,25,36,36,50,[.55,.35,.2])
 if (folder/'stairs.json').exists():
  j=json.loads((folder/'stairs.json').read_text());st=j['step']
  for k in range(st['count']):
   h=st['rise_cm']*(k+1);props.append(dict(shape='box',center_cm=[pos[0],pos[1]+j['start_y_cm']+st['first_cm']+(k+.5)*st['tread_cm']+6,h/2],size_cm=[200,st['tread_cm'],h],color=[.6,.58,.55],name='Step'))
 return props
def seated_times(segments):
 """(seconds the hips are on the seat, seconds the rise starts) from the beats of one actor, or None."""
 t=0.;first=last=None
 for g in segments:
  if g['action']=='sit_down' and first is None:first=t+1.8
  if g['action']=='stand_up':last=t+.4
  t+=g['duration']
 if first is None and any(g['action'] in ('sit','sit_talk','drink') for g in segments):first=0.
 return (first,last if last is not None else t) if first is not None else None
def lines_for(folder,speaker):
 p=Path(folder)/'scene.json'
 if not p.exists():return []
 return [dict(speaker=l.get('speaker',speaker),text=l['text'],start_s=l['start'],end_s=min(l['end']+.4,l['end']+1),audio=l.get('audio')) for l in json.loads(p.read_text()).get('lines',[])]
def lenient_validate(plan):
 """Validate every shot like the planner does, without the movie-level 2..6 shot / 90 s limits (a previs story can be longer)."""
 import copy,scene_prompt
 return dict(plan,shots=[scene_prompt.validate(copy.deepcopy(s)) for s in plan['shots']])
def run_previs(plan,name='movie',render=False,open_gui=True,direction=None,strict=False):
 """A movie plan -> one Blender scene, a camera per shot, shots laid end to end, actors walking their routes. direction = {sets:[...], shots:{title:{origin_cm, camera}}}."""
 qr=_qr();started=time.time();p=lenient_validate(plan);jobs=[];shots=[];start=1
 import story_lint,story_layout
 scenery_boxes=story_layout.scenery(p,direction)
 findings=story_lint.lint(p,direction);lint_lines=['story check:']+story_lint.report(findings)
 print(chr(10).join(lint_lines),flush=True)
 if strict and any(f['severity']=='error' for f in findings):return lint_lines+['stopped: fix the errors above (or run without --strict)']
 for k,shot in enumerate(p['shots']):
  inputs=actor_inputs(shot)
  jobs+=[(k,i,single) for i,single in enumerate(inputs)]
 with ThreadPoolExecutor(8) as pool:results=list(pool.map(lambda j:(j,build_actor(j[2],f's{j[0]}a{j[1]}',1)),jobs))
 report=[];built={};extra=[]
 for (k,i,single),(folder,ok,detail) in results:
  built.setdefault(k,[]).append((folder,ok,detail,single));report.append(f"{'PASS' if ok else 'FAIL'} shot {k+1} actor {i+1} ({single['character']}): {detail}")
 for k,shot in enumerate(p['shots']):
  actors=built[k]
  if not all((a[0]/'scene.blend').exists() for a in actors):continue
  length=shot_length(shot);xy=[s['actor_position_cm'] for f,ok,d,s in actors]
  xy=[[x+(direction or {}).get('shots',{}).get(shot.get('title',''),{}).get('origin_cm',[0,0])[0]*0,y] for x,y in xy]
  title=shot.get('title','shot %d'%(k+1));d_shot=(direction or {}).get('shots',{}).get(title,{});place=tuple(d_shot.get('origin_cm',[0,0]));ox,oy=place[0]+d_shot.get('offset_cm',[0,0])[0],place[1]+d_shot.get('offset_cm',[0,0])[1];cam=camera_for(shot,xy);cam.update(d_shot.get('camera',{}))   # offset_cm moves a shot within its place (e.g. the seat away from the standing area)
  for key in ('pos_cm','target_cm','to_pos_cm','to_target_cm'):
   if key in cam:cam[key]=[cam[key][0]+ox,cam[key][1]+oy,cam[key][2]]
  if (direction or {}).get('auto_camera') and not d_shot.get('camera_lock'):   # cameras chosen from the planned scenery, never in or behind a wall
   import story_camera;cam=story_camera.solve_shot(shot,(ox,oy),scenery_boxes.get(place,[]))
  lines=[l for f,ok,d,s in actors for l in lines_for(f,s['character'])]
  for f,ok,d,s in actors:
   times=seated_times(s['segments'])
   for q in props_for(f,s,d_shot.get('door_style')):
    q['center_cm']=[q['center_cm'][0]+ox,q['center_cm'][1]+oy,q['center_cm'][2]];q['place']=place   # scenery belongs to its place: it is there in every shot at that place
    extra.append(q)
  shots.append(dict(start=start,length=length,label=title,place=list(place),camera=cam,lines=lines,actors=[dict(folder=str(f),position_cm=[s['actor_position_cm'][0]+ox,s['actor_position_cm'][1]+oy],yaw=s['facing_yaw_deg']) for f,ok,d,s in actors]));start+=length
 for q in extra:   # permanent scenery: visible from the first to the last shot at its place
  place=q.pop('place');window=[s for s in shots if tuple(s['place'])==tuple(place)]
  if window:q['frames']=[window[0]['start'],window[-1]['start']+window[-1]['length']-1]
 story_props=[]
 for q in (direction or {}).get('props',[]):   # story props: world cm, optionally only visible in the named shots (only_in)
  q=dict(q)
  if q.get('place'):   # permanent story prop of a place
   window=[s for s in shots if tuple(s['place'])==tuple(q['place'])]
   if window:q['frames']=[window[0]['start'],window[-1]['start']+window[-1]['length']-1]
  elif q.get('only_in'):
   window=[s for s in shots if s['label'] in q['only_in']]
   if window:q['frames']=[window[0]['start'],window[-1]['start']+window[-1]['length']-1]
  story_props.append(q)
 folder,note=merge(dict(mode='movie',fps=24,shots=shots,width=640,height=360,trees=True,use_routes=True,sets=(direction or {}).get('sets'),props=extra+story_props),name,render,open_gui)
 report.append(f'movie {note}: {folder}'+(f'/previs.mp4' if render else '/previs.blend')+f'  ({start-1} frames, {time.time()-started:.0f}s)')
 return report
