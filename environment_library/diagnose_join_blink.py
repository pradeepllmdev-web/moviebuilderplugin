import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-run-blink/scene.blend'))
bpy.context.scene.frame_set(1)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and (o in list(rig.children_recursive) or any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))]
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
active=max(objects,key=lambda o:len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0)
bpy.context.view_layer.objects.active=active;bpy.ops.object.join()
r=[]
for k in active.data.shape_keys.key_blocks:
 if k.name not in ('BlinkL','BlinkR'):continue
 d=[(a.co-b.co).length for a,b in zip(k.data,k.relative_key.data)]
 r.append(dict(name=k.name,affected=sum(x>1e-5 for x in d),max_delta=max(d),relative=k.relative_key.name))
(H/'samples/lion-run-blink/join-diagnosis.json').write_text(json.dumps(r))
