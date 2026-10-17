"""Synthetic rig test: final attention continuity must not change the limbs."""
import bpy,json,sys,tempfile,math
from pathlib import Path
from mathutils import Quaternion
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'environment_library'))
from pose_continuity import blend_previous_pose
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.object.armature_add();rig=bpy.context.object
bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones[0].name='Head';bone=rig.data.edit_bones.new('Arm');bone.head=(1,0,0);bone.tail=(1,0,1);bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene;scene.frame_end=12
for bone in rig.pose.bones:
 bone.rotation_mode='QUATERNION'
 for frame in [1,12]:bone.rotation_quaternion=Quaternion((0,0,1),.7);bone.keyframe_insert('rotation_quaternion',frame=frame)
scratch=root/'.verification/head-continuity';scratch.mkdir(parents=True,exist_ok=True);path=scratch/'pose.json';path.write_text(json.dumps({'Head':{'rotation':[1,0,0,0],'location':[0,0,0]}}))
blend_previous_pose(scene,rig,path,24,bone_names={'Head'});scene.frame_set(1)
assert abs(rig.pose.bones['Head'].rotation_quaternion.angle)<.001
assert abs(rig.pose.bones['Arm'].rotation_quaternion.angle-.7)<.001
scene.frame_set(12);assert abs(rig.pose.bones['Head'].rotation_quaternion.angle-.7)<.001
print('PASS: attention continuity preserves the initial head pose and leaves arm animation intact')
