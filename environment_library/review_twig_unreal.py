import unreal,json
from pathlib import Path
lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_current_time(36);lib.set_lock_camera_cut_to_viewport(True)
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/twig-review.json').write_text(json.dumps({'ok':True,'frame':36}))
