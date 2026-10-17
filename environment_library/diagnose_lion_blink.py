import bpy,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent.parent;report={}
for folder in ('lion-run-lipsync','lion-run-blink'):
 bpy.ops.wm.open_mainfile(filepath=str(H/'samples'/folder/'scene.blend'));s=bpy.context.scene;s.frame_set(101)
 rigs=[o for o in s.objects if o.type=='ARMATURE']
 matrices=[round(v,6) for r in rigs for b in r.pose.bones for row in b.matrix for v in row]
 controls=[]
 for o in s.objects:
  if o.type!='MESH' or not o.data.shape_keys:continue
  keys=o.data.shape_keys.key_blocks
  for name in ('BlinkL','BlinkR'):
   if name not in keys:continue
   k=keys[name];basis=k.relative_key
   deltas=[(a.co-b.co).length for a,b in zip(k.data,basis.data)]
   controls.append(dict(mesh=o.name,key=name,value=k.value,affected=sum(v>1e-5 for v in deltas),max_local_delta=max(deltas,default=0)))
 report[folder]=dict(bone_pose_hash=hashlib.sha256(str(matrices).encode()).hexdigest(),controls=controls)
(H/'samples/lion-run-blink/diagnosis.json').write_text(json.dumps(report,indent=2))
