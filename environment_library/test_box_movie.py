import json
from pathlib import Path
from test_forest_shortcut import api,wait
def beat(action,duration,dialogue='',**extras):return dict(action=action,duration=duration,dialogue=dialogue,**extras)
def shot(title,segments,camera='full'):
 return dict(version=1,title=title,character='lion',environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera=camera,segments=segments,unsupported=[],notes=[])
# The pickup stand is straight ahead: lift, step back, make a walking turn, then carry along the new heading.
PLAN=dict(version=1,title='Leo - A Careful Delivery',unsupported=[],shots=[shot('Lift and carry',[beat('box_pickup',4,'A careful delivery.',emotion='curious'),beat('box_back',2,distance_cm=40),beat('turn',3,angle_deg=-90,radius_cm=60),beat('box_carry',4,distance_cm=120),beat('box_hold',2)]),shot('A gentle bump and safe landing',[beat('box_bump',3,'Oops. Gently.',emotion='alert'),beat('box_hold',2,emotion='curious'),beat('box_setdown',4),beat('idle',2,emotion='reassuring')]),shot('Job done',[beat('talk',4,'There. Safe and sound.',emotion='reassuring')],'medium')])
if __name__=='__main__':
 result=wait(api('/api/movie-pipeline',{'plan':PLAN,'render':False}));Path(__file__).with_name('box-movie-result.json').write_text(json.dumps({'movie_id':result['movie_id']}));print('Box preview ready',flush=True)
