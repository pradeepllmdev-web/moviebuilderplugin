"""Cache Unreal's existing asset thumbnail images; never fetch geometry."""
import json,urllib.request,urllib.parse,io
from PIL import Image
from pathlib import Path
H=Path(__file__).resolve().parent
D=H/'assets/thumbnails';D.mkdir(exist_ok=True)
manifest={};missing=[]
for asset in json.loads((H/'assets/prompt-catalog.json').read_text())['assets']:
 try:
  url='http://127.0.0.1:8520/thumbnail?'+urllib.parse.urlencode({'path':asset['path']})
  with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
  Image.open(io.BytesIO(data)).verify()
  suffix='.png' if data.startswith(b'\x89PNG') else '.jpg' if data.startswith(b'\xff\xd8') else None
  if not suffix:raise ValueError('Not an image')
  filename=asset['id']+suffix;(D/filename).write_bytes(data)
  manifest[asset['id']]='/assets/thumbnails/'+filename
 except Exception:missing.append(asset['id'])
(H/'assets/thumbnail-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Saved',len(manifest),'Missing',len(missing))
(H/'assets/thumbnail-missing.json').write_text(json.dumps(missing))
