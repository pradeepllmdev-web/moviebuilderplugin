import unreal,json
from pathlib import Path
lib=unreal.LevelSequenceEditorBlueprintLibrary
lib.pause()
lib.set_current_time(0)
lib.set_lock_camera_cut_to_viewport(True)
(Path(__file__).resolve().parent.parent/'samples/lion-jump/playback-ready.json').write_text(json.dumps({'ok':True,'frame':0}))
