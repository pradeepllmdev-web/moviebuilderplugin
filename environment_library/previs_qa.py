"""Blender script: check a built previs with real geometry and fix what it can, camera first.

blender -b previs.blend --python previs_qa.py -- spec.json [--verify]

For every shot (the merged scene has one camera per shot, Cam<k> aimed at Aim<k>):
  * candidate cameras around the actors (angle x distance x height, following the actors if they walk) are scored on real geometry:
      - actors inside the frame (head, hips and feet projected through the lens, with a margin) and of a sensible size for the shot type
      - nothing solid between the lens and the actors' heads and chests (Blender ray casts; small props are ignored)
      - the camera is not inside or against a wall, tree or rock (ray casts in 8 directions)
      - faces are visible (camera in front of each actor's facing; two actors facing each other are seen side on)
  * the best candidate is written back as keyframes, so the saved previs.blend already has the fixed cameras
  * actors are tested against walls and other solid scenery (body points inside their boxes) and reported
--verify only measures the current cameras. Writes qa.json next to the spec: per shot {camera, issues, metrics}.
Scenery = objects that are not under a Slot_* empty; actors = everything under one."""
import bpy,json,math,sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
args=sys.argv[sys.argv.index('--')+1:];spec=json.load(open(args[0]));verify='--verify' in args
scene=bpy.context.scene;fps=spec.get('fps',24)
bpy.context.view_layer.update()   # objects created by the merge script have stale world matrices until the depsgraph runs
IGNORE=('Ground','Bench','DrinkTable','TableLeg','Cup','Paw','Cub','Step','Crate','SideTable','Phone','Door','Lamp','Window','Awning','CafeSign')   # small or see-through: never judged as occluders
SOLID_NAMES=('DoorWall','Hut','Patio','Pole','Mountain','Snow','Pine','Trunk','House','Roof','Rock','Fence','Well','Counter')
TYPES={'full':dict(lens=28,radii=(300,380,460,560,680),heights=(130,170,220),fraction=(.30,.62)),
 'medium':dict(lens=34,radii=(190,240,300,360),heights=(120,150,185),fraction=(.28,.60)),
 'close':dict(lens=45,radii=(130,170,210),heights=(110,135,160),fraction=(.40,.80)),
 'reaction':dict(lens=45,radii=(130,170,210),heights=(110,135,160),fraction=(.40,.80))}
def actor_objects(slot):
 out=set();stack=[slot]
 while stack:
  o=stack.pop();out.add(o.name);stack.extend(o.children)
 return out
slots=sorted([o for o in scene.objects if o.name.startswith('Slot_')],key=lambda o:int(o.name.split('_')[1]))
shot_slots=[];index=0
for shot in spec['shots']:
 shot_slots.append(slots[index:index+len(shot['actors'])]);index+=len(shot['actors'])
actor_names=set().union(*[actor_objects(s) for s in slots]) if slots else set()
solids=[o for o in scene.objects if o.type=='MESH' and o.name not in actor_names and o.name.startswith(SOLID_NAMES) and not o.hide_viewport]
def aabb(o):
 """World box (x0,y0,z0,x1,y1,z1) of an unparented prop from its location, scale and yaw. Props are hidden outside their shots, and hidden
 objects keep stale matrices, so the transform is read directly."""
 import math as m
 sx,sy,sz=o.scale.x/2,o.scale.y/2,o.scale.z/2
 if abs(round(m.degrees(o.rotation_euler.z))%180-90)<1:sx,sy=sy,sx
 c=o.location;return (c.x-sx,c.y-sy,c.z-sz,c.x+sx,c.y+sy,c.z+sz)
rooms=[]
for o in scene.objects:
 if o.name.startswith('HutFloor'):
  b=aabb(o);rooms.append((b[0],b[1],b[3],b[4]))
def room_of(p,margin=0.):
 """Index of the room (HutFloor footprint) containing a point, or None when outside every room."""
 for i,(x0,y0,x1,y1) in enumerate(rooms):
  if x0-margin<p.x<x1+margin and y0-margin<p.y<y1+margin:return i
 return None
def keypoints(slot,frame):
 """Head, hips, feet of the actor under this slot at a frame, world metres, plus facing."""
 scene.frame_set(frame);rig=next((o for o in actor_objects_list(slot) if o.type=='ARMATURE'),None)
 pts={}
 for name,key in (('Head','head'),('Hips','hips'),('LeftFoot','lf'),('RightFoot','rf'),('Spine2','chest'),('LeftHand','lh'),('RightHand','rh')):
  b=next((b for b in rig.pose.bones if b.name.endswith(name)),None)
  if b:pts[key]=rig.matrix_world@b.head
 rz=slot.matrix_world.to_euler().z;facing=Vector((math.sin(rz),-math.cos(rz),0))
 return pts,facing
_cache={}
def actor_objects_list(slot):
 if slot.name not in _cache:_cache[slot.name]=[o for o in scene.objects if o.name in actor_objects(slot)]
 return _cache[slot.name]
def place_camera(cam,position,target,lens):
 cam.location=position;cam.data.lens=lens
 direction=target-position;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
def raycast(origin,point):
 direction=point-origin;distance=direction.length
 if distance<.05:return None
 hit,location,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction.normalized(),distance=distance-.08)
 return obj if hit and obj and obj.name not in actor_names and not obj.name.startswith(IGNORE) else None
def inside_geometry(position):
 """Distance (m) to the nearest solid within 0.9 m around the camera, or None."""
 nearest=None
 for k in range(8):
  a=k*math.pi/4;hit,loc,normal,i,obj,m=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),position,Vector((math.cos(a),math.sin(a),0)),distance=.9)
  if hit and obj and not obj.name.startswith(IGNORE) and obj.name not in actor_names:
   d=(loc-position).length;nearest=d if nearest is None else min(nearest,d)
 return nearest
