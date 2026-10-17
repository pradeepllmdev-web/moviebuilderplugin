import bpy,sys
from pathlib import Path
root=Path(__file__).parent.resolve()
body='--body' in sys.argv
attention='--attention' in sys.argv
performance='--performance' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(root/('the-last-lantern-performance.blend' if performance else 'the-last-lantern-attention.blend' if attention else 'the-last-lantern-body.blend' if body else 'the-last-lantern.blend')),load_ui=False,use_scripts=False)
destination=root/('performance-frames' if performance else 'attention-frames' if attention else 'body-frames' if body else 'frames');destination.mkdir(exist_ok=True)
bpy.context.scene.render.filepath=str(destination/'frame_')
bpy.ops.render.render(animation=True)
print('RENDER_COMPLETE',flush=True)
