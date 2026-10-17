"""Build the continuous preview for the latest completed conversation."""
import json,time
from pathlib import Path
from movie_render import soundtrack
from demo_client import command
H=Path(__file__).resolve().parent
job=json.loads((H/'forest-conversation-job.json').read_text())
if job['status']!='complete':raise RuntimeError('Conversation build has not completed')
D=H/'movie_jobs'/job['id'];movie=json.loads((D/'ready.json').read_text());soundtrack(movie,D)
(H/'conversation-active.txt').write_text(job['id'])
command('console_command',{'command':'py '+str(H/'build_conversation_master.py').replace('\\','/')})
deadline=time.monotonic()+90
while not (D/'master-result.json').exists():
 if time.monotonic()>deadline:raise TimeoutError('Master confirmation missing')
 time.sleep(.5)
report=json.loads((D/'master-result.json').read_text())
if not report.get('ok'):raise RuntimeError(report['error'])
print(json.dumps(report))
