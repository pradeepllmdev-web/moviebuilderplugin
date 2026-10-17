import json,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
base=dict(version=1,character='lion',environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',unsupported=[],notes=[])
plan=dict(version=1,title='Leo - Steady Palm Test',unsupported=[],shots=[dict(base,title='Hold the blue ball',camera='full',segments=[dict(action='hold_ball',duration=4,dialogue='Steady hands.')]),dict(base,title='Keep the ball steady',camera='medium',segments=[dict(action='hold_ball',duration=4,dialogue='Not a single wobble.')])])
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:8521'+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
job=api('/api/movie-pipeline',{'plan':plan});deadline=time.monotonic()+1200;last=None
while time.monotonic()<deadline:
 state=api('/api/jobs/'+job['id']);(H/'palm-test-job.json').write_text(json.dumps(state,indent=2))
 if state.get('stage')!=last:print(state.get('stage'),flush=True);last=state.get('stage')
 if state['status']=='failed':raise RuntimeError(state['error'])
 if state['status']=='complete':break
 time.sleep(2)
