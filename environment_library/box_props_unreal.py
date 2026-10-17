"""Independent, spawnable box and stands share the baked hand trajectory."""
import json,math,unreal
def apply(sequence,actors,folder,scene_folder,routes):
 paths=list(scene_folder.glob('actor_*/box-trajectory.json'))
 if not paths:return {'boxes':0}
 if len(paths)!=1:raise RuntimeError('Review box contact with one carrier at a time')
 data=json.loads(paths[0].read_text());frames=len(data['rows']);material=unreal.load_asset(folder+'/M_TrailBox');carrier=next(iter(routes.values()))
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();ground_cache={};ignore=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.SkeletalMeshActor) or a.get_actor_label().startswith('WindCue_')]
 def ground_at(x,y):
  key=(round(x/5),round(y/5))
  if key in ground_cache:return ground_cache[key]
  hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000),unreal.Vector(x,y,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,True);hit=hit.to_tuple() if hit is not None else (False,)
  if not hit[0]:raise RuntimeError('No ground for the box support')
  if abs(hit[5].z-carrier[-1]['location_cm'][2])>10 and abs(hit[5].z-carrier[0]['location_cm'][2])>10:raise RuntimeError('Box supports currently need a level surface within 10cm of the carrier ground')
  ground_cache[key]=hit[5].z;return hit[5].z
 if not material:
  material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_TrailBox',folder,unreal.Material,unreal.MaterialFactoryNew());color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.22,.09,.025,1);unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);unreal.MaterialEditingLibrary.recompile_material(material)
 def cube(label,position,scale,yaw=0):
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position));actor.set_actor_label('WindCue_'+label);actor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));actor.static_mesh_component.set_material(0,material);actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE);actor.set_actor_scale3d(unreal.Vector(*scale));actor.set_actor_rotation(unreal.Rotator(roll=0,pitch=0,yaw=yaw),False);ignore.append(actor);return actor
 def still(actor,position,scale,yaw):
  section=sequence.add_possessable(actor).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,frames)
  for channel,value in zip(section.get_all_channels(),list(position)+[0,0,yaw]+list(scale)):channel.add_key(unreal.FrameNumber(0),value);channel.add_key(unreal.FrameNumber(frames-1),value)
 def offset(x,y,lateral,forward,yaw):
  a=math.radians(yaw);return [x+lateral*math.cos(a)-forward*math.sin(a),y+lateral*math.sin(a)+forward*math.cos(a)]
 size=[v/100 for v in data['size_cm']];box=cube('TrailCrate',[0,0,0],size);section=sequence.add_possessable(box).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,frames);channels=section.get_all_channels();previous=None
 for row in data['rows']:
  if row['location_cm'] is None:raise RuntimeError('Box has no placement')
  position=list(row['location_cm'])
  # Box heights are above the ground under the box, like its stands, so pickup and set-down never pop.
  position[2]+=ground_at(position[0],position[1])
  yaw=row['box_yaw']
  if previous is not None:
   while yaw-previous>180:yaw-=360
   while yaw-previous<-180:yaw+=360
  previous=yaw
  for channel,value in zip(channels,position+[0,0,yaw]+size):channel.add_key(unreal.FrameNumber(row['frame']),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for index,stand in enumerate(data['stands']):
  x,y,top=stand['location_cm'];yaw=stand['yaw'];width,depth=stand['top_cm'];ground=ground_at(x,y);pieces=[([x,y,top-2+ground],[width/100,depth/100,.04])]
  for dx in [-width/2+3,width/2-3]:
   for dy in [-depth/2+3,depth/2-3]:pieces.append((offset(x,y,dx,dy,yaw)+[(top-4)/2+ground],[.04,.04,(top-4)/100]))
  for part,(position,scale) in enumerate(pieces):still(cube('BoxStand_'+str(index)+'_'+str(part),position,scale,yaw),position,scale,yaw)
 for index,bumper in enumerate(data['obstacles']):
  x,y,z=bumper['location_cm'];position=[x,y,z+ground_at(x,y)];scale=[.5,.08,.08];still(cube('BoxBumper_'+str(index),position,scale,bumper['yaw']),position,scale,bumper['yaw'])
 end=data['rows'][-1]
 return {'boxes':1,'id':data['end_state']['id'],'phase':data['end_state']['phase'],'stands':len(data['stands']),'size_cm':data['size_cm'],'end_location_cm':end['location_cm'],'keyed_contact_only':True}
