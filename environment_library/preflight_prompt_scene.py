import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
request=json.loads((H/'demos/scene-active.json').read_text())
D=H/'scene_jobs'/request['id']
errors=[]
if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():errors.append('Wrong Unreal project')
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():errors.append('Unreal has unsaved changes. Save or discard them in Unreal before building. No level was switched.')
(D/'preflight.json').write_text(json.dumps({'ok':not errors,'errors':errors}))
