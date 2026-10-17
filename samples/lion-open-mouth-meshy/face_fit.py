import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'audition.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;s.frame_set(1)
r=next(o for o in s.objects if o.type=='ARMATURE')
r.animation_data_clear()
for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
for o in s.objects:
 if o.type=='MESH':o.animation_data_clear()
c=s.camera;c.animation_data_clear();c.location=(0,-1.55,1.4);c.rotation_euler=(Vector((0,0,1.4))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=60
s.cycles.samples=8;s.render.filepath=str(H/'face-neutral.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'face-fit.blend'))
