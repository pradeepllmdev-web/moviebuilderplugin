import bpy,json
from pathlib import Path
root=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern.blend'),load_ui=False,use_scripts=False)
out={}
for name in ('RIG-Snow','Armature'):
 r=bpy.data.objects[name]
 out[name]={'controls':[b.name for b in r.pose.bones if (b.name.startswith('FK-') or b.name.startswith('CTRL-') or b.name in ('Spine','Chest','Hips')) and any(w in b.name.lower() for w in ('arm','fore','wrist','hand','spine','chest','hips','pelvis','thigh','shin','foot'))], 'switches':{b.name:{k:str(b[k])[:60] for k in b.keys() if any(w in k.lower() for w in ('ik','fk'))} for b in r.pose.bones if any(any(w in k.lower() for w in ('ik','fk')) for k in b.keys())}}
with bpy.data.libraries.load('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend',link=False) as (source,target):
 out['clip_candidates']=[n for n in source.actions if any(w in n.lower() for w in ('talk','listen','idle_3','agree','think'))][:30]
 target.actions=[n for n in source.actions if n in out['clip_candidates']][:1]
if target.actions:
 a=target.actions[0];out['clip_metadata']={'name':a.name,'properties':list(a.keys()),'frame_range':list(a.frame_range)}
(root/'body-source-metadata.json').write_text(json.dumps(out,indent=2));print('BODY_METADATA',json.dumps(out),flush=True)
