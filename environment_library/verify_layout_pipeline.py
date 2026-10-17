"""Fresh image analysis, optional layout, Unreal construction and preview demo."""
import json,base64,time,urllib.request,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'demos/Walkthrough';D.mkdir(exist_ok=True);B='http://127.0.0.1:8521'
def request(path,body=None):
 req=urllib.request.Request(B+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def wait(job):
 deadline=time.monotonic()+480
 while time.monotonic()<deadline:
  r=request('/api/jobs/'+job['id']);(D/'progress.json').write_text(json.dumps(r,indent=2))
  if r['status'] in ('ready','complete'):return r
  if r['status'] in ('failed','unsupported'):raise RuntimeError(r.get('error'))
  time.sleep(3)
 raise TimeoutError('Demo job timed out')
source=H/'demos/ForestMist/preview.png';shutil.copy2(source,D/'reference.png')
analysis=wait(request('/api/analyze',{'image':base64.b64encode(source.read_bytes()).decode()}));print('REFERENCE_ANALYZED',flush=True)
recipe=analysis['recipe'];recipe['layout']=json.loads((H/'demo_layout.json').read_text());(D/'input-recipe.json').write_text(json.dumps(recipe,indent=2))
done=wait(request('/api/build',{'recipe':recipe}));r=done['report'];assert len(r['layout']['rivers'])==1 and len(r['layout']['paths'])==1 and len(r['layout']['bridges'])==1 and len(r['layout']['forests'])==2
expected=recipe['layout']['rivers'][0]['points'];actual=r['layout']['rivers'][0]['points'];assert len(actual)==len(expected)
from layout import compile_layout
points=compile_layout(recipe['layout'])['rivers'][0]['points'];assert max(abs(a-b) for p,q in zip(points,actual) for a,b in zip(p,q))<1
shutil.copy2(H/done['preview'].lstrip('/'),D/'result.png')
manifest={'source_note':'Existing Unreal forest preview used as the reference image; not a new generated image','reference':'/demos/Walkthrough/reference.png','result':'/demos/Walkthrough/result.png','level':r['level'],'analysis':analysis['analysis'],'layout':recipe['layout'],'build':r,'paid_calls':0,'verification':{'river_coordinates_preserved_cm':True,'path_created':True,'bridge_created':True,'forest_regions_created':2}}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2));print('IMAGE_LAYOUT_DEMO_PASSED '+r['level'],flush=True)
