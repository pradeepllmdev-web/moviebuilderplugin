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
def pick(category,name):return next(x for x in a if x['category']==category and x['name']==name)['id']
bench=pick('furniture','bench');table=pick('furniture','table');spruce=pick('tree','Norway Spruce');birch=pick('tree','Silver Birch');rock=pick('rock','Mossy Forest Rock')
prompt=f'''Build Summit Crossing, a mountain checkpoint at golden hour, with a clear central crossroads and three small outpost buildings. This is a challenging layout; preserve every requested count and ID.
Roads exactly five: cross at cell[0,0] yaw0, straight at [0,1] yaw0, straight at [0,-1] yaw0, straight at [1,0] yaw90, straight at [-1,0] yaw90. No other road tiles.
Generated buildings exactly three, width_tiles3 depth_tiles3, southwest corners [-2800,1800], [1800,1800], [-2800,-2800]. Do not duplicate buildings as imported assets.
Use asset {bench} twice at [1700,-1800] and [1700,-2400], scale1. Use asset {table} once at [2300,-2100], scale1.
Use asset {spruce} twice at [-5500,3500] and [-5500,-3500], scale0.5. Use asset {birch} twice at [5500,3500] and [5500,-3500], scale0.5.
Use asset {rock} twice at [-4000,0] and [4000,0], scale0.5.
A distant mountain range behind at +Y, enabled true, height_cm40000 size_cm180000 distance_cm150000 side_deg90. Mood golden_hour. Keep the foreground flat and clear. No rivers or vehicles. Report unsupported details rather than inventing assets.'''
record={'prompt':prompt}
try:
 planned=wait(request('/plan',{'prompt':prompt}));plan=planned['plan'];record['plan']=plan
 counts={key:sum(x['asset_id']==key for x in plan.get('assets',[])) for key in [bench,table,spruce,birch,rock]}
 checks={'five_road_tiles':len(plan.get('roads',[]))==5,'three_buildings':len(plan.get('buildings',[]))==3,'two_benches':counts[bench]==2,'one_table':counts[table]==1,'four_trees':counts[spruce]==2 and counts[birch]==2,'two_rocks':counts[rock]==2,'mountain':plan.get('mountains',{}).get('enabled') is True}
 record['coverage']=checks;print('Coverage: '+json.dumps(checks),flush=True)
 # Build the validated plan, exposing any count omissions instead of claiming full compliance.
 done=wait(request('/build',{'plan':plan}));record['result']=done;print(done['preview'],flush=True)
except Exception as e:record['error']=str(e);print('FAILED: '+str(e),flush=True)
(H/'demos/challenging-prompt-test.json').write_text(json.dumps(record,indent=2))
