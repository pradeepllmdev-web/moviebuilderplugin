"""Scripted, fully clothed MPFB character with shared body and facial commands."""
import bpy,sys,json,math,argparse
from pathlib import Path
from mathutils import Vector,Quaternion
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--preset',type=Path);parser.add_argument('--output',type=Path)
parser.add_argument('--render',action='store_true');parser.add_argument('--animate-only',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT));sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from movie_production.appearance import validate_preset
preset=validate_preset(json.loads(args.preset.read_text())) if args.preset else None
name=preset['character_id'] if preset else 'rowan';label=name.title()
if args.output:HERE=args.output.resolve();HERE.mkdir(parents=True,exist_ok=True)
from bootstrap import initialize
bpy.ops.wm.read_factory_settings(use_empty=True);initialize()
from mpfb.services.humanservice import HumanService
from mpfb.services.assetservice import AssetService
from mpfb.services.targetservice import TargetService
from mpfb.services.faceservice import FaceService,ARKIT_FACEUNITS
from mpfb.entities.objectproperties import HumanObjectProperties
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler,TypedPerformanceBank
from movie_production.characters import speech_commands
from movie_production.blendshapes import BlendshapeController
from facerig import visemes

mesh=HumanService.create_human();mesh.name=label+'-Body'
for key,value in (preset['macro'] if preset else {'gender':1.,'age':.38,'muscle':.4}).items():
    HumanObjectProperties.set_value(key,value,entity_reference=mesh)
TargetService.reapply_macro_details(mesh)
if preset:
    targets_root=ROOT/'.verification/mpfb/source/src/mpfb/data/targets'
    for target,weight in preset['targets'].items():
        TargetService.load_target(mesh,str(targets_root/(target+'.target.gz')),weight=weight)
skin=AssetService.find_asset_absolute_path(preset['skin'] if preset else 'young_caucasian_male.mhmat',asset_subdir='skins')
if not skin:raise ValueError('Missing skin asset')
HumanService.set_character_skin(skin,mesh,skin_type='GAMEENGINE')
rig=HumanService.add_builtin_rig(mesh,'mixamo');rig.name=label+'-Rig'
assets=[('eyes','high-poly.mhclo','Eyes'),('eyebrows','eyebrow001.mhclo','Eyebrows'),
    ('eyelashes','eyelashes01.mhclo','Eyelashes'),('teeth','teeth_base.mhclo','Teeth'),('tongue','tongue01.mhclo','Tongue'),
    ('hair',preset['hair'] if preset else 'short02.mhclo','Hair'),
    ('clothes',preset['outfit'] if preset else 'male_casualsuit01.mhclo','Clothes'),
    ('clothes',preset['shoes'] if preset else 'shoes01.mhclo','Clothes')]
for directory,filename,kind in assets:
    path=AssetService.find_asset_absolute_path(filename,asset_subdir=directory)
    if not path:raise ValueError('Required asset missing: '+filename)
    HumanService.add_mhclo_asset(path,mesh,asset_type=kind,material_type='GAMEENGINE',subdiv_levels=0)
    print('ASSET_READY',kind,filename,flush=True)
if preset:
    # Palette is explicit art direction, not automatically inferred from the image.
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':continue
        if 'casualsuit' in obj.name:
            for material in obj.data.materials:
                if not material or not material.use_nodes:continue
                nodes=material.node_tree.nodes;links=material.node_tree.links
                bsdf=next((node for node in nodes if node.type=='BSDF_PRINCIPLED'),None)
                if not bsdf:continue
                coords=nodes.new('ShaderNodeTexCoord');split=nodes.new('ShaderNodeSeparateXYZ')
                links.new(coords.outputs['Generated'],split.inputs[0])
                mask=nodes.new('ShaderNodeMath');mask.operation='GREATER_THAN';mask.inputs[1].default_value=.55
                links.new(split.outputs['Z'],mask.inputs[0])
                palette=nodes.new('ShaderNodeMixRGB');palette.inputs[1].default_value=(.24,.17,.09,1);palette.inputs[2].default_value=(.025,.12,.13,1)
                links.new(mask.outputs[0],palette.inputs[0]);links.new(palette.outputs[0],bsdf.inputs['Base Color'])
        elif 'short01' in obj.name:
            for material in obj.data.materials:
                if not material or not material.use_nodes:continue
                bsdf=next((node for node in material.node_tree.nodes if node.type=='BSDF_PRINCIPLED'),None)
                if bsdf:
                    for link in list(bsdf.inputs['Base Color'].links):material.node_tree.links.remove(link)
                    bsdf.inputs['Base Color'].default_value=(.035,.018,.009,1)
