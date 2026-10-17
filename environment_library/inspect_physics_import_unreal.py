import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent/'physics_lab';data=json.loads((H/'import.json').read_text())
items=[]
for path in unreal.EditorAssetLibrary.list_assets(data['folder'],recursive=True):
 a=unreal.EditorAssetLibrary.find_asset_data(path)
 if str(a.asset_class_path.asset_name) in ('AnimSequence','SkeletalMesh','Skeleton'):
  items.append({'path':path,'class':str(a.asset_class_path.asset_name)})
(H/'asset-summary.json').write_text(json.dumps(items,indent=2))
