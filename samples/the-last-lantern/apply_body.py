import bpy,json,sys
from pathlib import Path
HERE=Path(__file__).parent.resolve();ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from movie_production.body import load_body_profile,ClipSampler,BodyRetargeter,smooth_activity
from movie_production.catalog import resolve_character
bpy.ops.wm.open_mainfile(filepath=str(HERE/'the-last-lantern.blend'),load_ui=False,use_scripts=False)
library=json.loads((ROOT/'movie_production/motion_library.json').read_text())
source_file=library['file']
with bpy.data.libraries.load(source_file,link=False) as (source,target):
    required=[library['actions'][name] for name in ('talk','listen')]
    if not set(required)<=set(source.actions):raise ValueError('Required existing motion clips missing')
    target.actions=list(required)
samplers={action.name:ClipSampler(action) for action in target.actions};plan=json.loads((HERE/'movie.json').read_text());report={}
for name,rig_name in [('snow','RIG-Snow'),('jacob','Armature')]:
    rig=bpy.data.objects[rig_name];profile=resolve_character(name,required_body_actions=('talk','listen'))['body']
    if profile['alignment_bone'] not in rig.pose.bones:
        print('AVAILABLE_ALIGNMENT',name,[b.name for b in rig.pose.bones if b.name.lower().startswith('def-spine')],flush=True)
    controller=BodyRetargeter(rig,profile,samplers['clip|Talking'],samplers['clip|Listen'])
    intervals=[(shot['start'],shot['start']+shot['duration']) for shot in plan['shots'] if shot['speaker']==name]
    for frame in list(range(1,385,2))+[384]:
        bpy.context.scene.frame_set(frame);t=(frame-1)/24;controller.key(frame,t,smooth_activity(t,intervals))
        if frame%96==1:print('BODY_PROGRESS',name,frame,flush=True)
    report[name]={'source_clips':['clip|Talking','clip|Listen'],'body_controls':list(profile['mapping'].values()),'frames':384,'root_and_feet_keyed':False,'face_controls_keyed':False}
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'the-last-lantern-body.blend'))
(HERE/'body-report.json').write_text(json.dumps(report,indent=2))
for frame in (37,133,229,325):
    bpy.context.scene.frame_set(frame);bpy.context.scene.render.filepath=str(HERE/f'body-preview-{frame}.png');bpy.ops.render.render(write_still=True)
print('BODY_READY',flush=True)
