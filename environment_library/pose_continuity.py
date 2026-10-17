"""Carry control poses across shot cuts; never serialize mesh geometry."""
import json
from pathlib import Path
def blend_previous_pose(scene,rig,path,fps,bone_names=None):
 if not path:return
 from mathutils import Quaternion,Vector
 pose=json.loads(Path(path).read_text());count=round(.4*fps)
 for frame in range(1,min(scene.frame_end,count)+1):
  scene.frame_set(frame);u=(frame-1)/max(1,count-1);u=u*u*(3-2*u)
  for bone in rig.pose.bones:
   if bone_names is not None and bone.name not in bone_names:continue
   if bone.name not in pose:continue
   old=pose[bone.name];bone.rotation_quaternion=Quaternion(old['rotation']).slerp(bone.rotation_quaternion,u);bone.location=Vector(old['location']).lerp(bone.location,u)
   bone.keyframe_insert('rotation_quaternion',frame=frame);bone.keyframe_insert('location',frame=frame)
def save_pose(scene,rig,path):
 scene.frame_set(scene.frame_end)
 Path(path).write_text(json.dumps({b.name:{'rotation':list(b.rotation_quaternion),'location':list(b.location)} for b in rig.pose.bones}))
