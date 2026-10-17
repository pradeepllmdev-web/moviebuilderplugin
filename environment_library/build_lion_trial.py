"""Free lion-only performance trial; builds an editable Unreal sequence, no video render."""
import json,math,subprocess,sys,time,uuid,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent;D=ROOT/'samples/lion-trial';D.mkdir(exist_ok=True)
PLUGIN=ROOT.parent/'blendplugin-next/scene_pipeline'
sys.path.insert(0,str(ROOT.parent/'3dobjectnew/server'))
from speech_visemes import sapi_speak
from demo_client import command
def status(stage):
 (D/'status.json').write_text(json.dumps({'stage':stage,'updated':time.time()}));print(stage,flush=True)
def seg(action,a,b,p,q,yaw,end=None):return dict(action=action,start=a,end=b,**{'from':p,'to':q},yaw_start=yaw,yaw_end=yaw if end is None else end,intensity=.55)
status('Preparing lion-only story and free local voices')
lines=[]
for i,(start,text) in enumerate([(0,'Welcome to my training ground. Today, I am chasing my own record.'),(6,'A good sprint starts with courage. And remembering to breathe!'),(12,'One more lap! If I keep going in circles, I will always find my way home.')]):
 speech=sapi_speak(text,D/f'voice-{i}','Microsoft David Desktop',1)
 import wave
 with wave.open(str(speech['wav'])) as wav:duration=wav.getnframes()/wav.getframerate()
 lines.append(dict(speaker='Leo',to='Leo',text=text,start=start,end=min(start+duration,18),audio=str(speech['wav']),tone='natural',manner='talk'))
segments=[seg('talk',0,6,[-3,0,0],[-3,0,0],0),seg('run',6,12,[-3,0,0],[3,0,0],90)]
for i in range(32):
 a=2*math.pi*i/32;b=2*math.pi*(i+1)/32
 p=[3*math.cos(a),3*math.sin(a),0];q=[3*math.cos(b),3*math.sin(b),0]
 yaw=math.degrees(math.atan2(q[0]-p[0],-(q[1]-p[1])))
 segments.append(seg('run',12+i*6/32,12+(i+1)*6/32,p,q,yaw,yaw+360/32))
plan=dict(title='Leo: The Circular Champion',scene_type='motion',duration=18,fps=24,floor_size=[24,24],actors=[dict(name='Leo',segments=segments)],obstacles=[],camera=dict(offset=[0,-7,2.7],lens_mm=42),lighting='golden',set='field',lines=lines)
catalog=json.loads((PLUGIN/'catalog.json').read_text());lion=dict(catalog['DemoLeo']);lion['gentle_conversation']=False
# Keep this diagnostic copy independent of conversation-only pose filtering.
(D/'catalog.json').write_text(json.dumps({'Leo':lion},indent=2));(D/'scene.json').write_text(json.dumps(plan,indent=2))
blender='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
def run(args,log):
 with (D/log).open('w') as stream:subprocess.run(args,cwd=PLUGIN,stdout=stream,stderr=subprocess.STDOUT,check=True)
status('Building standing, straight-run and circular-run animation in Blender')
run([blender,'-b','-t','6','--python-exit-code','1','-P',str(PLUGIN/'blender_runner.py'),'--',str(D),'--render','none'],'build.log')
status('Exporting body, face, camera and dialogue performance')
run([blender,'-b',str(D/'scene.blend'),'--python-exit-code','1','-P',str(PLUGIN/'export_performance.py'),'--','--out',str(D/'performance-18s'),'--plan',str(D/'scene.json'),'--combine-meshes'],'export.log')
status('Importing editable performance into Unreal')
request_id=uuid.uuid4().hex
result=command('production_import_performance',dict(request_id=request_id,package=str(D/'performance-18s'),environment='mountains',mood='golden_hour',source_level='/Game/EnvironmentDemos/PromptSet_75c53dbd326e'))['result']
deadline=time.monotonic()+900
while result.get('state') in ('pending','building') and time.monotonic()<deadline:
 time.sleep(2);result=command('production_result',dict(request_id=request_id))['result']
if result.get('state')!='done':raise RuntimeError(str(result))
(D/'native.json').write_text(json.dumps(result,indent=2));status('Unreal sequence built; ready for material and playback checks')


