import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;data=json.loads((H/'physics_lab/import.json').read_text());report={}
for character in data['characters']:
 mesh=unreal.load_asset(character['parts'][0]['mesh'])
 report[character['name']]=[str(n) for n in mesh.get_all_morph_target_names()]
(H/'delivery_scene/morph-names.json').write_text(json.dumps(report,indent=2))
