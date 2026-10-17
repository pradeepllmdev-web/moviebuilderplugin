import json
from pathlib import Path
from scale_policy import POLICY,pack_conversion
H=Path(__file__).resolve().parent
report={'policy_version':POLICY['version'],'units':'centimetres','packs':[]}
for pack in json.loads((H/'assets/unreal-import.json').read_text())['packs']:
 conversion=pack_conversion(pack);factor=conversion['uniform_scale']
 entries=[{'asset':m['path'],'native_dimensions_cm':[2*v for v in m['extent_cm']],
           'uniform_scale':factor,'dimensions_cm':[2*v*factor for v in m['extent_cm']],
           'anchor_status':'Bounds-grounded; semantic seat/door anchors require authoring'} for m in pack['meshes']]
 report['packs'].append({'name':pack['name'],'conversion':conversion,'assets':entries})
 print(pack['name']+': '+str(len(entries))+' assets, shared scale '+str(round(factor,4)))
(H/'assets/scale-registry.json').write_text(json.dumps(report,indent=2))
