"""Unreal weather placement and nondestructive material variants for generated sets."""
import unreal

def apply_weather(spec,folder,actors):
 from unreal_bridge.effects import handle_add_weather
 kind=spec['type'];mel=unreal.MaterialEditingLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
 cache={};changed=0
 def constant(value):
  n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);n.r=value;return n
 def connect(source,target,name):mel.connect_material_expressions(source,'',target,name)
 for actor in (actors.get_all_level_actors() if spec["wetness"]>0 and spec["snow_cover"]==0 else []):
  for comp in actor.get_components_by_class(unreal.MeshComponent):
   for slot in range(comp.get_num_materials()):
    original=comp.get_material(slot)
    if not original:continue
    # Imported instances may have elaborate parent parameters; leave them intact until supported.
    if not isinstance(original,unreal.Material):continue
    key=original.get_path_name()
    if key not in cache:
     mat=tools.duplicate_asset('M_Weather_'+str(len(cache)),folder,original)
     if not mat:raise RuntimeError('Could not duplicate weather material')
     base=mel.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
     if not base:continue
     if spec['wetness']>0:
      dark=constant(1-.35*spec['wetness']);multiply=mel.create_material_expression(mat,unreal.MaterialExpressionMultiply);connect(base,multiply,'A');connect(dark,multiply,'B');mel.connect_material_property(multiply,'',unreal.MaterialProperty.MP_BASE_COLOR)
      mel.connect_material_property(constant(.65-.55*spec['wetness']),'',unreal.MaterialProperty.MP_ROUGHNESS)
     mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);cache[key]=mat
    comp.set_material(slot,cache[key]);changed+=1
 snow_caps=0
 if spec['snow_cover']>0:
  mat=tools.create_asset('M_SnowCover',folder,unreal.Material,unreal.MaterialFactoryNew())
  color=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);color.constant=unreal.LinearColor(.8,.85,.9,1)
  mel.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
  rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.r=.9;mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
  cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
  for source in list(actors.get_all_level_actors()):
   label=source.get_actor_label()
   if label!='Kit_Ground' and not label.startswith('Kit_roof_'):continue
   origin,extent=source.get_actor_bounds(False)
   height=1+spec['snow_cover']*3
   cap=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(origin.x,origin.y,origin.z+extent.z+height/2))
   cap.set_actor_label('SnowCap_'+label);cap.static_mesh_component.set_static_mesh(cube);cap.static_mesh_component.set_material(0,mat);cap.static_mesh_component.set_collision_profile_name('NoCollision')
   cap.set_actor_scale3d(unreal.Vector(extent.x*2/100,extent.y*2/100,height/100));snow_caps+=1
 effect=None
 if kind!='none' and spec['intensity']>0:
  effect=handle_add_weather({'preset':kind,'intensity':spec['intensity'],'area':10000,'size':.35 if kind=='snow' else .5,'wind':spec['wind_cm_s'],'location':[0,0,0],'label':'PromptWeather'})
  weather=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='PromptWeather')
  component=weather.get_component_by_class(unreal.NiagaraComponent);component.activate(True);component.advance_simulation(90,1/30)
 return {'settings':spec,'effect':effect,'snow_caps':snow_caps,'material_slots_changed':changed,'material_variants':len(cache),'limitations':['Particle collision with roofs and interiors is not configured.','Snow cover uses simple flat caps on generated ground and roofs; no simulation, footprints or foliage accumulation.','Material instances retain original appearance; only direct materials receive surface variants.','Wetness changes surface shading; puddles and splashes are not implemented.']}
