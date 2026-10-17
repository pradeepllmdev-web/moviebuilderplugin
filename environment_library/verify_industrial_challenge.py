import json,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8000/api/environment-production'
def request(path,body=None):
 req=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def wait(job):
 end=time.monotonic()+400
 while time.monotonic()<end:
  data=request('/jobs/'+job['id'])
  if data['status']=='failed':raise RuntimeError(data['error'])
  if data['status'] in ('ready','complete'):return data
  time.sleep(2)
 raise TimeoutError()
a=json.loads((H/'assets/prompt-catalog.json').read_text())['assets']
def pick(category,name,pack=None):return next(x for x in a if x['category']==category and x['name']==name and (not pack or pack in x['tags']))['id']
warehouse=pick('building','building a','city-kit-industrial');office=pick('building','building h','city-kit-industrial');bench=pick('furniture','bench');rock=pick('rock','Nordic Beach Rocks')
prompt=f"""Create Freight Yard Seven, a stylized industrial depot courtyard in overcast daylight, mood overcast_drizzle. Different from a village: large imported warehouse buildings, a small office and a delivery access T junction. No trees and no mountains. No unsupported vehicles, containers or cranes.
IMPORTANT buildings MUST be []: all buildings below are installed asset placements, never duplicate them as generated buildings.
Roads exactly four tiles: tee at cell[0,0] yaw0 (open south/east/west, closed north), straight at [0,-1] yaw0, straight at [-1,0] yaw90, straight at [1,0] yaw90. Do not add a north road.
Assets exactly seven instances: use asset {warehouse} twice, at [-2800,2600] and [2800,2600], scale1. Use asset {office} once at [2800,-2600], scale1. Use asset {bench} twice at [-2200,-2200] and [-2200,-2700], scale1. Use asset {rock} twice at [-5000,0] and [5000,0], scale0.5. All coordinates are centimetres and asset positions are centres. Keep these requested counts and exact IDs. Report omissions explicitly."""
record={'prompt':prompt}
try:
 planned=wait(request('/plan',{'prompt':prompt}));plan=planned['plan'];record['plan']=plan
 counts={key:sum(x['asset_id']==key for x in plan.get('assets',[])) for key in [warehouse,office,bench,rock]}
 checks={'four_road_tiles':len(plan.get('roads',[]))==4,'no_generated_buildings':not plan.get('buildings'),'two_warehouses':counts[warehouse]==2,'one_office':counts[office]==1,'two_benches':counts[bench]==2,'two_rocks':counts[rock]==2,'no_mountains':not plan.get('mountains',{}).get('enabled',False)}
 record['coverage']=checks;print('Coverage: '+json.dumps(checks),flush=True)
 done=wait(request('/build',{'plan':plan}));record['result']=done;print(done['preview'],flush=True)
except Exception as e:record['error']=str(e);print('FAILED: '+str(e),flush=True)
(H/'demos/industrial-challenge-test.json').write_text(json.dumps(record,indent=2))
