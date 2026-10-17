import unreal,json,time,sys,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'delivery_scene';sys.path.insert(0,str(H))
from scale_policy import POLICY
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 actions=json.loads((D/'import.json').read_text());assert actions['ok']
 latest=json.loads((H/'demos/latest-house.json').read_text());house=json.loads((Path(latest['directory'])/'build-result.json').read_text())
 editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert editor.load_level(house['level'])
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
 wood=unreal.load_asset('/Game/EnvironmentAssets/HouseStudies/'+latest['id']+'/M_wood_floor_deck')
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
 paper_path=actions['folder']+'/ParcelPaper'
 paper_exists=unreal.EditorAssetLibrary.does_asset_exist(paper_path)
 paper=unreal.load_asset(paper_path) if paper_exists else tools.create_asset('ParcelPaper',actions['folder'],unreal.Material,unreal.MaterialFactoryNew())
 if not paper_exists:
  color=mel.create_material_expression(paper,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.4,.23,.08,1)
  mel.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR);mel.recompile_material(paper);unreal.EditorAssetLibrary.save_loaded_asset(paper)
 def box(label,loc,size,material=None,movable=False):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label)
  c=a.static_mesh_component;c.set_static_mesh(cube)
  if material:c.set_material(0,material)
  if movable:c.set_mobility(unreal.ComponentMobility.MOVABLE)
  c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(unreal.Vector(*[s/100 for s in size]));return a
 # The house terrace rises 20 cm from its surrounding ground.
 crate=box('DeliveryCrate',(285,-420,40),(80,80,80),wood,movable=True)
 crate.static_mesh_component.set_collision_profile_name('PhysicsActor');crate.static_mesh_component.set_mass_override_in_kg('',12,True)
 crate.static_mesh_component.set_notify_rigid_body_collision(True);crate.static_mesh_component.set_simulate_physics(True)
 parcel=box('DeliveryParcel',(285,-780,90),(36,30,28),paper,movable=True);parcel.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
 base=json.loads((H/'physics_lab/import.json').read_text());chars=[]
 for name,location in [('cat',[285,-780]),('lion',[110,-520])]:
  part=next(c for c in base['characters'] if c['name']==name)['parts'][0];height=POLICY['characters_cm'][name]
  ground_z=-20 if name=='cat' else 0
  actor=actors.spawn_actor_from_class(unreal.Character,unreal.Vector(*location,ground_z+height/2+3));actor.set_actor_label('Delivery_'+name)
  actor.capsule_component.set_capsule_size(23 if name=='cat' else 28,height/2,True);actor.capsule_component.set_collision_profile_name('Pawn')
  actor.capsule_component.set_notify_rigid_body_collision(True)
  c=actor.mesh;c.set_skeletal_mesh_asset(unreal.load_asset(part['mesh']));c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
  c.set_relative_location(unreal.Vector(-part['origin'][0],-part['origin'][1],-part['origin'][2]),False,False)
  c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
  c.override_animation_data(unreal.load_asset(actions['states'][name+'_idle']['animation']),True,True,0,1)
  c.set_update_animation_in_editor(True)
  c.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
  movement=actor.character_movement;movement.set_editor_property('run_physics_with_no_controller',True);movement.max_step_height=35
  movement.set_editor_property('enable_physics_interaction',True);movement.set_editor_property('initial_push_force_factor',2000);movement.set_editor_property('push_force_factor',4000)
  chars.append({'name':name,'actor':actor.get_actor_label(),'mesh':part['mesh']})
 name='DeliveryMishap_'+time.strftime('%Y%m%d_%H%M%S');path='/Game/EnvironmentDemos/'+name
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
 (D/'scene.json').write_text(json.dumps({'ok':True,'level':path,'id':name,'characters':chars,'source_house':house['level']},indent=2))
except Exception:(D/'scene.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()},indent=2));raise
