import sys,json,wave
from pathlib import Path
H=Path(__file__).resolve().parent/'delivery_scene';H.mkdir(exist_ok=True)
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
lines=[];parts=[]
for i,(actor,start,text) in enumerate([('cat',1,'Careful! Special delivery!'),('cat',6,'Whoa! That crate moved!'),('lion',10,'Easy, Amber. I will clear the way.'),('cat',16,'Next time, the parcel gets wheels!')]):
 v=speech_visemes.sapi_speak(text,H/('line-'+str(i+1)),'Microsoft Zira Desktop' if actor=='cat' else 'Microsoft David Desktop',0)
 lines.append(dict(actor=actor,start=start,text=text,duration=v['duration'],track=talk_animation.build_track(v['visemes'],v['duration'],emotion='warm',intensity=1)))
 with wave.open(str(v['wav'])) as w:rate=w.getframerate();parts.append((start,w.readframes(w.getnframes())))
duration=max(21,max(l['start']+l['duration']+.7 for l in lines));data=bytearray(round(duration*rate)*2)
for start,raw in parts:
 offset=round(start*rate)*2;data[offset:offset+len(raw)]=raw
with wave.open(str(H/'dialogue.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
(H/'plan.json').write_text(json.dumps(dict(title='Special Delivery, Extra Courage',duration=duration,lines=lines),indent=2))
print('Delivery dialogue ready; four new lines; no paid calls')
