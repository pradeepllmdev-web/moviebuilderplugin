import bpy,json,sys
from pathlib import Path
root=Path(__file__).parent.resolve();repo=root.parents[1];sys.path.insert(0,str(repo));sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.characters import RigController,load_profile
from movie_production.catalog import resolve_character
from movie_production.performance_tracks import RecordedBodySampler,TypedPerformanceBank
from movie_production.attention import attention_commands
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-attention.blend'),load_ui=False,use_scripts=False)
bank=TypedPerformanceBank(root/'performance/reference_bank.json');plan=json.loads((root/'movie.json').read_text());report={}
with bpy.data.libraries.load('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend',link=False) as (source,target):target.actions=['clip|Listen']
idle=ClipSampler(target.actions[0])
for name,rig_name,side,offset in [('snow','RIG-Snow',1,0),('jacob','Armature',-1,2)]:
    rig=bpy.data.objects[rig_name];profile=resolve_character(name,['talk','listen'])['body'];profile['gesture_strength']=.45;profile['max_angular_speed_degrees']=120
    body=BodyRetargeter(rig,profile,RecordedBodySampler(root/'performance/talk_body.npz',offset=offset),idle)
    intervals=[(shot['start'],shot['start']+shot['duration']) for shot in plan['shots'] if shot['speaker']==name]
    for frame in list(range(1,385,2))+[384]:
        bpy.context.scene.frame_set(frame);t=(frame-1)/24;body.key(frame,t,smooth_activity(t,intervals,fade=.65))
        if frame%96==1:print('PERFORMANCE_BODY',name,frame,flush=True)
    face_profile=load_profile(repo/'movie_production/profiles'/f'{name}.json');face_profile['properties']=[]
    face_profile['targets']=[target for target in face_profile['targets'] if target['channel'] in ('head_yaw','head_nod','head_roll','gaze','blink','brow','smile')]
    face=RigController(rig,face_profile,1.86)
    for frame in range(1,385):
        bpy.context.scene.frame_set(frame);t=(frame-1)/24;commands=attention_commands(name,t,plan['shots'],side);captured=bank.facial_commands(t,offset)
        commands['head_yaw']=max(-1,min(1,commands['head_yaw']+captured.pop('head_yaw_variation')))
        commands['gaze']=max(-1,min(1,commands['gaze']+captured.pop('gaze_variation')))
        commands.update(captured);face.key(frame,commands)
    report[name]={'body_reference':'talk_body','head_reference':'head_attention','expression_reference':'face_expression','existing_listening_clip_retained':True,'target_dialogue_lipsync_retained':True,'offset_seconds':offset,'root_and_legs_captured':False}
bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'the-last-lantern-performance.blend'))
(root/'performance-application.json').write_text(json.dumps(report,indent=2))
if '--no-stills' not in sys.argv:
    for frame in (49,145,241,337):
        bpy.context.scene.frame_set(frame);bpy.context.scene.render.filepath=str(root/f'performance-preview-{frame}.png');bpy.ops.render.render(write_still=True)
print('PERFORMANCE_APPLIED',flush=True)
