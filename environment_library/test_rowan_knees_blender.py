import bpy,sys,json
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from human_knees import correct_walk_knees
D=H.parent/'samples/rowan-knee-test';D.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(H/'scene_jobs/d451bd370a6b464f918527127601d52f/actor_0/scene.blend'),use_scripts=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
report=correct_walk_knees(s,rig,range(1,97))
if report['maximum_ankle_error_m']>.002:raise RuntimeError('Knee correction displaced the ankle')
(D/'check.json').write_text(json.dumps(report));bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
