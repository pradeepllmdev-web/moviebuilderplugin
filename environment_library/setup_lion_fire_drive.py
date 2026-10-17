import unreal,json,math,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-fire-drive'
try:
 record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);folder=record['level'].rsplit('/',1)[0]
 task=unreal.AssetImportTask();task.filename=str(H/'assets/kenney-car-kit/Models/FBX format/race.fbx');task.destination_path=folder+'/Car';task.destination_name='RaceCar';task.automated=True;task.save=True
 options=unreal.FbxImportUI();options.automated_import_should_detect_type=False;options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;options.import_as_skeletal=False;options.import_mesh=True;options.import_materials=True;options.import_textures=True
 options.static_mesh_import_data.set_editor_property('combine_meshes',True);task.options=options;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 mesh=next(unreal.load_asset(p) for p in task.imported_object_paths if isinstance(unreal.load_asset(p),unreal.StaticMesh))
 bounds=mesh.get_bounds();factor=450/(2*max(bounds.box_extent.x,bounds.box_extent.y))
 car=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0));car.set_actor_label('Leo_RaceCar');car.static_mesh_component.set_static_mesh(mesh);car.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
 def material(name,color):
  m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew());node=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-200,0);node.set_editor_property('constant',unreal.LinearColor(*color,1));unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR);unreal.MaterialEditingLibrary.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m);return m
 roadmat=material('RoadAsphalt',(.035,.035,.04));stripe=material('RoadPaint',(.85,.85,.75))
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
 def box(label,pos,scale,mat):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*pos));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(cube);a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_material(0,mat);return a
 box('FireEscapeRoad',[15000,0,-6],[400,8,.1],roadmat)
 for i in range(-5,85):box('RoadDash_'+str(i),[i*400,0,1],[1.5,.12,.02],stripe)
 from unreal_bridge.vfx import handle_add_vfx
 for i in range(13):
  for side in (-1,1):handle_add_vfx(dict(kind='fire',location=[i*2600,side*650,0],scale=2.1,label='RoadsideFire_'+str(i)+'_'+str(side),lit=i%3==0))
 lion=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Performance_Leo')
 def track(binding):
  t=binding.add_track(unreal.MovieScene3DTransformTrack);sec=t.add_section();sec.set_range(0,288);return sec.get_all_channels()
 car_channels=track(sequence.add_possessable(car));lion_binding=next(b for b in sequence.get_bindings() if any(o==lion for o in lib.get_bound_objects(sequence.get_binding_id(b))));lion_channels=track(lion_binding)
 camera_binding=next(b for b in sequence.get_bindings() if b.get_name()=='Transferred_Camera')
 for t in list(camera_binding.get_tracks()):
  if isinstance(t,unreal.MovieScene3DTransformTrack):camera_binding.remove_track(t)
 camera_channels=track(camera_binding);previous=None
 for frame in range(288):
  x=frame/24*2600;y=65*math.sin(frame/24*.7)
  # Car and driver use the same world path; the driver faces the road.
  transforms=[(car_channels,[x,y,12,0,0,90,factor,factor,factor]),(lion_channels,[x-40,y-25,0,0,0,-90,1,1,1])]
  if frame<96:pos=unreal.Vector(x+1000,y-750,420);target=unreal.Vector(x,y,100)
  elif frame<192:pos=unreal.Vector(x+100,y-850,230);target=unreal.Vector(x,y,105)
  else:pos=unreal.Vector(x+240,y-190,165);target=unreal.Vector(x-30,y-25,135)
  rot=unreal.MathLibrary.make_rot_from_x(target-pos);rotation=[rot.roll,rot.pitch,rot.yaw]
  if previous:rotation=[v+360*round((p-v)/360) for v,p in zip(rotation,previous)]
  previous=rotation;transforms.append((camera_channels,[pos.x,pos.y,pos.z]+rotation+[1,1,1]))
  for channels,values in transforms:
   for channel,value in zip(channels,values):channel.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for a in actors.get_all_level_actors():
  if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',6);a.set_actor_rotation(unreal.Rotator(pitch=-30,yaw=-45,roll=0),False)
  if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',2)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.set_current_time(48);lib.set_lock_camera_cut_to_viewport(True)
 (D/'action-ready.json').write_text(json.dumps({'ok':True,'car_source':'https://kenney.nl/assets/car-kit','license':'CC0','speed_kmh':93.6,'distance_m':310.9,'duration':12,'views':['road approach','side tracking','driver close-up'],'car_scale':factor},indent=2))
except Exception:(D/'action-ready.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
