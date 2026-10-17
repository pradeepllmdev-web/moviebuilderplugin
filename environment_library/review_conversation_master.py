import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
D=H/'movie_jobs'/((H/'conversation-active.txt').read_text().strip() if (H/'conversation-active.txt').exists() else 'bd5c6aec83ef40ef838a1ecb4b815c21')
r=json.loads((D/'master-result.json').read_text());lib=unreal.LevelSequenceEditorBlueprintLibrary
lib.open_level_sequence(unreal.load_asset(r['sequence']));lib.pause();lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(int((D/'review-frame.txt').read_text()))
