import bpy,json,sys,math
from pathlib import Path
root=Path(__file__).parent.resolve();repo=root.parents[1];sys.path.insert(0,str(repo))
from movie_production.characters import load_profile,RigController
from movie_production.attention import attention_commands
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-body.blend'),load_ui=False,use_scripts=False)
plan=json.loads((root/'movie.json').read_text());report={}
for name,rig_name,probe,side in [('snow','RIG-Snow','DEF-Head',1),('jacob','Armature','DEF-HEAD',-1)]:
    rig=bpy.data.objects[rig_name];profile=load_profile(repo/'movie_production/profiles'/f'{name}.json')
    # Restrict this pass to attention channels so speech/expressions/body survive.
    profile['targets']=[target for target in profile['targets'] if target['channel'] in ('head_yaw','head_nod','gaze')]
    profile['properties']=[]
    controller=RigController(rig,profile,1.86)
    for frame in range(1,385):
        bpy.context.scene.frame_set(frame);controller.key(frame,attention_commands(name,(frame-1)/24,plan['shots'],side))
    quaternions=[]
    for frame in (1,25,49,97,145,193,241,289,337,384):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();quaternions.append(rig.pose.bones[probe].matrix.to_quaternion().copy())
    maximum=max(math.degrees(2*math.acos(min(1,abs(quaternions[0].normalized().dot(q.normalized()))))) for q in quaternions)
    assert maximum>10,'Actual head did not turn: '+name
    report[name]={'actual_head_orientation_change_degrees':maximum,'control':next(t['bone'] for t in profile['targets'] if t['channel']=='head_yaw')}
bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'the-last-lantern-attention.blend'))
(root/'attention-verification.json').write_text(json.dumps(report,indent=2))
for frame in (() if '--no-stills' in sys.argv else (49,145,241,337)):
    bpy.context.scene.frame_set(frame);bpy.context.scene.render.filepath=str(root/f'attention-preview-{frame}.png');bpy.ops.render.render(write_still=True)
print('ATTENTION_READY',json.dumps(report),flush=True)
