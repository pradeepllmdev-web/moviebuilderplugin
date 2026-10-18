"""Sample movie plans for previs: a reel of every activity, and a small story. Run:
  python quick_review.py previs --plan previs_samples:STORY --render"""
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
def shot(title,actors,camera='full',**extra):
 return dict(version=1,title=title,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='morning_fog',lookdev='soft_portrait',camera=camera,unsupported=[],notes=[],actors=actors,**extra)
def actor(character,x,segments,y=0):return dict(character=character,position_cm=[x,y],segments=segments)
STORY=dict(version=1,title='Leo and Rowan',unsupported=[],shots=[
 shot('Arrival',[actor('lion',-150,[beat('walk',4,distance_cm=150),beat('wave',3,'Hello!')]),actor('rowan',150,[beat('idle',4),beat('wave',3)])]),
 shot('Greeting',[actor('lion',-34,[beat('handshake',5)]),actor('rowan',34,[beat('handshake',5)])]),
 shot('Rest',[actor('lion',0,[beat('sit_down',3),beat('drink',5),beat('stand_up',3)])]),
 shot('Farewell',[actor('lion',-60,[beat('hands_on_hips',3),beat('wave',3,'Goodbye!')]),actor('rowan',60,[beat('nod',3),beat('wave',3)])],camera='medium')])
