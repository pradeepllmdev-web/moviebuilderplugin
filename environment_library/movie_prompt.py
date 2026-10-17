"""Story-to-shots planning and persistent sequential build jobs."""
import asyncio,copy,json,os,sys,uuid,time
from pathlib import Path
from scene_prompt import SYSTEM as SCENE_SYSTEM,validate as validate_scene,environment_options,require_requested_controls
from scene_prompt_worker import worker as scene_worker
H=Path(__file__).resolve().parent
SYSTEM=SCENE_SYSTEM+'''\nInstead of one scene return a short movie: {"version":1,"title":"...","unsupported":[],"shots":[SCENE_PLAN,SCENE_PLAN,SCENE_PLAN]}. Use 2..6 shots, total <=90 seconds. Give every shot version1, title, environment, mood, camera, actors, unsupported, notes. Same cast and environment across shots unless story explicitly changes location. Include both actors in every shot of a two-character conversation, including listener idle beats. Keep actor start placements consistent, [-120,0] lion, [120,0] cat. Alternate full establishing, close dialogue and reaction views. focus:lion|cat|rowan|both chooses the camera subject. close/reaction only stationary. Final walking shot can move actors together on separated parallel paths. Short spoken lines, max8 words per 3 second beat. Do not invent contact actions. Dialogue beats must fit speech duration. No environmental reinterpretation between shots. Build previews before claiming cinematic realism.'''
SYSTEM+=' CRITICAL: notes and unsupported are arrays of short strings, never event objects or null. Put supported wind_gust, twig_snap and branch_fall objects only in each shot events array. These three events are supported. Every actor segment must include action and duration. Preserve explicit per-shot timings and cast. Do not use unsupported to store supported scene cues.'

def validate(raw):
 p=copy.deepcopy(raw)
 if p.get('version')!=1 or not isinstance(p.get('title'),str) or not 1<=len(p['title'])<=160:raise ValueError('Invalid movie title/version')
 if not isinstance(p.get('unsupported'),list) or any(not isinstance(x,str) for x in p['unsupported']):raise ValueError('Invalid unsupported list')
 if not isinstance(p.get('shots'),list) or not 2<=len(p['shots'])<=6:raise ValueError('Use 2..6 shots')
 for shot in p['shots']:
  shot.setdefault('version',1);shot.setdefault('unsupported',[]);shot.setdefault('notes',[])
 p['shots']=[validate_scene(s) for s in p['shots']]
 box_state={}
 for shot in p['shots']:
  for actor in shot.get('actors') or [{'character':shot['character'],'segments':shot['segments']}]:
   phase=box_state.get(actor['character'],'none')
   for beat in actor['segments']:
    action=beat['action']
    if action=='box_pickup':
     if phase!='none':raise ValueError('Use one box pickup per audition')
     phase='held'
    elif action in ['box_carry','box_back','box_hold','box_bump','box_setdown']:
     if phase!='held':raise ValueError(action+' requires an earlier pickup')
     if action=='box_setdown':phase='placed'
   box_state[actor['character']]=phase
 from sit_actions import validate as validate_sitting,SIT_ACTIONS
 seated={}
 for shot in p['shots']:
  for actor in shot.get('actors') or [{'character':shot['character'],'segments':shot['segments']}]:
   if any(g['action'] in SIT_ACTIONS for g in actor['segments']) or seated.get(actor['character']):
    seated[actor['character']]=validate_sitting(actor['segments'],seated.get(actor['character'],False))
 for s in p['shots']:
  if s['unsupported']:p['unsupported']+=s['unsupported']
 if sum(sum(g['duration'] for g in s['segments']) for s in p['shots'])>90:raise ValueError('Keep preview movie under 90 seconds')
 return p

