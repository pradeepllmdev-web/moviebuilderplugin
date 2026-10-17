"""New talking-animal head, preserving the earlier lion's body and source files."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
PLUGIN=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
SOURCE=PLUGIN.parent/'verification/lion-detailed/authored_probe.blend'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PLUGIN))
from movie_production.animal_head import build_head
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler
from movie_production.characters import speech_commands
from movie_production.blendshapes import BlendshapeController
from facerig import visemes
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(SOURCE),link=False) as (source,target):target.objects=['Lion_Realistic','output_unwrapped']
for obj in target.objects:
    if obj:bpy.context.scene.collection.objects.link(obj)
rig=bpy.data.objects['Lion_Realistic'];rig.animation_data_clear();rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
body_mesh=bpy.data.objects['output_unwrapped'];body_mesh.animation_data_clear();body_mesh.shape_key_clear()
# Keep original body untouched in its source file; mask old head on this local copy.
head_groups={group.index for group in body_mesh.vertex_groups if group.name in ('mixamorig:Head','mixamorig:HeadTop_End','headfront')}
keep=[vertex.index for vertex in body_mesh.data.vertices if vertex.co.z<1.08 and sum(group.weight for group in vertex.groups if group.group in head_groups)<.35]
group=body_mesh.vertex_groups.new(name='Leo preserved body');group.add(keep,1,'REPLACE')
mask=body_mesh.modifiers.new('Hide old head','MASK');mask.vertex_group=group.name
bpy.context.view_layer.update()
objects,anatomy=build_head(rig)
face_profile={'schema':'blendshape-controls/1','require_jaw_morph':False,
    'mapping':{'eyeBlinkLeft':'eyeBlinkLeft','eyeBlinkRight':'eyeBlinkRight','browInnerUp':'browInnerUp',
        'mouthStretchLeft':'mouthStretch','mouthStretchRight':'mouthStretch','mouthFunnel':'mouthFunnel',
        'mouthSmileLeft':'mouthSmile','mouthSmileRight':'mouthSmile','mouthClose':'mouthClose'}}
face=BlendshapeController(objects,face_profile)
body_profile={'schema':'body-retarget/1','anatomy':'biped','alignment_bone':'mixamorig:Spine2','source_alignment':'Spine2',
    'gesture_strength':.28,'max_angular_speed_degrees':90,'torso_limit_degrees':4,
    'mapping':{role:'mixamorig:'+role for role in ('Spine','Spine1','Spine2','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand')}}
with bpy.data.libraries.load(str(PLUGIN/'assets/realistic/clips.blend'),link=False) as (source,target):target.actions=['clip|Listen']
body=BodyRetargeter(rig,body_profile,RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz'),ClipSampler(target.actions[0]))
audio=PLUGIN.parent/'verification/lion-whisper/audio/voice_01.wav';frames=192;fps=24;start=.55
lines=[{'text':'Tonight, I will try something stronger. A whisper.','audio':str(audio),'start':start,'end':4.2,'manner':'talk','tone':'thoughtful'}]
vis,amp=visemes(lines,frames,fps);scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=frames;scene.render.fps=fps
scene.sequence_editor_create();head=rig.pose.bones['mixamorig:Head'];jaw=rig.pose.bones[anatomy['jaw_bone']]
head_axis=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
jaw_axis=jaw.bone.matrix_local.to_quaternion().inverted()@Vector((1,0,0))
def facial_key(frame,commands):
    face.key(frame,commands)
    jaw.rotation_mode='QUATERNION';jaw.rotation_quaternion=Quaternion(jaw_axis,math.radians(28)*commands.get('jaw',0));jaw.keyframe_insert('rotation_quaternion',frame=frame)
for frame in range(1,frames+1):
    scene.frame_set(frame);t=(frame-1)/fps;body.key(frame,t,smooth_activity(t,[(.5,4.4)],fade=.75))
    commands=speech_commands(vis,amp,frame-1);commands['jaw']*=.9
    commands.update(blink=max(max(0,1-abs(t-center)/.12) for center in (1.2,3.4,6.5)),brow=.18+.15*math.sin(t),smile=.12,mouth_close=float(vis['MBP'][frame-1]))
    facial_key(frame,commands)
    head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(head_axis,math.radians(10)*math.sin(t*.65));head.keyframe_insert('rotation_quaternion',frame=frame)
    for index,name in enumerate(anatomy['eye_bones']):
        bone=rig.pose.bones[name];axis=bone.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
        bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion(axis,math.radians(4)*math.sin(t*.8));bone.keyframe_insert('rotation_quaternion',frame=frame)
scene.frame_set(1);bpy.context.view_layer.update()
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-2.2,1.46));camera=bpy.context.object;camera.data.lens=60;aim(camera,(0,-.08,1.40));scene.camera=camera
for position,energy in [((1,-2,3),100),((-2,-1,2),65),((0,2,3),150)]:
    bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object;light.data.energy=energy;light.data.size=3;aim(light,(0,0,1.4))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object
mat=bpy.data.materials.new('Leo floor');mat.diffuse_color=(.045,.075,.10,1);floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Leo world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.14,.19,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'leo-talking.blend'))
(HERE/'face-profile.json').write_text(json.dumps(face_profile,indent=2));(HERE/'body-profile.json').write_text(json.dumps(body_profile,indent=2))
report=dict(anatomy,source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    audio=str(audio),audio_start=start,frames=frames,fps=fps,approach='New parametric stylized head over preserved biped body; not image-to-3D generation')
(HERE/'application.json').write_text(json.dumps(report,indent=2))
for name,commands in [('neutral',{'jaw':0,'blink':0}),('open',{'jaw':1,'blink':0}),('blink',{'jaw':0,'blink':1})]:
    scene.frame_set(1);facial_key(1,commands);bpy.context.view_layer.update()
    scene.render.filepath=str(HERE/(name+'.png'));bpy.ops.render.render(write_still=True)
print('LEO_ANATOMY_READY',flush=True)
