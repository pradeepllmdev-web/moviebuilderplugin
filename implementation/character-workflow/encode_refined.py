import json,sys
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
from character_workflow import encode
H=Path('implementation/character-workflow/amber-face-refinement').resolve()
base=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65/demo/standing')
t=json.loads((base/'track.json').read_text());encode(H/'talking-frames',base/'voice.wav',H/'amber-refined-talking.mp4',t['fps'],t['frames']/t['fps'],t['lead']);print('Refined clip encoded and decoded successfully')
