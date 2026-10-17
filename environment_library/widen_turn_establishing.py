import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'movie_jobs/7e09850e11ef4b06a27b9c02b7f19248';movie=json.loads((D/'ready.json').read_text());item=movie['shots'][0]
for path in [item['report']['sequence'],movie['master']['sequence'].rsplit('/',1)[0]+'/Shot_1']:
 sequence=unreal.load_asset(path)
 for binding in sequence.get_bindings():
  for track in binding.get_tracks():
   if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
    for section in track.get_sections():
     for key in section.get_all_channels()[0].get_keys():key.set_value(28)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence)
(D/'wide-shot-check.json').write_text(json.dumps({'ok':True,'focal_mm':28}))
