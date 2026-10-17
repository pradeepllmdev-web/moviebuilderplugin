import unreal,json
from pathlib import Path
r=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if isinstance(a,unreal.CineCameraActor):r.append({'name':a.get_actor_label(),'location':list(a.get_actor_location().to_tuple()),'lens':a.get_cine_camera_component().current_focal_length})
Path(__file__).resolve().parent.parent.joinpath('samples/lion-scramble/camera-check.json').write_text(json.dumps(r))
