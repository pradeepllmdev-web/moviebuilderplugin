import bpy
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
D=H/'scene_jobs/836a5fa2dacb4d9fa0b8015f37fe96cb'
bpy.ops.wm.open_mainfile(filepath=str(D/'actor_0/scene.blend'),use_scripts=False)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rig=next(o for o in s.objects if o.type=='ARMATURE');head=rig.matrix_world@rig.pose.bones['mixamorig:Head'].head
c=s.camera;c.animation_data_clear();c.location=head+Vector((0,-1.2,.06));c.rotation_euler=(head-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=55
s.render.resolution_x=512;s.render.resolution_y=512;s.cycles.samples=8;s.render.filepath=str(D/'blender-check.png');bpy.ops.render.render(write_still=True)
