"""Low table and cup for the drink activity (drink.json and seat.json from the Blender build). Collision-free props like the bench."""
import json,math,unreal
def apply(sequence,actors,folder,scene_folder,routes):
 paths=list(scene_folder.glob('actor_*/drink.json'))
 if not paths:return {'tables':0}
 drink=json.loads(paths[0].read_text());seat=json.loads(paths[0].with_name('seat.json').read_text());route=next(iter(routes.values()));root=route[seat['frame']]['location_cm'];yaw=route[seat['frame']]['yaw'];a=math.radians(yaw)
 def world(x,y):  # rig space (cm, forward is -Y) to level space
  lateral,forward=x,-y;return root[0]+lateral*math.cos(a)-forward*math.sin(a),root[1]+lateral*math.sin(a)+forward*math.cos(a)
 ground=root[2];material=unreal.load_asset(folder+'/M_TrailBox');table=drink['table']
 def spawn(label,mesh,position,scale):
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position));actor.set_actor_label(label);component=actor.static_mesh_component
  component.set_static_mesh(unreal.load_asset(mesh));component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);component.set_mobility(unreal.ComponentMobility.MOVABLE)
  if material:component.set_material(0,material)
  actor.set_actor_scale3d(unreal.Vector(*scale));actor.set_actor_rotation(unreal.Rotator(roll=0,pitch=0,yaw=yaw),False)
  section=sequence.add_possessable(actor).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,len(route))
  for channel,value in zip(section.get_all_channels(),list(position)+[0,0,yaw]+list(scale)):channel.add_key(unreal.FrameNumber(0),value);channel.add_key(unreal.FrameNumber(len(route)-1),value)
 tx,ty=world(*table['center']);thick=table['thickness_cm']
 spawn('WindCue_DrinkTable','/Engine/BasicShapes/Cube',[tx,ty,ground+table['top_cm']-thick/2],[table['size_cm'][0]/100,table['size_cm'][1]/100,thick/100])
 cx,cy=world(drink['cup_cm'][0],drink['cup_cm'][1]);cup=drink['cup']
 spawn('WindCue_DrinkCup','/Engine/BasicShapes/Cylinder',[cx,cy,ground+drink['cup_cm'][2]],[2*cup['radius_cm']/100,2*cup['radius_cm']/100,cup['height_cm']/100])
 return {'tables':1,'top_cm':table['top_cm'],'cup_location_cm':[round(cx,1),round(cy,1),round(ground+drink['cup_cm'][2],1)]}
