import json,uuid,threading
from pathlib import Path
from movie_render import worker
H=Path(__file__).resolve().parent;mid=(H/'conversation-active.txt').read_text().strip();job={'id':uuid.uuid4().hex,'status':'running'}
(H/'polished-render-job.json').write_text(json.dumps(job))
worker(job,threading.Lock(),mid,'draft')
(H/'polished-render-job.json').write_text(json.dumps(job,indent=2))
