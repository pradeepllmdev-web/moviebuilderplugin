"""Check root placement and orientation across adjacent generated shots."""
import json,math
from pathlib import Path
def check(movie,root):
 previous={};rows=[];props={};prop_rows=[]
 for item in movie['shots']:
  folder=Path(root)/'scene_jobs'/item['scene_id'];routes=json.loads((folder/'routes.json').read_text());plan=json.loads((folder/'plan.json').read_text());environment=plan.get('environment_id',plan['environment'])
  for actor,route in routes.items():
   key=(environment,actor)
   if key in previous:
    old=previous[key];new=route[0];delta=math.dist(old['location_cm'][:2],new['location_cm'][:2]);angle=abs((old['yaw']-new['yaw']+180)%360-180)
    rows.append({'shot':item['title'],'actor':actor,'root_xy_difference_cm':delta,'heading_difference_deg':angle,'ok':delta<2 and angle<1})
   previous[key]=route[-1]
  for path in folder.glob('actor_*/box-trajectory.json'):
   trajectory=json.loads(path.read_text());identity=trajectory['end_state']['id'];key=(environment,identity);current=trajectory['rows'][0]['location_cm']
   if key in props:
    delta=math.dist(props[key],current);prop_rows.append({'shot':item['title'],'id':identity,'position_difference_cm':delta,'ok':delta<1})
   props[key]=trajectory['rows'][-1]['location_cm']
 return {'ok':all(row['ok'] for row in rows+prop_rows),'boundaries':rows,'prop_boundaries':prop_rows,'scope':'Root XY/heading and keyed box placement; no perceptual or physics continuity certification'}
