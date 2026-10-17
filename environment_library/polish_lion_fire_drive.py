import unreal,json
from pathlib import Path
from unreal_bridge import vfx
D=Path(__file__).resolve().parent.parent/'samples/lion-fire-drive';record=json.loads((D/'native.json').read_text());folder=record['level'].rsplit('/',1)[0]
# Use varying noise channels for the flame silhouette; the source alpha is opaque.
old_folder=vfx.MAT_FOLDER;vfx.MAT_FOLDER=folder+'/FireMaterials'
try:
 code=vfx.FIRE_CODE.replace(').a',').r').replace(').b',').g')
 parent=vfx._material('M_RoadFire',unreal.BlendMode.BLEND_TRANSLUCENT,code,[('Height','scalar',798.),('Scale','scalar',147.),('Rise','scalar',260.),('Intensity','scalar',1.5)])
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label().startswith('RoadsideFire_') and isinstance(a,unreal.DynamicMeshActor):
   mi=vfx._instance(a.get_actor_label(),'LocalFire',parent,{'Height':798.,'Scale':147.,'Rise':260.,'Intensity':1.5})
   a.get_dynamic_mesh_component().set_material(0,mi)
finally:vfx.MAT_FOLDER=old_folder
sequence=unreal.load_asset(record['sequence'])
for binding in sequence.get_bindings():
 if binding.get_name()!='Performance_Leo':continue
 for track in binding.get_tracks():
  if isinstance(track,unreal.MovieScene3DTransformTrack):
   for section in track.get_sections():
    for key in section.get_all_channels()[2].get_keys():key.set_value(22)
unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0);unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(48)
(D/'polish-ready.json').write_text(json.dumps({'ok':True,'flame_noise':'varying red/green channels','driver_raised_cm':22}))
