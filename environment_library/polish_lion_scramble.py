import unreal,json,math,random
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-scramble';record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);route=json.loads((D/'route.json').read_text());actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rng=random.Random(27)
for a in actors.get_all_level_actors():
 label=a.get_actor_label()
 if label.startswith('ScannedBoulder_'):
  mesh=a.static_mesh_component.get_editor_property('static_mesh');bounds=mesh.get_bounds();size=rng.uniform(.5,.85);x=rng.choice([-1,1])*rng.uniform(95,150);y=rng.uniform(-10,170)
  a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False);a.set_actor_scale3d(unreal.Vector(size,size,size));a.set_actor_location(unreal.Vector(x-bounds.origin.x*size,y-bounds.origin.y*size,-(bounds.origin.z-bounds.box_extent.z)*size),False,False)
 if label.startswith('ScrambleContactRock_'):
  scale=a.get_actor_scale3d();a.set_actor_scale3d(unreal.Vector(scale.x,.30,scale.z))
 if isinstance(a,unreal.DirectionalLight):a.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=135,roll=0),False)
 if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',3)
for binding in sequence.get_bindings():
 for track in binding.get_tracks():
  if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
   for sec in track.get_sections():
    for key in sec.get_all_channels()[0].get_keys():key.set_value(40 if key.get_time().frame_number.value>=144 else 28)
 if binding.get_name()!='Transferred_Camera':continue
 for track in binding.get_tracks():
  if not isinstance(track,unreal.MovieScene3DTransformTrack):continue
  for section in track.get_sections():
   cc=section.get_all_channels()
   for i,c in enumerate(cc):
    for key in c.get_keys():
     f=key.get_time().frame_number.value;_,by,bz=route['root'][f];y=-by*100;z=bz*100
     pos=unreal.Vector(-420,y+350,z+230) if f<64 else unreal.Vector(-400,y+220,z+180) if f<144 else unreal.Vector(-170,y+250,z+155);target=unreal.Vector(0,y+10,z+(115 if f>=144 else 90));rot=unreal.MathLibrary.make_rot_from_x(target-pos)
     key.set_value([pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1][i])
unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_current_time(1);lib.set_current_time(96);lib.set_lock_camera_cut_to_viewport(True)
(D/'visual-polish.json').write_text(json.dumps({'ok':True,'dressing':'moved outside body corridor; smaller boulders','step_depth_cm':30,'camera':'full body front/side, final face view'}))


