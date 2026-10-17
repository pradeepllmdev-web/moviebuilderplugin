import unreal,json,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'delivery_scene';result={'ok':False,'states':{}}
try:
 base=json.loads((H/'physics_lab/import.json').read_text());actions=json.loads((D/'actions.json').read_text())
 folder='/Game/DeliveryStudies/'+Path(actions['directory']).name
 tools=unreal.AssetToolsHelpers.get_asset_tools()
 for entry in actions['states']:
  character=next(c for c in base['characters'] if c['name']==entry['character']);part=character['parts'][0]
  mesh=unreal.load_asset(part['mesh']);source=Path(entry['directory'])
  task=unreal.AssetImportTask();task.factory=unreal.FbxFactory();task.filename=str(source/(entry['state']+'.fbx'))
  task.destination_path=folder+'/'+entry['state'];task.destination_name=entry['state'];task.automated=True;task.replace_existing=False;task.save=True
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.import_as_skeletal=True;ui.import_mesh=False
  ui.import_animations=True;ui.import_materials=False;ui.import_textures=False;ui.skeleton=mesh.skeleton
  ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;task.options=ui
  tools.import_asset_tasks([task])
  anims=[a for p in unreal.EditorAssetLibrary.list_assets(task.destination_path,recursive=True) if isinstance((a:=unreal.load_asset(p)),unreal.AnimSequence)]
  if len(anims)!=1:raise RuntimeError('Expected exactly one animation for '+entry['state'])
  result['states'][entry['state']]={'animation':anims[0].get_path_name(),'character':entry['character'],
   'speed_cm_s':entry['native_speed_cm_s'],'duration':unreal.AnimationLibrary.get_sequence_length(anims[0])}
 result.update(ok=True,folder=folder)
except Exception:result['error']=traceback.format_exc()
(D/'import.json').write_text(json.dumps(result,indent=2))
