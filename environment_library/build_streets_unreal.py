"""Build a fresh modular kit demonstration; never modifies earlier maps."""
import unreal, json, sys, time, traceback
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from road_assembly import compile_streets, demo_recipe
try:
    if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path(): raise RuntimeError('Wrong project')
    recipe=demo_recipe()
    compiled=compile_streets(recipe)
    name='StreetKit_'+time.strftime('%Y%m%d_%H%M%S')
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
    # Physical height references next to the usable 100 x 220 cm doorway.
    for label,x,height in [('LionHeight185',420,185),('CatHeight150',480,150)]:
        box(label,[x,420,15+height/2],[20,20,height],0,'wood')
    from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
    from unreal_bridge.moods import handle_apply_mood
    handle_add_post_process({});handle_add_clouds({});handle_apply_mood({'mood':'blockbuster','weather':False,'sun_azimuth':280})
    cameras={'overview':{'location':[4100,-4900,4200],'target':[0,0,0]},'street':{'location':[450,-2100,180],'target':[50,0,100]}}
    cam=cameras['overview']
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*cam['location']),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*cam['location']),unreal.Vector(*cam['target'])),unreal.Name())
    level='/Game/EnvironmentDemos/'+name
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,level):raise RuntimeError('Map save failed')
    D=H/'demos'/name;D.mkdir(exist_ok=True)
    report=dict(level=level,biome='modular_streets',warnings=['Street blockout: four open road ends; no traffic, curb ramps or automatic navigation yet.'],cameras=cameras,part_count=len(recipe['tiles']),connection_count=len(compiled['links']),open_end_count=len(compiled['open_ports']),box_count=len(compiled['boxes']))
    for filename,data in [('recipe.json',recipe),('assembly.json',compiled),('build-result.json',report)]: (D/filename).write_text(json.dumps(data,indent=2))
    (H/'demos/latest-streets.json').write_text(json.dumps(dict(id=name,directory=str(D),cameras=cameras),indent=2))
except Exception:
    (H/'demos/streets-error.txt').write_text(traceback.format_exc());raise
