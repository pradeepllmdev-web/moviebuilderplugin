import bpy,json
p='C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend'
with bpy.data.libraries.load(p,link=False) as (s,t):print('AVAILABLE',json.dumps([n for n in s.actions if any(w in n.lower() for w in ['walk','running','run_','talking'])]))
