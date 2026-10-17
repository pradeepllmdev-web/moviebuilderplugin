import bpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'leo-talking.blend'),use_scripts=False,load_ui=False)
bpy.context.scene.render.resolution_x=640;bpy.context.scene.render.resolution_y=640
bpy.context.scene.cycles.samples=4
(HERE/'frames').mkdir(exist_ok=True);bpy.context.scene.render.filepath=str(HERE/'frames/frame_');bpy.ops.render.render(animation=True)
