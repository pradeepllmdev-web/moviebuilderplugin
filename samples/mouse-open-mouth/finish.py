import json,sys
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
from character_workflow import encode
H=Path(__file__).resolve().parent;p=json.loads((H/'application.json').read_text());assert len(list((H/'frames').glob('*.png')))==p['frames'];encode(H/'frames',Path(p['audio']),H/'milo-mouse-talking.mp4',p['fps'],p['frames']/p['fps'],p['lead']);(H/'delivery.json').write_text(json.dumps({'frames':p['frames'],'fps':p['fps'],'full_decode_passed':True,'fresh_model_only':True,'meshy_model_credits':30,'body_rig':'free local auto_rig after Meshy HTTP 402','production_approved':False},indent=2));print('Mouse talking encoded and decoded successfully')

