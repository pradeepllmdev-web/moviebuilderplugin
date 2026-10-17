import json,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
req=urllib.request.Request('http://127.0.0.1:8521/api/movie-finish',json.dumps({'movie_id':'952bbdad5b6f43d9b8f65066b839a95f'}).encode(),{'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=60) as r:job=json.load(r)
for _ in range(300):
 with urllib.request.urlopen('http://127.0.0.1:8521/api/jobs/'+job['id'],timeout=60) as r:state=json.load(r)
 (H/'palm-test-job.json').write_text(json.dumps(state,indent=2))
 if state['status']=='failed':raise RuntimeError(state['error'])
 if state['status']=='complete':break
 time.sleep(2)
