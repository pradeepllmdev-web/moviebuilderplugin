import json,urllib.request,time
from pathlib import Path
H=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8000/api/environment-production'
def request(path,body=None):
 req=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def wait(job):
 end=time.monotonic()+300
 while time.monotonic()<end:
  data=request('/jobs/'+job['id'])
  if data['status']=='failed':raise RuntimeError(data['error'])
  if data['status'] in ('ready','complete'):return data
  time.sleep(2)
 raise TimeoutError()
a=json.loads((H/'assets/prompt-catalog.json').read_text())['assets']
building=next(x for x in a if x['category']=='building' and 'suburban' in ' '.join(x['tags']))
bench=next(x for x in a if x['category']=='furniture' and x['name']=='bench')
table=next(x for x in a if x['category']=='furniture' and x['name']=='table')
tree=next(x for x in a if x['category']=='tree')
prompt=f'''Create a daylight roadside rest stop using installed new assets, mood blockbuster. IMPORTANT: return buildings as an EMPTY array [] because the building is an asset placement, not a generated modular building. Never put any entry in buildings. One straight road at cell [0,0], yaw0. Use asset {building['id']} ({building['name']}) at [5000,3000], scale1. Use asset {bench['id']} (bench) at [1200,-1200], scale1. Use asset {table['id']} (table) at [1600,-1200], scale1. Use asset {tree['id']} at [-3500,2500] and [-3500,-2500], scale0.5. Place furniture on the flat ground, separated from the building and road. No mountains. Use every named ID exactly, not substitutes.'''
planned=wait(request('/plan',{'prompt':prompt}));used={x['asset_id'] for x in planned['plan'].get('assets',[])};expected={x['id'] for x in (building,bench,table,tree)}
if not expected<=used:raise RuntimeError('AI omitted requested IDs: '+str(expected-used))
print('All four requested asset IDs selected',flush=True)
done=wait(request('/build',{'plan':planned['plan']}));(H/'demos/new-assets-prompt-test.json').write_text(json.dumps({'prompt':prompt,'plan':planned['plan'],'result':done},indent=2));print(done['preview'],flush=True)


