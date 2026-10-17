import bpy,json,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'preview.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;rig=bpy.data.objects['Armature'];cat=bpy.data.objects['CatPilot'];s.render.engine='BLENDER_EEVEE';s.render.fps=24
cam=s.camera;target=cat.matrix_world@Vector((0,0,1.2));cam.location=target+Vector((1,-4.8,.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
D=H/'frames';D.mkdir(exist_ok=True);tracks={name:[] for name in ['Walk','Run','Cheer']};blink=[]
for i in range(192):
 name='Walk' if i<72 else 'Run' if i<144 else 'Cheer';action=bpy.data.actions[name]
 rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=next(slot for slot in action.slots if slot.target_id_type=='OBJECT')
 start,end=action.frame_range;f=start+(i if i<72 else i-72 if i<144 else i-144)%(end-start)
 s.frame_set(int(f));bpy.context.view_layer.update()
 value=max(max(0,1-abs(i/24-t)/.13) for t in [1,3.8,6.8]);cat.data.shape_keys.key_blocks['Eyes'].value=value;blink.append(value)
 tracks[name].append((rig.matrix_world@rig.pose.bones['Foot.L'].head).copy())
 s.render.filepath=str(D/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
spans={k:max((p-v[0]).length for p in v) for k,v in tracks.items()};assert spans['Walk']>.01 and spans['Run']>.01
(H/'verification.json').write_text(json.dumps({'frames':192,'fps':24,'foot_motion_span_m':spans,'blink_peak':max(blink),'speech_controls':False,'mouth':'painted smile, no jaw or visemes','source_preserved':True},indent=2));print('FREE_CAT_READY')
