"""Lightweight keyed leaf drift in generated scenes; no foliage mesh edits."""
import math
import unreal
def add_wind_cues(sequence,actors,events,folder,frames):
 gusts=[e for e in events if e['type']=='wind_gust']
 for actor in list(actors.get_all_level_actors()):
  if actor.get_actor_label().startswith('WindCue_'):actors.destroy_actor(actor)
 from branch_event_unreal import add_branches
 branches=add_branches(sequence,actors,events,folder,frames)
 if not gusts:return {'leaves':0,'branches':branches}
 material=unreal.load_asset(folder+'/M_WindLeaf')
 if not material:
  material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_WindLeaf',folder,unreal.Material,unreal.MaterialFactoryNew());material.set_editor_property('two_sided',True)
  color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.12,.25,.035,1);unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);unreal.MaterialEditingLibrary.recompile_material(material)
 for index in range(10):
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector());actor.set_actor_label('WindCue_'+str(index));actor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'));actor.static_mesh_component.set_material(0,material);actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
  section=sequence.add_possessable(actor).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,frames);channels=section.get_all_channels()
  for frame in range(frames):
   t=frame/24;event=next((e for e in gusts if e['time']<=t<=e['time']+e.get('duration',2)),None);u=(t-event['time'])/event.get('duration',2) if event else 0;scale=.08 if event else 0
   values=[-220+440*u+index*9,100+index*17,110+index*9-45*u,30*math.sin(t*8+index),t*140+index*31,t*75,scale,scale*.45,scale]
   for channel,value in zip(channels,values):channel.add_key(unreal.FrameNumber(frame),value)
 return {'leaves':10,'branches':branches,'effect':'keyed leaf drift; tree wind depends on installed foliage materials'}
