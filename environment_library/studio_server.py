"""Local reference-image environment demo UI; scoped to the demo editor on 8520."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json,base64,uuid,threading,time,urllib.request,traceback,math,re
from reference_to_recipe import analyze,recipe_from_analysis,BIOMES,TERRAINS,MOODS
from demo_client import command,BASE
from layout import compile_layout
H=Path(__file__).resolve().parent;JOBS={};BUILD_LOCK=threading.RLock();JOBS_LOCK=threading.Lock()

def launch(target,job,*args,**kwargs):
 folder=H/'job_meta';folder.mkdir(exist_ok=True);path=folder/(job['id']+'.json');path.write_text(json.dumps(job))
 def run():
  try:target(job,*args,**kwargs)
  except Exception as error:job.update(status='failed',error=str(error)[:1500])
  finally:
   temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(job));temporary.replace(path)
 threading.Thread(target=run,daemon=True).start()

def open_worker(job,spec):
 if not BUILD_LOCK.acquire(blocking=False):job.update(status='failed',error='Unreal is busy building or opening a scene. Wait for it to finish.');return
 try:
  job['stage']='Checking unsaved changes in Unreal'
  request={'id':job['id'],**spec};(H/'demos/open-request.json').write_text(json.dumps(request))
  output=H/'demos'/('open-result-'+job['id']+'.json')
  command('console_command',{'command':'py '+str(H/'open_saved_unreal.py').replace('\\','/')})
  deadline=time.monotonic()+90
  while not output.exists():
   if time.monotonic()>deadline:raise TimeoutError('Unreal did not confirm opening. Inspect the editor before retrying.')
   time.sleep(.3)
  result=json.loads(output.read_text())
  if not result['ok']:raise RuntimeError(result['error'])
  job.update(status='complete',stage='Opened in Unreal',report=result)
 except Exception as error:job.update(status='failed',error=str(error)[:600])
 finally:BUILD_LOCK.release()

def prompt_worker(job,prompt=None,plan=None,reference=None):
 try:
  from prompt_environment import generate,validate
  if prompt is not None:
   observations=None
   if reference:
    job['stage']='Analyzing reference image locally';observations=analyze(reference)
   job['stage']='Planning image and text with the configured AI provider'
   plan=generate(prompt,observations);plan['contract_version']=1
   if observations:plan['reference_analysis']=observations
   planned=H/'demos/plans';planned.mkdir(exist_ok=True);(planned/(job['id']+'.json')).write_text(json.dumps({'prompt':prompt,'plan':plan},indent=2))
   job.update(status='ready',stage='Validated plan ready',plan=plan);return
  validate(plan)
  with BUILD_LOCK:
   name='PromptSet_'+uuid.uuid4().hex[:12];D=H/'demos'/name;D.mkdir(exist_ok=True)
   (D/'plan.json').write_text(json.dumps(plan,indent=2))
   (H/'demos/prompt-build-request.json').write_text(json.dumps({'id':name,'plan':plan}))
   job['stage']='Building modular set in Unreal'
   command('console_command',{'command':'py '+str(H/'build_prompt_unreal.py').replace('\\','/')})
   deadline=time.monotonic()+240
   while not (D/'build-result.json').exists():
    if (D/'error.txt').exists():raise RuntimeError((D/'error.txt').read_text()[-600:])
    if time.monotonic()>deadline:raise TimeoutError('Build timed out; inspect Unreal before retrying')
    time.sleep(1)
   job['stage']='Capturing preview';time.sleep(4)
   with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
   if not data.startswith(b'\x89PNG'):raise RuntimeError('Invalid Unreal preview')
   (D/'preview.png').write_bytes(data)
   job.update(status='complete',stage='Environment saved',preview='/demos/'+name+'/preview.png',report=json.loads((D/'build-result.json').read_text()))
 except Exception as exc:job.update(status='failed',error=str(exc)[:600])
def worker(job,image=None,recipe=None):
 try:
  if image:
   job['stage']='Analyzing reference locally';analysis=analyze(image);job['analysis']=analysis
   try:job['recipe']=recipe_from_analysis(analysis,'Reference_'+uuid.uuid4().hex[:10]);job['recipe']['reference_image']=str(image)
   except ValueError as exc:job.update(status='unsupported',error=str(exc));return
   job.update(status='ready',stage='Recipe ready for review');return
  with BUILD_LOCK:
   job['stage']='Building a new Unreal level';name=recipe['id'];D=H/'demos'/name;D.mkdir(parents=True,exist_ok=True)
   requestfile=H/'demos/build-request.json';requestfile.write_text(json.dumps(recipe,indent=2));(D/'recipe.json').write_text(json.dumps(recipe,indent=2))
   reply=command('console_command',{'command':'py '+str(H/'build_demo_in_unreal.py').replace('\\','/')})
   if reply.get('status')=='error':raise RuntimeError(reply.get('error','Unreal build command failed'))
   deadline=time.monotonic()+240
   while not (D/'build-result.json').exists():
    if (D/'error.txt').exists():raise RuntimeError((D/'error.txt').read_text()[-600:])
    if time.monotonic()>deadline:raise TimeoutError('Unreal build result is not ready; inspect the editor before retrying')
    time.sleep(1)
   report=json.loads((D/'build-result.json').read_text());job['stage']='Capturing Unreal preview';time.sleep(3)
   with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=45) as response:data=response.read()
   if not data.startswith(b'\x89PNG'):raise RuntimeError('Unreal did not return a preview image')
   (D/'preview.png').write_bytes(data);job.update(status='complete',stage='New Unreal level saved',preview='/demos/'+name+'/preview.png',report=report)
 except Exception as exc:job.update(status='failed',error=str(exc)[:600])
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(H),**kw)
 def allowed(self):return self.headers.get('Host','').split(':')[0] in ('127.0.0.1','localhost') and self.headers.get('Origin','') in ('','http://127.0.0.1:8521','http://localhost:8521')
 def send_json(self,data,status=200):
  blob=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(blob)
 def do_GET(self):
  if not self.allowed():self.send_error(403);return
  if self.path.startswith('/api/jobs/'):
   key=self.path.rsplit('/',1)[-1]
   if not re.fullmatch('[a-f0-9]{32}',key):self.send_json({'error':'Invalid job ID'},400);return
   job=JOBS.get(key);saved=H/'job_meta'/(key+'.json')
   if job is None and saved.is_file():
    job=json.loads(saved.read_text())
    if job.get('status')=='running':job.update(status='failed',error='Service restarted during this job. Inspect saved results and Unreal before retrying.')
   self.send_json(job or {'error':'Unknown job'},200 if job else 404);return
  if self.path=='/api/demos':
   items=[]
   for p in (H/'demos').glob('*/build-result.json'):
    r=json.loads(p.read_text());items.append({'id':p.parent.name,'level':r['level'],'biome':r['biome'],'preview':'/demos/'+p.parent.name+'/preview.png','warnings':r.get('warnings',[])})
   self.send_json(items);return
  if self.path=='/api/scene-capabilities':
   from scene_prompt import ACTIONS,environment_options
   self.send_json({'characters':['lion','cat','rowan'],'actions':ACTIONS,'activity_catalog':__import__('activities').summary(),'environments':environment_options(),'cameras':['full','medium','close','reaction'],'attention':{'yaw_deg':[-35,35],'pitch_deg':[-8,8]},'gaze_targets':['manual','forward','point (stationary shared target)','partner (stationary pairs only)'],'sound_events':['twig_snap','wind_gust'],'blink_enabled':{'rowan':True,'lion':True,'cat':False},'summary':'Lion, cat and Rowan; native human eyelids and eye gaze; dialogue, walking, running, circles, dance and isolated jumps. Lion: living eyes (blinks and gaze darts), box lift/back-step/turn/carry/set-down between stands, and sitting on a fitted bench (sit_down, sit, sit_talk, stand_up). One or two characters; saved environments; editable camera shots. Smooth head attention, stationary partner-facing gaze and timed twig sounds. Contact checks are conservative, not full physical simulation.'});return
  if self.path=='/api/set-pieces':
   from set_pieces import SET_PIECES,missing
   self.send_json([dict(id=k,title=v['title'],story=v['beats'],limits=v['limits'],missing=missing(k)) for k,v in SET_PIECES.items()]);return
  if self.path=='/api/movies':
   items=[]
   for p in sorted((H/'movie_jobs').glob('*/ready.json'),key=lambda file:file.stat().st_mtime,reverse=True):
    try:
     item=json.loads(p.read_text())
     if not item.get('calibration'):items.append(item)
    except (ValueError,OSError):continue
   self.send_json(items);return
  if self.path=='/api/scenes':
   items=[]
   for p in (H/'scene_jobs').glob('*/ready.json'):
    r=json.loads(p.read_text())
    if r.get('ok'):items.append({'id':p.parent.name,'plan':json.loads((p.parent/'plan.json').read_text()),'report':r})
   self.send_json(items);return
  if self.path=='/api/status':self.send_json({'running_jobs':sum(j['status']=='running' for j in JOBS.values())});return
  if self.path in ('/','/index.html'):self.path='/studio.html'
  super().do_GET()
 def do_POST(self):
  if not self.allowed():self.send_error(403);return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=18*1024*1024:raise ValueError('Upload is too large')
   body=json.loads(self.rfile.read(length));job={'id':uuid.uuid4().hex,'status':'running','stage':'Queued'}
   if self.path=='/api/open-folder':
    from unreal_open import open_folder
    self.send_json(open_folder(body));return
   if self.path=='/api/open-unreal':
    from unreal_open import resolve_open
    spec=resolve_open(body);JOBS[job['id']]=job;launch(open_worker,job,spec);self.send_json(job,202);return
   if self.path in ('/api/movie-pipeline','/api/movie-finish'):
    from movie_pipeline import worker as pipeline_worker
    kwargs={'plan':body['plan']} if self.path=='/api/movie-pipeline' else {'movie_id':body.get('movie_id')}
    if 'render' in body:
     if not isinstance(body['render'],bool):raise ValueError('render must be true or false')
     kwargs['render']=body['render']
    JOBS[job['id']]=job;launch(pipeline_worker,job,BUILD_LOCK,**kwargs);self.send_json(job,202);return
   if self.path in ('/api/movie-plan','/api/movie-build','/api/movie-render'):
    if self.path=='/api/movie-render':
     from movie_render import worker as movie_worker
     kwargs={'movie_id':body.get('movie_id'),'quality':body.get('quality','draft')}
    else:
     from movie_prompt import worker as movie_worker,validate as validate_movie
     kwargs={'prompt':body.get('prompt','')} if self.path=='/api/movie-plan' else {'plan':validate_movie(body['plan'])}
    JOBS[job['id']]=job;launch(movie_worker,job,BUILD_LOCK,**kwargs);self.send_json(job,202);return
   if self.path=='/api/story-to-unreal':
    from movie_to_unreal import worker as m2u
    prompt=body.get('prompt');story=body.get('story')
    for v in (prompt,story):
     if v is not None and (not isinstance(v,str) or not 5<=len(v.strip())<=20000):raise ValueError('prompt/story must contain 5..20000 characters')
    if not prompt and not story:raise ValueError('Give a prompt or a story')
    kwargs={'prompt':prompt.strip() if prompt else None,'story':(story.strip()+chr(10)) if story else None,'minutes':max(1,min(30,int(body.get('minutes',8)))),'bridge_url':body.get('bridge_url') or None,'dry_run':bool(body.get('dry_run')),'use_model':bool(body.get('use_model',True))}
    JOBS[job['id']]=job;launch(m2u,job,BUILD_LOCK,**kwargs);self.send_json(job,202);return
   if self.path in ('/api/route','/api/story-write'):
    prompt=body.get('prompt','')
    if not isinstance(prompt,str) or not 5<=len(prompt.strip())<=4000:raise ValueError('Prompt must contain 5..4000 characters')
    if self.path=='/api/route':
     import prompt_router;self.send_json(prompt_router.route(prompt.strip()));return
    import story_writer;minutes=max(1,min(30,int(body.get('minutes',8))));text,notes=story_writer.write_story(prompt.strip(),minutes,use_model=bool(body.get('use_model',True)));self.send_json(dict(story=text,notes=notes));return
   if self.path in ('/api/set-piece-plan','/api/set-piece-build'):
    from set_pieces import worker as piece_worker
    if self.path=='/api/set-piece-plan':
     prompt=body.get('prompt','')
     if not isinstance(prompt,str) or not 5<=len(prompt.strip())<=4000:raise ValueError('Prompt must contain 5..4000 characters')
     kwargs={'prompt':prompt.strip()}
    else:kwargs={'piece':body.get('piece'),'seconds':body.get('seconds')}
    JOBS[job['id']]=job;launch(piece_worker,job,BUILD_LOCK,**kwargs);self.send_json(job,202);return
   if self.path in ('/api/scene-plan','/api/scene-build'):
    from scene_prompt_worker import worker as scene_worker
    from scene_prompt import validate
    kwargs={'prompt':body.get('prompt','')} if self.path=='/api/scene-plan' else {'plan':validate(body['plan'])}
    JOBS[job['id']]=job;launch(scene_worker,job,BUILD_LOCK,**kwargs);self.send_json(job,202);return
   if self.path in ('/api/prompt-plan','/api/prompt-build'):
    if self.path=='/api/prompt-plan':
     prompt=body.get('prompt','')
     if not isinstance(prompt,str) or not 5<=len(prompt.strip())<=4000:raise ValueError('Prompt must contain 5..4000 characters')
     kwargs={'prompt':prompt.strip()}
     if body.get('image'):
      data=base64.b64decode(body['image'].split(',')[-1],validate=True)
      if len(data)>12*1024*1024:raise ValueError('Reference image exceeds 12 MB')
      suffix='.png' if data.startswith(b'\x89PNG') else '.jpg' if data.startswith(b'\xff\xd8') else None
      if not suffix:raise ValueError('Reference must be PNG or JPEG')
      folder=H/'references';folder.mkdir(exist_ok=True);reference=folder/(job['id']+suffix);reference.write_bytes(data);kwargs['reference']=reference
    else:
     from prompt_environment import validate
     validate(body['plan']);kwargs={'plan':body['plan']}
    JOBS[job['id']]=job;launch(prompt_worker,job,**kwargs);self.send_json(job,202);return
   if self.path=='/api/analyze':
    data=base64.b64decode(body['image'].split(',')[-1],validate=True)
    if len(data)>12*1024*1024:raise ValueError('Image exceeds 12 MB')
    suffix='.png' if data.startswith(b'\x89PNG') else '.jpg' if data.startswith(b'\xff\xd8') else None
    if not suffix:raise ValueError('Use a PNG or JPEG reference image')
    folder=H/'references';folder.mkdir(exist_ok=True);image=folder/(job['id']+suffix);image.write_bytes(data);kwargs={'image':image}
   elif self.path=='/api/build':
    incoming=body['recipe'];p=incoming['params'];analysis={'category':'natural_outdoor',**{k:p[k] for k in ('biome','terrain','river','mountains','mood','density')}}
    recipe=recipe_from_analysis(analysis,'ImageSet_'+uuid.uuid4().hex[:10]);recipe['reference_image']=incoming.get('reference_image');recipe['analysis']=incoming.get('analysis',analysis);recipe['params']['seed']=int(p.get('seed',51))
    if not 0<=recipe['params']['seed']<=1000000:raise ValueError('Seed outside supported range')
    if incoming.get('layout'):
     recipe['layout']=incoming['layout'];recipe['compiled_layout']=compile_layout(incoming['layout'])
     if recipe['compiled_layout'].get('camera'):recipe['camera']=recipe['compiled_layout']['camera']
    kwargs={'recipe':recipe}
   else:self.send_error(404);return
   JOBS[job['id']]=job;launch(worker,job,**kwargs);self.send_json(job,202)
  except Exception as exc:self.send_json({'error':str(exc)},400)
if __name__=='__main__':print('Environment demo studio: http://127.0.0.1:8521',flush=True);ThreadingHTTPServer(('127.0.0.1',8521),Handler).serve_forever()
