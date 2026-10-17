import json,time,urllib.request
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
results=[]
for kind in ('rain','snow'):
 plan={'mood':'overcast_drizzle','buildings':[{'position_cm':[-1800,400],'width_tiles':3,'depth_tiles':3},{'position_cm':[1000,400],'width_tiles':3,'depth_tiles':3}],'roads':[{'id':'main','kind':'straight','cell':[0,0]}],'assets':[],'unsupported':[],'weather':{'type':kind,'intensity':.12 if kind=='snow' else .3,'wind_cm_s':[40,15],'wetness':.85 if kind=='rain' else 0,'snow_cover':.85 if kind=='snow' else 0},'mountains':{'enabled':kind=='snow','height_cm':35000,'size_cm':180000,'distance_cm':150000,'side_deg':90}}
 try:
  done=wait(request('/build',{'plan':plan}));results.append({'kind':kind,'plan':plan,'result':done});print(kind+': '+done['preview'],flush=True)
 except Exception as e:results.append({'kind':kind,'error':str(e)});print(kind+' FAILED '+str(e),flush=True);break
 (H/'demos/weather-tests.json').write_text(json.dumps(results,indent=2))
(H/'demos/weather-tests.json').write_text(json.dumps(results,indent=2))
