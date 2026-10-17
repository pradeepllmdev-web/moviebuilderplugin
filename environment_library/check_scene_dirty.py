import unreal,json
from pathlib import Path
u=unreal.EditorLoadingAndSavingUtils
p=u.get_dirty_map_packages()+u.get_dirty_content_packages()
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/dirty-scene-check.json').write_text(json.dumps([x.get_name() for x in p]))
