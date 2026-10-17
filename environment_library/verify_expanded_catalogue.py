import json,time,urllib.request
from pathlib import Path
H=Path('environment_library');assets=json.loads((H/'assets/prompt-catalog.json').read_text())['assets']
building=next(a for a in assets if a['category']=='building' and 'suburban' in ' '.join(a['tags']))
chair=next(a for a in assets if a['category']=='furniture' and a['name']=='chair')
plan=dict(mood='blockbuster',buildings=[],roads=[dict(id='road',kind='straight',cell=[0,0])],assets=[dict(asset_id=building['id'],position_cm=[5000,0],scale=1),dict(asset_id=chair['id'],position_cm=[1000,-1000],scale=1)],unsupported=[])
base='http://127.0.0.1:8000/api/environment-production'
req=urllib.request.Request(base+'/build',json.dumps({'plan':plan}).encode(),{'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:job=json.load(r)
end=time.monotonic()+200
while time.monotonic()<end:
 with urllib.request.urlopen(base+'/jobs/'+job['id']) as r:data=json.load(r)
 if data['status']=='failed':raise RuntimeError(data['error'])
 if data['status']=='complete':
  expected={a['id']:a['base_scale'] for a in (building,chair)}
  for placed in data['report']['placed_assets']:assert abs(placed['scale']-expected[placed['id']])<1e-8
  (H/'demos/expanded-catalogue-test.json').write_text(json.dumps(data,indent=2));print('Verified building and furniture placement scales; '+data['report']['level']);break
 time.sleep(2)
else:raise TimeoutError()
