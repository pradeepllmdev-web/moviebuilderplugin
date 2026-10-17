"""Public-API stepping-turn, listening and portrait audition."""
import json
from pathlib import Path
from test_forest_shortcut import api,wait
H=Path(__file__).resolve().parent
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
def shot(title,camera,lion,rowan,partner=False):
 if partner:
  for g in lion+rowan:g['look_at']='partner'
 return dict(version=1,title=title,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera=camera,focus='lion' if camera=='close' else 'both',unsupported=[],notes=[],actors=[dict(character='lion',position_cm=[-120,0],facing_yaw_deg=-90 if partner else 0,segments=lion),dict(character='rowan',position_cm=[180,160],facing_yaw_deg=90,segments=rowan)])
PLAN=dict(version=1,title='Leo - A Call on the Trail',unsupported=[],shots=[
 shot('Stop and step toward Rowan','full',[beat('walk',2,distance_cm=80),beat('idle',2,emotion='curious',look_yaw_deg=-20),beat('turn',2,angle_deg=-90,radius_cm=80),beat('idle',2)],[beat('idle',2),beat('talk',2,'Leo, wait!',emotion='alert'),beat('idle',4,emotion='curious')]),
 shot('Listen before replying','close',[beat('talk',3,'What did you find?',emotion='curious'),beat('idle',2,emotion='reassuring')],[beat('idle',3,emotion='curious'),beat('talk',2,'The safer path.',emotion='reassuring')],True),
 shot('Turn back and continue','full',[beat('talk',2,'I will check.',emotion='reassuring'),beat('turn',2,angle_deg=90,radius_cm=80),beat('walk',2,distance_cm=100),beat('idle',2)],[beat('idle',8,emotion='reassuring')])])
if __name__=='__main__':
 (H/'turn-conversation-plan.json').write_text(json.dumps(PLAN,indent=2))
 result=wait(api('/api/movie-pipeline',{'plan':PLAN,'render':False}))
 (H/'turn-conversation-result.json').write_text(json.dumps({'movie_id':result['movie_id'],'title':PLAN['title']}))
 print('Editable turning and dialogue audition ready',flush=True)
