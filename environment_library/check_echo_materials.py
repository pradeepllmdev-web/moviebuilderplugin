import unreal,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');job=json.loads((H/'samples/echo-inspector/job-status.json').read_text())
rows=[]
for shot in job['result']['shots']:
 for char in shot['transfer_characters']:
  mesh=unreal.load_asset(char['mesh']);slots=mesh.get_editor_property('materials')
  original=unreal.load_asset('/Game/PhysicsLab/package_20261015_101957/'+('lion/lion.lion' if char['name']=='Leo' else 'cat/cat.cat'))
  old=original.get_editor_property('materials');rows.append({'name':char['name'],'new':[str(s.material_slot_name) for s in slots],'original':[str(s.material_slot_name) for s in old]})
(H/'samples/echo-inspector/material-slots.json').write_text(json.dumps(rows,indent=2))
