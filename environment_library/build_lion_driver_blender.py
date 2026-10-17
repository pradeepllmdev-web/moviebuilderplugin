import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-fire-drive';D.mkdir(exist_ok=True);sys.path.insert(0,str(H.parent/'blendplugin-next/scene_pipeline'))
from realistic_rig import build_nla
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-grip-ik/scene.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
for bone in rig.pose.bones:
 for c in list(bone.constraints):bone.constraints.remove(c)
 bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion();bone.location=(0,0,0);bone.scale=(1,1,1)
rig.location=(0,0,0)
s=bpy.context.scene;s.frame_end=288;s.render.fps=24
catalog=json.loads((H/'samples/lion-grip-ik/catalog.json').read_text());info=catalog['Leo'];info['motion_defaults']['pilot']='Sit_Idle'
actor=dict(name='Leo',segments=[dict(action='pilot',start=0,end=12,**{'from':[0,0,0],'to':[0,0,0]},yaw_start=0,yaw_end=0,intensity=.2)])
warnings=[];build_nla(rig,info,actor,24,warnings,s.camera);s.frame_set(1);bpy.context.view_layer.update()
baseline={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=baseline[b.name]
for side,sign in [('Left',1),('Right',-1)]:
 fore=next(b for b in rig.pose.bones if b.name.endswith(side+'ForeArm'))
 target=bpy.data.objects.new('Wheel Grip '+side,None);s.collection.objects.link(target);target.location=(sign*.24,-.55,1.05)
 constraint=fore.constraints.new('IK');constraint.target=target;constraint.chain_count=2;constraint.use_stretch=False;constraint.iterations=128
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for key in obj.data.shape_keys.key_blocks:key.value=0
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=1,frame_end=288,step=1,only_selected=True,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
camera=s.camera;camera.animation_data_clear();camera.data.animation_data_clear();camera.location=(2,-4,2);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=40
plan=dict(title='Leo — Through the Fire',scene_type='motion',duration=12,fps=24,floor_size=[24,24],actors=[actor],obstacles=[],camera=dict(offset=[2,-4,2],lens_mm=40),lighting='day',set='field',lines=[])
(D/'scene.json').write_text(json.dumps(plan));(D/'catalog.json').write_text(json.dumps(catalog));(D/'driver-check.json').write_text(json.dumps({'warnings':warnings,'blink_disabled':True}))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
