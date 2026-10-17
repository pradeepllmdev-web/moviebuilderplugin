"""Exercise public prompt planning and preview-first movie production."""
import json,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
PROMPT='''Create The Forest Shortcut, a 30 second stylized short with lion Leo and adult clothed human Rowan. Exactly six shots of five seconds each, same saved forest RealisticRiver_20261015_093641, morning_fog throughout. Both actors in every shot. Lion starts [-120,0], Rowan [120,0], facing_yaw_deg 0 throughout. Rowan remains stationary throughout because his walking is not calibrated. Short dialogue and listening facial expressions, restrained manual head glances within 25 degrees; no body turns. Use full establishing, medium observation, and reaction/close dialogue cameras. Moving shots must use full camera. Keep both characters' positions continuous across cuts.
Shot1 full: both idle, a wind gust at 0.6 lasting 2 seconds; lion says "A shortcut through the trees!" during an idle/talk beat.
Shot2 Rowan reaction: Rowan says "Wait. Listen to those branches." Lion listens curiously. Manual head glances, no partner or point gaze.
Shot3 medium: a falling branch at time1 lasting1 second, landing at [0,200], length90cm. Both stationary. Leo says "Stay there. I will check." Alert faces. Use branch_fall, no collision or contact.
Shot4 full: Leo walks for2 seconds distance100cm then idles3 seconds, looking forward. Rowan idles5 seconds.
Shot5 full: Leo runs for2 seconds distance200cm then idles3 seconds. Rowan idles5 seconds. No circle, jump, dancing, props, or extra actors. Parallel +Y route with lion x=-120; branch is clear of this path.
Shot6 lion close: both stationary; Leo says "This way is clear. Come on!" Rowan listens reassuringly. No new motion. Use manual glances and expressions, not unsupported physical interaction. This prototype does not promise physical branch collision, full body turns or Rowan locomotion.'''
def api(path,body=None):
 request=urllib.request.Request('http://127.0.0.1:8521'+path,json.dumps(body).encode() if body is not None else None,{'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)
def wait(job):
 last=None;deadline=time.monotonic()+2400
 while time.monotonic()<deadline:
  state=api('/api/jobs/'+job['id']);(H/'forest-shortcut-job.json').write_text(json.dumps(state,indent=2))
  if state.get('stage')!=last:print(state.get('stage'),flush=True);last=state.get('stage')
  if state['status']=='failed':raise RuntimeError(state.get('error'))
  if state['status'] in ['complete','ready']:return state
  time.sleep(2)
 raise TimeoutError('Inspect the active job before retrying')
if __name__=='__main__':
 result=wait(api('/api/movie-plan',{'prompt':PROMPT}));plan=result['plan'];(H/'forest-shortcut-plan.json').write_text(json.dumps(plan,indent=2))
 if plan['unsupported']:raise ValueError(plan['unsupported'])
 if len(plan['shots'])!=6 or abs(sum(sum(g['duration'] for g in s['segments']) for s in plan['shots'])-30)>.01:raise ValueError('Review planner duration before building')
 result=wait(api('/api/movie-pipeline',{'plan':plan,'render':False}));(H/'forest-shortcut-result.json').write_text(json.dumps({'movie_id':result['movie_id'],'title':plan['title']}))
 print('Editable preview ready; inspect continuity before rendering',flush=True)
