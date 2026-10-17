"""Fetch two official CC0 architectural surfaces, retaining provenance."""
import json, urllib.request, zipfile, hashlib
from pathlib import Path
H=Path(__file__).resolve().parent/'assets'
records=[]
for name in ['wood_floor_deck','painted_plaster_wall']:
 destination=(H/'source'/name).resolve();destination.mkdir(parents=True,exist_ok=True)
 files=[]
 for suffix in ['diff','rough','nor_dx']:
  filename=name+'_'+suffix+'_2k.jpg'
  url='https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/'+name+'/'+filename
  path=destination/filename
  if not path.exists():
   temporary=path.with_suffix('.part');urllib.request.urlretrieve(url,temporary);temporary.replace(path)
  with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  files.append(dict(role=suffix,path=str(path),url=url,sha256=digest))
 records.append(dict(id=name,source='https://polyhaven.com/a/'+name,license='CC0-1.0',
                     license_reference='https://polyhaven.com/license',files=files,directory=str(destination)))
 print(name+': three 2K maps downloaded',flush=True)
(H/'house-materials.json').write_text(json.dumps(records,indent=2))
