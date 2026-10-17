"""Blender-only rig inspection/audition; emits metadata, never geometry arrays."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/'rigged.glb'))
rigs=[obj for obj in bpy.context.scene.objects if obj.type=='ARMATURE']
if len(rigs)!=1:raise ValueError('Expected exactly one rig')
rig=rigs[0];rig.animation_data_clear()
meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH' and any(mod.type=='ARMATURE' and mod.object==rig for mod in obj.modifiers)]
if not meshes:raise ValueError('No body meshes bound to the generated skeleton')
for obj in bpy.context.scene.objects:
    if obj.type=='MESH' and obj not in meshes:obj.hide_render=True
for mesh in meshes:mesh.animation_data_clear()
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
points=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
low=min(p.z for p in points);high=max(p.z for p in points);height=high-low
center=Vector(((min(p.x for p in points)+max(p.x for p in points))/2,(min(p.y for p in points)+max(p.y for p in points))/2,low))
# Preserve imported hierarchy. Scene framing uses bounds, no model reconstruction.
report={'schema':'character-audition/1','name':'lion-open-mouth','bones':list(rig.pose.bones.keys()),
    'mesh_count':len(meshes),'face_shape_keys':{obj.name:[k.name for k in obj.data.shape_keys.key_blocks] for obj in meshes if obj.data.shape_keys},
    'height':height,'body_status':'not-tested','face_status':'unverified'}
(HERE/'capabilities.json').write_text(json.dumps(report,indent=2))
print('RIG_METADATA',json.dumps(report),flush=True)
if '--inspect-only' in sys.argv:raise SystemExit(0)
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler
available={name.split(':')[-1]:name for name in rig.pose.bones.keys()}
roles=['Spine','Spine1','Spine2','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand']
mapping={role:available[role] for role in roles if role in available}
if 'Spine02' in available and 'Spine01' in available:
    # Meshy's current native names run opposite their numeric labels.
    spine_names=['Spine02','Spine01','Spine']
    if not all(rig.data.bones[available[child]].parent==rig.data.bones[available[parent]] for parent,child in zip(spine_names,spine_names[1:])):
        raise ValueError('Unrecognized Meshy spine hierarchy; calibrate explicitly')
    mapping.update(dict(zip(roles[:3],[available[name] for name in spine_names])))
if not all(role in mapping for role in roles[3:]):raise ValueError('Missing canonical arm bones; explicit calibration needed')
alignment='Spine2' if 'Spine2' in mapping else 'Spine'
profile={'schema':'body-retarget/1','anatomy':'biped','mapping':mapping,
    'alignment_bone':mapping[alignment],'source_alignment':alignment,'gesture_strength':.35,
    'max_angular_speed_degrees':100,'torso_limit_degrees':5}
(HERE/'body-profile.json').write_text(json.dumps(profile,indent=2))
with bpy.data.libraries.load('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend',link=False) as (source,target):target.actions=['clip|Listen']
idle=ClipSampler(target.actions[0]);talk=RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz')
body=BodyRetargeter(rig,profile,talk,idle)
scene=bpy.context.scene;scene.render.fps=24;scene.frame_start=1;scene.frame_end=144
head=rig.pose.bones.get(available.get('Head',''))
for frame in range(1,145):
    scene.frame_set(frame);t=(frame-1)/24
    body.key(frame,t,smooth_activity(t,[(.6,5.5)],fade=.7))
    if head:
        # Rotate around armature vertical; transform to native head-local axes.
        axis=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
        head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(12)*math.sin(t*.9))
        head.keyframe_insert('rotation_quaternion',frame=frame)
scene.frame_set(1);bpy.context.view_layer.update()
report.update(body_status='audition-generated; review-required',head_status='head-turn-audition',
    face_status='facial controls require separate calibration; lipsync not applied',body_profile='body-profile.json')
(HERE/'capabilities.json').write_text(json.dumps(report,indent=2))
def aim(obj,at):obj.rotation_euler=(Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=center+Vector((0,-height*2.1,height*.65)))
camera=bpy.context.object;camera.data.lens=52;aim(camera,center+Vector((0,0,height*.53)));scene.camera=camera
for position,power,size in [((1,-2,3),500,3),((-2,-1,2),280,3),((0,2,3),450,2)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(position)*height*.7)
    light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;aim(light,center+Vector((0,0,height*.5)))
bpy.ops.mesh.primitive_plane_add(size=height*200,location=(center.x,center.y,low-.005))
floor=bpy.context.object;mat=bpy.data.materials.new('Studio floor');mat.diffuse_color=(.12,.16,.19,1);floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Studio world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.25,.3,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'audition.blend'))
if '--render' in sys.argv:
    (HERE/'frames').mkdir(exist_ok=True);scene.render.filepath=str(HERE/'frames/frame_');bpy.ops.render.render(animation=True)
else:
    scene.frame_set(60);scene.render.filepath=str(HERE/'audition-preview.png');bpy.ops.render.render(write_still=True)

