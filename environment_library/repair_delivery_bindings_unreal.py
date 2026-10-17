import unreal,json,traceback
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene';report={}
try:
 info=json.loads((D/'sequence.json').read_text())
 unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
 assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(info['level'])
 sequence=unreal.load_asset(info['sequence']);unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
 unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem).fix_actor_references()
 unreal.EditorAssetLibrary.save_loaded_asset(sequence)
 bindings=[]
 for binding in sequence.get_bindings():
  objects=unreal.LevelSequenceEditorBlueprintLibrary.get_bound_objects(sequence.get_binding_id(binding))
  bindings.append({'name':str(binding.get_display_name()),'resolved':len(objects)})
 report['bindings']=bindings
 if any(b['resolved']==0 and b['name'].startswith('DeliveryShot_') for b in bindings):raise RuntimeError('A camera binding is still unresolved')
 report['ok']=True
except Exception:report.update(ok=False,error=traceback.format_exc())
(D/'binding-repair.json').write_text(json.dumps(report,indent=2))
