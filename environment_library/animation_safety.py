"""Sample bone control transforms locally and return bounded diagnostic metadata."""
import math
def inspect_motion(scene,rig,frames):
 previous={};maximum=0;bone_name='';bad=False;scale_max=0;frame_at=None
 for frame in range(1,frames+1):
  scene.frame_set(frame)
  for bone in rig.pose.bones:
   q=bone.rotation_quaternion.copy();values=list(q)+list(bone.location)+list(bone.scale)
   if not all(math.isfinite(v) for v in values):bad=True;continue
   scale_max=max(scale_max,max(abs(v) for v in bone.scale))
   if bone.name in previous:
    difference=previous[bone.name].rotation_difference(q);angle=math.degrees(2*math.acos(min(1,abs(difference.w))))
    if angle>maximum:maximum=angle;bone_name=bone.name;frame_at=frame
   previous[bone.name]=q
 return {'ok':not bad and maximum<=120 and scale_max<=2,'maximum_rotation_step_deg':round(maximum,3),'bone_at_maximum':bone_name,'frame_at_maximum':frame_at,'maximum_bone_scale':scale_max,'nonfinite':bad,'limits':'Large control discontinuities only; does not certify natural gait or mesh deformation.'}
