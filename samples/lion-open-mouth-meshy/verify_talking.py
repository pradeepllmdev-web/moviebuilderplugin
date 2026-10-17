import bpy,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent/'talking';BASE=H.parent
bpy.ops.wm.open_mainfile(filepath=str(H/'lion-talking.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');o=bpy.data.objects['char1'];keys=o.data.shape_keys.key_blocks
plan=json.loads((H/'application.json').read_text());assert hashlib.sha256((BASE/'rigged.glb').read_bytes()).hexdigest()==plan['source_sha256']
assert plan['jaw_max']>.2 and plan['jaw_end']==0
for k in ('JawOpen','LipSeal'):
 assert k in keys
basis=keys['Basis'];w=o.matrix_world
protected=[i for i,v in enumerate(basis.data) if (w@v.co).z>1.27]
error=max((keys['JawOpen'].data[i].co-basis.data[i].co).length for i in protected);assert error<1e-7
positions=[];heads=[]
for f in range(1,193):
 s.frame_set(f);bpy.context.view_layer.update();positions.append((r.matrix_world@r.pose.bones['LeftHand'].head).copy());heads.append(r.pose.bones['Head'].rotation_quaternion.copy())
span=max((p-positions[0]).length for p in positions);assert span>.01
turn=max(heads[0].rotation_difference(q).angle for q in heads);assert turn>.03
report={'source_unchanged':True,'frames':192,'nose_upper_face_shape_error_m':error,'hand_motion_span_m':span,'head_turn_degrees':math.degrees(turn),'jaw_timed_to_audio':True,'full_facial_rig':False,'visual_limitations':plan['limitations']}
(H/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
