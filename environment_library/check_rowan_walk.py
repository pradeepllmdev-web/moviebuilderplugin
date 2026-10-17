"""Compact knee audit; no model geometry is emitted."""
import bpy,json,math
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'scene_jobs/d451bd370a6b464f918527127601d52f'
bpy.ops.wm.open_mainfile(filepath=str(D/'actor_0/scene.blend'),use_scripts=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');report={}
for side in ['Left','Right']:
 values=[]
 for f in range(1,97):
  bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
  hip,knee,ankle=[rig.pose.bones['mixamorig:'+side+n].head.copy() for n in ['UpLeg','Leg','Foot']]
  angle=180-math.degrees((hip-knee).angle(ankle-knee));axis=ankle-hip;project=hip+axis*((knee-hip).dot(axis)/axis.length_squared);forward=-(knee-project).y
  values.append({'frame':f,'flex_deg':round(angle,2),'forward_bend_m':round(forward,4)})
 report[side]={'flex_range':[min(v['flex_deg'] for v in values),max(v['flex_deg'] for v in values)],'frame24':values[23],'backward_frames':[v['frame'] for v in values if v['forward_bend_m']<-.015]}
(H/'rowan-knee-check.json').write_text(json.dumps(report,indent=2))
