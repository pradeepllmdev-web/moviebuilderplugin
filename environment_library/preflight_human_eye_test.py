import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/rowan-eye-test'
errors=[]
if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():errors.append('Wrong project')
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():errors.append('Unsaved Unreal changes; no scene switched')
(D/'preflight.json').write_text(json.dumps({'ok':not errors,'errors':errors}))
