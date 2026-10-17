"""Inspect eye-control locality locally; never emit mesh coordinates."""
import bpy,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent.parent/'blendplugin-next/scene_pipeline'))
from realistic_rig import load_realistic
bpy.ops.wm.read_factory_settings(use_empty=True)
info=json.loads((H.parent.parent/'blendplugin-next/scene_pipeline/catalog.json').read_text())['DemoAmber']
load_realistic(info)
report={'eye_bones':[],'meshes':[]}
for o in bpy.context.scene.objects:
 if o.type=='ARMATURE':report['eye_bones'] += [b.name for b in o.data.bones if any(s in b.name.lower() for s in ('eye','lid'))]
 if o.type!='MESH':continue
 row={'name':o.name,'eye_controls':[]}
 keys=o.data.shape_keys
 if keys:
  basis=keys.key_blocks[0]
  zs=[v.co.z for v in basis.data];lo=min(zs);height=max(zs)-lo
  for k in keys.key_blocks:
   if not any(s in k.name.lower() for s in ('blink','eye','lid')):continue
   changed=[i for i,(a,b) in enumerate(zip(basis.data,k.data)) if (a.co-b.co).length>1e-5]
   row['eye_controls'].append({'name':k.name,'changed_count':len(changed),'below_upper_face_count':sum(basis.data[i].co.z<lo+height*.72 for i in changed),'max_displacement':round(max(((basis.data[i].co-k.data[i].co).length for i in changed),default=0),5)})
 report['meshes'].append(row)
(H/'cat-eye-audit.json').write_text(json.dumps(report,indent=2))
sys.path.insert(0,str(H))
from safe_shape_join import join_preserving_shapes
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
active=max(meshes,key=lambda o:len(o.data.vertices))
join_preserving_shapes(meshes,active)
checks=[]
keys=active.data.shape_keys
for key in keys.key_blocks:
 if 'blink' not in key.name.lower():continue
 deltas=[(a.co-b.co).length for a,b in zip(key.data,keys.key_blocks[0].data)]
 checks.append({'name':key.name,'affected':sum(d>1e-5 for d in deltas),'max_delta':round(max(deltas),5)})
(H/'cat-eye-join-check.json').write_text(json.dumps(checks,indent=2))
print('Eye-control summary saved; no geometry emitted.')
