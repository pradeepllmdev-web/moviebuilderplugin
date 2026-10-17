import json,urllib.request,time
from pathlib import Path
H=Path('environment_library');BASE='http://127.0.0.1:8000/api/environment-production'
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
prompt='Build a small village with two houses beside one straight road tile at cell [0,0] yaw0. Houses at [-1800,-400] and [1000,-400], width_tiles3 depth_tiles3. Three spruce trees at [-3500,-2000], [-3500,2000], [3500,2000]. There is a mountain behind the village at +Y. Use mountain height50000 size180000 distance140000 side90. Golden hour.'
plan=wait(request('/plan',{'prompt':prompt}));(H/'demos/unified-test-plan.json').write_text(json.dumps(plan,indent=2));print('PLAN READY',flush=True)
done=wait(request('/build',{'plan':plan['plan']}));(H/'demos/unified-test-result.json').write_text(json.dumps(done,indent=2));print(done['report']['level'],flush=True);print('Mountain built:',bool(done['report'].get('mountains')),flush=True)
