"""Prepared biped lion driven by the same semantic face/body flow as humans."""
import bpy,json,sys,math,hashlib,argparse
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--repair',action='store_true');parser.add_argument('--output',type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if args.output:HERE=args.output.resolve();HERE.mkdir(parents=True,exist_ok=True)
PLUGIN=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
SOURCE=PLUGIN.parent/'verification/lion-detailed/authored_probe.blend'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PLUGIN))
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler,TypedPerformanceBank
from movie_production.characters import speech_commands
from movie_production.blendshapes import BlendshapeController
from movie_production.lion_eyelids import add_lids
from facerig import visemes
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(SOURCE),link=False) as (source,target):
    target.objects=['Lion_Realistic','output_unwrapped','Lion_Realistic InnerMouth']
for obj in target.objects:
    if obj:bpy.context.scene.collection.objects.link(obj)
rig=bpy.data.objects['Lion_Realistic'];meshes=[obj for obj in rig.children_recursive if obj.type=='MESH']
print('LION_APPENDED',flush=True)
rig.animation_data_clear();rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
for obj in meshes:
    obj.animation_data_clear()
    if obj.data.shape_keys:
        obj.data.shape_keys.animation_data_clear()
        for key in obj.data.shape_keys.key_blocks:key.value=0
bpy.context.view_layer.update();repair_report=None
if args.repair:
    from movie_production.repair_lion import repair
    additions,repair_report=repair(rig)
    meshes=[obj for obj in rig.children_recursive if obj.type=='MESH']
else:meshes.extend(add_lids(rig))
profile={'schema':'blendshape-controls/1','name':'prepared-biped-lion-v4',
    'mapping':{'jawOpen':'Lion_JawOpen','eyeBlinkLeft':'Lion_LidClosure_L','eyeBlinkRight':'Lion_LidClosure_R',
        'mouthFunnel':'Lion_Round','mouthStretchLeft':'Lion_Wide','mouthStretchRight':'Lion_Wide',
        'mouthClose':'Lion_Close','mouthPressLeft':'Lion_Press','mouthPressRight':'Lion_Press',
        'browInnerUp':'BrowUp','mouthSmileLeft':'Smile','mouthSmileRight':'Smile'},
    'limits':'12 existing asset-specific controls plus fitted closure lids; no independent eyes or articulated tongue. Not ARKit-52.'}
if args.repair:
    profile['require_jaw_morph']=False;profile['mapping'].pop('jawOpen')
    profile['mapping'].update(eyeBlinkLeft='Repair_Blink_L',eyeBlinkRight='Repair_Blink_R')
    profile['mapping'].update(mouthFunnel='Repair_Round',mouthStretchLeft='Repair_Wide',mouthStretchRight='Repair_Wide',
        mouthClose='Repair_Close',mouthPressLeft='Repair_Press',mouthPressRight='Repair_Press',mouthSmileLeft='Repair_Smile',mouthSmileRight='Repair_Smile')
    profile['limits']='Original lion face with fitted jaw/teeth/tongue/eyes/lids. Calibrated for this exact asset.'
(HERE/'face-profile.json').write_text(json.dumps(profile,indent=2));face=BlendshapeController(meshes,profile)
body_profile={'schema':'body-retarget/1','anatomy':'biped','alignment_bone':'mixamorig:Spine2','source_alignment':'Spine2',
    'gesture_strength':.28,'max_angular_speed_degrees':90,'torso_limit_degrees':4,
    'mapping':{role:'mixamorig:'+role for role in ('Spine','Spine1','Spine2','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand')}}
