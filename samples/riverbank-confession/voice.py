import sys,json,wave
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path(__file__).resolve().parent
lines=[('cat','worried','Leo... I need to tell you something. I took the shortcut.'),('lion','sad',"So... you did not run the whole race?"),('cat','sad',"No. I wanted to win. I am sorry."),('lion','sad','Winning is fun. But I thought we were racing together.'),('cat','worried','Can we try again? No shortcuts this time.'),('lion','warm','Together. And this time, the loser buys the picnic!')]
start=1.;plan=[];parts=[]
for i,(actor,emotion,text) in enumerate(lines):
 v=speech_visemes.sapi_speak(text,H/f'line-{i+1}','Microsoft Zira Desktop' if actor=='cat' else 'Microsoft David Desktop',-1 if i<5 else 0)
 track=talk_animation.build_track(v['visemes'],v['duration'],emotion=emotion,intensity=1.08)
 plan.append({'actor':actor,'emotion':emotion,'text':text,'start':start,'duration':v['duration'],'track':track})
 with wave.open(str(v['wav'])) as w:rate=w.getframerate();parts.append((start,w.readframes(w.getnframes())))
 start+=v['duration']+(1.0 if i in (0,2,3) else .65)
duration=start+1.;data=bytearray(round(duration*rate)*2)
for start,raw in parts:data[round(start*rate)*2:round(start*rate)*2+len(raw)]=raw
with wave.open(str(H/'dialogue.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
(H/'plan.json').write_text(json.dumps({'title':'No Shortcuts','duration':duration,'fps':24,'lines':plan},indent=2));print(json.dumps({'duration':duration,'lines':len(plan),'paid_calls':0}))
