import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'scene_jobs/296cfdd87b0049759ebf460ee51e2814'
r=json.loads((D/'ready.json').read_text());lib=unreal.LevelSequenceEditorBlueprintLibrary
lib.open_level_sequence(unreal.load_asset(r['sequence']));lib.pause();lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(23)
(D/'review.json').write_text(json.dumps({'frame':23,'ok':True}))

