"""Preserve faulty animation, disable just eyelid morphs on the isolated test."""
import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-run-blink'
record=json.loads((D/'native.json').read_text());path=record['characters'][0]['animation']
if not path.startswith('/Game/StudioProduction/'):raise RuntimeError('Unexpected test asset')
backup=path.split('.')[0]+'_BeforeBlinkFix'
if not unreal.EditorAssetLibrary.does_asset_exist(backup):
 unreal.EditorAssetLibrary.duplicate_asset(path,backup)
animation=unreal.load_asset(path);controller=animation.get_editor_property('controller')
controller.open_bracket('Disable isolated faulty eyelid morphs',False)
try:
 for name in ('BlinkL','BlinkR'):
  times,values=unreal.AnimationLibrary.get_float_keys(animation,name)
  unreal.AnimationLibrary.add_float_curve_keys(animation,name,list(times),[0.]*len(times))
finally:controller.close_bracket(False)
unreal.EditorAssetLibrary.save_loaded_asset(animation)
unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(100)
(D/'blink-disabled.json').write_text(json.dumps({'ok':True,'frame':100,'disabled':['BlinkL','BlinkR'],'backup':backup}))
