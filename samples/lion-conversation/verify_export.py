"""Native and portable lion motion checks; only small diagnostics are printed."""
import bpy,json,math,hashlib,sys,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);HERE=args.directory.resolve()
bpy.ops.wm.open_mainfile(filepath=str(HERE/'lion-talking.blend'),use_scripts=False,load_ui=False)
rig=bpy.data.objects['Lion_Realistic'];meshes=[obj for obj in rig.children_recursive if obj.type=='MESH']
lighting=[obj.name for obj in bpy.context.scene.objects if obj.type in ('CAMERA','LIGHT')]
profile=json.loads((HERE/'face-profile.json').read_text());application=json.loads((HERE/'application.json').read_text())
def sample(rig,meshes):
    controls={name:next(obj.data.shape_keys.key_blocks[key] for obj in meshes if obj.data.shape_keys and key in obj.data.shape_keys.key_blocks)
              for name,key in profile['mapping'].items()}
    tracks={name:[] for name in controls};positions={name:[] for name in ('LeftHand','RightHand','Hips','LeftFoot','RightFoot')};heads=[]
    if 'repair' in application:tracks['jaw_angle_radians']=[]
    for frame in range(1,193):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        for name,key in controls.items():tracks[name].append(key.value)
        if 'repair' in application:tracks['jaw_angle_radians'].append(rig.pose.bones[application['repair']['jaw_bone']].rotation_quaternion.angle)
        for name in positions:positions[name].append((rig.matrix_world@rig.pose.bones['mixamorig:'+name].head).copy())
        heads.append(rig.pose.bones['mixamorig:Head'].matrix.to_quaternion().copy())
    spans={name:max((p-points[0]).length for p in points) for name,points in positions.items()}
    steps={name:max((b-a).length for a,b in zip(points,points[1:])) for name,points in positions.items()}
    head=max(math.degrees(heads[0].rotation_difference(q).angle) for q in heads)
    jaw=tracks['jaw_angle_radians'] if 'repair' in application else tracks['jawOpen']
    assert max(jaw)>(.05 if 'repair' in application else .2) and jaw[0]<.01 and jaw[-1]<.01,'Jaw speech gate'
    assert max(tracks['eyeBlinkLeft'])>.99 and max(tracks['eyeBlinkRight'])>.99,'Blink gate'
    assert all(spans[name]<1e-5 for name in ('Hips','LeftFoot','RightFoot')),'Feet/root gate'
    assert max(spans['LeftHand'],spans['RightHand'])>.03 and max(steps.values())<.18,'Body gesture gate'
    assert head>8,'Head gate'
    return {'facial_ranges':{name:[min(values),max(values)] for name,values in tracks.items()},'body_span_m':spans,'body_max_step_m':steps,'head_range_degrees':head},tracks
native,reference=sample(rig,meshes);report={'native':native,'unreal_verified':False}
bpy.context.scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT')
for obj in [rig]+meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(HERE/'lion-animated.glb'),export_format='GLB',use_selection=True,
    export_animation_mode='SCENE',export_anim_scene_split_object=False,export_force_sampling=True,
    export_morph=True,export_morph_animation=True,export_skins=True,export_apply=False)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(HERE/'lion-animated.glb'))
rig=next(obj for obj in bpy.context.scene.objects if obj.type=='ARMATURE');meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
report['glb_roundtrip'],imported=sample(rig,meshes)
report['facial_timing_max_error']=max(abs(a-b) for name,values in reference.items() for a,b in zip(values,imported[name]))
assert report['facial_timing_max_error']<(1e-4 if 'repair' in application else 1e-5),'Facial export timing changed'
report['source_unchanged']=hashlib.sha256(Path(application['source']).read_bytes()).hexdigest()==application['source_sha256']
assert report['source_unchanged'],'Source file changed'
report['passed']=True;(HERE/'verification.json').write_text(json.dumps(report,indent=2));print('LION_VERIFIED',report['passed'],flush=True)
with bpy.data.libraries.load(str(HERE/'lion-talking.blend'),link=False) as (source,target):
    target.objects=lighting;target.worlds=['Lion World']
for obj in target.objects:
    if obj:bpy.context.scene.collection.objects.link(obj)
scene=bpy.context.scene;scene.camera=next(obj for obj in target.objects if obj and obj.type=='CAMERA');scene.world=target.worlds[0]
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=640 if 'repair' in application else 768;scene.render.resolution_y=scene.render.resolution_x;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.frame_set(157)
scene.render.filepath=str(HERE/'glb-blink.png');bpy.ops.render.render(write_still=True)
