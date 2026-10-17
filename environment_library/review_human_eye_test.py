import unreal,json,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/rowan-eye-test'
try:
 r=json.loads((D/'import-job.json').read_text())['result']
 lib=unreal.LevelSequenceEditorBlueprintLibrary
 lib.open_level_sequence(unreal.load_asset(r['sequence']));lib.pause();lib.set_lock_camera_cut_to_viewport(True)
 frame=int((D/'review-frame.txt').read_text()) if (D/'review-frame.txt').exists() else 35
 lib.set_current_time(frame)
 animation=unreal.load_asset(r['characters'][0]['animation'])
 mesh=unreal.load_asset(r['characters'][0]['mesh'])
 names=[str(n) for n in mesh.get_all_morph_target_names()]
 (D/'material-check.json').write_text(json.dumps([{'slot':str(slot.material_slot_name),'material':slot.material_interface.get_path_name() if slot.material_interface else None} for slot in mesh.get_editor_property('materials')],indent=2))
 (D/'unreal-eye-check.json').write_text(json.dumps({'ok':True,'frame':frame,'eye_targets':[n for n in names if n.startswith('eye')],'facial_import':r['characters'][0]['facial'],'sequence':r['sequence'],'level':r['level']},indent=2))
except Exception:
 (D/'unreal-eye-check.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
