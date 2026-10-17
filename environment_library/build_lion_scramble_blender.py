"""Short stepped-rock scramble, with planted feet and one side support."""
import bpy,sys,json,math,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-scramble';D.mkdir(exist_ok=True);sys.path.insert(0,str(H.parent/'blendplugin-next/scene_pipeline'))
from realistic_rig import build_nla
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-grip-ik/scene.blend'));s=bpy.context.scene;s.frame_end=192;s.render.fps=24
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False);rig.hide_viewport=False;rig.animation_data_clear();rig.animation_data_create()
for b in rig.pose.bones:
 for c in list(b.constraints):b.constraints.remove(c)
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
catalog=json.loads((H/'samples/lion-grip-ik/catalog.json').read_text());info=catalog['Leo'];info['motion_defaults']['walk']='Walking';actor=dict(name='Leo',segments=[dict(action='walk',start=0,end=8,**{'from':[0,0,0],'to':[0,0,0]},yaw_start=0,yaw_end=0,intensity=.3)])
warnings=[];build_nla(rig,info,actor,24,warnings,s.camera)
def bone(part):return next(b for b in rig.pose.bones if b.name.endswith(part))
def ease(u):u=max(0,min(1,u));return u*u*(3-2*u)
def foot(side,t,arc=True):
 left=side=='Left';pos=Vector((.17 if left else -.17,.495 if left else .605,.10))
 steps=[(.3,1.,-.25,.1),(2.,2.7,.35,.22),(4.,4.7,1.05,.34),(6.,6.7,1.75,.46)] if left else [(1.,1.7,-.05,.1),(3.,3.7,.55,.22),(5.,5.7,1.25,.34),(7.,7.7,1.95,.46)]
 for start,end,y,z in steps:
  target=Vector((pos.x,-y*.55,z))
  if t<start:return pos
  if t<end:
   u=ease((t-start)/(end-start));p=pos.lerp(target,u)
   if arc:p.z+=.14*math.sin(math.pi*u)
   return p
  pos=target
 return pos
roots=[];paths={'Left':[],'Right':[]};free_hand=[];hips=bone('Hips');hip_delta=hips.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-.16))/rig.matrix_world.to_scale().z
head=bone('Head')
for f in range(1,193):
 t=(f-1)/24;l=foot('Left',t,False);r=foot('Right',t,False);root=Vector((0,(l.y+r.y)/2,(l.z+r.z)/2-.1));roots.append(list(root));rig.location=root;rig.keyframe_insert('location',frame=f);hips.location=hip_delta;hips.keyframe_insert('location',frame=f)
 for side in paths:paths[side].append(foot(side,t))
 s.frame_set(f);bpy.context.view_layer.update();free_hand.append(rig.matrix_world@bone('LeftHand').head)
targets={}
for side in paths:
 target=bpy.data.objects.new('Planted '+side,None);s.collection.objects.link(target);targets[side]=target;ik=bone(side+'Leg').constraints.new('IK');ik.target=target;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
support=bpy.data.objects.new('Side support grip',None);s.collection.objects.link(support);ik=bone('LeftForeArm').constraints.new('IK');ik.target=support;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
errors=[];hand_errors=[];foot_errors=[];worst={};clearance=[];target_keys=[]
for f in range(1,193):
 t=(f-1)/24;s.frame_set(f)
 for side in paths:targets[side].location=paths[side][f-1]
 blend=ease((t-2.5)/.5)*(1-ease((t-4.)/.5));support.location=free_hand[f-1].lerp(Vector((.40,-.40,.90)),blend)
 for target in list(targets.values())+[support]:target.update_tag()
 rig.update_tag();bpy.context.view_layer.update()
 for side in paths:
  value=(rig.matrix_world@bone(side+'Foot').head-paths[side][f-1]).length;errors.append(value);foot_errors.append(value)
  if value>worst.get('error',0):worst={'error':value,'frame':f,'side':side,'hip':list(rig.matrix_world@bone(side+'UpLeg').head),'ankle':list(paths[side][f-1]),'lengths':[bone(side+'UpLeg').length*.01,bone(side+'Leg').length*.01]}
 if blend>.95:
  value=(rig.matrix_world@bone('LeftHand').head-support.location).length;errors.append(value);hand_errors.append(value)
 h=rig.matrix_world@head.head;surface=.36 if -h.y>.77 else .24 if -h.y>.41 else .12 if -h.y>.08 else 0;clearance.append(h.z-.30-surface)
 for side in paths:target_keys.append((targets[side],f,paths[side][f-1].copy()))
 target_keys.append((support,f,support.location.copy()))
for target,f,pos in target_keys:target.location=pos;target.keyframe_insert('location',frame=f)
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for k in obj.data.shape_keys.key_blocks:k.value=0
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=1,frame_end=192,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
for track in rig.animation_data.nla_tracks:track.mute=True
rig.location=(0,0,0)
camera=s.camera;camera.animation_data_clear();camera.data.animation_data_clear();camera.location=(3,-3,2);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=40
plan=dict(title='Leo — Boulder Scramble',scene_type='motion',duration=8,fps=24,floor_size=[24,24],actors=[actor],obstacles=[],camera=dict(offset=[3,-3,2],lens_mm=40),lighting='day',set='field',lines=[])
(D/'scene.json').write_text(json.dumps(plan));(D/'catalog.json').write_text(json.dumps(catalog));(D/'route.json').write_text(json.dumps({'root':roots,'feet':{n:[list(v) for v in p] for n,p in paths.items()}}));(D/'clearance-check.json').write_text(json.dumps({'max_contact_joint_error_cm':max(errors)*100,'mean_error_cm':sum(errors)/len(errors)*100,'minimum_head_envelope_above_route_cm':min(clearance)*100,'head_envelope_radius_cm':30,'model':'stepped heightfield; side support checked visually','warnings':warnings,'worst':worst,'foot_max_cm':max(foot_errors)*100,'support_hand_max_cm':max(hand_errors)*100}))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))

