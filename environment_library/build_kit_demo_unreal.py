"""Create furnished and city sample levels from the imported CC0 kits."""
import unreal, json, traceback, time
import sys
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from scale_policy import pack_conversion,grounded_location
try:
    request = json.loads((H / 'assets/kit-request.json').read_text())
    pack = next(p for p in json.loads((H / 'assets/unreal-import.json').read_text())['packs'] if p['name'] == request['pack'])
    conversion=pack_conversion(pack)
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    from unreal_bridge.environment import handle_add_clouds, handle_add_post_process
    handle_add_clouds({})
    handle_add_post_process({})
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,2000), unreal.Rotator(-45,-35,0))
    sun.light_component.set_editor_property('intensity', 5.0)
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,1200))
    sky.light_component.set_editor_property('real_time_capture', True)
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0,0,0))
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -25))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
    floor.set_actor_scale3d(unreal.Vector(2000, 2000, .5))
    floor.set_actor_label('DemoGround')
    if request['pack'] == 'furniture-kit':
        for label, location, scale in [('BackWall',(0,500,150),(10,.2,3)),('SideWall',(-500,100,150),(.2,8,3))]:
            wall = actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location))
            wall.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
            wall.set_actor_scale3d(unreal.Vector(*scale))
            wall.set_actor_label(label)
    placed = []
    if request['pack'] == 'furniture-kit':
        desired = [('loungeSofa', -180, 100, 100), ('tableCoffee', -180, -60, 45), ('chair', 110, 100, 100),
                   ('bookcaseOpen', 170, 310, 190), ('bedDouble', -240, 350, 100), ('lampRoundFloor', 30, 260, 170)]
    else:
        desired = [(Path(m['path'].split('.')[0]).name, (i % 4 - 1.5) * 1100, (i // 4) * 1600, 700) for i,m in enumerate(pack['meshes'][:8])]
    for name, x, y, height in desired:
        entry = next((m for m in pack['meshes'] if m['path'].split('.')[-1].lower() == name.lower()), None)
        if entry is None:
            continue
        mesh = unreal.load_asset(entry['path'])
        bounds = mesh.get_bounds()
        factor = conversion['uniform_scale']
        offset=grounded_location(list(bounds.origin.to_tuple()),list(bounds.box_extent.to_tuple()),factor)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x+offset[0],y+offset[1],offset[2]))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(factor, factor, factor))
        actor.set_actor_label('Kit_' + name)
        placed.append({'mesh': entry['path'], 'scale': factor, 'dimensions_cm':[2*v*factor for v in bounds.box_extent.to_tuple()]})
    location = unreal.Vector(650,-850,480) if request['pack']=='furniture-kit' else unreal.Vector(3400,-4300,2600)
    target = unreal.Vector(0,150,70) if request['pack']=='furniture-kit' else unreal.Vector(0,700,200)
    rotation = unreal.MathLibrary.find_look_at_rotation(location,target)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(location,rotation,unreal.Name())
    camera = actors.spawn_actor_from_class(unreal.CineCameraActor,location,rotation)
    camera.set_actor_label('EnvironmentPreviewCamera')
    path = '/Game/EnvironmentDemos/' + request['id']
    n = 1
    while unreal.EditorAssetLibrary.does_asset_exist(path):
        n += 1
        path = '/Game/EnvironmentDemos/' + request['id'] + '_v' + str(n)
    assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
    destination = H / 'demos' / request['id']
    destination.mkdir(exist_ok=True)
    (destination / 'build-result.json').write_text(json.dumps({'level':path,'pack':request['pack'],'biome':request['pack'],'placed':placed,'scale_conversion':conversion,'finished_at':time.time()},indent=2))
except Exception:
    (H / 'assets/kit-error.txt').write_text(traceback.format_exc())
    raise
