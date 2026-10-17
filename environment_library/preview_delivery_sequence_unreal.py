import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene';report=json.loads((D/'sequence.json').read_text())
sequence=unreal.load_asset(report['sequence'])
unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(144)
