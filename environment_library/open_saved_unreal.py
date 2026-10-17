"""Guard editor state before opening a saved studio environment/scene."""
import unreal,json,traceback
from pathlib import Path
H=Path(__file__).resolve().parent
request=json.loads((H/'demos/open-request.json').read_text())
output=H/'demos'/('open-result-'+request['id']+'.json')
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong Unreal project')
 if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():raise RuntimeError('Unreal has unsaved changes. Save or discard them in Unreal, then try again. No level was switched.')
 if not unreal.EditorAssetLibrary.does_asset_exist(request['level']):raise RuntimeError('Saved level is missing in this Unreal project')
 if not unreal.EditorLoadingAndSavingUtils.load_map(request['level']):raise RuntimeError('Unreal could not load the level')
 if request.get('sequence'):
  seq=unreal.load_asset(request['sequence'])
  if not seq:raise RuntimeError('Level opened, but the saved sequence is missing')
  if not unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq):raise RuntimeError('Level opened, but Sequencer could not open')
  unreal.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
  unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0)
 output.write_text(json.dumps({'ok':True,'level':request['level'],'sequence':request.get('sequence')}))
except Exception as error:
 output.write_text(json.dumps({'ok':False,'error':str(error)}))
