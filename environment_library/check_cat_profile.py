import bpy,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin')
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/amber-open-mouth-v2/fresh-talking.blend'))
rigs=[]
for o in bpy.context.scene.objects:
 if o.type=='ARMATURE':rigs.append({'name':o.name,'bones':len(o.data.bones),'hips':[b.name for b in o.data.bones if 'hip' in b.name.lower() or 'pelvis' in b.name.lower()],'first_names':[b.name for b in list(o.data.bones)[:4]]})
(H/'environment_library/cat-rig-check.json').write_text(json.dumps({'rigs':rigs,'jaw_meshes':sum(1 for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.key_blocks.get('JawOpen'))}))
