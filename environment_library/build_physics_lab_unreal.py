"""Build real Character capsules, collision geometry and a simulated rigid-body crate."""
import unreal,json,time,traceback,sys
from pathlib import Path
H=Path(__file__).resolve().parent/'physics_lab'
sys.path.insert(0,str(H.parent))
from scale_policy import POLICY
try:
 data=json.loads((H/'import.json').read_text());assert data['ok']
 name='AnimalPhysics_'+time.strftime('%Y%m%d_%H%M%S');folder=data['folder']
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
 def mat(name,color):
  if unreal.EditorAssetLibrary.does_asset_exist(folder+'/'+name):return unreal.load_asset(folder+'/'+name)
  m=tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
  c=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(*color,1)
  mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR);mel.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m);return m
 ground=mat('LabGround',[.2,.24,.25]);orange=mat('LabCrate',[.55,.19,.045]);blue=mat('LabRamp',[.06,.22,.3])
 def box(label,loc,size,material,movable=False):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label)
  c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,material);c.set_collision_profile_name('BlockAll')
  if movable:c.set_mobility(unreal.ComponentMobility.MOVABLE)
  a.set_actor_scale3d(unreal.Vector(*[n/100 for n in size]));return a
 box('LabFloor',(0,0,-50),(5000,2500,100),ground)
 ramp=box('LabRamp',(-600,0,70),(900,1500,40),blue);ramp.set_actor_rotation(unreal.Rotator(pitch=10,yaw=0,roll=0),False)
 box('LabPlatform',(350,0,90),(1050,1500,180),blue)
 box('LabStep',(800,250,192.5),(150,300,25),blue)
 box('LabWall',(1650,0,450),(80,1600,900),ground)
 crate=box('LabPhysicsCrate',(650,-250,250),(140,140,140),orange,True)
 c=crate.static_mesh_component;c.set_collision_profile_name('PhysicsActor');c.set_mass_override_in_kg('',18,True)
 c.set_notify_rigid_body_collision(True);c.set_simulate_physics(True)
 results=[]
 for item,y in zip(data['characters'],[-250,250]):
  height=POLICY['characters_cm'][item['name']]
  part=max(item['parts'],key=lambda p:p['extent'][2]);mesh=unreal.load_asset(part['mesh']);animation=unreal.load_asset(part['animation'])
  actor=actors.spawn_actor_from_class(unreal.Character,unreal.Vector(-1600,y,height/2+3));actor.set_actor_label('Physics_'+item['name'])
  capsule=actor.capsule_component;capsule.set_capsule_size(28 if item['name']=='lion' else 23,height/2,True);capsule.set_collision_profile_name('Pawn')
  comp=actor.mesh;comp.set_skeletal_mesh_asset(mesh);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
  comp.set_relative_location(unreal.Vector(-part['origin'][0],-part['origin'][1],-part['origin'][2]),False,False)
  comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE);comp.override_animation_data(animation,True,True,0,1)
  comp.set_update_animation_in_editor(True)
  move=actor.character_movement;move.set_editor_property('run_physics_with_no_controller',True)
  move.max_walk_speed=260;move.max_step_height=35;move.set_walkable_floor_angle(45)
  move.set_editor_property('enable_physics_interaction',True)
  move.set_editor_property('push_force_factor',8000);move.set_editor_property('initial_push_force_factor',3000)
  results.append({'name':item['name'],'actor':actor.get_actor_label(),'height_cm':height,'mesh':part['mesh'],
                  'animation':part['animation'],'capsule_half_height':height/2,'mesh_offset':list(comp.get_editor_property('relative_location').to_tuple())})
 from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
 from unreal_bridge.moods import handle_apply_mood
 handle_add_clouds({});handle_add_post_process({});handle_apply_mood({'mood':'blockbuster','weather':False})
 location=unreal.Vector(-1400,-2100,1000);target=unreal.Vector(0,0,220)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(location,unreal.MathLibrary.find_look_at_rotation(location,target),unreal.Name())
 path='/Game/EnvironmentDemos/'+name;assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
 report={'ok':True,'level':path,'characters':results,'crate_mass_kg':18,'camera':{'location':[-1400,-2100,1000],'target':[0,0,220]},
         'status':'Character grounding and rigid-body test arena; foot IK and natural hit reactions are not implemented'}
 (H/'lab.json').write_text(json.dumps(report,indent=2))
except Exception:(H/'lab.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()},indent=2));raise
