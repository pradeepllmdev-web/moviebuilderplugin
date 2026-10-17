"""Build a fresh modular kit demonstration; never modifies earlier maps."""
import unreal, json, sys, time, traceback
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import importlib,prompt_environment
importlib.reload(prompt_environment)
from prompt_environment import validate, catalogue
try:
    if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path(): raise RuntimeError('Wrong project')
    request=json.loads((H/'demos/prompt-build-request.json').read_text())
    name=request['id']
    if not __import__('re').fullmatch(r'PromptSet_[a-f0-9]{12}',name):raise ValueError('Invalid build ID')
    recipe=request['plan']
    compiled=validate(recipe)
    if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():raise RuntimeError('Save unsaved Unreal map changes before building a new environment')
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
    house=json.loads((H/'demos/latest-house.json').read_text())['id']
    folder='/Game/EnvironmentAssets/HouseStudies/'+house+'/'
    mats={k:unreal.load_asset(folder+v) for k,v in {'wood':'M_wood_floor_deck','plaster':'M_painted_plaster_wall','ground':'M_Ground'}.items()}
    tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
    for key,color in {'asphalt':(.035,.04,.045),'pavement':(.32,.34,.35),'paint':(.85,.83,.72)}.items():
        mat=tools.create_asset('M_'+key,'/Game/EnvironmentAssets/StreetStudies/'+name,unreal.Material,unreal.MaterialFactoryNew())
        node=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);node.constant=unreal.LinearColor(*color,1)
        mel.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
        rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);rough.r=.85
        mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat);mats[key]=mat
    def box(label,loc,size,yaw,material):
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(yaw=yaw))
        actor.set_actor_label(label);comp=actor.static_mesh_component;comp.set_static_mesh(cube)
        if mats.get(material):comp.set_material(0,mats[material])
        comp.set_collision_profile_name('NoCollision' if material=='paint' else 'BlockAll')
        actor.set_actor_scale3d(unreal.Vector(*[v/100 for v in size]))
        return actor
    box('Kit_Ground',[0,0,-35],[14000,14000,30],0,'ground')
    for b in compiled['boxes']:box('Kit_'+b['id'],b['position_cm'],b['size_cm'],b['yaw'],b['material'])
    asset_map={a['id']:a for a in catalogue()};placed_assets=[]
    for i,item in enumerate(compiled['asset_placements']):
        entry=asset_map[item['asset_id']];mesh=unreal.load_asset(entry['path'])
        if not mesh:raise ValueError('Installed asset missing: '+entry['id'])
        x,y=item['position_cm'];scale=item.get('scale',1)*entry.get('base_scale',1)
        actor=actors.spawn_actor_from_class(unreal.SkeletalMeshActor if entry.get('mesh_type')=='skeletal' else unreal.StaticMeshActor,unreal.Vector(x,y,-entry['bottom_cm']*scale))
        actor.set_actor_label('Catalogue_'+str(i)+'_'+entry['category'])
        if entry.get('mesh_type')=='skeletal':actor.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
        else:actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
        placed_assets.append({'id':entry['id'],'scale':scale,'label':actor.get_actor_label()})
    mountain=compiled['mountains'];mountain_result=None
    if mountain['enabled']:
        from unreal_bridge.mountains import handle_add_mountain
        import math
        angle=math.radians(mountain['side_deg']);distance=mountain['distance_cm']
        mountain_result=handle_add_mountain({'template':'alpine_range','size':mountain['size_cm'],'height':mountain['height_cm'],'resolution':96,'location':[math.cos(angle)*distance,math.sin(angle)*distance,-2000],'rotation':mountain['side_deg']+90,'seed':51,'label':'PromptMountainBackdrop'})
    from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
    from unreal_bridge.moods import handle_apply_mood
    handle_add_post_process({});handle_add_clouds({});handle_apply_mood({'mood':recipe['mood'],'weather':False,'sun_azimuth':280})
    import weather_unreal;importlib.reload(weather_unreal)
    weather_result=weather_unreal.apply_weather(compiled['weather'],'/Game/EnvironmentAssets/WeatherStudies/'+name,actors)
    cameras={'overview':{'location':[4100,-4900,4200],'target':[0,0,0]},'street':{'location':[1600,-6500,2400],'target':[0,1800,1600]}}
    cam=cameras['street'] if mountain['enabled'] or compiled['weather']['type']!='none' else cameras['overview']
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*cam['location']),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*cam['location']),unreal.Vector(*cam['target'])),unreal.Name())
    level='/Game/EnvironmentDemos/'+name
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,level):raise RuntimeError('Map save failed')
    D=H/'demos'/name;D.mkdir(exist_ok=True)
    report=dict(weather=weather_result,placed_assets=placed_assets,mountains=mountain_result,reference_analysis=recipe.get('reference_analysis'),contract_version=1,level=level,biome='prompt_modular_set',warnings=['Blockout architecture; no traffic or automatic navigation.']+list(recipe.get('unsupported',[]))+(weather_result['limitations'] if compiled['weather']['type']!='none' else []),cameras=cameras,part_count=len(recipe['buildings'])+len(recipe['roads']),connection_count=len(compiled['road_links']),open_end_count=compiled['open_road_ends'],box_count=len(compiled['boxes']))
    for filename,data in [('recipe.json',recipe),('assembly.json',compiled),('build-result.json',report)]: (D/filename).write_text(json.dumps(data,indent=2))
    (H/'demos/latest-prompt.json').write_text(json.dumps(dict(id=name,directory=str(D),cameras=cameras),indent=2))
except Exception:
    (H/'demos'/request['id']).mkdir(exist_ok=True);(H/'demos'/request['id']/'error.txt').write_text(traceback.format_exc());raise

