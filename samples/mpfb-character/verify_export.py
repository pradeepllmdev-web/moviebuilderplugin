"""Native motion/deformation checks and a portable GLB roundtrip."""
import bpy,sys,json,math,argparse
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));from bootstrap import initialize
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE);parser.add_argument('--name',default='rowan')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
HERE=args.directory.resolve();name=args.name;label=name.title()
initialize()
bpy.ops.wm.open_mainfile(filepath=str(HERE/(name+'.blend')),use_scripts=False,load_ui=False)
from mpfb.services.exportservice import ExportService
mesh=bpy.data.objects[label+'-Body'];rig=bpy.data.objects[label+'-Rig'];profile=json.loads((HERE/'face-profile.json').read_text())
def inspect(mesh,rig):
    keys=mesh.data.shape_keys.key_blocks;selected=['jawOpen','eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','browInnerUp']
    deltas={name:max((vertex.co-basis.co).length for vertex,basis in zip(keys[profile['mapping'][name]].data,keys[0].data)) for name in selected}
    values={name:[] for name in selected};positions={name:[] for name in ('LeftHand','RightHand','Hips','LeftFoot','RightFoot')};head=[]
    for frame in range(1,145):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        for name in selected:values[name].append(keys[profile['mapping'][name]].value)
        for name in positions:positions[name].append((rig.matrix_world@rig.pose.bones['mixamorig:'+name].head).copy())
        head.append(rig.pose.bones['mixamorig:Head'].matrix.to_quaternion().copy())
    spans={name:max((p-points[0]).length for p in points) for name,points in positions.items()}
    steps={name:max((b-a).length for a,b in zip(points,points[1:])) for name,points in positions.items()}
    head_span=max(math.degrees(head[0].rotation_difference(q).angle) for q in head)
    for name in selected:assert deltas[name]>1e-5,'Empty deformation '+name
    assert max(values['jawOpen'])>.1,'Speech motion missing'
    assert max(values['eyeBlinkLeft'])>.9 and max(values['eyeBlinkRight'])>.9,'Blink missing'
    assert all(spans[name]<1e-5 for name in ('Hips','LeftFoot','RightFoot')),'Feet/root motion'
    assert max(spans['LeftHand'],spans['RightHand'])>.03 and max(steps.values())<.18,'Gesture motion invalid'
    assert head_span>8,'Head motion missing'
    return {'shape_deformation_max_m':deltas,'animated_value_ranges':{name:[min(track),max(track)] for name,track in values.items()},
        'body_span_m':spans,'body_max_step_m':steps,'head_variation_degrees':head_span,'_samples':values}
report={'native':inspect(mesh,rig),'unreal_verified':False}
native_samples=report['native'].pop('_samples')
# Bake only masks on each shape; preserve expression keys and armature animation.
bpy.context.scene.frame_set(1)
facial_actions={obj.name:(obj.data.shape_keys.animation_data.action,obj.data.shape_keys.animation_data.action_slot)
    for obj in bpy.context.scene.objects if obj.type=='MESH' and obj.data.shape_keys
    and obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action}
ExportService.bake_modifiers_remove_helpers(mesh,bake_masks=True,bake_subdiv=False,remove_helpers=True,also_proxy=True)
for name,(action,slot) in facial_actions.items():
    keys=bpy.data.objects[name].data.shape_keys
    if keys:
        keys.animation_data_create();keys.animation_data.action=action
        if slot:keys.animation_data.action_slot=slot
bpy.ops.object.select_all(action='DESELECT')
characters=[obj for obj in bpy.context.scene.objects if obj.type in ('MESH','ARMATURE') and (obj==rig or obj.parent==rig)]
for obj in characters:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(HERE/(name+'-animated.glb')),export_format='GLB',use_selection=True,
    export_animation_mode='SCENE',export_anim_scene_split_object=False,export_force_sampling=True,export_morph=True,export_morph_animation=True,
    export_skins=True,export_apply=False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/(name+'-animated.glb')))
imported_rig=next(obj for obj in bpy.context.scene.objects if obj.type=='ARMATURE')
imported_mesh=next(obj for obj in bpy.context.scene.objects if obj.type=='MESH' and obj.data.shape_keys and profile['mapping']['jawOpen'] in obj.data.shape_keys.key_blocks)
report['glb_roundtrip']=inspect(imported_mesh,imported_rig)
imported_samples=report['glb_roundtrip'].pop('_samples')
report['facial_timing_max_error']=max(abs(a-b) for name,track in native_samples.items() for a,b in zip(track,imported_samples[name]))
assert report['facial_timing_max_error']<1e-5,'Facial export timing changed'
report['passed']=True
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print('VERIFIED',json.dumps(report),flush=True)
