"""Fast iteration loop: one command builds, prints every check on a few lines, and saves one picture.

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
 folder=OUT/f'shot{index+1}_{time.strftime("%H%M%S")}_{os.getpid()}';folder.mkdir(parents=True)
 (folder/'plan.json').write_text(json.dumps(shot_inputs(plan,index)))
 started=time.time();log=folder/'build.log'
 with open(log,'w') as handle:code=subprocess.call([BLENDER,'-b','-t',str(threads),'--python-exit-code','1','-P',str(H/'build_prompt_scene_blender.py'),'--',str(folder)],stdout=handle,stderr=subprocess.STDOUT)
 lines=[f'shot {index+1}: blender build {"ok" if code==0 else "FAILED"} in {time.time()-started:.0f}s']
 if code:lines.append('  '+next((l.strip() for l in reversed(log.read_text(errors='ignore').splitlines()) if 'Error' in l and 'script failed' not in l),'see '+str(log)))
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
 parser.add_argument('mode',choices=['shot','movie','frames']);parser.add_argument('target',nargs='?');parser.add_argument('frame_list',nargs='?')
 parser.add_argument('--plan',default='test_box_movie:PLAN');parser.add_argument('--frames');parser.add_argument('--view',choices=['side','face'],default='side');parser.add_argument('--no-sheet',action='store_true')
 args=parser.parse_args();sys.path.insert(0,str(H))
 if args.mode=='shot':run_shot(args)
 elif args.mode=='movie':run_movie(args)
 else:report(args.target,[int(f) for f in (args.frame_list or args.frames).split(',')])
