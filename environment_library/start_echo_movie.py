import urllib.request,json,time
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/echo-inspector';movie=json.loads((D/'movie.json').read_text());base='http://127.0.0.1:8000/api/studio'
def request(path,body=None):
 req=urllib.request.Request(base+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
 except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode()[:1000])
tool=request('/tools?engine=combined');print('Combined tool available:',tool.get('available'),flush=True)
if not tool.get('available'):raise RuntimeError(tool.get('error'))
plan=request('/scenes/'+str(movie['scene_id'])+'/plan',{'engine':'combined','bindings':movie['bindings'],'environment':'mountains','mood':'golden_hour','source_level':movie['source_level']});(D/'production-plan.json').write_text(json.dumps(plan,indent=2))
job=request('/jobs',{'plan_id':plan['plan_id']});(D/'job.json').write_text(json.dumps(job,indent=2));print('JOB '+job['id'],flush=True)
