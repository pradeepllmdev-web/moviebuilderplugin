import unreal,json
from pathlib import Path
p='/Game/UnrealBridge/FX/NS_Weather'
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/assets/weather-system-check.json').write_text(json.dumps({'exists':unreal.EditorAssetLibrary.does_asset_exist(p),'path':p}))
