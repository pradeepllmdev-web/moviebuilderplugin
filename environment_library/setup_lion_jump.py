import unreal,json,math,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-jump'
try:
 record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);folder=record['level'].rsplit('/',1)[0];actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
 asset=next(a for a in json.loads((H/'environment_library/assets/prompt-catalog.json').read_text())['assets'] if a['id']=='rock.27e7c46097');scan=unreal.load_asset(asset['path']);material=scan.get_material(0)
 task=unreal.AssetImportTask();task.filename=str(H/'samples/lion-scramble/RockStep.fbx');task.destination_path=folder;task.destination_name='LandingRock';task.automated=True;task.save=True;ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;ui.import_as_skeletal=False;ui.import_materials=False;task.options=ui;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=unreal.load_asset(folder+'/LandingRock');mesh.set_material(0,material);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 for name,y in [('TakeoffRock',-60),('LandingRock',50)]:
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,y,12.5));a.set_actor_label(name);a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(unreal.Vector(1.2,.70,.25))
 for x in (-110,110):
  for y in (-65,50):
   a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0));a.set_actor_label('RockEdgeDressing');a.static_mesh_component.set_static_mesh(scan);bounds=scan.get_bounds();size=.6;a.set_actor_scale3d(unreal.Vector(size,size,size));a.set_actor_location(unreal.Vector(x-bounds.origin.x*size,y-bounds.origin.y*size,-(bounds.origin.z-bounds.box_extent.z)*size),False,False)
 lion=next(b for b in sequence.get_bindings() if b.get_name()=='Performance_Leo');sec=lion.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,288);cc=sec.get_all_channels()
 for row in json.loads((D/'route.json').read_text()):
  for c,v in zip(cc,row['location_cm']+[0,0,0,1,1,1]):c.add_key(unreal.FrameNumber(row['frame']),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for b in sequence.get_bindings():
  for t in b.get_tracks():
   if isinstance(t,unreal.MovieSceneFloatTrack) and str(t.get_property_name())=='CurrentFocalLength':
    for sec in t.get_sections():
     for k in sec.get_all_channels()[0].get_keys():k.set_value(32)
  if b.get_name()!='Transferred_Camera':continue
  for t in list(b.get_tracks()):
   if isinstance(t,unreal.MovieScene3DTransformTrack):b.remove_track(t)
  sec=b.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,288);channels=sec.get_all_channels();pos=unreal.Vector(420,220,230);target=unreal.Vector(0,-5,105);rot=unreal.MathLibrary.make_rot_from_x(target-pos)
  for frame in (0,287):
   for c,v in zip(channels,[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):c.add_key(unreal.FrameNumber(frame),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for a in actors.get_all_level_actors():
  if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',5);a.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=-135,roll=0),False)
  if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',3)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.open_level_sequence(sequence);lib.set_current_time(48);lib.set_lock_camera_cut_to_viewport(True)
 (D/'ready.json').write_text(json.dumps({'ok':True,'duration':12,'gap_cm':40,'platform_height_cm':25,'camera':'one fixed view','dialogue':'That looked closer from over there.','landing':'animation and ground correction; no rigid-body impact simulation'},indent=2))
except Exception:(D/'ready.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
