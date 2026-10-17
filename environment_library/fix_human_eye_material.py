"""Convert the existing free eye texture to a native Unreal material on this copy."""
import unreal,json,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/rowan-eye-test'
try:
 r=json.loads((D/'import-job.json').read_text())['result'];folder=r['level'].rsplit('/',1)[0]+'/Character_0'
 source=json.loads((D/'eye-source-material.json').read_text())[0]['images'][0]['path']
 texture=unreal.load_asset(folder+'/RowanEyeColour')
 if not texture:
  task=unreal.AssetImportTask();task.filename=str(Path(source).resolve());task.destination_path=folder;task.destination_name='RowanEyeColour';task.automated=True;task.save=True
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);texture=unreal.load_asset(folder+'/RowanEyeColour')
 if not texture:raise RuntimeError('Eye texture import failed')
 material=unreal.load_asset(folder+'/M_RowanEyes')
 if not material:material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_RowanEyes',folder,unreal.Material,unreal.MaterialFactoryNew())
 lib=unreal.MaterialEditingLibrary
 lib.delete_all_material_expressions(material)
 node=lib.create_material_expression(material,unreal.MaterialExpressionTextureSample);node.texture=texture
 lib.connect_material_property(node,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
 # MPFB packs the clear outer eye shell into the texture alpha.
 # Opaque FBX materials hide the iris behind that shell.
 material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
 lib.connect_material_property(node,'A',unreal.MaterialProperty.MP_OPACITY_MASK)
 rough=lib.create_material_expression(material,unreal.MaterialExpressionConstant);rough.r=.35;lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
 lib.recompile_material(material);unreal.EditorAssetLibrary.save_loaded_asset(material)
 mesh=unreal.load_asset(r['characters'][0]['mesh']);slots=list(mesh.get_editor_property('materials'))
 for slot in slots:
  if 'high-poly' in str(slot.material_slot_name):slot.set_editor_property('material_interface',material)
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if isinstance(actor,unreal.SkeletalMeshActor):
   comp=actor.skeletal_mesh_component
   for i,slot in enumerate(slots):
    if 'high-poly' in str(slot.material_slot_name):comp.set_material(i,material)
 unreal.EditorLoadingAndSavingUtils.save_current_level()
 (D/'eye-material-fix.json').write_text(json.dumps({'ok':True,'material':material.get_path_name()}))
except Exception:(D/'eye-material-fix.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
