import unreal,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library')
D=H/'scene_jobs/632af1db41d941b29c23bb519824d6dc';r=json.loads((D/'native.json').read_text());s=unreal.load_asset(r['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.open_level_sequence(s);lib.pause();lib.set_current_time(120);lib.set_lock_camera_cut_to_viewport(True)
(D/'playback-check.json').write_text(json.dumps({'ok':True,'review_frame':120,'binding_names':[b.get_name() for b in s.get_bindings()],'frame_count':s.get_playback_end()}))