def evaluate(cam,shot_k,shot,offset,lens,frames,kind,state):
 """Cost and issue list of one candidate camera offset (metres, relative to the actors' focus point) over sample frames."""
 cost=0.;issues=set();spec_t=TYPES[kind]
 for f in frames:
  actors=[keypoints(s,f) for s in shot_slots[shot_k]];hips=[a[0]['hips'] for a in actors];focus=sum(hips,Vector())/len(hips);focus.z=1.0 if len(actors)==1 else 1.1
  position=focus+Vector(offset);position.z=offset[2]
  if position.z<.5:return 1e9,{'below ground'}
  if room_of(position,.35)!=room_of(focus):return 1e9,{'camera in the other room'}   # camera and actors share the same space: all inside a room or all outside
  place_camera(cam,position,focus,lens);off=0;occl=0;sizes=[]
  for pts,facing in actors:
   for key in ('head','hips','lf','rf') if kind=='full' else ('head','chest'):
    p=pts.get(key)
    if p is None:continue
    v=world_to_camera_view(scene,cam,p)
    if v.z<=0 or not(.05<v.x<.95 and .04<v.y<.96):off+=1
   head,foot=pts['head'],(pts.get('lf') or pts['hips'])
   vh,vf=world_to_camera_view(scene,cam,head),world_to_camera_view(scene,cam,foot if kind=='full' else pts['hips'])
   sizes.append(abs(vh.y-vf.y))
   d=(position-pts['hips']);d.z=0
   if d.length>1e-3:
    d.normalize();face=facing.dot(d)
    if len(actors)==2:   # two actors: see them side on, not along the line between them
     other=[x[0]['hips'] for x in actors if x[0] is not pts][0]-pts['hips'];other.z=0
     if other.length>1e-3:
      along=abs(d.dot(other.normalized()))
      if along>.55:cost+=6*(along-.55)
    cost+=0 if face>.15 else 40*(.15-face)
    if face<-.2:issues.add('seen from behind')
  if off:cost+=100*off;issues.add('actor out of frame')
  lo,hi=spec_t['fraction'];frac=max(sizes)
  if frac<lo:cost+=60*(lo-frac);issues.add('actor too small')
  if frac>hi:cost+=60*(frac-hi);issues.add('actor too large')
  if off:continue
  for pts,facing in actors:
   for key in ('head','chest'):
    p=pts.get(key)
    if p is not None and raycast(position,p):occl+=1
  if occl:cost+=80*occl;issues.add('view blocked by scenery')
  near=inside_geometry(position)
  if near is not None:cost+=150*(.9-near)/.9+60;issues.add('camera against scenery')
  if shot.get('camera_dist'):pass
 return cost/len(frames),issues
def collisions(shot_k,frames):
 """Body points inside solid scenery boxes."""
 found=set()
 for f in frames:
  for slot in shot_slots[shot_k]:
   pts,facing=keypoints(slot,f)
   for key,p in pts.items():
    for o in solids:
     b=aabb(o);lo=Vector(b[:3]);hi=Vector(b[3:])
     if lo.x+.05<p.x<hi.x-.05 and lo.y+.05<p.y<hi.y-.05 and lo.z<p.z<hi.z:found.add(f'{slot.name} {key} inside {o.name}')
 return sorted(found)
report=[]
for k,shot in enumerate(spec['shots']):
 cam=scene.objects.get('Cam%d'%k);aim=scene.objects.get('Aim%d'%k)
 if cam is None:continue
 start,length=shot['start'],shot['length'];frames=[start+round((length-1)*u) for u in (.1,.5,.9)];kind=shot.get('kind') or ('close' if shot.get('label','').lower().startswith('close') else 'full')
 kind=shot.get('camera_kind',kind);t=TYPES.get(kind,TYPES['full'])
 best=None
 if verify:
  cost,issues=0,set()
  report.append(dict(shot=k+1,label=shot['label'],kind=kind,issues=sorted(issues),collisions=collisions(k,frames)));continue
 for angle in range(0,360,15):
  for radius in t['radii']:
   for height in t['heights']:
    offset=(math.cos(math.radians(angle))*radius/100,math.sin(math.radians(angle))*radius/100,height/100)
    cost,issues=evaluate(cam,k,shot,offset,t['lens'],frames,kind,None)
    if best is None or cost<best[0]:best=(cost,offset,issues)
    if cost<2:break
 cost,offset,issues=best
 # write the chosen camera as keyframes that follow the actors
 for obj in (cam,aim):
  obj.animation_data_clear()
 step=max(1,length//12)
 for f in list(range(start,start+length,step))+[start+length-1]:
  scene.frame_set(f);hips=[keypoints(s,f)[0]['hips'] for s in shot_slots[k]];focus=sum(hips,Vector())/len(hips);focus.z=1.0 if len(hips)==1 else 1.1
  aim.location=focus;aim.keyframe_insert('location',frame=f);cam.location=Vector((focus.x+offset[0],focus.y+offset[1],offset[2]));cam.keyframe_insert('location',frame=f)
 cam.data.lens=t['lens']
 for obj in (cam,aim):
  if obj.animation_data and obj.animation_data.action:
   action=obj.animation_data.action
   curves=list(action.fcurves) if hasattr(action,'fcurves') else [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
   for fc in curves:
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 report.append(dict(shot=k+1,label=shot['label'],kind=kind,cost=round(cost,1),offset_m=[round(v,2) for v in offset],lens=t['lens'],issues=sorted(issues),collisions=collisions(k,frames)))
scene.frame_set(1)
if not verify:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
json.dump(report,open(args[0].replace('spec.json','qa.json'),'w'),indent=1)
print('QA_DONE',len(report))
