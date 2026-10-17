"""Restore approved lion materials on the new test copy and open its camera preview."""
import unreal,json,re,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'samples/lion-branch'
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 record=json.loads((D/'native.json').read_text());level=record['level']
 if not level.startswith('/Game/StudioProduction/'):raise RuntimeError('Unexpected level')
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 current=world.get_path_name().split('.')[0]
 if current!=level and (unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()):raise RuntimeError('Save Unreal changes before opening the lion test')
 mesh=unreal.load_asset(record['characters'][0]['mesh']);old=unreal.load_asset('/Game/PhysicsLab/package_20261015_101957/lion/lion.lion')
 normalize=lambda name:re.sub(r'_\d{3}$','',str(name))
 source={normalize(s.material_slot_name):s.material_interface for s in old.get_editor_property('materials')}
 slots=list(mesh.get_editor_property('materials'))
 for slot in slots:slot.set_editor_property('material_interface',source[normalize(slot.material_slot_name)])
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 if current!=level:unreal.EditorLoadingAndSavingUtils.load_map(level)
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if isinstance(actor,unreal.DirectionalLight):actor.light_component.set_editor_property('intensity',3)
  if isinstance(actor,unreal.SkyLight):actor.light_component.set_editor_property('intensity',1.5)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 sequence=unreal.load_asset(record['sequence']);unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
 trajectory=json.loads((D/'trajectory.json').read_text())
 for binding in sequence.get_bindings():
  bound=unreal.LevelSequenceEditorBlueprintLibrary.get_bound_objects(sequence.get_binding_id(binding))
  if not any(isinstance(o,unreal.SkeletalMeshActor) and o.get_actor_label()=='Performance_Leo' for o in bound):continue
  track=binding.add_track(unreal.MovieScene3DTransformTrack);section=track.add_section();section.set_range(0,480)
  channels=section.get_all_channels()
  previous=None
  for key in trajectory:
   x,y,z=key['position'];yaw=-key['yaw']
   if previous is not None:yaw+=360*round((previous-yaw)/360)
   previous=yaw
   for channel,value in zip(channels,[x*100,-y*100,z*100,0,0,yaw,1,1,1]):
    channel.add_key(unreal.FrameNumber(key['frame']),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence)
 unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
 unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(48)
 (D/'ready.json').write_text(json.dumps({'ok':True,'level':level,'sequence':record['sequence'],'duration':20}))
except Exception:
 (D/'ready.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
