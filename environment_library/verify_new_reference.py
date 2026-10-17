import json,base64,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
def request(path,body=None):
 r=urllib.request.Request('http://127.0.0.1:8521'+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(r,timeout=20) as response:return json.load(response)
source=H/'demos/RiverbankGolden/preview.png';job=request('/api/analyze',{'image':base64.b64encode(source.read_bytes()).decode()});deadline=time.monotonic()+600
while time.monotonic()<deadline:
 result=request('/api/jobs/'+job['id']);(H/'demos/new-reference-check.json').write_text(json.dumps(result,indent=2))
 if result['status']=='ready':
  assert not result['analysis'].get('analysis_cache_hit');assert result['recipe']['params']['river'] in ('near','far');print('FRESH_IMAGE_ANALYSIS_PASSED '+json.dumps({'biome':result['analysis']['biome'],'river':result['analysis']['river'],'cached':False}),flush=True);break
 if result['status'] in ('failed','unsupported'):raise RuntimeError(result.get('error'))
 time.sleep(3)
else:raise TimeoutError('New image analysis timed out')
