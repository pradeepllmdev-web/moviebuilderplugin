"""Update only generated audition cameras, leaving source characters intact."""
import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'movie_jobs/7e09850e11ef4b06a27b9c02b7f19248';movie=json.loads((D/'ready.json').read_text());item=movie['shots'][1]
pos=unreal.Vector(240,370,165);target=unreal.Vector(-40,160,120);rot=unreal.MathLibrary.make_rot_from_x(target-pos);changed=[]
for path in [item['report']['sequence'],movie['master']['sequence'].rsplit('/',1)[0]+'/Shot_2']:
 sequence=unreal.load_asset(path);count=0
 for binding in sequence.get_bindings():
  for track in binding.get_tracks():
   if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
    for section in track.get_sections():
     for key in section.get_all_channels()[0].get_keys():key.set_value(42)
   if 'Transferred_Camera' in binding.get_name() and isinstance(track,unreal.MovieScene3DTransformTrack):
    for section in track.get_sections():
     for channel,value in zip(section.get_all_channels(),[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):
      for key in channel.get_keys():key.set_value(value)
     count+=1
 if count!=1:raise RuntimeError('Expected one generated camera transform')
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);changed.append(count)
(D/'closeup-framing-check.json').write_text(json.dumps({'ok':True,'camera_tracks_updated':changed}))
