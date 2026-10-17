import bpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False,load_ui=False)
(D/'frames').mkdir(exist_ok=True);s=bpy.context.scene;s.render.filepath=str(D/'frames/frame_');bpy.ops.render.render(animation=True)
