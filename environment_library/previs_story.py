"""Sample story for Blender previs: 'Leo and the Missing Cup' (about 80 s, 12 shots, 4 low-poly places).

  python quick_review.py previs --plan previs_story:STORY --direction previs_story:DIRECTION --render

STORY is an ordinary movie plan (every shot uses `actors`; positions are local to the shot's place). DIRECTION adds what the
planner does not know about: the low-poly sets and where they are in the world, each shot's place (origin_cm) and camera
(pos/target in local cm, to_pos/to_target for a dolly). Both are previs-only; Unreal builds replace the sets later."""
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
def actor(character,x,y,segments,**extra):return dict(character=character,position_cm=[x,y],segments=segments,**extra)
def shot(title,actors,camera='full'):
 return dict(version=1,title=title,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='golden_hour',lookdev='soft_portrait',camera=camera,unsupported=[],notes=[],actors=actors)
STORY=dict(version=1,title='Leo and the Missing Cup',unsupported=[],shots=[
 shot('1 Dawn',[actor('lion',0,0,[beat('sleep',5),beat('get_up',3)])]),
 shot('2 Missing',[actor('lion',0,0,[beat('look_around',3),beat('think',4,'Where did I leave my cup?')])],'medium'),
 shot('3 To the river',[actor('lion',0,-150,[beat('walk',5,distance_cm=260)])]),
 shot('4 Found it',[actor('lion',-150,60,[beat('pick_up',5),beat('celebrate',3,'Found it!')])]),
 shot('5 Bridge',[actor('lion',0,100,[beat('carry_walk',6,distance_cm=360)])]),
 shot('6 A friendly face',[actor('lion',0,-100,[beat('walk',4,distance_cm=200)]),actor('rowan',0,162,[beat('wave',4,'Leo! Over here!')])]),
 shot('7 Handshake',[actor('lion',-28,100,[beat('handshake',4)]),actor('rowan',28,100,[beat('handshake',4,'Welcome, friend!')])]),
 shot('8 Tea time',[actor('lion',0,0,[beat('sit_down',3),beat('drink',6),beat('stand_up',3)])]),
 shot('9 Laughing',[actor('lion',-60,0,[beat('laugh',5)],facing_yaw_deg=-90),actor('rowan',60,0,[beat('laugh',5)],facing_yaw_deg=90)]),
 shot('10 Farewell hug',[actor('lion',-27,0,[beat('hug',5)]),actor('rowan',27,0,[beat('hug',5)])]),
 shot('11 The climb',[actor('lion',0,-100,[beat('climb_stairs',6,distance_cm=220)])]),
 shot('12 Summit',[actor('lion',0,40,[beat('celebrate',4,'What a view!'),beat('wave',4,'Goodbye, everyone!')])]),
])
CLEARING,RIVER,VILLAGE,SUMMIT=[0,0],[6000,0],[12000,0],[18000,0]   # 60 m apart so each place has its own surroundings
def cam(pos,target,lens=32,to_pos=None,to_target=None):
 c=dict(pos_cm=pos,target_cm=target,lens=lens)
 if to_pos:c.update(to_pos_cm=to_pos,to_target_cm=to_target or target)
 return c
DIRECTION=dict(
 sets=[dict(kind='forest',origin_cm=CLEARING),dict(kind='river',origin_cm=RIVER),dict(kind='village',origin_cm=VILLAGE),dict(kind='mountains',origin_cm=SUMMIT)],
 shots={
  '1 Dawn':dict(origin_cm=CLEARING,camera=cam([320,380,170],[0,0,50],32,[250,300,110],[0,0,80])),
  '2 Missing':dict(origin_cm=CLEARING,camera=cam([260,200,150],[0,0,110],40)),
  '3 To the river':dict(origin_cm=RIVER,camera=cam([380,-200,120],[0,-100,90],32,[380,100,120],[0,150,90])),
  '4 Found it':dict(origin_cm=RIVER,camera=cam([-60,380,150],[-150,60,100],35)),
  '5 Bridge':dict(origin_cm=RIVER,camera=cam([400,100,140],[0,150,80],32,[400,380,140],[0,420,80])),
  '6 A friendly face':dict(origin_cm=VILLAGE,camera=cam([350,0,140],[0,60,100],32,[350,80,140])),
  '7 Handshake':dict(origin_cm=VILLAGE,camera=cam([0,270,135],[0,100,105],36)),
  '8 Tea time':dict(origin_cm=VILLAGE,camera=cam([330,40,110],[0,40,70],36)),
  '9 Laughing':dict(origin_cm=VILLAGE,camera=cam([0,300,140],[0,0,100],32)),
  '10 Farewell hug':dict(origin_cm=VILLAGE,camera=cam([0,260,140],[0,0,105],38)),
  '11 The climb':dict(origin_cm=SUMMIT,camera=cam([380,-60,100],[0,-20,40],32,[330,40,110],[0,10,60])),
  '12 Summit':dict(origin_cm=SUMMIT,camera=cam([150,350,60],[0,0,120],28,[150,300,140],[0,0,110])),
 })
