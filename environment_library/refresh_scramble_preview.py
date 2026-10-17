import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-scramble';r=json.loads((D/'native.json').read_text());s=unreal.load_asset(r['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary
lib.close_level_sequence();lib.open_level_sequence(s);lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(96)
