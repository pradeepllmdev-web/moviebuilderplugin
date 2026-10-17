import unreal,json,math
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2';record=json.loads((D/'native.json').read_text());folder=record['level'].rsplit('/',1)[0];sequence=unreal.load_asset(record['sequence'])
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
task=unreal.AssetImportTask();task.filename=str(D/'SteeringRing.fbx');task.destination_path=folder+'/Car';task.destination_name='SteeringRing';task.automated=True;task.save=True
ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;ui.import_as_skeletal=False;ui.import_materials=True;ui.import_textures=True;task.options=ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=next(unreal.load_asset(p) for p in task.imported_object_paths if isinstance(unreal.load_asset(p),unreal.StaticMesh))
wheel=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0));wheel.set_actor_label('AnimatedSteeringWheel');wheel.static_mesh_component.set_static_mesh(mesh);wheel.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
sec=sequence.add_possessable(wheel).add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,288);channels=sec.get_all_channels()
for f in range(288):
 t=f/24;x=t*2600;y=65*math.sin(t*.7);bob=7+1.2*math.sin(t*2.8)
 for c,v in zip(channels,[x+36.75,y-35,bob+101.25,math.degrees(.1*math.sin(t*.7)),0,0,.85,.85,.85]):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
for binding in sequence.get_bindings():
 if binding.get_name()=='Performance_Leo':
  for track in binding.get_tracks():
   if isinstance(track,unreal.MovieScene3DTransformTrack):
    for section in track.get_sections():
     cc=section.get_all_channels()
     for i in (6,7,8):
      for k in cc[i].get_keys():k.set_value(.85)
     for k in cc[2].get_keys():k.set_value(k.get_value()+12)
for a in actors.get_all_level_actors():
 if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',8)
 if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',3)
checks=[]
for binding in sequence.get_bindings():
 if binding.get_name().startswith('Supercar_Wheel_'):
  track=next(t for t in binding.get_tracks() if isinstance(t,unreal.MovieScene3DTransformTrack));keys=track.get_sections()[0].get_all_channels()[4].get_keys();checks.append({'name':binding.get_name(),'spin_degrees_first':keys[0].get_value(),'spin_degrees_last':keys[-1].get_value(),'samples':len(keys)})
unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_current_time(0);lib.set_current_time(48);lib.set_lock_camera_cut_to_viewport(True)
(D/'motion-check.json').write_text(json.dumps({'ok':True,'wheels':checks,'steering_wheel_keys':288,'driver_scale':.85,'physics':'keyframed motion; not vehicle dynamics simulation'},indent=2))
