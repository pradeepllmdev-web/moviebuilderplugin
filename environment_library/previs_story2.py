"""Second previs story, a harder one: 'Storm at the Mountain Hut' (about 85 s, 13 shots, 5 places).
Falls, getting up, a rescue handshake, stairs, a door, tea, a storm scare, sleep and a summit; two actors in half the shots.

  python quick_review.py previs --plan previs_story2:STORY --direction previs_story2:DIRECTION

Same format as previs_story.py. Rowan only stands, gestures, falls and gets up (his walking is not calibrated)."""
from previs_story import beat,actor,shot,cam
FOREST,RIVER,MOUNTAIN,HUT,SUMMIT=[0,0],[6000,0],[12000,0],[18000,0],[24000,0]
STORY=dict(version=1,title='Storm at the Mountain Hut',unsupported=[],shots=[
 shot('1 Trailhead',[actor('lion',-60,0,[beat('look_around',4)],facing_yaw_deg=-90),actor('rowan',60,0,[beat('think',4,'The storm is coming.')],facing_yaw_deg=90)]),
 shot('2 Hurry',[actor('lion',0,-150,[beat('carry_walk',6,distance_cm=330)])]),
 shot('3 Falling branch',[actor('lion',0,100,[beat('startle',3),beat('dodge',3)])]),
 shot('4 The fall',[actor('lion',-100,0,[beat('startle',4)],facing_yaw_deg=-90),actor('rowan',100,0,[beat('fall_back',4)],facing_yaw_deg=90)]),
 shot('5 Get up',[actor('lion',-100,0,[beat('nod',4)],facing_yaw_deg=-90),actor('rowan',100,0,[beat('get_up',4)],facing_yaw_deg=90)]),
 shot('6 Thank you',[actor('lion',-28,0,[beat('handshake',4)]),actor('rowan',28,0,[beat('handshake',4,'Thank you, Leo.')])]),
 shot('7 The climb',[actor('lion',0,-100,[beat('climb_stairs',6,distance_cm=220)])]),
 shot('8 The hut',[actor('lion',0,-60,[beat('open_door',5),beat('stunned',3,'Nobody is home?')])]),
 shot('9 Warm tea',[actor('lion',0,0,[beat('sit_down',3),beat('drink',6),beat('stand_up',3)])]),
 shot('10 Thunder',[actor('lion',-70,0,[beat('startle',3)],facing_yaw_deg=-90),actor('rowan',70,0,[beat('startle',3)],facing_yaw_deg=90)]),
 shot('11 Sleep',[actor('lion',-70,0,[beat('sleep',6)],facing_yaw_deg=-90),actor('rowan',90,0,[beat('sleep',6)],facing_yaw_deg=90)]),
 shot('12 Morning',[actor('lion',-70,0,[beat('get_up',3),beat('hands_on_hips',3)],facing_yaw_deg=-90),actor('rowan',90,0,[beat('get_up',3),beat('laugh',3)],facing_yaw_deg=90)]),
 shot('13 Summit',[actor('lion',-60,0,[beat('celebrate',4,'We made it!'),beat('wave',4)],facing_yaw_deg=-45),actor('rowan',60,0,[beat('celebrate',4),beat('wave',4,'Goodbye, storm!')],facing_yaw_deg=45)]),
])
DIRECTION=dict(
 sets=[dict(kind='forest',origin_cm=FOREST),dict(kind='river',origin_cm=RIVER),dict(kind='mountains',origin_cm=MOUNTAIN),dict(kind='village',origin_cm=HUT),dict(kind='mountains',origin_cm=SUMMIT)],
 shots={
  '1 Trailhead':dict(origin_cm=FOREST,camera=cam([0,330,150],[0,0,100],32)),
  '2 Hurry':dict(origin_cm=RIVER,camera=cam([380,-200,120],[0,-100,90],32,[380,150,120],[0,200,90])),
  '3 Falling branch':dict(origin_cm=RIVER,camera=cam([60,330,140],[0,100,100],35)),
  '4 The fall':dict(origin_cm=MOUNTAIN,camera=cam([0,320,120],[0,0,70],30,[0,300,90])),
  '5 Get up':dict(origin_cm=MOUNTAIN,camera=cam([0,300,100],[0,0,70],32,[0,260,150],[0,0,100])),
  '6 Thank you':dict(origin_cm=MOUNTAIN,camera=cam([0,270,135],[0,0,105],36)),
  '7 The climb':dict(origin_cm=MOUNTAIN,camera=cam([380,-60,100],[0,-20,40],32,[330,40,110],[0,10,60])),
  '8 The hut':dict(origin_cm=HUT,camera=cam([220,260,130],[0,-20,100],32,[160,200,120],[0,0,100])),
  '9 Warm tea':dict(origin_cm=HUT,camera=cam([330,40,110],[0,40,70],36)),
  '10 Thunder':dict(origin_cm=HUT,camera=cam([0,300,140],[0,0,100],32)),
  '11 Sleep':dict(origin_cm=HUT,camera=cam([40,260,200],[10,0,20],32,[40,220,260],[10,0,20])),
  '12 Morning':dict(origin_cm=HUT,camera=cam([0,300,130],[10,0,90],32)),
  '13 Summit':dict(origin_cm=SUMMIT,camera=cam([0,380,60],[0,0,120],28,[0,300,150],[0,0,110])),
 })
