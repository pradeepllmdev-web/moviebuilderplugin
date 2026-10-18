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
  subprocess.Popen([qr.BLENDER,str(folder/'previs.blend'),'--python',str(H/'view_setup.py'),'--',str(folder),spec['mode']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return folder,'ok'
def run_gallery(names,character='lion',open_gui=True):
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
 folder,note=merge(dict(mode='gallery',fps=24,shots=shots,columns=8,gap_cm=300),'gallery',False,open_gui)
 report.append(f'gallery: {note} -> {folder}/previs.blend  ({time.time()-started:.0f}s)')
 return report
def pair_plan(name,left='lion',right='rowan'):
 """Two-actor test shot for a contact activity: both do the beat, spacing inside the reach limit."""
 import activities,contact_actions
 beats=activities.ACTIVITIES[name]['test_beats'];spacing=contact_actions.REACH_LIMIT_CM[name]-8
 def actor(ch,x):return dict(character=ch,position_cm=[x,0],segments=[dict(action=a,duration=d,dialogue='') for a,d in beats])
 shot=dict(version=1,title=name,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera='full',unsupported=[],notes=[],actors=[actor(left,-spacing/2),actor(right,spacing/2)])
 import scene_prompt
 return dict(version=1,title=name+' check',unsupported=[],shots=[scene_prompt.validate(shot)])
def _pair_check(a,b):
 import contact_actions
 try:return contact_actions.pair_check(a,b)
 except Exception as error:return dict(ok=False,reason=str(error)[:100])
def run_previs(plan,name='movie',render=False,open_gui=True):
 """A validated movie plan -> one Blender scene, a camera per shot, shots laid end to end."""
 from movie_prompt import validate
 qr=_qr();started=time.time();p=validate(plan);jobs=[];shots=[];start=1
 for k,shot in enumerate(p['shots']):
  singles=qr.shot_inputs(plan,k) if not shot.get('actors') else None
  inputs=[singles] if singles else actor_inputs(shot)
  jobs+=[(k,i,single) for i,single in enumerate(inputs)]
 with ThreadPoolExecutor(8) as pool:results=list(pool.map(lambda j:(j,build_actor(j[2],f's{j[0]}a{j[1]}',1)),jobs))
 report=[];built={}
 for (k,i,single),(folder,ok,detail) in results:
  built.setdefault(k,[]).append((folder,ok,detail,single));report.append(f"{'PASS' if ok else 'FAIL'} shot {k+1} actor {i+1} ({single['character']}): {detail}")
 for k,shot in enumerate(p['shots']):
  actors=built[k]
  if not all((a[0]/'scene.blend').exists() for a in actors):continue
  length=shot_length(shot);xy=[s['actor_position_cm'] for f,ok,d,s in actors]
  shots.append(dict(start=start,length=length,label=shot.get('title','shot %d'%(k+1)),camera=camera_for(shot,xy),actors=[dict(folder=str(f),position_cm=s['actor_position_cm'],yaw=s['facing_yaw_deg']) for f,ok,d,s in actors]));start+=length
 folder,note=merge(dict(mode='movie',fps=24,shots=shots,width=640,height=360,trees=True),name,render,open_gui)
 report.append(f'movie {note}: {folder}'+(f'/previs.mp4' if render else '/previs.blend')+f'  ({start-1} frames, {time.time()-started:.0f}s)')
 return report