def generate(prompt):
 if not isinstance(prompt,str) or not 5<=len(prompt.strip())<=4000:raise ValueError('Prompt must contain 5..4000 characters')
 sys.path.insert(0,str(H.parent.parent/'3dobjectnew/server'));import scene_ai;scene_ai.load_env_file()
 async def call():
  system=SYSTEM+'\nAvailable environment_id values: '+json.dumps(environment_options())
  raw=await scene_ai._call_openai_json(system,prompt,os.environ.get('OPENAI_API_KEY',''),None)
  reports=H/'planner_reports';reports.mkdir(exist_ok=True);(reports/('movie-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(raw,indent=2))
  try:
   from scene_director import complete_controls
   return await complete_controls(validate(raw),prompt,scene_ai,validate,require_requested_controls)
  except (ValueError,KeyError,TypeError) as e:return require_requested_controls(validate(await scene_ai._call_openai_json(system,prompt+'\nRepair '+json.dumps(raw)+'\nError '+str(e),os.environ.get('OPENAI_API_KEY',''),None)),prompt)
 return asyncio.run(call())

def worker(job,lock,prompt=None,plan=None):
 try:
  if prompt is not None:job['stage']='Planning story and camera shots';job.update(status='ready',stage='Movie plan ready',plan=generate(prompt));return
  p=validate(plan)
  if p['unsupported']:raise ValueError('Revise unsupported requests before building: '+'; '.join(p['unsupported']))
  D=H/'movie_jobs'/job['id'];D.mkdir(parents=True);(D/'plan.json').write_text(json.dumps(p,indent=2));saved=[];positions={};headings={};carry={};props={}
  # Every stand of the movie's box path stands from the first shot (single carrier per environment).
  from box_timeline import movie_stands
  from character_profiles import profile as character_profile
  scene_stands={}
  for s in p['shots']:
   for a in s.get('actors') or [{'character':s['character'],'segments':s['segments']}]:
    if a['character']=='lion' and any(g['action'].startswith('box_') for g in a['segments']):scene_stands.setdefault((s.get('environment_id',s['environment']),'lion'),True)
  for key in scene_stands:
   shots=[next(a for a in (s.get('actors') or [{'character':s['character'],'segments':s['segments']}]) if a['character']=='lion')['segments'] for s in p['shots'] if s.get('environment_id',s['environment'])==key[0] and any(a['character']=='lion' for a in (s.get('actors') or [{'character':s['character']}]))]
   scene_stands[key]=movie_stands(shots,character_profile('lion')['box'])
  for i,s in enumerate(p['shots']):
   if not s.get('actors'):s['actors']=[{'character':s['character'],'segments':s['segments'],'position_cm':[0,0]}]
   # Preserve the last root position across cuts in the same environment.
   for a in s.get('actors',[]):
    previous=positions.get((s.get('environment_id',s['environment']),a['character']))
    if previous:a['position_cm']=previous
    heading=headings.get((s.get('environment_id',s['environment']),a['character']))
    if heading is not None:a['facing_yaw_deg']=heading;a['motion_heading']=True
    stands=scene_stands.get((s.get('environment_id',s['environment']),a['character']))
    if stands:a['box_scene_stands']=stands
   child={'id':uuid.uuid4().hex,'status':'running'};job['stage']='Building shot '+str(i+1)+' of '+str(len(p['shots']))+' - '+s['title'];job['active_shot']=i+1
   scene_worker(child,lock,plan=s,carry_poses=carry,carry_props=props)
   if child['status']!='complete':raise RuntimeError('Shot '+str(i+1)+': '+child.get('error','Build incomplete'))
   scene_id=child['scene_id'];folder=H/'scene_jobs'/scene_id;routes=json.loads((folder/'routes.json').read_text());profiles=json.loads((folder/'profiles.json').read_text())
   for name,rows in routes.items():
    key=(s.get('environment_id',s['environment']),profiles[name]);positions[key]=rows[-1]['location_cm'][:2]
    if key in headings or any(g['action']=='turn' for a in s['actors'] if a['character']==profiles[name] for g in a['segments']):headings[key]=(rows[-1]['yaw']+180)%360-180
   for actor_index,actor in enumerate(s.get('actors') or [{'character':s['character']} ]):
    pose=folder/('actor_'+str(actor_index))/'end-pose.json'
    if pose.exists():carry[actor['character']]=str(pose)
    prop=folder/('actor_'+str(actor_index))/'box-end-state.json'
    if prop.exists():props[actor['character']]=json.loads(prop.read_text())
   saved.append({'scene_id':scene_id,'title':s['title'],'report':child['report']});(D/'progress.json').write_text(json.dumps({'shots':saved}))
  result={'id':job['id'],'title':p['title'],'shots':saved,'rendered':False};(D/'ready.json').write_text(json.dumps(result,indent=2));job.update(status='complete',stage='All editable shots saved; review before rendering',movie_id=job['id'],report=result)
 except Exception as e:job.update(status='failed',error=str(e)[:1500])
