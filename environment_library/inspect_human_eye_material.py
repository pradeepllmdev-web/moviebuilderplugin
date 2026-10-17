import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/rowan-eye-test'
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False)
rows=[]
for m in bpy.data.materials:
 if 'high-poly' not in m.name:continue
 rows.append({'material':m.name,'images':[{'name':n.image.name,'path':bpy.path.abspath(n.image.filepath)} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'links':[[l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name] for l in m.node_tree.links]})
(D/'eye-source-material.json').write_text(json.dumps(rows,indent=2))
(D/'attachment-check.json').write_text(json.dumps([{'name':o.name,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'parent_bone':o.parent_bone,'modifiers':[(m.type,m.object.name if m.type=='ARMATURE' and m.object else None) for m in o.modifiers]} for o in bpy.context.scene.objects if o.type=='MESH'],indent=2))
(D/'neutral-key-check.json').write_text(json.dumps({o.name:[k.name for k in o.data.shape_keys.key_blocks if abs(k.value)>.001] for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys}))
