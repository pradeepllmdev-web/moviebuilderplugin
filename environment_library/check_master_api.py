import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
sub=unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
(H/'master-api.json').write_text(json.dumps({'convert':getattr(sub,'convert_to_spawnable').__doc__,'subsection':unreal.MovieSceneSubSection.set_sequence.__doc__},indent=2))
