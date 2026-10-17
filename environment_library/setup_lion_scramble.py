import unreal,json,math,random,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-scramble';H=D.parents[1]
try:
 record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);folder=record['level'].rsplit('/',1)[0];route=json.loads((D/'route.json').read_text());actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
 catalog=json.loads((H/'environment_library/assets/prompt-catalog.json').read_text());asset=next(a for a in catalog['assets'] if a['id']=='rock.27e7c46097');scanned=unreal.load_asset(asset['path'])
 if not scanned:raise RuntimeError('Installed scanned rock not found')
 material=scanned.get_material(0)
 task=unreal.AssetImportTask();task.filename=str(D/'RockStep.fbx');task.destination_path=folder;task.destination_name='RockStep';task.automated=True;task.save=True;ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;ui.import_as_skeletal=False;ui.import_materials=False;task.options=ui;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);step=unreal.load_asset(folder+'/RockStep')
 def rock(label,mesh,pos,scale):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*pos));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(unreal.Vector(*scale));return a
 step.set_material(0,material);unreal.EditorAssetLibrary.save_loaded_asset(step)
 for i,(y,height) in enumerate([(22,12),(63,24),(102,36)]):rock('ScrambleContactRock_'+str(i),step,[0,y,height/2],[1.05,.43,height/100])
 rock('SideBraceContact',step,[52,40,44.5],[.25,.36,.89])
 bounds=scanned.get_bounds();rng=random.Random(84)
 for i in range(18):
  x=rng.choice([-1,1])*rng.uniform(66,150);y=rng.uniform(-5,160);size=rng.uniform(.8,1.7);bottom=(bounds.origin.z-bounds.box_extent.z)*size
  a=rock('ScannedBoulder_'+str(i),scanned,[x,y,-bottom],[size,size,size]);a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=rng.uniform(0,360),roll=0),False)
 def transform(binding):
  section=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,192);return section.get_all_channels()
 cc=transform(next(b for b in sequence.get_bindings() if b.get_name()=='Performance_Leo'))
 camera_binding=next(b for b in sequence.get_bindings() if b.get_name()=='Transferred_Camera')
 for track in list(camera_binding.get_tracks()):
  if isinstance(track,unreal.MovieScene3DTransformTrack):camera_binding.remove_track(track)
 cam=transform(camera_binding)
 for f,(x,y,z) in enumerate(route['root']):
  y=-y*100;z*=100
  for c,v in zip(cc,[0,y,z,0,0,0,1,1,1]):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  pos=unreal.Vector(280,y+330,z+200) if f<64 else unreal.Vector(280,y+150,z+150) if f<144 else unreal.Vector(140,y+230,z+145);target=unreal.Vector(0,y+10,z+100);rot=unreal.MathLibrary.make_rot_from_x(target-pos)
  for c,v in zip(cam,[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for a in actors.get_all_level_actors():
  if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',5);a.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=-75,roll=0),False)
  if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',2)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.set_current_time(1);lib.set_current_time(96);lib.set_lock_camera_cut_to_viewport(True)
 (D/'ready.json').write_text(json.dumps({'ok':True,'duration':8,'rise_m':.36,'scanned_dressing_rocks':18,'views':['front three-quarter','side','face reveal'],'contact_surfaces':'rounded stepped rocks with scanned-rock material; surrounding scanned rocks are dressing'},indent=2))
except Exception:(D/'ready.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
