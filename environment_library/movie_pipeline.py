"""Reviewed movie plan -> editable shots -> quality gates -> master -> website draft."""
import json,re,time,uuid,subprocess
from pathlib import Path
from demo_client import command
from movie_quality import check_movie
H=Path(__file__).resolve().parent

class ProgressJob(dict):
 def __init__(self,parent,**kwargs):super().__init__(**kwargs);self.parent=parent
 def __setitem__(self,key,value):
  super().__setitem__(key,value)
  if key=='stage':self.parent['stage']=value
 def update(self,*args,**kwargs):
  values=dict(*args,**kwargs)
  for key,value in values.items():self[key]=value

def worker(job,lock,plan=None,movie_id=None,render=True):
 if not lock.acquire(blocking=False):job.update(status='failed',error='Unreal is busy. Retry after the current job.');return
 try:
  if plan is not None:
   from movie_prompt import worker as build,validate
   plan=validate(plan)
   environments={(s.get('environment_id') or s['environment'],s['mood']) for s in plan['shots']}
   if len(environments)!=1:raise ValueError('Continuous master currently requires one shared environment and lighting mood across shots.')
   child=ProgressJob(job,id=job['id'],status='running');build(child,lock,plan=plan)
   if child['status']!='complete':raise RuntimeError(child.get('error','Shot build failed'))
   movie_id=child['movie_id']
  if not re.fullmatch('[a-f0-9]{32}',str(movie_id or '')):raise ValueError('Invalid saved movie ID')
  D=H/'movie_jobs'/movie_id;movie=json.loads((D/'ready.json').read_text());job['stage']='Checking animation tracks, facial targets, dialogue and routes'
  saved_plan=json.loads((D/'plan.json').read_text())
  if len({(s.get('environment_id') or s['environment'],s['mood']) for s in saved_plan['shots']})!=1:raise ValueError('Continuous master currently requires one shared environment and lighting mood across shots.')
  quality=check_movie(movie,H);(D/'quality.json').write_text(json.dumps(quality,indent=2))
  if not quality['ok']:raise RuntimeError('; '.join(quality['errors']))
  from movie_render import soundtrack
  soundtrack(movie,D);job['stage']='Building continuous Unreal master with mixed audio'
  request_id=uuid.uuid4().hex
  (H/'master-build-request.json').write_text(json.dumps({'movie_id':movie_id,'request_id':request_id,'save_generated':plan is not None}))
  output=D/('master-result-'+request_id+'.json')
  command('console_command',{'command':'py '+str(H/'build_conversation_master.py').replace('\\','/')})
  deadline=time.monotonic()+180
  while not output.exists():
   if time.monotonic()>deadline:raise TimeoutError('Master confirmation timed out; inspect Unreal before retrying')
   time.sleep(.5)
  result=json.loads(output.read_text())
  if not result['ok']:raise RuntimeError(result['error'])
  if render:
   from movie_render import worker as render_movie
   child=ProgressJob(job,id=uuid.uuid4().hex,status='running');render_movie(child,lock,movie_id,'draft')
   if child['status']!='complete':raise RuntimeError(child.get('error','Render failed'))
  movie=json.loads((D/'ready.json').read_text())
  if render:
   from movie_render import ffmpeg
   subprocess.run([ffmpeg(),'-y','-loglevel','error','-ss','0.5','-i',str(D/'movie.mp4'),'-frames:v','1',str(D/'preview.png')],check=True,timeout=60,capture_output=True);movie['poster']='preview.png'
  movie['quality_checks']=quality;(D/'ready.json').write_text(json.dumps(movie,indent=2))
  job.update(status='complete',stage='Movie ready: continuous Unreal preview'+(' and website draft' if render else ''),movie_id=movie_id,report=movie)
 except Exception as error:job.update(status='failed',error=str(error)[:1500])
 finally:lock.release()
