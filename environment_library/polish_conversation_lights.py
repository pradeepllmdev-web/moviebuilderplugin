"""Adjust only generated fill lights in the latest conversation copies."""
import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'movie_jobs'/(H/'conversation-active.txt').read_text().strip();movie=json.loads((D/'ready.json').read_text())
for item in movie['shots']:
 r=item['report'];folder=r['level'].rsplit('/',1)[0]
 unreal.EditorAssetLibrary.save_directory(folder,only_if_is_dirty=True,recursive=True)
 if not unreal.EditorLoadingAndSavingUtils.load_map(r['level']):raise RuntimeError('Cannot load generated shot')
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if actor.get_actor_label().startswith('Acting_Fill_'):
   actor.light_component.set_editor_property('intensity',5)
   actor.light_component.set_editor_property('volumetric_scattering_intensity',0)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(D/'lighting-check.json').write_text(json.dumps({'ok':True,'fill_intensity':5,'volumetric_scattering':0}))
