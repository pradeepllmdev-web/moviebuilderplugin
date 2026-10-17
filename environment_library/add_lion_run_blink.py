"""Add only two eyelid blinks to the approved run and mouth animation."""
import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'samples/lion-run-blink'
source=H.parent/'samples/lion-run-lipsync'
bpy.ops.wm.open_mainfile(filepath=str(source/'scene.blend'))
count=0
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or not obj.data.shape_keys:continue
 keys=obj.data.shape_keys.key_blocks
 for name in ('BlinkL','BlinkR'):
  if name not in keys:continue
  count+=1;key=keys[name]
  for frame in range(1,145):
   value=0.
   for start in (37,98):
    elapsed=frame-start
    if 0<=elapsed<=2:value=elapsed/2
    elif 2<elapsed<=3:value=1.
    elif 3<elapsed<=6:value=(6-elapsed)/3
   key.value=value;key.keyframe_insert('value',frame=frame)
if not count:raise RuntimeError('No eyelid controls found')
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
(D/'blink-check.json').write_text(json.dumps({'eyelid_controls':count,'blink_start_frames':[37,98],'body_and_mouth':'preserved from approved source'}))
