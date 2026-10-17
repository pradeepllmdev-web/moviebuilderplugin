"""Native eye material conversion for generated Rowan copies."""
import unreal
from pathlib import Path
def apply_eye_material(mesh_path):
 folder=mesh_path.rsplit('/',1)[0]
 source=str(Path(__file__).resolve().parent.parent/'.verification/mpfb/assets/eyes/materials/brown_eye.png')
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
 mesh=unreal.load_asset(mesh_path);slots=list(mesh.get_editor_property('materials'))
 for slot in slots:
  if 'high-poly' in str(slot.material_slot_name):slot.set_editor_property('material_interface',material)
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if isinstance(actor,unreal.SkeletalMeshActor) and actor.get_actor_label()=='Performance_Rowan':
   comp=actor.skeletal_mesh_component
   for i,slot in enumerate(slots):
    if 'high-poly' in str(slot.material_slot_name):comp.set_material(i,material)
 # Caller saves its generated level after setup.
 return {'ok':material.get_editor_property('blend_mode')==unreal.BlendMode.BLEND_MASKED,'material':material.get_path_name(),'texture':texture.get_path_name(),'alpha_mask':True}
