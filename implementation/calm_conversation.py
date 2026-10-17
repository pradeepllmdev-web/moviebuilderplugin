"""Opt-in smoothing of evaluated upper-body poses; lower-body contacts are preserved."""
def calm_upper_body(rig,scene,radius=3,strength=.7):
 import bpy
 from mathutils import Quaternion
 from realistic_rig import fcurves
 names=[b.name for b in rig.pose.bones if any(part in b.name for part in ('Spine','Neck','Head','Shoulder','Arm','ForeArm'))]
 samples={name:[] for name in names};frames=list(range(scene.frame_start,scene.frame_end+1))
 for frame in frames:
  scene.frame_set(frame)
  for name in names:
   bone=rig.pose.bones[name];local=rig.convert_space(pose_bone=bone,matrix=bone.matrix,from_space='POSE',to_space='LOCAL')
   q=local.to_quaternion()
   if samples[name] and samples[name][-1].dot(q)<0:q.negate()
   samples[name].append(q.copy())
 action=bpy.data.actions.new(rig.name+' Calm conversation')
 rig.animation_data_create();rig.animation_data.action=action
 for name in names:
  bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION'
  for constraint in list(bone.constraints):bone.constraints.remove(constraint)
  values=samples[name];neutral=values[0]
  for i,frame in enumerate(frames):
   total=[0.,0.,0.,0.];weight=0
   for j in range(max(0,i-radius),min(len(values),i+radius+1)):
    w=radius+1-abs(i-j);weight+=w
    for component in range(4):total[component]+=values[j][component]*w
   q=Quaternion([v/weight for v in total]).normalized()
   bone.rotation_quaternion=neutral.slerp(q,strength);bone.keyframe_insert('rotation_quaternion',frame=frame)
 for curve in fcurves(action):
  for key in curve.keyframe_points:key.interpolation='LINEAR'
 scene.frame_set(scene.frame_start)
 return {'upper_body_bones':len(names),'filter_radius_frames':radius,'gesture_strength':strength}
