import bpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent
acting='--acting' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(H/('riverbank-race-acting.blend' if acting else 'riverbank-race.blend')),use_scripts=False,load_ui=False)
s=bpy.context.scene;D=H/('frames-acting' if acting else 'frames');D.mkdir(exist_ok=True)
for f in range(1,s.frame_end+1):
 s.frame_set(f);s.render.filepath=str(D/f'{f-1:05d}.png');bpy.ops.render.render(write_still=True)
print('RACE_RENDER_COMPLETE')
