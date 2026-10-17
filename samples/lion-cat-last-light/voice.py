import sys,json,wave
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path(__file__).resolve().parent
lines=[('cat','Leo, the path has disappeared. How will we get home?'),('lion','Look, Amber. One little light is still shining.'),('cat','It is so small. Is it enough?'),('lion','Enough for the next step. We will find the way together.')]
start=1.0;plan=[];parts=[];rate=None
for i,(actor,text) in enumerate(lines):
 d=H/f'line-{i+1}';v=speech_visemes.sapi_speak(text,d,'Microsoft Zira Desktop' if actor=='cat' else 'Microsoft David Desktop',-1)
 t=talk_animation.build_track(v['visemes'],v['duration'],emotion='warm',intensity=1.05)
 plan.append({'actor':actor,'text':text,'start':start,'duration':v['duration'],'track':t})
 with wave.open(str(v['wav'])) as w:
  assert w.getnchannels()==1 and w.getsampwidth()==2
  rate=w.getframerate();parts.append((start,w.readframes(w.getnframes())))
 start+=v['duration']+.7
duration=start+1.0;data=bytearray(round(duration*rate)*2)
for start,raw in parts:data[round(start*rate)*2:round(start*rate)*2+len(raw)]=raw
with wave.open(str(H/'dialogue.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
(H/'plan.json').write_text(json.dumps({'title':'The Last Light','fps':24,'duration':duration,'lines':plan},indent=2))
print(json.dumps({'duration':duration,'lines':len(plan)}))
