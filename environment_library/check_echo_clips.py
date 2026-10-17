import bpy,json
from pathlib import Path
p='C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend'
with bpy.data.libraries.load(p,link=False) as (source,target):
 result={name:('clip|'+name) in source.actions for name in ['Talking','Idle_3','Standing_Arguing']}
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/samples/echo-inspector/clip-check.json').write_text(json.dumps(result))
