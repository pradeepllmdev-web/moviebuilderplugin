import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
H=Path('samples/cat-pilot/talking').resolve()
spoken=speech_visemes.sapi_speak('Hello! I am the cat pilot. Now I can talk, blink, and smile. Ready for a little adventure?',H,'Microsoft David Desktop',-1)
track=talk_animation.build_track(spoken['visemes'],spoken['duration'],emotion='warm',intensity=1.2)
(H/'track.json').write_text(json.dumps(track));print(json.dumps({'duration':spoken['duration'],'frames':track['frames'],'voice':spoken['voice']}))
