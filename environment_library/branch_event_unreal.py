"""A small keyed branch audition; deliberately separate from collision physics."""
import unreal

def frame_camera(sequence,events,frames):
 cues=[e for e in events if e['type']=='branch_fall']
 if not cues:return 0
 x,y=cues[0]['position_cm'];target=unreal.Vector(x/2,y/2,100);pos=target+unreal.Vector(600,350,250);rot=unreal.MathLibrary.make_rot_from_x(target-pos);changed=0
 for binding in sequence.get_bindings():
  for track in binding.get_tracks():
   if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
    for section in track.get_sections():
     for key in section.get_all_channels()[0].get_keys():key.set_value(28)
   if 'Transferred_Camera' in binding.get_name() and isinstance(track,unreal.MovieScene3DTransformTrack):
    for section in track.get_sections():
     values=[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]
     for channel,value in zip(section.get_all_channels(),values):
      for key in list(channel.get_keys()):channel.remove_key(key)
      channel.add_key(unreal.FrameNumber(0),value);channel.add_key(unreal.FrameNumber(frames-1),value)
     changed+=1
 if not changed:raise RuntimeError('No cinematic camera track found for branch framing')
 return changed

def add_branches(sequence,actors,events,folder,frames):
 cues=[e for e in events if e['type']=='branch_fall']
 if not cues:return 0
 material=unreal.load_asset(folder+'/M_BranchWood')
 if not material:
  material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_BranchWood',folder,unreal.Material,unreal.MaterialFactoryNew())
  color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.12,.045,.012,1)
  unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);unreal.MaterialEditingLibrary.recompile_material(material)
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 for index,event in enumerate(cues):
  x,y=event['position_cm']
  hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000),unreal.Vector(x,y,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE,True)
  data=hit.to_tuple() if hit is not None else (False,)
  if not data[0]:raise RuntimeError('No ground at the branch landing site')
  ground=data[5].z
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,ground+260));actor.set_actor_label('WindCue_Branch_'+str(index))
  component=actor.static_mesh_component;component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'));component.set_material(0,material);component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);component.set_mobility(unreal.ComponentMobility.MOVABLE)
  section=sequence.add_possessable(actor).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,frames);channels=section.get_all_channels()
  for frame in range(frames):
   u=max(0,min(1,(frame/24-event['time'])/event['duration']));z=ground+4+256*(1-u*u)
   values=[x,y,z,0,90,12*u,.06,.06,event['length_cm']/100]
   for channel,value in zip(channels,values):channel.add_key(unreal.FrameNumber(frame),value)
 return len(cues)
