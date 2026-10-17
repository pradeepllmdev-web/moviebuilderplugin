import unreal,json,traceback,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
try:
 from unreal_bridge.realworld import scan_library
 entries=[]
 for category,groups in scan_library().items():
  if category not in ('tree','rock','fern','grass','cliff','debris'):continue
  for group in groups:
   for path in group.get('meshes',[])[:4]:
    mesh=unreal.load_asset(path)
    if not isinstance(mesh,(unreal.StaticMesh,unreal.SkeletalMesh)):continue
    bounds=mesh.get_imported_bounds() if isinstance(mesh,unreal.SkeletalMesh) else mesh.get_bounds();e=bounds.box_extent;o=bounds.origin
    entries.append(dict(id=category+'.'+hashlib.sha256(path.encode()).hexdigest()[:10],mesh_type='skeletal' if isinstance(mesh,unreal.SkeletalMesh) else 'static',category=category,name=group.get('name',path.split('/')[-1]),path=path,dimensions_cm=[2*e.x,2*e.y,2*e.z],bottom_cm=o.z-e.z,style='scanned',tags=[category,group.get('name','')]))
 scales=json.loads((H/'assets/scale-registry.json').read_text())
 sources={p['name']:p for p in json.loads((H/'assets/manifest.json').read_text())}
 for pack in scales['packs']:
  source=sources[pack['name']]
  for item in pack['assets']:
   path=item['asset'];mesh=unreal.load_asset(path)
   if not isinstance(mesh,unreal.StaticMesh):continue
   b=mesh.get_bounds();name=path.split('.')[-1]
   import re
   display=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',name).replace('_',' ')
   category='furniture' if pack['name']=='furniture-kit' else 'building' if name.lower().startswith('building') else 'street_prop'
   entries.append(dict(id=category+'.'+hashlib.sha256(path.encode()).hexdigest()[:10],mesh_type='static',category=category,name=display,path=path,dimensions_cm=item['dimensions_cm'],bottom_cm=b.origin.z-b.box_extent.z,base_scale=item['uniform_scale'],style='stylized',tags=[category,display,pack['name']],source=source['source'],creator=source['creator'],license=source['license'],anchor_status=item['anchor_status']))
 (H/'assets/prompt-catalog.json').write_text(json.dumps({'version':1,'assets':entries},indent=2))
except Exception:
 (H/'assets/prompt-catalog-error.txt').write_text(traceback.format_exc());raise
