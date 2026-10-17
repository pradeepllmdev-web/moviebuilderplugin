"""Stable two-bone arm contact on a synthetic rig, without any character mesh."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'));from box_hands import solve_arm
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.object.armature_add();rig=bpy.context.object;bpy.ops.object.mode_set(mode='EDIT');upper=rig.data.edit_bones[0];upper.name='Upper';upper.head=(0,0,1);upper.tail=(.5,0,1);fore=rig.data.edit_bones.new('Fore');fore.head=(.5,0,1);fore.tail=(1,0,1);fore.parent=upper;hand=rig.data.edit_bones.new('Hand');hand.head=(1,0,1);hand.tail=(1.1,0,1);hand.parent=fore;bpy.ops.object.mode_set(mode='OBJECT')
for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
previous=None;maximum_step=0;maximum_error=0
for frame in range(100):
 target=Vector((.6,-.35,1-.1*math.sin(math.pi*frame/99)));solve_arm(rig,rig.pose.bones['Hand'],target,1,Vector((.8,.1,1.1)));bpy.context.view_layer.update();maximum_error=max(maximum_error,(rig.pose.bones['Hand'].head-target).length)
 current=rig.pose.bones['Fore'].rotation_quaternion.copy()
 if previous:maximum_step=max(maximum_step,math.degrees(previous.rotation_difference(current).angle))
 previous=current
assert maximum_error<.001,maximum_error
assert maximum_step<10,maximum_step
print('PASS: synthetic arm reaches its target continuously without elbow flips')
