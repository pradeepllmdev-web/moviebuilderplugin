"""A solid bench under the measured seat (seat.json from the Blender build). Collision-free prop like the box stands."""
import json,math,unreal
SIZE_CM=(70,32)  # width (lateral), depth (forward)
def apply(sequence,actors,folder,scene_folder,routes):
 paths=list(scene_folder.glob('actor_*/seat.json'))
 if not paths:return {'benches':0}
 if len(paths)!=1:raise RuntimeError('Seat review supports one seated character at a time')
 seat=json.loads(paths[0].read_text());route=next(iter(routes.values()));root=route[seat['frame']]['location_cm'];yaw=route[seat['frame']]['yaw']
 a=math.radians(yaw);lateral,forward=seat['lateral_cm'],seat['forward_cm']-3
 x=root[0]+lateral*math.cos(a)-forward*math.sin(a);y=root[1]+lateral*math.sin(a)+forward*math.cos(a)
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();ignore=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.SkeletalMeshActor)]
 hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000),unreal.Vector(x,y,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,True);hit=hit.to_tuple() if hit is not None else (False,)
 if not hit[0]:raise RuntimeError('No ground under the seat')
 ground=hit[5].z;top=seat['top_cm']
 if abs(ground-root[2])>10:raise RuntimeError('Seat needs level ground within 10 cm of the character')
 material=unreal.load_asset(folder+'/M_TrailBox')
 if not material:
  material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_TrailBox',folder,unreal.Material,unreal.MaterialFactoryNew());color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.22,.09,.025,1);unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);unreal.MaterialEditingLibrary.recompile_material(material)
 position=[x,y,ground+top/2];scale=[SIZE_CM[0]/100,SIZE_CM[1]/100,top/100]
 bench=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position));bench.set_actor_label('WindCue_SeatBench');component=bench.static_mesh_component
 component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));component.set_material(0,material);component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);component.set_mobility(unreal.ComponentMobility.MOVABLE)
 bench.set_actor_scale3d(unreal.Vector(*scale));bench.set_actor_rotation(unreal.Rotator(roll=0,pitch=0,yaw=yaw),False)
 section=sequence.add_possessable(bench).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,len(route))
 for channel,value in zip(section.get_all_channels(),position+[0,0,yaw]+scale):channel.add_key(unreal.FrameNumber(0),value);channel.add_key(unreal.FrameNumber(len(route)-1),value)
 return {'benches':1,'top_cm':top,'location_cm':[round(x,1),round(y,1),round(ground,1)],'size_cm':list(SIZE_CM)}
