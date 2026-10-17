import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
p=json.loads((H/'demos/CharacterStories/plate-request.json').read_text())
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(p['level'])
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if any(actor.get_actor_label().startswith(label) for label in p.get('hide_labels',[])):
  actor.set_is_temporarily_hidden_in_editor(True)
loc=p['location'];target=p['target']
if p.get('ground_camera'):
 from unreal_bridge.forest import _ground_hit
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ignore=[a for a in actors if not a.get_actor_label().endswith('_Ground')]
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 hit=_ground_hit(world,loc[0],loc[1],ignore)
 if hit:
  loc[2]=hit[0].z+180;target[2]=hit[0].z+130
location=unreal.Vector(*loc);rotation=unreal.MathLibrary.find_look_at_rotation(location,unreal.Vector(*target))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(location,rotation,unreal.Name())
