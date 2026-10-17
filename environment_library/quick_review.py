"""Fast iteration loop: one command builds, prints every check on a few lines, and saves one picture.

  python quick_review.py activity drink    feasibility from cached body numbers (instant), then a one-shot Blender build of just that activity
  python quick_review.py shot 1            Blender-only build of shot 1 (~10 s) + check summary + side-view sheet
  python quick_review.py shot all          every shot in parallel Blender processes (~one shot's time); --no-sheet skips pictures
  python quick_review.py movie             full Unreal preview via the studio server (~1.5 min) + checks + frame sheet
  python quick_review.py frames ID 60,130  re-capture Unreal frames of an existing movie (no rebuild)

Options: --plan module:VAR (default test_box_movie:PLAN), --frames 60,130,... (Unreal frame numbers).
Output goes to quick_review/<name>/; the sheet path is printed last. Restart studio_server.py after code changes."""
import argparse,importlib,json,math,os,subprocess,sys,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'quick_review'
BLENDER='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
STUDIO='http://127.0.0.1:8521';BRIDGE='http://127.0.0.1:8500'
CHECKS=['box-contact-check.json','box-clearance-check.json','motion-safety.json','build-check.json','box-prop-check.json','box-camera-check.json','camera-check.json']

def post(url,body,timeout=60):
 request=urllib.request.Request(url,json.dumps(body).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=timeout) as response:return json.loads(response.read())
def get(url):
 with urllib.request.urlopen(url,timeout=30) as response:return json.loads(response.read())
def load_plan(spec):
 module,name=spec.split(':');return getattr(importlib.import_module(module),name)

def summary(folder):
 """One line per check, only the numbers that decide pass/fail."""
 lines=[]
 def read(name):
  for path in (folder/name,folder/'actor_0'/name):
   if path.exists():return json.loads(path.read_text())
 c=read('box-clearance-check.json')
 if c:lines.append(f"clearance  ok={c['ok']} deepest={c['deepest']['depth_cm']:.2f}cm ({c['deepest'].get('action')}, {c['deepest'].get('bone_group')}) stand_gap={c['stands']['minimum_gap_cm']:.1f}cm")
 c=read('box-contact-check.json')
 if c:lines.append('wrists     hands off the box this shot' if not c['contact_samples'] else f"wrists     ok={c['ok']} max_error={c['maximum_wrist_target_error_cm']:.3f}cm posture_capped={c.get('posture_capped_frames')}")
 c=read('motion-safety.json')
 if c:lines.append(f"safety     ok={c['ok']} max_step={c['maximum_rotation_step_deg']:.0f}deg {c['bone_at_maximum']} @frame {c.get('frame_at_maximum')}")
 c=read('build-check.json')
 if c:
  drift=[]
  for item in c.get('stationary_foot_lock',[]):
   for key,value in (item.items() if 'Left' not in item else [('stand',item)]):
    if isinstance(value,dict) and 'Left' in value:drift.append(f"{key.replace('moving_','')}:{value['Left']['after_cm']}/{value['Right']['after_cm']}")
  lines.append('foot drift '+' '.join(drift)+' cm (left/right after lock)')
 c=read('seat.json')
 if c:lines.append(f"seat       top={c['top_cm']}cm spread={c['spread_cm']}cm at lateral {c['lateral_cm']} forward {c['forward_cm']} lean_capped={sum(c.get('lean_capped_frames',{}).values())}")
 c=read('tail-check.json')
 if c:lines.append(f"tail       ok={c['ok']} lift_max={c.get('max_lift_deg')}deg verts={c.get('tail_vertices')}")
 c=read('gesture-check.json')
 if c:lines.append(f"gesture    ok={c['ok']} clips={c['clips']} hand travel L/R={c['travel_cm']['LeftHand']}/{c['travel_cm']['RightHand']}cm peak above head L/R={c['left_hand_peak_above_head_cm']}/{c['right_hand_peak_above_head_cm']}cm")
 c=read('drink-check.json')
 if c:lines.append(f"drink      ok={c['ok']} muzzle_to_rim={c['muzzle_to_rim_cm']}cm hand_to_target={c['hand_to_target_cm']}cm hand_to_cup={c['hand_to_cup_cm']}cm nod={c['nod_deg']}deg table_top={c['table_top_cm']}cm")
 c=read('seat-prop-check.json')
 if c and c.get('benches'):lines.append(f"bench prop top={c['top_cm']}cm at {c['location_cm']}")
 c=read('eye-life-check.json')
 if c:lines.append(f"eyes       controls={c['controls']} blinks={c['blinks']} at {c['blink_frames']} max_gaze={c['max_gaze']}")
 c=read('box-camera-check.json')
 if c:lines.append(f"camera     side={c['side']} face_covered={c['covered_samples']}/{c['samples']}")
 c=read('camera-check.json')
 if c:lines.append(f"framing    head_out={c['head_outside_samples']} feet_out={c['feet_outside_samples']}")
 c=read('box-prop-check.json')
 if c and c.get('boxes'):lines.append(f"box prop   phase={c['phase']} stands={c['stands']} end={[round(v) for v in c['end_location_cm']]}")
 return lines