(HERE/'body-profile.json').write_text(json.dumps(body_profile,indent=2))
with bpy.data.libraries.load(str(PLUGIN/'assets/realistic/clips.blend'),link=False) as (source,target):target.actions=['clip|Listen']
idle=ClipSampler(target.actions[0]);body=BodyRetargeter(rig,body_profile,RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz'),idle)
bank=TypedPerformanceBank(ROOT/'samples/the-last-lantern/performance/reference_bank.json')
audio=PLUGIN.parent/'verification/lion-whisper/audio/voice_01.wav'
frames=192;fps=24;start=.55
lines=[{'text':'Tonight, I will try something stronger. A whisper.','audio':str(audio),'start':start,'end':4.2,'tone':'quiet, thoughtful','manner':'talk'}]
vis,amp=visemes(lines,frames,fps)
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=frames;scene.render.fps=fps
scene.timeline_markers.clear()
scene.render.use_sequencer=False
for imported_scene in bpy.data.scenes:
    # Blender 5.2's frame evaluation can retain sequencer dependencies from legacy scenes.
    if imported_scene.sequence_editor is None:imported_scene.sequence_editor_create()
print('ANIMATION_START',flush=True)
head=rig.pose.bones['mixamorig:Head'];rotation=head.bone.matrix_local.to_quaternion()
axes=[rotation.inverted()@Vector(axis) for axis in [(0,0,1),(1,0,0),(0,1,0)]]
for frame in range(1,frames+1):
    scene.frame_set(frame);t=(frame-1)/fps;body.key(frame,t,smooth_activity(t,[(.5,4.4)],fade=.75))
    captured=bank.facial_commands(t);commands=speech_commands(vis,amp,frame-1)
    commands['jaw']*=.75
    commands.update(blink=max(captured['blink']*.85,max(0,1-abs(t-6.5)/.13)),
        brow=captured['brow']*.45,smile=.08,mouth_close=float(vis['MBP'][frame-1])*.65,
        lip_press=float(vis['FV'][frame-1])*.5)
    face.key(frame,commands)
    if repair_report:
        jaw=rig.pose.bones[repair_report['jaw_bone']]
        axis=jaw.bone.matrix_local.to_quaternion().inverted()@Vector((1,0,0))
        jaw.rotation_mode='QUATERNION';jaw.rotation_quaternion=Quaternion(axis,math.radians(14)*commands['jaw'])
        jaw.keyframe_insert('rotation_quaternion',frame=frame)
        tongue=rig.pose.bones[repair_report['tongue_bone']]
        tongue.location=tongue.bone.matrix_local.to_3x3().inverted()@Vector((0,0,.04*commands['jaw']))
        tongue.keyframe_insert('location',frame=frame)
        for name in repair_report['eye_bones']:
            eye=rig.pose.bones[name];axis=eye.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
            eye.rotation_mode='QUATERNION';eye.rotation_quaternion=Quaternion(axis,captured['gaze_variation']*.25)
            eye.keyframe_insert('rotation_quaternion',frame=frame)
    yaw=math.radians(11)*math.sin(t*.7);nod=math.radians(2.5)*math.sin(t*1.1)
    head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axes[0],yaw)@Quaternion(axes[1],nod)
    head.keyframe_insert('rotation_quaternion',frame=frame)
scene.frame_set(1);bpy.context.view_layer.update()
head_target=rig.matrix_world@head.head+Vector((0,0,.11))
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=head_target+Vector((0,-2.3,.03)));camera=bpy.context.object;camera.data.lens=55;scene.camera=camera
for frame,distance,z in [(1,2.5,-.08),(24,1.9,.02),(130,1.9,.02),(192,2.5,-.08)]:
    camera.location=head_target+Vector((0,-distance,.04));aim(camera,head_target+Vector((0,0,z)))
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
for position,energy in [((1,-2,3),120),((-2,-1,2),70),((0,2,3),180)]:
    bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=3;aim(light,head_target)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object
mat=bpy.data.materials.new('Lion studio');mat.diffuse_color=(.06,.09,.12,1);floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Lion World');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.17,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.22
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.use_motion_blur=False
scene.render.resolution_x=640 if args.repair else 768;scene.render.resolution_y=scene.render.resolution_x;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'lion-talking.blend'))
report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'body_anatomy':'upright biped lion','existing_facial_controls':12,'new_eyelid_controls':2,'shared_face_adapter':True,'shared_body_adapter':True,
    'audio':str(audio),'audio_start':start,'frames':frames,'fps':fps,
    'unsupported':['independent eye gaze','articulated tongue','quadruped locomotion'],
    'face_setup':'Existing prepared v4 mouth/expression morphs plus new fitted lid overlays; original blink morphs held neutral. No reference image required.'}
if repair_report:report.update(repair=repair_report,face_setup=repair_report['approach'],unsupported=['quadruped locomotion','detailed phoneme-specific tongue articulation'])
(HERE/'application.json').write_text(json.dumps(report,indent=2))
peak=max(range(frames),key=lambda i:speech_commands(vis,amp,i)['jaw'])+1
for frame,name in [(1,'neutral'),(peak,'speech'),(157,'blink')]:
    scene.frame_set(frame);scene.render.filepath=str(HERE/(name+'.png'));bpy.ops.render.render(write_still=True)
print('LION_READY',flush=True)
