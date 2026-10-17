"""Close-up eye-life audition: blinks before lines and on attention shifts, gaze darts leading head turns."""
def beat(action,duration,dialogue='',**extras):return dict(action=action,duration=duration,dialogue=dialogue,**extras)
def shot(title,segments,camera='close'):
 return dict(version=1,title=title,character='lion',environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera=camera,eye_life=True,segments=segments,unsupported=[],notes=[])
PLAN=dict(version=1,title='Leo - Living Eyes',unsupported=[],shots=[
 shot('Something in the trees',[beat('idle',3,emotion='curious'),beat('idle',3,emotion='alert',look_yaw_deg=25),beat('talk',4,'Did you hear that?',emotion='curious',look_yaw_deg=0)]),
 shot('Only the wind',[beat('idle',2,emotion='neutral',look_yaw_deg=-20),beat('talk',4,'Only the wind. We are safe.',emotion='reassuring',look_yaw_deg=0)])])
