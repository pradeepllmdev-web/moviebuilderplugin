"""Stitch consecutive NLA clips at the feet so recorded root offsets never pop.

Mocap clips such as Stand_To_Sit / Sit_To_Stand are not in place: each starts with the body somewhere
else on the floor, so a crossfade between them slides the whole body up to ~40 cm. For every strip
after the first, the clip's horizontal hips track is shifted (on a private copy of its action) so its
feet at the segment start land where the previous strip's feet were at that moment. In-clip motion,
like sitting back onto a seat, is kept. Between two seated clips the hips are the anchor instead: they rest
on the seat, so the body never slides along it (the feet may shift, like someone settling before standing)."""
import bpy
from mathutils import Vector
FEET=('LeftFoot','RightFoot')

def _bone(rig,suffix):return next(b for b in rig.pose.bones if b.name.endswith(suffix))
def _action_frame(strip,frame):
 """Scene frame -> frame inside the strip's action (scale, repeat, reverse)."""
 first,last=strip.action_frame_start,strip.action_frame_end;length=max(1e-6,last-first);local=(frame-strip.frame_start)/max(1e-6,strip.scale)
 local=min(local,length*strip.repeat-1e-4)%length if strip.repeat>1 else min(local,length)
 return last-local if strip.use_reverse else first+local
def _anchors(scene,rig,action,frame):
 """World feet midpoint and hips of one action evaluated alone at an action frame."""
 data=rig.animation_data;saved=(data.action,[t.mute for t in data.nla_tracks])
 for track in data.nla_tracks:track.mute=True
 data.action=action
 if hasattr(data,'action_slot') and action.slots:data.action_slot=action.slots[0]
 scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 point=(sum((rig.matrix_world@_bone(rig,f).head for f in FEET),Vector())/2,rig.matrix_world@_bone(rig,'Hips').head)
 data.action=saved[0]
 for track,mute in zip(data.nla_tracks,saved[1]):track.mute=mute
 return point
def _curves(action):
 """F-curves of a layered (Blender 4.4+) or legacy action."""
 if getattr(action,'layers',None):
  return [c for layer in action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]
 return list(action.fcurves)
def stitch(scene,rig,tolerance_cm=1.,seated_ratio=.8,first_hips=None,first_feet=False):
 """Align every motion strip to the one before it. Returns per-strip horizontal shifts in cm."""
 hips=_bone(rig,'Hips');strips=sorted((s for t in rig.animation_data.nla_tracks for s in t.strips if s.action and not t.name.startswith(('Foot lock','Jump','Flinch','Gesture'))),key=lambda s:s.frame_start)
 rest=(rig.matrix_world@hips.bone.matrix_local).to_3x3().inverted();report=[];users={};standing=(rig.matrix_world@hips.bone.head_local).z
 for s in strips:users[s.action.name]=users.get(s.action.name,0)+1
 def shift_hips(strip,shift):
  if users[strip.action.name]>1:strip.action=strip.action.copy();users[strip.action.name]=1
  local=rest@shift
  for curve in _curves(strip.action):
   if curve.data_path==f'pose.bones["{hips.name}"].location':
    for key in curve.keyframe_points:key.co.y+=local[curve.array_index];key.handle_left.y+=local[curve.array_index];key.handle_right.y+=local[curve.array_index]
 if first_hips is not None and strips:
  # A shot that opens mid-pose (e.g. already seated) places its first clip's hips at the character's anchor.
  _,hips_now=_anchors(scene,rig,strips[0].action,_action_frame(strips[0],strips[0].frame_start));shift=first_hips-hips_now
  shift_hips(strips[0],shift);report.append({'strip':strips[0].name,'shift_cm':round(shift.length*100,1),'anchor':'seat'})
 elif first_feet and strips:
  # A shot that opens with a clip that is not in place (e.g. sit_down) stands it on the rest-pose feet, where an idle would be.
  rest_feet=sum((rig.matrix_world@_bone(rig,f).bone.head_local for f in FEET),Vector())/2;feet_now,_=_anchors(scene,rig,strips[0].action,_action_frame(strips[0],strips[0].frame_start))
  shift=Vector((rest_feet.x-feet_now.x,rest_feet.y-feet_now.y,0));shift_hips(strips[0],shift);report.append({'strip':strips[0].name,'shift_cm':round(shift.length*100,1),'anchor':'rest feet'})
 for previous,strip in zip(strips,strips[1:]):
  # The boundary is where the new strip is fully blended in.
  boundary=strip.frame_start+strip.blend_in
  (feet_before,hips_before)=_anchors(scene,rig,previous.action,_action_frame(previous,min(boundary,previous.frame_end)));(feet_after,hips_after)=_anchors(scene,rig,strip.action,_action_frame(strip,boundary))
  # Seated on both sides: the hips rest on the seat, so anchor them (height too); otherwise anchor the feet.
  seated=max(hips_before.z,hips_after.z)<standing*seated_ratio
  shift=hips_before-hips_after if seated else Vector((feet_before.x-feet_after.x,feet_before.y-feet_after.y,0))
  if shift.length*100<tolerance_cm:report.append({'strip':strip.name,'shift_cm':0});continue
  shift_hips(strip,shift)
  report.append({'strip':strip.name,'shift_cm':round(shift.length*100,1),'anchor':'hips' if seated else 'feet'})
 return report
