import json,base64,urllib.request,time
from pathlib import Path
H=Path('environment_library');base='http://127.0.0.1:8000/api/environment-production'
body={'prompt':'Use the reference for forest atmosphere. Build one small ranger cabin at [1000,1000], width_tiles3 depth_tiles3, and exactly one spruce tree at [-6000,-6000], scale0.5, far away from the building. No other asset placements. Morning fog. No mountains or river. Report unsupported dense undergrowth if not represented.','image':'data:image/png;base64,'+base64.b64encode((H/'demos/Walkthrough/reference.png').read_bytes()).decode()}
req=urllib.request.Request(base+'/plan',json.dumps(body).encode(),{'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=60) as r:job=json.load(r)
end=time.monotonic()+360
while time.monotonic()<end:
 with urllib.request.urlopen(base+'/jobs/'+job['id']) as r:data=json.load(r)
 if data['status']=='failed':raise RuntimeError(data['error'])
 if data['status']=='ready':
  assert data['plan'].get('reference_analysis');(H/'demos/combined-reference-test.json').write_text(json.dumps(data,indent=2));print('Combined image + text plan ready; reference observations persisted');break
 time.sleep(2)
else:raise TimeoutError()

