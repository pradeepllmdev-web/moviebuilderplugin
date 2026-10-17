import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path(__file__).resolve().parent
text='The forest has gone quiet. But someone is still out there. This little lantern may not light the whole forest. But it can light the next step. Follow me. We will find the way home, together.'
s=speech_visemes.sapi_speak(text,H,'Microsoft David Desktop',-1)
t=talk_animation.build_track(s['visemes'],s['duration'],emotion='warm',intensity=1.05)
(H/'track.json').write_text(json.dumps(t))
print(json.dumps({'duration':s['duration'],'frames':t['frames']}))