def activity_plan(name,character='lion'):
 """Smallest valid movie for an activity: its test beats in shot 1, an idle second shot (movies need 2+)."""
 import activities
 beat=lambda a,d:dict(action=a,duration=d,dialogue='')
 def shot(title,beats):return dict(version=1,title=title,character=character,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera='full',eye_life=True,segments=[beat(a,d) for a,d in beats],unsupported=[],notes=[])
 return dict(version=1,title=name+' check',unsupported=[],shots=[shot(name,activities.ACTIVITIES[name]['test_beats']),shot('Rest',[('idle',2),('talk',2)])])

def run_all(names,character='lion'):
  """Every named activity in parallel Blender processes; one PASS/FAIL line each from its own checks."""
  import activities,body_measures
  from concurrent.futures import ThreadPoolExecutor
  if not body_measures.load(character):build_shot(activity_plan('sit',character),0,'side',None,False)
  measures=body_measures.load(character);threads=max(1,(os.cpu_count() or 8)//8);results={}
  def one(n):
   verdict=activities.feasibility(n,measures)
   if not verdict.get('ok'):return n,False,'infeasible: '+str(verdict.get('reason'))
   lines=build_shot(activity_plan(n,character),0,'side',None,False,threads);text=chr(10).join(lines)
   if 'FAILED' in lines[0]:return n,False,lines[1].strip()[:110] if len(lines)>1 else 'build failed'
   bad=[l.strip().split()[0] for l in lines if 'ok=False' in l]
   if bad:return n,False,'failed checks: '+', '.join(bad)
   import ast;g=next((l for l in lines if l.strip().startswith('gesture')),None)
   if g:
    clips=ast.literal_eval(g[g.index('['):g.index(']')+1]);played=next((c.split('|')[1].split(' ')[0] for c in clips if 'Idle' not in c and 'Guard' not in c),'?');return n,True,'clip '+played+' '+g[g.index('hand travel'):].strip()
   return n,True,' '.join(l.strip()[:90] for l in lines if l.strip().startswith('drink'))
  with ThreadPoolExecutor(8) as pool:
   return [f"{'PASS' if ok else 'FAIL'} {n}: {detail}" for n,ok,detail in pool.map(one,names)]

def run_activity(args):
 """Instant feasibility from cached body measurements, then a one-shot Blender build with its checks."""
 import activities,body_measures
 name=args.target;character=args.character;started=time.time()
 if name in ('all','gestures'):
  names=[n for n in activities.ACTIVITIES if name=='all' or n in activities.GESTURES];print(chr(10).join(run_all(names,character)))
  print(f'{len(names)} activities in {time.time()-started:.0f}s');return
 measures=body_measures.load(character)
 if not measures:
  print(f'no cached body measurements for {character}; measuring with a sit shot');build_shot(activity_plan('sit',character),0,'side',None,False);measures=body_measures.load(character)
 verdict=activities.feasibility(name,measures)
 print('feasibility '+json.dumps({k:v for k,v in verdict.items() if k not in ('limits',)})+f'  ({time.time()-started:.2f}s)')
 if args.feasibility_only or not verdict.get('ok'):return
 print(chr(10).join(build_shot(activity_plan(name,character),0,args.view,args.frames,not args.no_sheet)))


def shot_inputs(plan,index):
 """Plan.json for one shot as the worker writes it, chaining box state/position/heading from earlier shots."""
 from movie_prompt import validate
 from box_timeline import build,movie_stands
 from character_profiles import profile
 p=validate(plan);carry=profile('lion')['box'];shots=[s['segments'] for s in p['shots']]
 stands=movie_stands(shots,carry) if any(g['action'].startswith('box_') for s in shots for g in s) else None
 state=None;position=[0,0];heading=0
 for segments in shots[:index]:
  if state is None and not any(g['action'].startswith('box_') for g in segments):continue
  result=build(segments,position,state,24,heading,carry,stands);state=result['end_state'];last=result['rows'][-1]
  position=[position[0]+last['root_cm'][0],position[1]+last['root_cm'][1]];heading=last['yaw']
 shot=p['shots'][index];single={k:v for k,v in shot.items() if k!='actors'}
 single.update(motion_heading=index>0 and heading!=0,partner_gaze=None,facing_yaw_deg=heading,actor_position_cm=position,carry_pose=None,box_state=state,box_scene_stands=stands)
 return single

SHEET_SCRIPT=r'''
import bpy,json,sys
from mathutils import Vector
D,out,frames,view=sys.argv[sys.argv.index('--')+1:][:4];frames=[int(f) for f in frames.split(',')]
s=bpy.context.scene
import os
traj=json.load(open(D+'/box-trajectory.json')) if os.path.exists(D+'/box-trajectory.json') else None
if traj:
 w,d,h=traj['size_cm'];bpy.ops.mesh.primitive_cube_add(size=1);box=bpy.context.object;box.scale=(w/100,d/100,h/100)
 m=bpy.data.materials.new('box');m.diffuse_color=(.55,.3,.12,1);box.data.materials.append(m)
 for r in traj['rows']:l=r['local_cm'];box.location=(l[0]/100,-l[1]/100,l[2]/100);box.keyframe_insert('location',frame=r['frame']+1)
rig=next(o for o in s.objects if o.type=='ARMATURE')
if os.path.exists(D+'/seat.json') and os.path.exists(D+'/route.json'):
 # Bench proxy: fixed in the world; the rig stays at the origin, so it moves opposite to the root.
 seat=json.load(open(D+'/seat.json'));route=json.load(open(D+'/route.json'));at=route[seat['frame']]['location_cm']
 bpy.ops.mesh.primitive_cube_add(size=1);bench=bpy.context.object;bench.name='Cube_bench';bench.scale=(.7,.32,seat['top_cm']/100)
 m=bpy.data.materials.new('bench');m.diffuse_color=(.35,.22,.1,1);bench.data.materials.append(m)
 for r in route:
  dy=(r['location_cm'][1]-at[1])/100;bench.location=(seat['lateral_cm']/100,-(seat['forward_cm']-3)/100+dy,seat['top_cm']/200);bench.keyframe_insert('location',frame=r['frame']+1)
if os.path.exists(D+'/drink.json'):
 # Table and cup proxies in rig space (cm -> m, forward is -Y; the rig stays at the origin).
 d=json.load(open(D+'/drink.json'));tb=d['table'];top=tb['top_cm']/100;th=tb['thickness_cm']/100
 bpy.ops.mesh.primitive_cube_add(size=1);table=bpy.context.object;table.name='Cube_table';table.scale=(tb['size_cm'][0]/100,tb['size_cm'][1]/100,th);table.location=(tb['center'][0]/100,tb['center'][1]/100,top-th/2)
 bpy.ops.mesh.primitive_cylinder_add(radius=d['cup']['radius_cm']/100,depth=d['cup']['height_cm']/100);cup=bpy.context.object;cup.name='Cube_cup';cup.location=(d['cup_cm'][0]/100,d['cup_cm'][1]/100,d['cup_cm'][2]/100)
for o in s.objects:
 if o.type=='MESH' and o.parent is None and not any(m.type=='ARMATURE' for m in o.modifiers) and not o.name.startswith('Cube'):o.hide_render=True
cam=bpy.data.objects.new('Q',bpy.data.cameras.new('Q'));s.collection.objects.link(cam);s.camera=cam;cam.data.lens=35
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='RANDOM' if view=='face' else 'MATERIAL';s.render.resolution_x=300;s.render.resolution_y=360
for i,f in enumerate(frames):
 s.frame_set(f)
 if view=='face':
  # Follow the head: eyes sit ~33cm ahead of and 20cm above the head bone at rest.
  head=next(b for b in rig.pose.bones if b.name.endswith('Head'));turn=(rig.matrix_world@head.matrix).to_quaternion()@head.bone.matrix_local.to_quaternion().inverted()@rig.matrix_world.to_quaternion().inverted();aim=rig.matrix_world@head.head+turn@Vector((0,-.335,.2));cam.location=aim+turn@Vector((.06,-1.2,.03));cam.data.lens=120
 else:cam.location=(2.6,-0.6,1.1);aim=Vector((0,-.35,.85))
 cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=out+'/b_%04d.png'%f;bpy.ops.render.render(write_still=True)
'''

def tile(paths,target,labels,width=480):
 from PIL import Image,ImageDraw
 images=[Image.open(p).convert('RGB') for p in paths];height=round(width*images[0].height/images[0].width);columns=min(4,len(images));rows=math.ceil(len(images)/columns)
 sheet=Image.new('RGB',(columns*width,rows*height),'white')
 for i,(image,label) in enumerate(zip(images,labels)):
  image=image.resize((width,height));ImageDraw.Draw(image).text((6,4),label,fill=(255,255,0));sheet.paste(image,((i%columns)*width,(i//columns)*height))
 sheet.save(target);return target

def build_shot(plan,index,view='side',frames=None,sheet=True,threads=6):
 """Blender-only build of one shot; returns printable lines (summary + sheet path)."""
 folder=OUT/f'shot{index+1}_{plan["shots"][index].get("title","").replace(" ","_")[:12]}_{time.strftime("%H%M%S")}_{os.getpid()}';folder.mkdir(parents=True,exist_ok=True)
 (folder/'plan.json').write_text(json.dumps(shot_inputs(plan,index)))
 started=time.time();log=folder/'build.log'
 with open(log,'w') as handle:code=subprocess.call([BLENDER,'-b','-t',str(threads),'--python-exit-code','1','-P',str(H/'build_prompt_scene_blender.py'),'--',str(folder)],stdout=handle,stderr=subprocess.STDOUT)
 lines=[f'shot {index+1}: blender build {"ok" if code==0 else "FAILED"} in {time.time()-started:.0f}s']
 if code:lines.append('  '+next((l.strip() for l in reversed(log.read_text(errors='ignore').splitlines()) if 'Error' in l and 'script failed' not in l),'see '+str(log)))
 title=plan['shots'][index].get('title');import activities
 if code==0 and title in activities.GESTURES:
  beats=activities.ACTIVITIES[title]['test_beats'];start=sum(d for a,d in beats[:[a for a,d in beats].index(title)])
  subprocess.call([BLENDER,'-b',str(folder/'scene.blend'),'--python',str(H/'gesture_check.py'),'--',str(folder),str(start),str(start+dict(beats)[title])],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 lines+=['  '+line for line in summary(folder)]
 if not sheet or not (folder/'scene.blend').exists():return lines
 eyes=folder/'eye-life-check.json'
 if view=='face' and not frames and eyes.exists():frames=','.join(str(s+1+k) for s in json.loads(eyes.read_text())['blink_frames'][:3] for k in (-4,3))
 frames=frames or ','.join(str(round(f)) for f in (lambda n:[n*k/6+1 for k in range(6)])(round(sum(g['duration'] for g in plan['shots'][index]['segments'])*24)-1))
 script=folder/'sheet.py';script.write_text(SHEET_SCRIPT)
 subprocess.call([BLENDER,'-b',str(folder/'scene.blend'),'--python',str(script),'--',str(folder),str(folder),frames,view],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 shots=sorted(folder.glob('b_*.png'))
 if shots:lines.append('  sheet: '+str(tile(shots,folder/'sheet.png',['frame '+p.stem[2:].lstrip('0') for p in shots],300)))
 return lines
def run_shot(args):
 """One shot, or every shot of the plan in parallel Blender processes ('all')."""
 plan=load_plan(args.plan);started=time.time()
 if args.target=='all':
  from concurrent.futures import ThreadPoolExecutor
  count=len(plan['shots']);threads=max(2,(os.cpu_count() or 8)//count)
  with ThreadPoolExecutor(count) as pool:results=list(pool.map(lambda i:build_shot(plan,i,args.view,None,not args.no_sheet,threads),range(count)))
  for lines in results:print(chr(10).join(lines))
  print(f'all {count} shots in {time.time()-started:.0f}s')
 else:print(chr(10).join(build_shot(plan,int(args.target or 1)-1,args.view,args.frames,not args.no_sheet)))

def capture(movie_id,frames,folder):
 master=json.loads((H/'movie_jobs'/movie_id/'master-result.json').read_text())
 project=Path(post(BRIDGE+'/',{'command':'production_info','params':{}})['result']['project'])/'Saved'/'Screenshots'
 # Editor-only icons, volumes and selection outlines would cover the character.
 for flag in ('BillboardSprites','Volumes','Selection','Bounds'):post(BRIDGE+'/',{'command':'console_command','params':{'command':f'ShowFlag.{flag} 0'}})
 paths=[]
 for frame in frames:
  post(BRIDGE+'/',{'command':'preview_sequence_frame','params':{'sequence_path':master['sequence'],'frame':frame}});time.sleep(2)
  before=set(project.rglob('*.png')) if project.exists() else set()
  post(BRIDGE+'/',{'command':'console_command','params':{'command':'HighResShot 640x360'}})
  for _ in range(30):
   new=(set(project.rglob('*.png')) if project.exists() else set())-before
   if new:break
   time.sleep(.5)
  if not new:print(f'  frame {frame}: no screenshot');continue
  time.sleep(.5);target=folder/f'ue_{frame:04d}.png';target.write_bytes(max(new,key=lambda p:p.stat().st_mtime).read_bytes());paths.append(target)
 return tile(paths,folder/'sheet.png',['frame '+p.stem[3:].lstrip('0') for p in paths]) if paths else None

def default_frames(plan):
 """Middle and ends of every shot on the master timeline."""
 frames=[];start=0
 for shot in plan['shots']:
  length=round(sum(g['duration'] for g in shot['segments'])*24);frames+=[start+round(length*k) for k in (.2,.5,.85)];start+=length
 return frames

def run_movie(args):
 plan=load_plan(args.plan);started=time.time()
 job=post(STUDIO+'/api/movie-pipeline',{'plan':plan,'render':False});stage=None
 while True:
  job=get(STUDIO+'/api/jobs/'+job['id'])
  if job.get('stage')!=stage:stage=job.get('stage');print(f"  {time.time()-started:4.0f}s {stage}",flush=True)
  if job['status'] in ('complete','failed','ready'):break
  time.sleep(2)
 print(f"movie {job['status']} in {time.time()-started:.0f}s")
 if job['status']=='failed':print('  '+job.get('error',''));return
 report(job['movie_id'],args.frames and [int(f) for f in args.frames.split(',')] or default_frames(plan))

def report(movie_id,frames):
 folder=OUT/f'movie_{movie_id[:8]}';folder.mkdir(parents=True,exist_ok=True);ready=json.loads((H/'movie_jobs'/movie_id/'ready.json').read_text())
 for shot in ready['shots']:
  print(shot['title']);[print('  '+line) for line in summary(H/'scene_jobs'/shot['scene_id'])]
 sheet=capture(movie_id,frames,folder)
 if sheet:print('sheet: '+str(sheet))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 parser.add_argument('mode',choices=['shot','movie','frames','activity']);parser.add_argument('target',nargs='?');parser.add_argument('frame_list',nargs='?')
 parser.add_argument('--plan',default='test_box_movie:PLAN');parser.add_argument('--frames');parser.add_argument('--view',choices=['side','face'],default='side');parser.add_argument('--no-sheet',action='store_true');parser.add_argument('--character',default='lion');parser.add_argument('--feasibility-only',action='store_true')
 args=parser.parse_args();sys.path.insert(0,str(H))
 if args.mode=='shot':run_shot(args)
 elif args.mode=='activity':run_activity(args)
 elif args.mode=='movie':run_movie(args)
 else:report(args.target,[int(f) for f in (args.frame_list or args.frames).split(',')])
