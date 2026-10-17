"""Save only assets owned by the isolated Rowan audition."""
import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/rowan-eye-test'
r=json.loads((D/'import-job.json').read_text())['result'];folder=r['level'].rsplit('/',1)[0]
for path in unreal.EditorAssetLibrary.list_assets(folder,recursive=True,include_folder=False):
 unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True)
(D/'save-check.json').write_text(json.dumps({'remaining_dirty':[p.get_path_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())]}))
