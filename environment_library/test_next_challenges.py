"""Public-API demos for shared-event acting and a separate walk/stop test."""
import json,time,urllib.request,sys
from pathlib import Path
H=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8521'
def api(path,body=None):
 req=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'} if body else {})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def wait(job):
 deadline=time.monotonic()+1800;last=None
 while time.monotonic()<deadline:
  state=api('/api/jobs/'+job['id']);(H/'next-challenge-job.json').write_text(json.dumps(state,indent=2))
  if state.get('stage')!=last:print(state.get('stage'),flush=True);last=state.get('stage')
  if state['status']=='failed':raise RuntimeError(state['error'])
  if state['status']=='complete':return state
  time.sleep(2)
 raise TimeoutError('Inspect production job before retrying')
base=dict(version=1,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',unsupported=[],notes=[])
def pair(title,camera,duration,speaker=None,text='',emotion='alert',events=None):
 return dict(base,title=title,camera=camera,focus=speaker or 'both',events=events or [],actors=[dict(character=c,position_cm=[-120,0] if c=='rowan' else [120,0],facing_yaw_deg=0,segments=[dict(action='talk' if c==speaker else 'idle',duration=duration,dialogue=text if c==speaker else '',look_at='point',look_target_cm=[0,800,155],emotion=emotion)]) for c in ['rowan','lion']])
wind=dict(version=1,title='A Breath Through the Trees',unsupported=[],shots=[pair('The gust','medium',3,events=[dict(type='wind_gust',time=.6,duration=2)]),pair('Rowan notices','reaction',3,'rowan','What was that?','curious'),pair('Leo reassures','close',4,'lion','Only the wind. We are safe.','reassuring')])
def walking(title,segments):return dict(base,title=title,camera='full',character='lion',segments=segments)
walk=dict(version=1,title='Leo - Walk Stop and Restart',unsupported=[],shots=[walking('Walk then stop',[dict(action='walk',duration=3,distance_cm=180,dialogue=''),dict(action='idle',duration=2,dialogue='')]),walking('Pause then restart',[dict(action='idle',duration=2,dialogue=''),dict(action='walk',duration=3,distance_cm=180,dialogue='')])])
results=[]
for plan in ([wind] if '--wind-only' in sys.argv else [walk] if '--walking-only' in sys.argv else [wind,walk]):
 result=wait(api('/api/movie-pipeline',{'plan':plan}));results.append({'title':plan['title'],'movie_id':result['movie_id']});(H/'next-challenge-results.json').write_text(json.dumps(results,indent=2))
 # Save only this just-generated movie's owned assets before the next build.
 (H/'challenge-save-request.json').write_text(json.dumps({'movie_id':result['movie_id']}));api('/api/status')
 import sys
 sys.path.insert(0,str(H));from demo_client import command
 command('console_command',{'command':'py '+str(H/'save_challenge_assets.py').replace('\\','/')})
