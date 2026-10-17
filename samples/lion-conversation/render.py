import bpy,sys,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);HERE=args.directory.resolve()
bpy.ops.wm.open_mainfile(filepath=str(HERE/'lion-talking.blend'),use_scripts=False,load_ui=False)
(HERE/'frames').mkdir(exist_ok=True)
bpy.context.scene.cycles.samples=4
bpy.context.scene.render.filepath=str(HERE/'frames/frame_');bpy.ops.render.render(animation=True)
