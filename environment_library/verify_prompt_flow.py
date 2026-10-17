import json,urllib.request,time
from pathlib import Path
H=Path(__file__).resolve().parent
BASE='http://127.0.0.1:8521'
def request(path,body=None):
 r=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
 with urllib.request.urlopen(r,timeout=60) as response:return json.load(response)
def wait(job):
 deadline=time.monotonic()+300
 while time.monotonic()<deadline:
  data=request('/api/jobs/'+job['id'])
  if data['status']=='failed':raise RuntimeError(data['error'])
  if data['status'] in ('ready','complete'):return data
  time.sleep(2)
 raise TimeoutError('Job did not complete')
if __name__=='__main__':
 planned=wait(request('/api/prompt-plan',{'prompt':'Create two small houses beside a straight road with three spruce trees away from buildings, at golden hour. Keep the set compact.'}))
 (H/'demos/prompt-test-plan.json').write_text(json.dumps(planned['plan'],indent=2))
 print('PLAN READY',flush=True)
 done=wait(request('/api/prompt-build',{'plan':planned['plan']}))
 (H/'demos/prompt-test-result.json').write_text(json.dumps(done,indent=2))
 print('BUILD COMPLETE '+done['report']['level'],flush=True)
