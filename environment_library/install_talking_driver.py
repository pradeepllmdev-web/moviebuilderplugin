import unreal,json,re,traceback,time,math
from pathlib import Path
from unreal_bridge.performance_production import _import_character
from unreal_bridge.audio import _add_audio_track
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-driver-talk';scene_dir=H/'samples/lion-drive-v2'
try:
 record=json.loads((scene_dir/'native.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if world.get_path_name().split('.')[0]!=record['level']:raise RuntimeError('Open improved supercar scene first')
 lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();sequence=unreal.load_asset(record['sequence']);package=D/'performance-v2';manifest=json.loads((package/'manifest.json').read_text());folder=record['level'].rsplit('/',1)[0]+'/TalkingDriver_'+str(int(time.time()))
 actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Performance_Leo');component=actor.get_component_by_class(unreal.SkeletalMeshComponent);old=component.get_editor_property('skeletal_mesh_asset')
 mesh,animation,character,notes=_import_character(package,manifest['characters'][0],folder,24,288)
 normalize=lambda n:re.sub(r'_\d{3}$','',str(n));materials={normalize(s.material_slot_name):s.material_interface for s in old.get_editor_property('materials')};slots=list(mesh.get_editor_property('materials'))
 for slot in slots:
  if normalize(slot.material_slot_name) not in materials:raise RuntimeError('Unmatched material '+str(slot.material_slot_name))
  slot.set_editor_property('material_interface',materials[normalize(slot.material_slot_name)])
 mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh);component.set_skeletal_mesh_asset(mesh);component.set_update_animation_in_editor(True)
 for binding in sequence.get_bindings():
  if binding.get_name()=='Performance_Leo':
   if not (D/'lowered-fit.json').exists():
    for t in binding.get_tracks():
     if isinstance(t,unreal.MovieScene3DTransformTrack):
      for sec in t.get_sections():
       for key in sec.get_all_channels()[2].get_keys():key.set_value(key.get_value()-8)
   for track in binding.get_tracks():
    if isinstance(track,unreal.MovieSceneSkeletalAnimationTrack):
     for section in track.get_sections():params=section.get_editor_property('params');params.set_editor_property('animation',animation);section.set_editor_property('params',params)
  if binding.get_name()=='AnimatedSteeringWheel':
   for track in binding.get_tracks():
    if isinstance(track,unreal.MovieScene3DTransformTrack):
     for section in track.get_sections():
      if not (D/'lowered-fit.json').exists():
       for key in section.get_all_channels()[2].get_keys():key.set_value(key.get_value()-15)
      for key in section.get_all_channels()[3].get_keys():
       f=key.get_time().frame_number.value;key.set_value(-math.degrees(.08*math.sin(f/24*.7)))
 for track in list(sequence.get_tracks()):
  if isinstance(track,unreal.MovieSceneAudioTrack):sequence.remove_track(track)
 for i,line in enumerate(manifest['audio']):
  task=unreal.AssetImportTask();task.filename=str(package/line['file']);task.destination_path=folder+'/Audio';task.destination_name='DriverLine_'+str(i);task.automated=True;task.save=True;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);sound=unreal.load_asset(folder+'/Audio/DriverLine_'+str(i))
  _add_audio_track(sequence,24,288,dict(sound=sound.get_path_name(),start_seconds=line['start_seconds']),sound)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.set_current_time(0);lib.set_current_time(210);lib.set_lock_camera_cut_to_viewport(True)
 (D/'lowered-fit.json').write_text(json.dumps({'driver_lowered_cm':8,'wheel_lowered_cm':15}))
 (D/'installed.json').write_text(json.dumps({'ok':True,'character':character,'audio_lines':len(manifest['audio']),'sequence':record['sequence'],'warnings':notes},indent=2))
except Exception:(D/'installed.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))

