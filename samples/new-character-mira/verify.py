"""Audition motion gates using bone transforms only."""
import bpy,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'audition.blend'),use_scripts=False,load_ui=False)
rig=next(obj for obj in bpy.context.scene.objects if obj.type=='ARMATURE')
probes=['LeftHand','RightHand','LeftFoot','RightFoot','Hips','Head'];positions={name:[] for name in probes};rotations=[]
for frame in range(1,145):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    for name in probes:positions[name].append((rig.matrix_world@rig.pose.bones[name].head).copy())
    rotations.append(rig.pose.bones['Head'].matrix.to_quaternion().copy())
spans={name:max((p-values[0]).length for p in values) for name,values in positions.items()}
steps={name:max((b-a).length for a,b in zip(values,values[1:])) for name,values in positions.items()}
head=max(math.degrees(rotations[0].rotation_difference(q).angle) for q in rotations)
assert all(spans[name]<.00001 for name in ('LeftFoot','RightFoot','Hips')),'Root or feet moved'
assert max(spans[name] for name in ('LeftHand','RightHand'))>.03,'No body gesture'
assert max(steps.values())<.18,'Motion discontinuity'
assert head>8,'Head turn absent'
report={'frames':144,'motion_span_m':spans,'max_step_m':steps,'head_variation_degrees':head,
    'body_motion_gates':'passed','facial_lipsync':'unavailable: generated asset has no facial rig','production_catalog_approved':False}
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
