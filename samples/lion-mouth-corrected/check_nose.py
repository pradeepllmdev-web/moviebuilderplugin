"""Regression gate: speech must not deform the nose or upper muzzle."""
import bpy,json,math
from pathlib import Path
from mathutils import Quaternion,Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'lion-talking.blend'),use_scripts=False,load_ui=False)
rig=bpy.data.objects['Lion_Realistic'];surface=bpy.data.objects['output_unwrapped'];scene=bpy.context.scene
scene.frame_set(1);transform=rig.matrix_world.inverted()@surface.matrix_world
protected=[v.index for v in surface.data.vertices if 1.28<(transform@v.co).z<1.37 and abs((transform@v.co).x)<.10 and (transform@v.co).y<-.30]
assert protected,'No nose/upper-muzzle probes'
keys=surface.data.shape_keys.key_blocks
assert all(abs(keys[name].value)<1e-6 for name in ('Lion_JawOpen','Lion_Round','Lion_Wide','Lion_Close','Lion_Press')),'Legacy nose-level speech shape is active'
jaw=rig.pose.bones['Repair-Jaw'];axis=jaw.bone.matrix_local.to_quaternion().inverted()@Vector((1,0,0))
def positions(opened):
    jaw.rotation_quaternion=Quaternion(axis,math.radians(14) if opened else 0)
    for key in keys:
        if key.name.startswith('Repair_'):key.value=1 if opened else 0
    rig.update_tag();surface.update_tag();bpy.context.view_layer.update()
    evaluated=surface.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    points=[(surface.matrix_world@mesh.vertices[index].co).copy() for index in protected];evaluated.to_mesh_clear();return points
closed=positions(False);opened=positions(True)
error=max((a-b).length for a,b in zip(closed,opened));assert error<1e-6,'Speech moved the nose/upper muzzle'
report={'protected_probe_count':len(protected),'nose_speech_displacement_max_m':error,'mouth_line_z':1.244,
    'legacy_nose_level_shapes_disabled':True,'passed':True}
(HERE/'nose-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
