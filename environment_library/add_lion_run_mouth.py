"""Add only mouth shape keys to the user's approved running animation."""
import bpy,sys,json,math
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'samples/lion-run-lipsync'
sys.path.insert(0,str(H.parent.parent/'3dobjectnew/server'))
from speech_visemes import sapi_speak
speech=sapi_speak('I am running toward my next adventure. Here I come!',D/'dialogue','Microsoft David Desktop',1)
plan=json.loads((D/'scene.json').read_text());plan['lines']=[dict(speaker='Leo',to='Leo',text='I am running toward my next adventure. Here I come!',start=0,end=5.8,audio=str(speech['wav']),tone='natural',manner='talk')]
(D/'scene.json').write_text(json.dumps(plan,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'samples/lion-single-run/scene.blend'))
sys.path.insert(0,str(H.parent.parent/'blendplugin-next/scene_pipeline'))
from facerig import visemes
scene=bpy.context.scene
_,amp=visemes(plan['lines'],scene.frame_end,scene.render.fps)
previous=0.;filtered=[]
for value in amp:
 alpha=1-math.exp(-1/(24*(.065 if value>previous else .14)))
 previous+=max(-.18,min(.18,alpha*(value-previous)));filtered.append(previous*.8)
count=0
for obj in scene.objects:
 if obj.type!='MESH' or not obj.data.shape_keys:continue
 keys=obj.data.shape_keys.key_blocks
 for name in ('JawOpen','LipSeal'):
  if name not in keys:continue
  count+=1;key=keys[name]
  for frame,value in enumerate(filtered,1):
   key.value=value if name=='JawOpen' else max(0,1-value*3)
   key.keyframe_insert('value',frame=frame)
if not count:raise RuntimeError('Lion mouth controls missing')
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
print('MOUTH_ONLY: body animation preserved; keyed mouth controls',count)
