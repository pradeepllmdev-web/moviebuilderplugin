"""Build independent reviewed Rowan auditions using the production worker."""
import json,threading,uuid,sys
from pathlib import Path
from scene_prompt_worker import worker
H=Path(__file__).resolve().parent
def beat(action,duration,text='',**kwargs):return dict(action=action,duration=duration,dialogue=text,**kwargs)
base=dict(version=1,environment='forest',mood='morning_fog',unsupported=[],notes=[])
plans=[dict(base,title='Rowan and Leo - Morning Greeting',camera='close',focus='rowan',actors=[dict(character='rowan',position_cm=[-120,0],segments=[beat('talk',3,'Good morning, my friend!',look_at='partner'),beat('idle',3,look_at='partner')]),dict(character='lion',position_cm=[120,0],segments=[beat('idle',3,look_at='partner'),beat('talk',3,'Ready for an adventure?',look_at='partner')])]),dict(base,title='Rowan - Walk and Talk',camera='full',character='rowan',segments=[beat('walk',4,'Let us explore this forest.',distance_cm=180),beat('talk',2,'What a beautiful morning!',look_yaw_deg=12)])]
results=[]
for p in (plans[1:] if '--walking-only' in sys.argv else plans):
 job={'id':uuid.uuid4().hex,'status':'running'};worker(job,threading.Lock(),plan=p);results.append(job)
 (H/'rowan-demo-results.json').write_text(json.dumps(results,indent=2))
 if job['status']!='complete':break
