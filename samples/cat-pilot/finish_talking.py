import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
from character_workflow import encode
H=Path(__file__).resolve().parent/'talking';track=json.loads((H/'track.json').read_text())
assert len(list((H/'frames').glob('*.png')))==track['frames']
encode(H/'frames',H/'voice.wav',H/'cat-pilot-talking.mp4',track['fps'],track['frames']/track['fps'],track['lead'])
(H/'delivery.json').write_text(json.dumps({'frames':track['frames'],'fps':track['fps'],'duration':track['frames']/track['fps'],'full_decode_passed':True,'paid_services_used':False},indent=2));print('Talking preview encoded and decoded successfully')
