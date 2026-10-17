import unreal,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library')
paths=json.loads((H/'dirty-scene-check.json').read_text())
for p in paths:
 if not p.startswith(('/Game/StudioProduction/7361524b60174729aa025cab022bb94f/','/Game/StudioProduction/8350a2bff0ad44eab633a2466f9d83c9/')):raise ValueError('Unexpected package')
 if not unreal.EditorAssetLibrary.save_asset(p,only_if_is_dirty=True):raise RuntimeError('Could not save '+p)
(H/'dirty-scene-saved.json').write_text(json.dumps({'ok':True,'saved':len(paths)}))
