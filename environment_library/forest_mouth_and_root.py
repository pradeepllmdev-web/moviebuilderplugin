import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'3dobjectnew/server'))
from speech_visemes import sapi_speak
from facerig import visemes
from realistic_rig import fcurves
lines=[]
for i,(at,text) in enumerate(plan.get('test_dialogue',[(0,'The forest has a secret. Every trail has a rhythm.'),(5,'Listen! That is the sound of adventure catching up!'),(10,'Round the clearing! I think the trees are cheering.'),(15,'And now, my famous victory dance!')])):
 speech=sapi_speak(text,out/f'voice-{i}','Microsoft David Desktop',1)
 lines.append(dict(speaker='Leo',to='Leo',text=text,start=at,end=at+4.8,audio=str(speech['wav']),tone='natural',manner='talk'))
plan['lines']=lines;(out/'scene.json').write_text(json.dumps(plan,indent=2))
_,amp=visemes(lines,s.frame_end,24);previous=0;filtered=[]
for v in amp:
 previous+=max(-.18,min(.18,(1-math.exp(-1/(24*(.065 if v>previous else .14))))*(v-previous)))
 filtered.append(previous*.8)
for obj in s.objects:
 if obj.type!='MESH' or not obj.data.shape_keys:continue
 for name in ('JawOpen','LipSeal'):
  key=obj.data.shape_keys.key_blocks.get(name)
  if key:
   for frame,v in enumerate(filtered,1):key.value=v if name=='JawOpen' else max(0,1-v*3);key.keyframe_insert('value',frame=frame)
# Explicit world travel is applied to the Unreal actor, independently of skeletal clips.
trajectory=[]
for frame in range(1,s.frame_end+1):
 g,u,pos,yaw=sample(plan['actors'][0],(frame-1)/24)
 trajectory.append(dict(frame=frame-1,position=list(pos),yaw=yaw))
(out/'trajectory.json').write_text(json.dumps(trajectory))
for rig in realistic.values():
 action=rig.animation_data.action
 if action:
  for curve in fcurves(action):
   if curve.data_path in ('location','rotation_euler'):
    for point in curve.keyframe_points:point.co.y=rig['base_yaw'] if curve.data_path=='rotation_euler' and curve.array_index==2 else 0
 rig.location=(0,0,0);rig.rotation_euler.z=rig['base_yaw']
