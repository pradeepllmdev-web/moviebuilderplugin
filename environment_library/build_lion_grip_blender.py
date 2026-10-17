"""Stationary object-led two-arm IK test. No facial/body overlays or geometry logs."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-grip-ik';D.mkdir(exist_ok=True)
P=H.parent/'blendplugin-next/scene_pipeline';sys.path.insert(0,str(P))
from realistic_rig import build_nla
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-single-run/scene.blend'))
s=bpy.context.scene;s.frame_end=192;s.render.fps=24
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False)
rig.animation_data_clear()
bpy.context.view_layer.objects.active=rig;rig.hide_set(False);rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for side in ('Left','Right'):
 for part,child in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:
  a=next(b for b in rig.data.edit_bones if b.name.endswith(side+part));b=next(b for b in rig.data.edit_bones if b.name.endswith(side+child))
  if (a.head-b.head).length>.01:a.tail=b.head.copy()
 hand=next(b for b in rig.data.edit_bones if b.name.endswith(side+'Hand'));fore=next(b for b in rig.data.edit_bones if b.name.endswith(side+'ForeArm'))
 hand.tail=hand.head+(hand.head-fore.head).normalized()*10
bpy.ops.object.mode_set(mode='OBJECT')
for bone in rig.pose.bones:
 for c in list(bone.constraints):bone.constraints.remove(c)
 bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion();bone.location=(0,0,0);bone.scale=(1,1,1)
catalog=json.loads((H/'samples/lion-single-run/catalog.json').read_text());info=catalog['Leo']
rig.location=(0,0,0);rig.rotation_mode='XYZ';rig.rotation_euler.z=rig['base_yaw']
actor=dict(name='Leo',segments=[dict(action='idle',start=0,end=8,**{'from':[0,0,0],'to':[0,0,0]},yaw_start=0,yaw_end=0,intensity=.2)])
rig.animation_data_create();build_nla(rig,info,actor,24,[],s.camera);s.frame_set(1);bpy.context.view_layer.update()
baseline={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=baseline[b.name]
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for k in obj.data.shape_keys.key_blocks:k.value=0
def bone(part):return next(b for b in rig.pose.bones if b.name.endswith(part))
def empty(name,pos):
 o=bpy.data.objects.new(name,None);s.collection.objects.link(o);o.location=pos;return o
bpy.context.view_layer.update()
targets={};initial={}
for side,sign in [('Left',1),('Right',-1)]:
 hand=bone(side+'Hand');initial[side]=rig.matrix_world@hand.head
 target=empty('Grip '+side,initial[side]);targets[side]=target
 forearm=bone(side+'ForeArm');ik=forearm.constraints.new('IK');ik.target=target;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
 pole=empty('Elbow '+side,Vector((sign*.9,-.1,.8)));ik.pole_angle=0
 foot=bone(side+'Foot');anchor=empty('Planted '+side,rig.matrix_world@foot.head)
 leg=bone(side+'Leg');constraint=leg.constraints.new('IK');constraint.target=anchor;constraint.chain_count=2;constraint.use_stretch=False
hips=bone('Hips');hip_initial=hips.location.copy();hip_world_rotation=(rig.matrix_world.to_quaternion()@hips.bone.matrix_local.to_quaternion())
def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
branch=[];errors=[]
for f in range(1,193):
 t=(f-1)/24
 lift=ease((t-2)/2)*(1-ease((t-5)/2))
 crouch=(1-lift)*ease(t/1.5)*(1-ease((t-7)/1))
 hips.location=hip_initial+hip_world_rotation.inverted()@Vector((0,0,-.45*crouch))/rig.matrix_world.to_scale().z
 hips.keyframe_insert('location',frame=f)
 z=.28+.67*lift;center=Vector((0,-.40,z));row={'frame':f-1,'position':list(center),'grips':{}}
 for side,sign in [('Left',1),('Right',-1)]:
  grip=center+Vector((sign*.28,0,.04));weight=ease(t/1.8)*(1-ease((t-7)/.8))
  targets[side].location=initial[side].lerp(grip,weight);targets[side].keyframe_insert('location',frame=f)
  row['grips'][side]=list(grip)
 branch.append(row)
 s.frame_set(f);bpy.context.view_layer.update()
 desired={side:initial[side].lerp(center+Vector((sign*.28,0,.04)),weight) for side,sign in [('Left',1),('Right',-1)]}
 if 48<=f<=168:
  for side in ('Left','Right'):errors.append(((rig.matrix_world@bone(side+'Hand').head)-desired[side]).length)
 if f==96:(D/'debug.json').write_text(json.dumps({side:{'hand':list(rig.matrix_world@bone(side+'Hand').head),'target':list(targets[side].location),'arm':list(rig.matrix_world@bone(side+'Arm').head),'tail':list(rig.matrix_world@bone(side+'Hand').tail),'forearm_tail':list(rig.matrix_world@bone(side+'ForeArm').tail),'scale':list(rig.scale)} for side in ('Left','Right')}))
# Bake IK to the character action; export must not depend on external targets.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=1,frame_end=192,step=1,only_selected=True,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
camera=s.camera
if camera.animation_data:camera.animation_data_clear()
camera.location=(2.2,-4,1.6);camera.rotation_euler=(Vector((0,-.3,.8))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=40
plan=dict(title='Leo — fixed grip IK test',scene_type='motion',duration=8,fps=24,floor_size=[24,24],actors=[actor],obstacles=[],camera=dict(offset=[2.2,-4,1.6],lens_mm=40),lighting='day',set='field',lines=[])
(D/'scene.json').write_text(json.dumps(plan));(D/'catalog.json').write_text(json.dumps(catalog));(D/'branch-path.json').write_text(json.dumps(branch))
(D/'ik-check.json').write_text(json.dumps({'max_wrist_target_error_cm':max(errors)*100,'mean_error_cm':sum(errors)/len(errors)*100,'samples':len(errors),'finger_bones':sum('finger' in b.name.lower() or 'thumb' in b.name.lower() for b in rig.pose.bones)}))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))





