import unreal,json,math,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-branch'
try:
 record=json.loads((D/'native.json').read_text());world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if world.get_path_name().split('.')[0]!=record['level']:raise RuntimeError('Open the forest test first')
 lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();sequence=unreal.load_asset(record['sequence'])
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for actor in actors.get_all_level_actors():
  if isinstance(actor,unreal.DirectionalLight):
   actor.set_actor_rotation(unreal.Rotator(pitch=-30,yaw=-65,roll=0),False)
   c=actor.light_component;c.set_editor_property('intensity',8);c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',5600)
  if isinstance(actor,unreal.SkyLight):actor.light_component.set_editor_property('intensity',2.5)
  if isinstance(actor,unreal.ExponentialHeightFog):actor.component.set_editor_property('fog_density',.008)
  if isinstance(actor,unreal.PostProcessVolume):
   settings=actor.get_editor_property('settings')
   for name,value in [('override_auto_exposure_bias',True),('auto_exposure_bias',1.0),('override_color_grading_intensity',True),('color_grading_intensity',0.)]:settings.set_editor_property(name,value)
   actor.set_editor_property('settings',settings)
 trajectory=json.loads((D/'trajectory.json').read_text())
 for binding in sequence.get_bindings():
  if binding.get_name()!='Transferred_Camera':continue
  for track in list(binding.get_tracks()):
   if isinstance(track,unreal.MovieScene3DTransformTrack):binding.remove_track(track)
  section=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,480);channels=section.get_all_channels();previous=None
  for key in trajectory:
   frame=key['frame'];x,y,z=key['position'];target=unreal.Vector(x*100,-y*100,100)
   offset=(240,480,140) if frame<96 else (260,480,140) if frame<216 else (300,440,120) if frame<336 else (260,480,140) if frame<408 else (0,440,120)
   pos=target+unreal.Vector(*offset);rot=unreal.MathLibrary.make_rot_from_x(target-pos);rotation=[rot.roll,rot.pitch,rot.yaw]
   if previous:rotation=[v+360*round((p-v)/360) for v,p in zip(rotation,previous)]
   previous=rotation
   for channel,value in zip(channels,[pos.x,pos.y,pos.z]+rotation+[1,1,1]):channel.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(48)
 (D/'morning.json').write_text(json.dumps({'ok':True,'views':['closer walking','three-quarter running','elevated circle','closer dance']}))
except Exception:(D/'morning.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
