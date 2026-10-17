import unreal,json
from pathlib import Path
s=unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
r={'tick':str(s.get_tick_resolution()),'display':str(s.get_display_rate()),'bindings':[]}
for b in s.get_bindings():
 for t in b.get_tracks():
  if isinstance(t,unreal.MovieScene3DTransformTrack):
   c=t.get_sections()[0].get_all_channels()[0];keys=c.get_keys();r['bindings'].append({'name':b.get_name(),'keys':len(keys),'first':str(keys[0].get_time()),'last':str(keys[-1].get_time()),'doc':c.add_key.__doc__})
Path(__file__).resolve().parent.parent.joinpath('samples/lion-forest-adventure/keys.json').write_text(json.dumps(r))
