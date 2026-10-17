import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent/'delivery_scene';H.mkdir(exist_ok=True)
source='C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend'
with bpy.data.libraries.load(source,link=False) as (src,dst):
 names=[n for n in src.actions if any(n.endswith('|'+s) for s in ['Walking','Idle_3','Listen','Body_Hit','Hit_Reaction','Step_Push','Bend_Pick_Up'])]
(H/'available-clips.json').write_text(json.dumps(names,indent=2))
print('Available delivery motion clips: '+str(len(names)))
