"""Opt-in ARKit eye tracks and MPFB copy preparation; no model data output."""
import math,sys

def eye_values(time):
 blink=max(max(0,1-abs(time-center)/.125) for center in (1.5,4.2,7.5,10.7,14.1,17.6,21.2,24.5,28.1,31.6,35.2,38.5))
 gaze=.22*math.sin(time*.9)
 return {'eyeBlinkLeft':blink,'eyeBlinkRight':blink,'eyeLookInLeft':max(0,gaze),'eyeLookOutRight':max(0,gaze),'eyeLookOutLeft':max(0,-gaze),'eyeLookInRight':max(0,-gaze)}

def animate_eyes(scene,frames,fps,timeline=None):
 for frame in range(1,frames+1):
  time=(frame-1)/fps
  beat=next((g for g in (timeline or []) if g['start']<=time<g['end']),{})
  emotion=beat.get('emotion','neutral');strength=min(1,max(0,(time-beat.get('start',0))/.5))
  expression={'browInnerUp':(.28 if emotion=='alert' else .12 if emotion=='curious' else .04)*strength,'mouthSmileLeft':(.14 if emotion=='reassuring' else .02)*strength,'mouthSmileRight':(.14 if emotion=='reassuring' else .02)*strength}
  eyes=eye_values(time)
  if beat.get('look_at') in ['partner','point']:
   # Head now carries partner direction; avoid an unrelated wandering eye cue.
   eyes.update({n:0 for n in eyes if 'Look' in n})
  for obj in scene.objects:
   if obj.type!='MESH' or not obj.data.shape_keys:continue
   for name,value in {**eyes,**expression}.items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=value;key.keyframe_insert('value',frame=frame)

def prepare_export(scene,rig,root):
 import bpy
 sys.path.insert(0,str(root/'samples/mpfb-character'))
 from bootstrap import initialize
 initialize()
 from mpfb.services.exportservice import ExportService
 mesh=next(o for o in scene.objects if o.name.startswith('Rowan-Body'))
 scene.frame_set(1)
 actions={o.name:(o.data.shape_keys.animation_data.action,o.data.shape_keys.animation_data.action_slot) for o in scene.objects if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data and o.data.shape_keys.animation_data.action}
 ExportService.bake_modifiers_remove_helpers(mesh,bake_masks=True,bake_subdiv=False,remove_helpers=True,also_proxy=True)
 for name,(action,slot) in actions.items():
  keys=bpy.data.objects[name].data.shape_keys
  if keys:
   keys.animation_data_create();keys.animation_data.action=action
   if slot:keys.animation_data.action_slot=slot
 from safe_shape_join import join_preserving_shapes
 meshes=[o for o in scene.objects if o.type=='MESH' and (o in list(rig.children_recursive) or any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))]
 join_preserving_shapes(meshes,mesh)
