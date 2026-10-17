import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-jump';r=json.loads((D/'native.json').read_text());s=unreal.load_asset(r['sequence']);route=json.loads((D/'route.json').read_text())
for b in s.get_bindings():
 if b.get_name()!='Performance_Leo':continue
 for t in b.get_tracks():
  if isinstance(t,unreal.MovieScene3DTransformTrack):
   for sec in t.get_sections():
    for k in sec.get_all_channels()[2].get_keys():k.set_value(route[k.get_time().frame_number.value]['location_cm'][2])
unreal.EditorAssetLibrary.save_loaded_asset(s);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_current_time(1);lib.set_current_time(60);lib.set_lock_camera_cut_to_viewport(True)
(D/'sole-applied.json').write_text(json.dumps({'ok':True,'landing_review_frame':60}))
