import unreal,json
from pathlib import Path
u=unreal.EditorLoadingAndSavingUtils
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/demos/editor-state.json').write_text(json.dumps({'maps':[p.get_name() for p in u.get_dirty_map_packages()],'content':[p.get_name() for p in u.get_dirty_content_packages()],'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()}))
