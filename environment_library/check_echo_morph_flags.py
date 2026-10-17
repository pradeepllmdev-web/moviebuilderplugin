import unreal,json
from pathlib import Path
D=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/samples/echo-inspector');job=json.loads((D/'job-status.json').read_text());rows=[]
for shot in job['result']['shots']:
 for char in shot['transfer_characters']:
  mesh=unreal.load_asset(char['mesh']);skeleton=mesh.skeleton;names=[str(n) for n in mesh.get_all_morph_target_names()]
  flags={name:unreal.AnimationLibrary.get_curve_meta_data_morph_target(skeleton,name) for name in names if name in ['JawOpen','JawClose','BlinkL','BlinkR']}
  rows.append({'shot':shot['shot_id'],'name':char['name'],'flags':flags})
(D/'morph-flags.json').write_text(json.dumps(rows,indent=2))
