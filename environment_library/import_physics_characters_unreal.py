import unreal,json,traceback,time
from pathlib import Path
H=Path(__file__).resolve().parent/'physics_lab'
report={'ok':False,'characters':[]}
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 package=Path(json.loads((H/'latest-package.json').read_text())['directory'])
 manifest=json.loads((package/'manifest.json').read_text());folder='/Game/PhysicsLab/'+package.name
 tools=unreal.AssetToolsHelpers.get_asset_tools()
 for character in manifest['characters']:
  task=unreal.AssetImportTask();task.factory=unreal.FbxFactory();task.filename=str(package/character['file'])
  task.destination_path=folder+'/'+character['name'];task.automated=True;task.replace_existing=False;task.save=True
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.import_as_skeletal=True
  ui.import_mesh=True;ui.import_animations=True;ui.import_materials=True;ui.import_textures=True
  ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
  ui.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True);task.options=ui
  if not unreal.EditorAssetLibrary.does_asset_exist(task.destination_path+'/'+character['name']):tools.import_asset_tasks([task])
  assets=[unreal.load_asset(str(p)) for p in unreal.EditorAssetLibrary.list_assets(task.destination_path,recursive=True)]
  meshes=[a for a in assets if isinstance(a,unreal.SkeletalMesh)];animations=[a for a in assets if isinstance(a,unreal.AnimSequence)]
  parts=[]
  for mesh in meshes:
   bounds=mesh.get_imported_bounds();skel=mesh.skeleton
   animation=next((a for a in animations if a.get_editor_property('skeleton')==skel),None)
   if animation:
    available={str(n) for n in mesh.get_all_morph_target_names()}
    controller=animation.get_editor_property('controller');controller.open_bracket('Animal facial performance',False)
    try:
     for channel in character['facial_channels']:
      if channel['name'] not in available:continue
      lib=unreal.AnimationLibrary
      if lib.does_curve_exist(animation,channel['name'],unreal.RawCurveTrackTypes.RCT_FLOAT):lib.remove_curve(animation,channel['name'])
      lib.add_curve(animation,channel['name'],unreal.RawCurveTrackTypes.RCT_FLOAT,False)
      lib.add_float_curve_keys(animation,channel['name'],[i/manifest['fps'] for i in range(len(channel['values']))],channel['values'])
    finally:controller.close_bracket(False)
    unreal.EditorAssetLibrary.save_loaded_asset(animation)
   parts.append({'mesh':mesh.get_path_name(),'animation':animation.get_path_name() if animation else None,
    'origin':list(bounds.origin.to_tuple()),'extent':list(bounds.box_extent.to_tuple()),'morph_count':len(mesh.get_all_morph_target_names())})
  if not parts or any(not p['animation'] for p in parts):raise RuntimeError('Missing skeletal mesh or animation for '+character['name'])
  report['characters'].append({'name':character['name'],'parts':parts})
 report.update(ok=True,folder=folder)
except Exception:report['error']=traceback.format_exc()
(H/'import.json').write_text(json.dumps(report,indent=2))
