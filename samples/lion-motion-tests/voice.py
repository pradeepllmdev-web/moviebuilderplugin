import sys,os,json,wave
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
for line in Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/.env').read_text(encoding='utf-8-sig').splitlines():
 if line.startswith('OPENAI_API_KEY='):os.environ['OPENAI_API_KEY']=line.split('=',1)[1].strip().strip('\"\'')
os.environ['VOICE_PROVIDER']='openai'
from sound import tts
specs=[('standing','Hello! I am Leo. Watch my eyes, my face, and my hands while I speak.'),('walking','Now I am walking and talking. My steps should feel steady and relaxed.'),('running','Time to run! I am picking up speed, but I can still talk to you.'),('circle','Around the track I go! Watch my turns, my stride, and my balance as I race.')]
plan=[]
for name,text in specs:
 p=H/(name+'.wav');tts(text,'fable','Friendly animated lion, clear conversational English','natural and lively',p)
 with wave.open(str(p)) as f:duration=len(f.readframes(f.getnframes()))/(f.getframerate()*f.getnchannels()*f.getsampwidth())
 plan.append({'name':name,'text':text,'audio':str(p),'duration':max(7,round(duration+.8,2))})
 print(name,round(duration,2),flush=True)
(H/'plan.json').write_text(json.dumps(plan,indent=2))

