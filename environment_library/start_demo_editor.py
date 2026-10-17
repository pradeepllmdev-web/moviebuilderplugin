"""Run inside the independent verification project; original levels stay intact."""
import unreal,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/demos');H.mkdir(exist_ok=True)
import unreal_bridge
unreal_bridge.stop_server();unreal_bridge.start_server(port=8520)
from unreal_bridge.realworld import handle_real_assets
inventory=handle_real_assets({})
(H/'asset-inventory.json').write_text(json.dumps(inventory,indent=2))
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
(H/'editor-ready.json').write_text(json.dumps({'project':unreal.Paths.get_project_file_path(),'bridge':'http://127.0.0.1:8520','plugin':unreal_bridge.__file__,'biomes':list(inventory['biomes']),'asset_groups':{k:len(v) for k,v in inventory['assets'].items()}},indent=2))
unreal.log('ENVIRONMENT_DEMO_READY')
