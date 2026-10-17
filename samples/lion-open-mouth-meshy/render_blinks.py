import bpy,shutil,json
from pathlib import Path
BASE=Path(__file__).resolve().parent;H=BASE/'talking-blink';(H/'frames').mkdir(exist_ok=True)
for p in (BASE/'talking/frames').glob('frame_*.png'):shutil.copy2(p,H/'frames'/p.name)
bpy.ops.wm.open_mainfile(filepath=str(H/'lion-talking.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;s.cycles.samples=4
frames=list(range(26,34))+list(range(76,85))+list(range(142,151))
for frame in frames:
 s.frame_set(frame);s.render.filepath=str(H/'frames'/f'frame_{frame:04d}.png');bpy.ops.render.render(write_still=True)
(H/'render-manifest.json').write_text(json.dumps({'rerendered_blink_frames':frames,'unchanged_frames_copied_from':'../talking/frames','total_frames':192},indent=2))
