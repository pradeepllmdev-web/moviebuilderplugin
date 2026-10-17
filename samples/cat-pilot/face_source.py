import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'preview.blend'),use_scripts=False,load_ui=False)
r=bpy.data.objects['Armature'];o=bpy.data.objects['CatPilot'];r.animation_data_clear()
for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
o.data.shape_keys.key_blocks['Eyes'].value=0
s=bpy.context.scene;target=r.matrix_world@r.pose.bones['Head'].head
print('HEAD',list(target));print('TRANSFORMS',list(o.location),list(o.scale),list(r.scale))
c=s.camera;c.location=target+Vector((0,-2.1,.25));c.data.lens=65;target+=Vector((0,0,.23));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();s.render.resolution_x=s.render.resolution_y=640;s.render.filepath=str(H/'face-source.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'face-source.blend'))
