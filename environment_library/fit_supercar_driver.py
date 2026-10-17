"""Fit the existing seated performance inside the measured car envelope."""
import unreal,json,math
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2';record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
# Keep the car unchanged. Fit the oversized anthropomorphic head under its roof.
scale=.60;seat=[-25.,-45.,45.]
old=json.loads((D/'fit-before.json').read_text())['Performance_Leo'];hips=old['joints']['Hips'];origin=old['location']
offset=[seat[i]-(hips[i]-origin[i])/.85*scale for i in range(3)]
for binding in sequence.get_bindings():
 if binding.get_name()!='Performance_Leo':continue
 for track in binding.get_tracks():
  if not isinstance(track,unreal.MovieScene3DTransformTrack):continue
  for section in track.get_sections():
   cc=section.get_all_channels()
   for channel in cc:
    for key in channel.get_keys():
     frame=key.get_time().frame_number.value;t=frame/24
     i=cc.index(channel)
     if i==0:value=t*2600+offset[0]
     elif i==1:value=65*math.sin(t*.7)+offset[1]
     elif i==2:value=offset[2]+1.2*math.sin(t*2.8)
     elif i in (6,7,8):value=scale
     else:continue
     key.set_value(value)
unreal.EditorAssetLibrary.save_loaded_asset(sequence);lib.set_current_time(1);lib.set_current_time(0)
(D/'seat-calibration.json').write_text(json.dumps({'scale':scale,'pelvis_target_cm':seat,'actor_offset_cm':offset,'car_length_m':4.6,'roof_top_cm':119.1},indent=2))

