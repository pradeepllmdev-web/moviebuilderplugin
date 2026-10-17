import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-forest-adventure'
seq=unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Performance_Leo')
state={'i':0,'wait':0};frames=[0,119,239,299,359,400];rows=[];token=None
unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0)
def tick(dt):
 global token
 state['wait']+=1
 if state['wait']<3:return
 state['wait']=0;p=actor.get_actor_location();rows.append({'frame':frames[state['i']],'location_cm':[p.x,p.y,p.z]});state['i']+=1
 if state['i']==len(frames):
  (D/'movement-check.json').write_text(json.dumps({'positions':rows,'camera_cuts':sum(len(t.get_sections()) for t in seq.get_tracks() if isinstance(t,unreal.MovieSceneCameraCutTrack))},indent=2))
  unreal.unregister_slate_post_tick_callback(token);unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(48);return
 unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(frames[state['i']])
token=unreal.register_slate_post_tick_callback(tick)
