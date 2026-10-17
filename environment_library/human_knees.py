"""Two-bone knee-plane correction preserving sampled hip/ankle positions."""
import math
from mathutils import Vector

def correct_walk_knees(scene,rig,frames):
 import bpy
 corrected=0;max_error=0
 for frame in frames:
  scene.frame_set(frame);bpy.context.view_layer.update()
  for side in ('Left','Right'):
   thigh,shin,foot=[rig.pose.bones['mixamorig:'+side+n] for n in ('UpLeg','Leg','Foot')]
   a,b,c=[bone.head.copy() for bone in (thigh,shin,foot)]
   length1=(b-a).length;length2=(c-b).length;line=c-a;distance=line.length
   if distance<1e-6:continue
   axis=line.normalized();forward=Vector((0,-1,0));pole=forward-axis*forward.dot(axis)
   if pole.length<1e-5:continue
   pole.normalize();along=(length1*length1-length2*length2+distance*distance)/(2*distance)
   height=math.sqrt(max(0,length1*length1-along*along));desired=a+axis*along+pole*height
   foot_matrix=foot.matrix.copy();thigh_matrix=thigh.matrix.copy();shin_matrix=shin.matrix.copy()
   rotation=(b-a).rotation_difference(desired-a).to_matrix().to_4x4()
   thigh.matrix=rotation@thigh_matrix;thigh.matrix.translation=a;bpy.context.view_layer.update()
   rotation=(c-b).rotation_difference(c-desired).to_matrix().to_4x4()
   shin.matrix=rotation@shin_matrix;shin.matrix.translation=desired;bpy.context.view_layer.update()
   foot.matrix=foot_matrix;bpy.context.view_layer.update()
   max_error=max(max_error,(foot.head-c).length)
   for bone in (thigh,shin,foot):bone.keyframe_insert('rotation_quaternion',frame=frame)
   corrected+=1
 return {'corrected_leg_frames':corrected,'maximum_ankle_error_m':max_error}
