"""Verify anatomical jaw/eyes and exported animation with small reports."""
import bpy,json,hashlib,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'leo-talking.blend'),use_scripts=False,load_ui=False)
rig=bpy.data.objects['Lion_Realistic'];meshes=[obj for obj in rig.children_recursive if obj.type=='MESH']
def inspect(rig,meshes):
    jaw=[];lid=[];feet=[];tongue=[];closures=[]
    for frame in range(1,193):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        jaw.append(rig.pose.bones['Leo-Jaw'].rotation_quaternion.angle)
        lid.append(next(obj.data.shape_keys.key_blocks['eyeBlinkLeft'].value for obj in meshes if obj.data.shape_keys and 'eyeBlinkLeft' in obj.data.shape_keys.key_blocks))
        feet.append((rig.matrix_world@rig.pose.bones['mixamorig:LeftFoot'].head).copy())
        tongue.append((rig.matrix_world@rig.pose.bones['Leo-Tongue'].head).copy())
        closures.append(next(obj.data.shape_keys.key_blocks['mouthClose'].value for obj in meshes if obj.data.shape_keys and 'mouthClose' in obj.data.shape_keys.key_blocks))
    assert max(jaw)>.15 and jaw[0]<.001 and jaw[-1]<.001,'Jaw motion gate'
    assert max(lid)>.99,'Blink gate'
    assert max((point-feet[0]).length for point in feet)<1e-5,'Foot gate'
    assert rig.data.bones['Leo-Tongue'].parent.name=='Leo-Jaw','Tongue must follow jaw'
    assert any('upper tooth' in obj.name for obj in meshes) and any('lower tooth' in obj.name for obj in meshes),'Separate teeth missing'
    assert max(closures)>.01,'Lip closure motion missing'
    tongue_motion=max((point-tongue[0]).length for point in tongue)
    assert tongue_motion>.01,'Tongue did not follow the moving jaw'
    return {'jaw_max_degrees':math.degrees(max(jaw)),'blink_max':max(lid),'lip_closure_max':max(closures),'tongue_motion_m':tongue_motion,'tongue_is_jaw_child':True,'feet_stationary':True},jaw,lid
native,jaw,lid=inspect(rig,meshes);report={'native':native,'unreal_verified':False}
scene=bpy.context.scene;scene.frame_set(1)
body=bpy.data.objects['output_unwrapped'];mask=body.modifiers['Hide old head'];index=list(body.modifiers).index(mask)
body.modifiers.move(index,0);bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.modifier_apply(modifier=mask.name)
bpy.ops.object.select_all(action='DESELECT')
for obj in [rig]+meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(HERE/'leo-animated.glb'),export_format='GLB',use_selection=True,
    export_animation_mode='SCENE',export_anim_scene_split_object=False,export_force_sampling=True,export_morph=True,export_morph_animation=True,export_skins=True,export_apply=False)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(HERE/'leo-animated.glb'))
rig=next(obj for obj in bpy.context.scene.objects if obj.type=='ARMATURE');meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
report['glb_roundtrip'],new_jaw,new_lid=inspect(rig,meshes)
report['jaw_timing_max_error']=max(abs(a-b) for a,b in zip(jaw,new_jaw));report['blink_timing_max_error']=max(abs(a-b) for a,b in zip(lid,new_lid))
assert report['jaw_timing_max_error']<1e-4 and report['blink_timing_max_error']<1e-5,'Export changed facial timing'
plan=json.loads((HERE/'application.json').read_text());report['source_unchanged']=hashlib.sha256(Path(plan['source']).read_bytes()).hexdigest()==plan['source_sha256']
assert report['source_unchanged'];report['passed']=True
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print('ANATOMY_AND_EXPORT_VERIFIED',flush=True)
