"""Story 3: 'The Lion Cafe' (about 55 s, 10 shots, one place). Leo opens a street cafe; Rowan is the first customer.
  python quick_review.py previs --plan previs_story3:STORY --direction previs_story3:DIRECTION"""
from previs_story import beat,actor,shot,cam
CAFE=[0,0]
STORY=dict(version=1,title='The Lion Cafe',unsupported=[],shots=[
 shot('1 Opening',[actor('lion',0,60,[beat('hands_on_hips',3,'Open for business!'),beat('nod',3)])]),
 shot('2 First customer',[actor('lion',-40,80,[beat('wave',4)],facing_yaw_deg=-20),actor('rowan',60,260,[beat('wave',4,'Good morning, Leo!')],facing_yaw_deg=180)]),
 shot('3 Welcome',[actor('lion',-28,100,[beat('handshake',4,'Welcome to my cafe!')]),actor('rowan',28,100,[beat('handshake',4)])]),
 shot('4 The order',[actor('lion',-150,-250,[beat('carry_walk',6,distance_cm=240)])]),
 shot('5 Oops',[actor('lion',0,0,[beat('startle',3,'Whoa!'),beat('dodge',3)])]),
 shot('6 Laughing',[actor('lion',-60,0,[beat('laugh',4)],facing_yaw_deg=-90),actor('rowan',60,0,[beat('laugh',4)],facing_yaw_deg=90)]),
 shot('7 Tea together',[actor('lion',0,0,[beat('sit_down',3),beat('drink',6),beat('stand_up',3)])]),
 shot('8 Cheers',[actor('lion',-60,0,[beat('celebrate',4,'To good friends!')],facing_yaw_deg=-90),actor('rowan',60,0,[beat('celebrate',4)],facing_yaw_deg=90)]),
 shot('9 Hug',[actor('lion',-27,0,[beat('hug',5)]),actor('rowan',27,0,[beat('hug',5)])]),
 shot('10 See you',[actor('lion',-60,0,[beat('wave',4,'See you tomorrow!')]),actor('rowan',60,0,[beat('wave',4)])]),
])
DIRECTION=dict(sets=[dict(kind='cafe',origin_cm=CAFE)],shots={
 '1 Opening':dict(camera=cam([180,420,160],[0,-100,110],32,[120,330,140],[0,-100,110])),
 '2 First customer':dict(camera=cam([300,200,140],[0,150,110],32,[260,120,140])),
 '3 Welcome':dict(camera=cam([0,400,150],[0,100,105],32)),
 '4 The order':dict(camera=cam([380,-250,120],[-150,-200,90],32,[380,0,120],[-150,0,90])),
 '5 Oops':dict(camera=cam([200,160,130],[0,0,100],40)),
 '6 Laughing':dict(camera=cam([0,300,140],[0,0,100],32)),
 '7 Tea together':dict(camera=cam([330,40,110],[0,40,70],36)),
 '8 Cheers':dict(camera=cam([0,300,140],[0,0,105],34)),
 '9 Hug':dict(camera=cam([0,260,140],[0,0,105],38)),
 '10 See you':dict(camera=cam([0,330,150],[0,0,105],30,[0,260,150])),
})