FaceService.load_targets(mesh,load_microsoft_visemes=False,load_arkit_faceunits=True)
FaceService.interpolate_targets(mesh)
names=list(mesh.data.shape_keys.key_blocks.keys())
mapping={semantic:next((name for name in names if name==semantic or name.endswith('/'+semantic) or name.endswith(':'+semantic) or name.endswith('-'+semantic)),None) for semantic in ARKIT_FACEUNITS}
mapping={semantic:name for semantic,name in mapping.items() if name}
if len(mapping)<52:
    print('FACE_KEY_NAMES',names,flush=True)
    raise ValueError('Expected 52 mapped ARKit face units, found '+str(len(mapping)))
profile={'schema':'blendshape-controls/1','name':name+'-mpfb','mapping':mapping}
(HERE/'face-profile.json').write_text(json.dumps(profile,indent=2))
meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
controller=BlendshapeController(meshes,profile)
body_profile={'schema':'body-retarget/1','anatomy':'biped','alignment_bone':'mixamorig:Spine2','source_alignment':'Spine2',
    'gesture_strength':.4,'max_angular_speed_degrees':100,'torso_limit_degrees':5,
    'mapping':{role:'mixamorig:'+role for role in ('Spine','Spine1','Spine2','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand')}}
(HERE/'body-profile.json').write_text(json.dumps(body_profile,indent=2))
with bpy.data.libraries.load('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend',link=False) as (source,target):target.actions=['clip|Listen']
idle=ClipSampler(target.actions[0]);body=BodyRetargeter(rig,body_profile,RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz'),idle)
bank=TypedPerformanceBank(ROOT/'samples/the-last-lantern/performance/reference_bank.json')
audio=ROOT/'samples/the-last-lantern/audio/line_2.wav'
speech=[{'text':'Only if we stop walking.','audio':str(audio),'start':.75,'end':3.4,'manner':'talk','tone':'warm'}]
frames=144;vis,amp=visemes(speech,frames,24)
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=frames;scene.render.fps=24
head=rig.pose.bones['mixamorig:Head'];axis=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
for frame in range(1,frames+1):
    scene.frame_set(frame);t=(frame-1)/24;body.key(frame,t,smooth_activity(t,[(.6,3.7)],fade=.7))
    commands=speech_commands(vis,amp,frame-1);captured=bank.facial_commands(t)
    commands.update(blink=captured['blink'],brow=captured['brow']*.6,smile=.12,gaze=captured['gaze_variation'])
    # Deliberate eye-blink audition at the end, after the dialogue.
    commands['blink']=max(commands['blink'],max(0,1-abs(t-4.65)/.12))
    controller.key(frame,commands)
    head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(12)*math.sin(t*.85))
    head.keyframe_insert('rotation_quaternion',frame=frame)
if '--animate-only' in sys.argv:raise SystemExit(0)
def aim(obj,at):obj.rotation_euler=(Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()
scene.frame_set(1);bpy.context.view_layer.update()
head_at=rig.matrix_world@head.head;hips=rig.matrix_world@rig.pose.bones['mixamorig:Hips'].head
bpy.ops.object.camera_add(location=head_at+Vector((0,-1.8,.05)))
camera=bpy.context.object;camera.data.lens=55;aim(camera,head_at+Vector((0,0,-.06)));scene.camera=camera
# Wider start/end framing, close face view throughout the spoken line.
for frame,distance,z in [(1,2.7,-.3),(20,1.55,-.02),(100,1.55,-.02),(144,2.7,-.3)]:
    camera.location=head_at+Vector((0,-distance,.06));aim(camera,head_at+Vector((0,0,z)))
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
for position,power,size in [((1,-2,3),180,3),((-2,-1,2),90,3),((0,2,3),200,2)]:
    bpy.ops.object.light_add(type='AREA',location=Vector(position));light=bpy.context.object
    light.data.energy=power;light.data.shape='DISK';light.data.size=size;aim(light,head_at)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object
mat=bpy.data.materials.new('Studio floor');mat.diffuse_color=(.08,.12,.16,1);floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.2,.25,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=8 if preset else 16;scene.cycles.use_denoising=True
scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(name+'.blend')))
report={'name':name,'generator':'MPFB 2.0.18','body_bones':len(rig.pose.bones),'face_units':len(mapping),
    'shape_keys_per_object':{obj.name:len(obj.data.shape_keys.key_blocks) for obj in meshes if obj.data.shape_keys},
    'voice':str(audio),'body':'shared captured talking/listening adapter','face':'shared speech commands + captured expression bank',
    'appearance_preset':str(args.preset) if args.preset else None,
    'production_approved':False,'limitations':'Human template creation, approximate likeness. Upper-body audition; Unreal not yet tested.'}
(HERE/'capabilities.json').write_text(json.dumps(report,indent=2));print('CHARACTER_READY',json.dumps(report),flush=True)
if '--render' in sys.argv:
    (HERE/'frames').mkdir(exist_ok=True);scene.render.filepath=str(HERE/'frames/frame_');bpy.ops.render.render(animation=True)
else:
    for frame in (43,113):
        scene.frame_set(frame);scene.render.filepath=str(HERE/f'preview-{frame}.png');bpy.ops.render.render(write_still=True)
