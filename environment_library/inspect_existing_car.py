import bpy,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent.parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(H.parent/'blendplugin-next/scene_pipeline/assets/vehicles/car_open.glb'))
r=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  corners=[o.matrix_world@Vector(c) for c in o.bound_box];lo=[min(c[i] for c in corners) for i in range(3)];hi=[max(c[i] for c in corners) for i in range(3)]
  r.append({'name':o.name,'center':[(a+b)/2 for a,b in zip(lo,hi)],'size':[b-a for a,b in zip(lo,hi)]})
(H/'samples/lion-drive-v2/car-parts.json').write_text(json.dumps(r,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(H/'samples/lion-drive-v2/car-source.blend'))
