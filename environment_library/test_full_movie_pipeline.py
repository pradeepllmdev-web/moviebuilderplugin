"""Exercise the same main-app APIs exposed by the full-movie button."""
import json,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8000/api/movie-studio'
def api(path,body=None):
 req=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
def wait(job):
 last=None;deadline=time.monotonic()+1800
 while time.monotonic()<deadline:
  state=api('/jobs/'+job['id']);(H/'full-pipeline-test-job.json').write_text(json.dumps(state,indent=2))
  if state.get('stage')!=last:print(state.get('stage'),flush=True);last=state.get('stage')
  if state['status']=='failed':raise RuntimeError(state['error'])
  if state['status'] in ['ready','complete']:return state
  time.sleep(2)
 raise TimeoutError('Pipeline test timed out; inspect job before retrying')
prompt='Create a new 8 second, exactly two-shot stationary movie titled The River Secret. Use Rowan and lion in the installed environment RealisticRiver_20261015_093641, forest, morning_fog, same environment and lighting in both shots. Shot 1: medium view of both for 4 seconds, Rowan says "The river knows a secret." Lion listens. Shot 2: lion close-up for 4 seconds, lion says "Then we should listen." Rowan listens with a reassuring smile. Both look at each other with partner gaze. No walking or new contact actions. Each shot includes both characters with the same positions [-120,0] Rowan and [120,0] lion. No unsupported requests.'
planned=wait(api('/movie/plan',{'prompt':prompt}));plan=planned['plan']
if plan['unsupported']:raise RuntimeError('Planner returned unsupported requests')
for shot in plan['shots']:
 if shot.get('environment_id')!='RealisticRiver_20261015_093641':raise RuntimeError('Planner did not retain the requested installed environment')
(H/'full-pipeline-test-plan.json').write_text(json.dumps(plan,indent=2))
finished=wait(api('/movie/pipeline',{'plan':plan}));(H/'full-pipeline-test-result.json').write_text(json.dumps(finished,indent=2));print('FULL_PIPELINE_COMPLETE '+finished['movie_id'],flush=True)
