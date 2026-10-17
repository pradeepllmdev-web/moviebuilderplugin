"""Run inside the verification editor; preserve all existing assets and levels."""
import unreal, json, traceback, time
from pathlib import Path
H = Path(__file__).resolve().parent
OUT = H / 'assets'
report = {'started_at': time.time(), 'packs': [], 'errors': []}
try:
    project = unreal.Paths.get_project_file_path()
    if 'LatestSceneVerification' not in project:
        raise RuntimeError('Import requires the separate verification project')
    for pack in json.loads((OUT / 'manifest.json').read_text()):
        folder = Path(pack['directory']) / 'Models' / 'FBX format'
        destination = '/Game/EnvironmentAssets/Kenney/' + pack['name'].replace('-', '_')
        tasks = []
        for file in sorted(folder.glob('*.fbx')):
            name = file.stem.replace('-', '_')
            if unreal.EditorAssetLibrary.does_asset_exist(destination + '/' + name):
                continue
            task = unreal.AssetImportTask()
            task.filename = str(file)
            task.destination_path = destination
            task.destination_name = name
            task.automated = True
            task.replace_existing = False
            task.save = True
            options = unreal.FbxImportUI()
            options.import_mesh = True
            options.import_as_skeletal = False
            options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            options.automated_import_should_detect_type = False
            options.import_materials = True
            options.import_textures = True
            options.static_mesh_import_data.combine_meshes = True
            options.static_mesh_import_data.auto_generate_collision = True
            task.options = options
            tasks.append(task)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
        meshes = []
        for path in unreal.EditorAssetLibrary.list_assets(destination, recursive=True):
            data = unreal.EditorAssetLibrary.find_asset_data(path)
            if str(data.asset_class_path.asset_name) == 'StaticMesh':
                mesh = unreal.load_asset(path)
                bounds = mesh.get_bounds()
                meshes.append({'path': path, 'extent_cm': [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
                               'material_slots': len(mesh.static_materials),
                               'materials_present': all(m.material_interface is not None for m in mesh.static_materials)})
        entry = {'name': pack['name'], 'destination': destination, 'expected': len(list(folder.glob('*.fbx'))), 'meshes': meshes}
        report['packs'].append(entry)
        (OUT / 'unreal-import.json').write_text(json.dumps(report, indent=2))
    report['finished_at'] = time.time()
except Exception:
    report['errors'].append(traceback.format_exc())
finally:
    (OUT / 'unreal-import.json').write_text(json.dumps(report, indent=2))
