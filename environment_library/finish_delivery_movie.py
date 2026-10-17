import json,wave,subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from PIL import Image
D=Path(__file__).resolve().parent/'delivery_scene'
render=json.loads((D/'mrq-result.json').read_text());assert render['success']
F=Path(render['directory']);count=render['frames_expected'];fps=render['fps']
for i in range(count):assert (F/f'{i:04d}.png').exists(),i
plan=json.loads((D/'plan.json').read_text());sim=json.loads((D/'simulation.json').read_text())
with wave.open(str(D/'dialogue.wav')) as w:rate=w.getframerate();voice=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
N=round(count/fps*rate);voice=np.pad(voice,(0,max(0,N-len(voice))))[:N];t=np.arange(N)/rate;audio=voice.copy()
for hz in [130.81,164.81,196]:audio+=.003*np.sin(2*np.pi*hz*t)*(1-np.exp(-t*2))*np.minimum(1,np.maximum(0,(count/fps-t)/.8))
rng=np.random.default_rng(52)
for event in sim['events']:
 if event['event'].endswith('_engine_hit'):
  offset=round(event['time']*rate);n=min(round(.25*rate),N-offset);u=np.arange(n)/rate
  audio[offset:offset+n]+=(.08*np.sin(2*np.pi*85*u)+.025*rng.normal(size=n))*np.exp(-u*22)
transitions=[e for e in sim['events'] if e['event']=='animation_transition']
for i,event in enumerate(transitions):
 if not event['action'].endswith('_walk'):continue
 end=next((e['time'] for e in transitions[i+1:] if e['character']==event['character']),count/fps)
 for contact in np.arange(event['time']+.2,end,.43):
  offset=round(contact*rate);n=min(round(.08*rate),N-offset);u=np.arange(n)/rate
  audio[offset:offset+n]+=.018*rng.normal(size=n)*np.exp(-u*65)
with wave.open(str(D/'soundtrack.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(audio,-.98,.98)*32767).astype('<i2').tobytes())
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
(D/'captions.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f"{stamp(l['start'])} --> {stamp(l['start']+l['duration'])}\n{'Amber' if l['actor']=='cat' else 'Leo'}: {l['text']}" for l in plan['lines']),encoding='utf-8')
ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-y','-framerate',str(fps),'-i',str(F/'%04d.png'),'-i',str(D/'soundtrack.wav'),'-frames:v',str(count),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-c:a','aac','-movflags','+faststart',str(D/'special-delivery.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([ff,'-v','error','-i',str(D/'special-delivery.mp4'),'-f','null','-'],check=True)
Image.open(F/'0400.png').save(D/'poster.png')
for label,frame in [('arrival',60),('reaction',150),('help',280),('ending',440)]:Image.open(F/f'{frame:04d}.png').save(D/(label+'.png'))
(D/'delivery.json').write_text(json.dumps({'title':plan['title'],'duration':count/fps,'fps':fps,'frames':count,'resolution':render['resolution'],
 'full_decode_passed':True,'method':'Unreal Movie Render Queue; recorded collision physics baked into Sequencer',
 'engine_hit_events':[e for e in sim['events'] if e['event'].endswith('_engine_hit')],
 'limitations':['Flat-ground foot drift reduced but still 4–8 cm; no general runtime terrain IK','Parcel follows wrist midpoint; no finger grasp constraints','Basic materials and offline synthesized voices','Preview render uses one temporal/spatial sample']},indent=2))
print('DELIVERY_MOVIE_READY: 504 frames, 24 fps, 21 seconds, full decode passed')
