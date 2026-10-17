"""Build a fresh modular kit demonstration; never modifies earlier maps."""
import unreal, json, sys, time, traceback
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from modular_assembly import compile_recipe, room_recipe
try:
    if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path(): raise RuntimeError('Wrong project')
    recipe=room_recipe()
    # Roof and stairs displayed separately so the assembled interior stays visible.
    recipe['parts'] += [dict(id='roof_sample',kind='roof',position_cm=[1200,100,0]),dict(id='stairs_sample',kind='stairs',position_cm=[1200,500,0])]
    compiled=compile_recipe(recipe)
    name='ModularKit_'+time.strftime('%Y%m%d_%H%M%S')
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
    house=json.loads((H/'demos/latest-house.json').read_text())['id']
    folder='/Game/EnvironmentAssets/HouseStudies/'+house+'/'
    mats={k:unreal.load_asset(folder+v) for k,v in {'wood':'M_wood_floor_deck','plaster':'M_painted_plaster_wall','ground':'M_Ground'}.items()}
    def box(label,loc,size,yaw,material):
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(yaw=yaw))
        actor.set_actor_label(label);comp=actor.static_mesh_component;comp.set_static_mesh(cube)
        if mats.get(material):comp.set_material(0,mats[material])
        comp.set_collision_profile_name('BlockAll')
        actor.set_actor_scale3d(unreal.Vector(*[v/100 for v in size]))
        return actor
    box('Kit_Ground',[500,300,-35],[10000,10000,30],0,'ground')
    for b in compiled['boxes']:box('Kit_'+b['id'],b['position_cm'],b['size_cm'],b['yaw'],b['material'])
    # Physical height references next to the usable 100 x 220 cm doorway.
    for label,x,height in [('LionHeight185',260,185),('CatHeight150',340,150)]:
        box(label,[x,-100,height/2],[20,20,height],0,'wood')
    from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
    from unreal_bridge.moods import handle_apply_mood
    handle_add_post_process({});handle_add_clouds({});handle_apply_mood({'mood':'blockbuster','weather':False,'sun_azimuth':280})
    cameras={'overview':{'location':[1500,-1400,1150],'target':[500,250,90]},'doorway':{'location':[420,-650,165],'target':[340,200,140]}}
    cam=cameras['overview']
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*cam['location']),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*cam['location']),unreal.Vector(*cam['target'])),unreal.Name())
    level='/Game/EnvironmentDemos/'+name
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,level):raise RuntimeError('Map save failed')
    D=H/'demos'/name;D.mkdir(exist_ok=True)
    report=dict(level=level,biome='modular_architecture',warnings=['Architecture blockout: no glazing, automatic interior dressing or full collision/path validation yet.'],cameras=cameras,part_count=len(recipe['parts']),box_count=len(compiled['boxes']))
    for filename,data in [('recipe.json',recipe),('assembly.json',compiled),('build-result.json',report)]: (D/filename).write_text(json.dumps(data,indent=2))
    (H/'demos/latest-modular.json').write_text(json.dumps(dict(id=name,directory=str(D),cameras=cameras),indent=2))
except Exception:
    (H/'demos/modular-error.txt').write_text(traceback.format_exc());raise
