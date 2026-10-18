"""Background orchestration. Unique output directories preserve all previous scenes."""
import json,subprocess,time,uuid
from pathlib import Path
from scene_prompt import validate,generate,resolve_environment
from scene_gaze import conversation_context
from demo_client import command
H=Path(__file__).resolve().parent
PYTHON=H.parent.parent/'3dobjectnew/server/.venv/Scripts/python.exe'
BLENDER='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
PLUGIN=H.parent.parent/'blendplugin-next/scene_pipeline'

def worker(job,lock,prompt=None,plan=None,carry_poses=None,carry_props=None):
 try:
  if prompt is not None:
   job['stage']='Planning actions, dialogue and environment';job.update(plan=generate(prompt),status='ready',stage='Scene plan ready for review');return
  p=validate(plan)
  if p['unsupported']:raise ValueError('Unsupported requests must be removed before building: '+'; '.join(p['unsupported']))
  if not lock.acquire(blocking=False):raise RuntimeError('Unreal is busy; retry after the current job finishes')
  try:
   D=H/'scene_jobs'/job['id'];D.mkdir(parents=True);(D/'plan.json').write_text(json.dumps(p,indent=2))
   def run(args,name):
    with (D/name).open('w') as stream:
     completed=subprocess.run(args,cwd=PLUGIN,stdout=stream,stderr=subprocess.STDOUT,timeout=900)
    if completed.returncode:raise RuntimeError(name+': '+(D/name).read_text(errors='replace')[-1200:])
   job['stage']='Building body animation, speech, mouth shapes and grounding'
   actors=p.get('actors') or [dict(character=p['character'],segments=p['segments'],position_cm=[0,0])]
   for i,actor in enumerate(actors):
    boxed=(carry_props or {}).get(actor['character']) or any(g['action'].startswith('box_') for g in actor['segments'])
    if actor.get('motion_heading') and any(g['action'] not in ['walk','run','idle','talk','turn'] and not (boxed and g['action'].startswith('box_')) for g in actor['segments']):raise ValueError('After a walking turn, use walk/run/idle/talk/turn (or box actions); build other actions in a separate audition')
    part=D/('actor_'+str(i));part.mkdir();single={k:v for k,v in p.items() if k!='actors'};single.update(character=actor['character'],segments=actor['segments']);single['motion_heading']=actor.get('motion_heading',False);single['partner_gaze']=conversation_context(p,actor);single['facing_yaw_deg']=actor.get('facing_yaw_deg',0);single['actor_position_cm']=actor.get('position_cm',[0,0]);import contact_actions;from character_profiles import PROFILES as _P;single.update(contact_actions.pair_inputs(actors,i,{k:v['height_cm'] for k,v in _P.items()}));single['carry_pose']=(carry_poses or {}).get(actor['character']);(part/'plan.json').write_text(json.dumps(single))
    single['box_state']=(carry_props or {}).get(actor['character']);single['box_scene_stands']=actor.get('box_scene_stands');(part/'plan.json').write_text(json.dumps(single))
    run([BLENDER,'-b','-t','6','--python-exit-code','1','-P',str(H/'build_prompt_scene_blender.py'),'--',str(part)],'build-'+str(i)+'.log')
   run([BLENDER,'-b','-t','6','--python-exit-code','1','-P',str(H/'merge_prompt_scene_blender.py'),'--',str(D)],'merge.log')
   job['stage']='Exporting the reusable character performance'
   run([BLENDER,'-b',str(D/'scene.blend'),'--python-exit-code','1','-P',str(PLUGIN/'export_performance.py'),'--','--out',str(D/'performance'),'--plan',str(D/'scene.json'),'--combine-meshes'],'export.log')
   job['stage']='Checking Unreal project and unsaved changes'
   (H/'demos/scene-active.json').write_text(json.dumps({'id':job['id']}));command('console_command',{'command':'py '+str(H/'preflight_prompt_scene.py').replace('\\','/')});deadline=time.monotonic()+60
   while not (D/'preflight.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Unreal preflight timed out')
    time.sleep(.5)
   preflight=json.loads((D/'preflight.json').read_text())
   if not preflight['ok']:raise RuntimeError('; '.join(preflight['errors']))
   job['stage']='Importing a new editable Unreal scene';rid=uuid.uuid4().hex
   r=command('production_import_performance',dict(request_id=rid,package=str(D/'performance'),environment=p['environment'],mood=p['mood'],source_level=resolve_environment(p['environment_id']) if p.get('environment_id') else None))['result'];deadline=time.monotonic()+900
   while r.get('state') in ['pending','building']:
    if time.monotonic()>deadline:raise TimeoutError('Unreal import timed out. Inspect editor before retrying.')
    time.sleep(2);r=command('production_result',{'request_id':rid})['result']
   if r.get('state')!='done':raise RuntimeError(str(r))
   (D/'native.json').write_text(json.dumps(r,indent=2));job['stage']='Applying movement paths, camera and jump contact surfaces'
   (H/'demos/scene-active.json').write_text(json.dumps({'id':job['id']}));command('console_command',{'command':'py '+str(H/'setup_prompt_scene_unreal.py').replace('\\','/')});deadline=time.monotonic()+120
   while not (D/'ready.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Unreal did not confirm scene setup')
    time.sleep(.5)
   ready=json.loads((D/'ready.json').read_text())
   if not ready['ok']:raise RuntimeError(ready['error'][-1200:])
   job.update(status='complete',stage='Saved and opened in Unreal - play Sequencer',report=ready,scene_id=job['id'])
  finally:lock.release()
 except Exception as e:job.update(status='failed',error=str(e)[:1500])
