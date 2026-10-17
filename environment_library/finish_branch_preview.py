import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-branch'
lib=unreal.LevelSequenceEditorBlueprintLibrary;s=lib.get_current_level_sequence()
for b in s.get_bindings():
 if b.get_name()!='Story_FallenBranch':continue
 for t in b.get_tracks():
  if isinstance(t,unreal.MovieScene3DTransformTrack):
   for sec in t.get_sections():
    for key in sec.get_all_channels()[2].get_keys():key.set_value(max(8,key.get_value()))
unreal.EditorAssetLibrary.save_loaded_asset(s)
lib.set_current_time(0)
