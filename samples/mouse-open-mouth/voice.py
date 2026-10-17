import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path(__file__).resolve().parent
s=speech_visemes.sapi_speak('Hello! I am Milo, the mouse. Watch me talk, blink, and smile. It is a beautiful day for an adventure.',H,'Microsoft David Desktop',-1)
t=talk_animation.build_track(s['visemes'],s['duration'],emotion='warm',intensity=1.15);(H/'track.json').write_text(json.dumps(t));print(json.dumps({'duration':s['duration'],'frames':t['frames']}))
