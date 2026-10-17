import unreal,json,math
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2';sequence=unreal.load_asset(json.loads((D/'native.json').read_text())['sequence'])
for binding in sequence.get_bindings():
 if binding.get_name()!='Transferred_Camera':continue
 for track in binding.get_tracks():
  if not isinstance(track,unreal.MovieScene3DTransformTrack):continue
  for section in track.get_sections():
   channels=section.get_all_channels()
   for i,channel in enumerate(channels):
    for key in channel.get_keys():
     f=key.get_time().frame_number.value
     if f<192:continue
     t=f/24;x=t*2600;y=65*math.sin(t*.7);pos=unreal.Vector(x+160,y-170,108);target=unreal.Vector(x-25,y-45,82);rot=unreal.MathLibrary.make_rot_from_x(target-pos)
     key.set_value([pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1][i])
unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.LevelSequenceEditorBlueprintLibrary.pause();unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0);unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(48);unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
