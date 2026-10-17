import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene'
world=unreal.EditorLevelLibrary.get_game_world();actor=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Character) if a.get_actor_label()=='Delivery_cat')
report=[]
for obj,prop in [(actor.capsule_component,'on_component_hit'),(actor,'on_actor_hit')]:
 try:
  delegate=obj.get_editor_property(prop)
  report.append({'property':prop,'type':str(type(delegate)),'can_bind':hasattr(delegate,'add_callable')})
 except Exception as error:report.append({'property':prop,'error':str(error)})
(D/'event-api.json').write_text(json.dumps(report,indent=2))
