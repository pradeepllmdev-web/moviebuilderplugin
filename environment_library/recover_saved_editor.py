"""Restart the bridge and open the saved test; preserve any restored dirty packages."""
import unreal,json,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent;output=H/'samples/editor-recovery.json'
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 import unreal_bridge
 unreal_bridge.stop_server();unreal_bridge.start_server(port=8520)
 dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
 if dirty:
  output.write_text(json.dumps({'ok':False,'bridge_ready':True,'message':'Recovered unsaved packages are present. Save All before opening the saved test.'}))
 else:
  record=json.loads((H/'samples/lion-scramble/native.json').read_text());unreal.EditorLoadingAndSavingUtils.load_map(record['level'])
  sequence=unreal.load_asset(record['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.open_level_sequence(sequence);lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(0)
  output.write_text(json.dumps({'ok':True,'bridge_ready':True,'level':record['level'],'sequence':record['sequence']}))
except Exception:output.write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
