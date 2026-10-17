import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
latest=json.loads((H/'demos/latest-house.json').read_text());D=Path(latest['directory'])
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
 if isinstance(actor,unreal.PointLight):actor.light_component.set_editor_property('intensity',1.5)
report=json.loads((D/'build-result.json').read_text());path=report['level']+'_LightingFixed'
assert not unreal.EditorAssetLibrary.does_asset_exist(path)
assert unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),path)
report['level']=path
(D/'build-result.json').write_text(json.dumps(report,indent=2))
