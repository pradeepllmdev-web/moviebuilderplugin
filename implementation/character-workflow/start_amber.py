import httpx,json
from pathlib import Path
p=Path('C:/Users/nagal/Downloads/Generated Image October 14, 2026 - 5_29PM.jpg')
with httpx.Client(timeout=60) as c:
 with p.open('rb') as f:r=c.post('http://127.0.0.1:8000/api/movies/files?kind=image',files={'file':(p.name,f,'image/jpeg')})
 r.raise_for_status();file=r.json()
 r=c.post('http://127.0.0.1:8000/api/character-workflows',json={'reference_file_id':file['id'],'name':'Amber Cat','text':'Hello! I am Amber. Today we are testing my smile, my eyes, and the way I move.','anatomy':'biped'})
 r.raise_for_status();job=r.json();Path('implementation/character-workflow/amber-job.json').write_text(json.dumps(job,indent=2));print(json.dumps({'id':job['id'],'status':job['status'],'reference_file_id':file['id']}))
