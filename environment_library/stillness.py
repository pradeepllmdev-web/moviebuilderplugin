"""Stillness: no hand or leg movement without a purpose.

A standing `idle` beat plays a mocap idle that sways the arms and shifts the legs for no reason. Here the limbs, hips and feet hold the pose
they have at the start of the beat (easing in and out over a quarter second), while spine, neck, head, eyes and blinks stay alive, so a
listening character looks attentive, not restless. Beats with a purpose keep their motion: speech gestures (talk with dialogue), contact
and prop beats, walking, sitting. Opt out of the hold for one beat with natural=True on it.
Runs in Blender after the other pose edits (contact, drink); story_lint flags gestures that have neither dialogue nor a stated purpose."""
HELD=('Shoulder','Arm','Hand','Leg','Foot','Toe','Hips')   # substrings of the bone names: arms, hands and every finger (they contain Hand), legs, feet, toes, hips
def hold_idle(scene,rig,timeline,fps):
 """Freeze limbs and hips over every idle beat; returns the number of frames held."""
 import bpy
 bones=[b for b in rig.pose.bones if any(k in b.name.split(':')[-1] for k in HELD) and not b.name.split(':')[-1].startswith(('Head','Neck','Spine'))]
 held=0
 for g in timeline:
  if g['action']!='idle' or g.get('natural'):continue
  first,last=round(g['start']*fps)+1,round(g['end']*fps)
  if last-first<6:continue
  scene.frame_set(first);bpy.context.view_layer.update();frozen={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in bones}
  ramp=max(2,round(fps/4))
  for f in range(first,last+1):
   w=min(1.,(f-first)/ramp,(last-f)/ramp);w=max(0.,w)
   w=1.-(1.-w)  # 0 at the edges, 1 inside
   scene.frame_set(f)
   for b in bones:
    loc,rot=frozen[b.name]
    if rot.dot(b.rotation_quaternion)<0:rot=rot.copy();rot.negate()
    b.location=b.location.lerp(loc,w);b.rotation_quaternion=b.rotation_quaternion.slerp(rot,w)
    b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f)
   held+=1
 return held
