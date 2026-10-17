"""Exercise the live image -> recipe -> NEW Unreal level -> preview path."""
import json,base64,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;B='http://127.0.0.1:8521';progress=H/'demos/reference-pipeline-check.json'
def request(path,body=None):
 req=urllib.request.Request(B+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def wait(job):
 deadline=time.monotonic()+480
 while time.monotonic()<deadline:
  result=request('/api/jobs/'+job['id']);progress.write_text(json.dumps(result,indent=2))
  if result['status'] in ('ready','complete'):return result
  if result['status'] in ('failed','unsupported'):raise RuntimeError(result.get('error'))
  time.sleep(3)
 raise TimeoutError('Pipeline verification timed out')
source=H/'demos/ForestMist/preview.png'
analysis=wait(request('/api/analyze',{'image':base64.b64encode(source.read_bytes()).decode()}))
assert analysis['recipe']['params']['biome'] in ('nordic_forest','birch_grove','beech_woods')
print('IMAGE_ANALYZED '+json.dumps({'biome':analysis['recipe']['params']['biome'],'mood':analysis['recipe']['params']['mood']}),flush=True)
done=wait(request('/api/build',{'recipe':analysis['recipe']}));assert done['report']['level'].startswith('/Game/EnvironmentDemos/ImageSet_')
(H/'demos/reference-pipeline-verified.json').write_text(json.dumps({'source':'Unreal forest preview used as a test reference, not a user-provided image','analysis':analysis,'build':done,'paid_calls':0,'exact_reconstruction':False},indent=2));print('REFERENCE_PIPELINE_PASSED '+done['report']['level'],flush=True)
