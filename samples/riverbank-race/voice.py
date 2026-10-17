import sys,json,wave
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path(__file__).resolve().parent
lines=[('cat',.6,'Race you to the bridge!'),('lion',2.5,'Ready? Go!'),('cat',7,'Try to keep up, Leo!'),('lion',13,'You win! Next time, I pick the shortcut.')]
plan=[];parts=[]
for i,(actor,start,text) in enumerate(lines):
 v=speech_visemes.sapi_speak(text,H/f'line-{i+1}','Microsoft Zira Desktop' if actor=='cat' else 'Microsoft David Desktop',0)
 tr=talk_animation.build_track(v['visemes'],v['duration'],emotion='warm',intensity=1.05)
 plan.append({'actor':actor,'start':start,'text':text,'duration':v['duration'],'track':tr})
 with wave.open(str(v['wav'])) as w:rate=w.getframerate();parts.append((start,w.readframes(w.getnframes())))
duration=max(18.0,max(l['start']+l['duration']+.8 for l in plan));data=bytearray(round(duration*rate)*2)
for start,raw in parts:data[round(start*rate)*2:round(start*rate)*2+len(raw)]=raw
with wave.open(str(H/'dialogue.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
(H/'plan.json').write_text(json.dumps({'title':'The Riverbank Dash','duration':duration,'fps':24,'lines':plan},indent=2));print(json.dumps({'duration':duration,'lines':len(plan),'paid_calls':0}))
