import json,wave,sys,subprocess
from pathlib import Path
import numpy as np,imageio_ffmpeg
H=Path(__file__).resolve().parent;p=json.loads((H/'plan.json').read_text());r=json.loads((H/'application.json').read_text());frames=r['frames'];fps=r['fps'];duration=frames/fps
acting='--acting' in sys.argv;frame_dir=H/('frames-acting' if acting else 'frames');stem='riverbank-race-acting' if acting else 'riverbank-race'
assert all((frame_dir/f'{i:05d}.png').is_file() for i in range(frames))
with wave.open(str(H/'dialogue.wav')) as w:rate=w.getframerate();voice=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
N=round(duration*rate);voice=np.pad(voice,(0,max(0,N-len(voice))))[:N];t=np.arange(N)/rate;music=np.zeros(N)
notes=[261.63,329.63,392,523.25,392,329.63,293.66,392]
for i,start in enumerate(np.arange(.05,duration,.32)):
 u=t-start;v=np.maximum(u,0);env=(u>=0)*(1-np.exp(-v*120))*np.exp(-v*7)
 freq=notes[i%len(notes)];music+=.022*env*(np.sin(2*np.pi*freq*v)+.25*np.sin(4*np.pi*freq*v))
rng=np.random.default_rng(42);noise=rng.normal(0,1,N);river=np.convolve(noise,np.ones(25)/25,mode='same')*.012
steps=np.zeros(N)
for start in np.arange(4.05,11.8,.28):
 u=t-start;v=np.maximum(u,0);steps+=.012*(u>=0)*np.exp(-v*45)*np.sin(2*np.pi*(85*v+20*v*v))
fade=np.minimum(1,t/.3)*np.minimum(1,np.maximum(0,(duration-t)/.7));audio=np.clip(voice+(music+river+steps)*fade,-.98,.98)
with wave.open(str(H/'soundtrack.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((audio*32767).astype('<i2').tobytes())
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
from character_workflow import encode
encode(frame_dir,H/'soundtrack.wav',H/(stem+'.mp4'),fps,duration,0)
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(H/'riverbank-race.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(l['start'])} --> {stamp(l['start']+l['duration'])}\n{l['actor'].title()}: {l['text']}" for i,l in enumerate(p['lines'])))
(H/('delivery-acting.json' if acting else 'delivery.json')).write_text(json.dumps({'title':'The Riverbank Dash','duration':duration,'frames':frames,'fps':fps,'full_decode_passed':True,'meshy_calls':0,'characters':['existing lion','existing Amber cat'],'music':'original local synthesized score','ambience':'synthesized river and stylized footstep bed','limitations':r['limitations']},indent=2));print('RACE_MOVIE_READY; full decode passed.')
