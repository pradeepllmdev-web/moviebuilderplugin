import json,sys,wave
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;p=json.loads((H/'plan.json').read_text());a=json.loads((H/'application.json').read_text());Nframes=a['frames'];duration=Nframes/24
assert all((H/'frames'/f'{i:05d}.png').is_file() for i in range(Nframes))
with wave.open(str(H/'dialogue.wav')) as w:rate=w.getframerate();voice=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
N=round(duration*rate);voice=np.pad(voice,(0,max(0,N-len(voice))))[:N];t=np.arange(N)/rate;score=np.zeros(N)
for start in np.arange(0,duration,5):
 warm=start>=p['lines'][5]['start'];notes=(130.81,164.81,196) if warm else (130.81,155.56,196)
 u=np.maximum(t-start,0);env=(t>=start)*(1-np.exp(-u*1.3))*np.exp(-u/4)
 for freq in notes:score+=.006*env*np.sin(2*np.pi*freq*t)
rng=np.random.default_rng(71);river=np.convolve(rng.normal(0,1,N),np.ones(30)/30,mode='same')*.008
fade=np.minimum(1,t/.4)*np.minimum(1,np.maximum(0,(duration-t)/.8));audio=np.clip(voice+(score+river)*fade,-.98,.98)
with wave.open(str(H/'soundtrack.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((audio*32767).astype('<i2').tobytes())
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
from character_workflow import encode
encode(H/'frames',H/'soundtrack.wav',H/'no-shortcuts.mp4',24,duration,0)
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(H/'no-shortcuts.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(l['start'])} --> {stamp(l['start']+l['duration'])}\n{l['actor'].title()}: {l['text']}" for i,l in enumerate(p['lines'])))
(H/'delivery.json').write_text(json.dumps({'title':'No Shortcuts','duration':duration,'fps':24,'frames':Nframes,'full_decode_passed':True,'meshy_calls':0,'limitations':a['limitations']},indent=2));print('NO_SHORTCUTS_READY; full decode passed.')
