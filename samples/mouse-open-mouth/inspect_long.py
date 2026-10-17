import bpy,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(H/'fresh-talking.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;s.frame_set(60);r=next(o for o in s.objects if o.type=='ARMATURE');body=next(o for o in s.objects if o.type=='MESH' and o.data.shape_keys and 'JawClose' in o.data.shape_keys.key_blocks)
points=[body.matrix_world@Vector(p) for p in body.bound_box];lo=min(p.z for p in points);hi=max(p.z for p in points);h=hi-lo;center=Vector((0,0,(lo+hi)/2));c=s.camera;c.data.type='ORTHO';c.data.ortho_scale=h*1.3;c.location=center+Vector((h*.25,-h*3,h*.12));c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();s.render.resolution_x=640;s.render.resolution_y=800;s.render.filepath=str(H/'long-shot-before.png');bpy.ops.render.render(write_still=True)
report={}
for name in ['Chest','Hips','LeftUpperArm','LeftLowerArm','LeftHand','RightUpperArm','RightLowerArm','RightHand']:
 b=r.pose.bones[name];report[name]={'head_world':[round(x,4) for x in r.matrix_world@b.head],'length':round(b.length,4)}
(H/'arm-check.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(H/'long-shot-setup.blend'))
