import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'source/CatPilot.blend'),use_scripts=False,load_ui=False)
report={'rigs':[{'name':o.name,'bones':list(o.pose.bones.keys())} for o in bpy.data.objects if o.type=='ARMATURE'],'shapes':{o.name:[k.name for k in o.data.shape_keys.key_blocks] for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys},'actions':[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]}
(H/'capabilities.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
