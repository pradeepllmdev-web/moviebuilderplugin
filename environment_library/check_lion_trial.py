import unreal,json
from pathlib import Path
report=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if a.get_actor_label().startswith(('Performance_','Transferred_')):
  origin,extent=a.get_actor_bounds(False)
  report.append(dict(name=a.get_actor_label(),location=str(a.get_actor_location()),bounds_center=str(origin),bounds_extent=str(extent)))
Path(__file__).resolve().parent.parent.joinpath('samples/lion-trial/bounds.json').write_text(json.dumps(report,indent=2))
