import unreal,json,re
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');job=json.loads((H/'samples/echo-inspector/job-status.json').read_text())
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);reports=[]
normalize=lambda name:re.sub(r'_\d{3}$','',name)
for shot in job['result']['shots']:
 if not shot['native_scene'].startswith('/Game/StudioProduction/'):raise RuntimeError('Unexpected target')
 if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():raise RuntimeError('Save current map before polishing movie')
 for char in shot['transfer_characters']:
  mesh=unreal.load_asset(char['mesh']);slots=list(mesh.get_editor_property('materials'))
  old=unreal.load_asset('/Game/PhysicsLab/package_20261015_101957/'+('lion/lion.lion' if char['name']=='Leo' else 'cat/cat.cat'))
  source={normalize(str(s.material_slot_name)):s.material_interface for s in old.get_editor_property('materials')}
  for slot in slots:
   key=normalize(str(slot.material_slot_name))
   if key not in source:raise RuntimeError('Unmatched character material '+key)
   slot.set_editor_property('material_interface',source[key])
  mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh);reports.append({'name':char['name'],'matched_slots':len(slots)})
 unreal.EditorLoadingAndSavingUtils.load_map(shot['native_scene'])
 for actor in actors.get_all_level_actors():
  if isinstance(actor,unreal.DirectionalLight):
   actor.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=140,roll=0),False);actor.light_component.set_editor_property('intensity',3)
  if isinstance(actor,unreal.SkyLight):actor.light_component.set_editor_property('intensity',1.5)
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();unreal.EditorLoadingAndSavingUtils.save_map(world,shot['native_scene'])
(H/'samples/echo-inspector/polish.json').write_text(json.dumps({'ok':True,'materials':reports}))
