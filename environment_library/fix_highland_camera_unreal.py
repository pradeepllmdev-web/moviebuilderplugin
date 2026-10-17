import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
items=json.loads((H/'demos/environment-collection.json').read_text())
item=next(i for i in items if i['biome']=='rocky_highland')
D=H/'demos'/item['id']
report=json.loads((D/'build-result.json').read_text())
location=unreal.Vector(-4500,-6000,3500);target=unreal.Vector(1000,10000,1800)
rotation=unreal.MathLibrary.find_look_at_rotation(location,target)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(location,rotation,unreal.Name())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
 if actor.get_actor_label()=='EnvironmentPreviewCamera':
  actor.set_actor_location(location,False,False)
  actor.set_actor_rotation(rotation,False)
path=report['level']+'_CameraFixed'
assert not unreal.EditorAssetLibrary.does_asset_exist(path)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
report.update(level=path,camera={'location':[-4500,-6000,3500],'target':[1000,10000,1800]})
(D/'build-result.json').write_text(json.dumps(report,indent=2))
item['level']=path
(H/'demos/environment-collection.json').write_text(json.dumps(items,indent=2))
