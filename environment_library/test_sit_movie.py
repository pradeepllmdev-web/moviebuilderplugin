"""Bench audition: sit down, a seated line, stand up."""
def beat(action,duration,dialogue='',**extras):return dict(action=action,duration=duration,dialogue=dialogue,**extras)
def shot(title,segments,camera='full',**extras):
 return dict(version=1,title=title,character='lion',environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera=camera,eye_life=True,segments=segments,unsupported=[],notes=[],**extras)
PLAN=dict(version=1,title='Leo - A Moment to Rest',unsupported=[],shots=[
 shot('Taking a seat',[beat('idle',2,emotion='neutral'),beat('sit_down',3),beat('sit',3,emotion='reassuring')]),
 shot('Thinking out loud',[beat('sit_talk',4,'This is a fine place to rest.',emotion='reassuring'),beat('sit',2,emotion='curious')],'medium'),
 shot('Back on his feet',[beat('sit',2),beat('stand_up',3),beat('idle',2,emotion='alert')])])
