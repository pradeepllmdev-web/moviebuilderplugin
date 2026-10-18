"""Story 3: 'The Lion Cafe' (about 70 s, 11 shots, one place). Leo walks up to the closed cafe, opens the door, has a first tea at his own
table, Rowan arrives, they shake hands at the entrance, Leo carries a cup inside, a mishap, laughter, a hug and goodbye.
The door gets walls, a room, a roof, a lit window, an awning, a sign and patio tables automatically (door_style 'cafe'), and everything
stays in place for every shot. Written against story_lint.py: travel into the place, scenery is permanent, actors face each other.
  python quick_review.py previs --plan previs_story3:STORY --direction previs_story3:DIRECTION"""
from previs_story import beat,actor,shot,cam
CAFE=[0,0]
STORY=dict(version=1,title='The Lion Cafe',unsupported=[],shots=[
 shot('1 Closed cafe',[actor('lion',-63,-290,[beat('walk',4,distance_cm=230)])]),
 shot('2 Opening',[actor('lion',-63,-60,[beat('open_door',5,'Open for business!'),beat('nod',3)])]),
 shot('3 Morning tea',[actor('lion',0,0,[beat('sit_down',3),beat('drink',6),beat('stand_up',3)])]),
 shot('4 First customer',[actor('lion',-30,-60,[beat('nod',4)],facing_yaw_deg=-90),actor('rowan',110,-60,[beat('wave',4,'Good morning, Leo!')],facing_yaw_deg=90)]),
 shot('5 Welcome',[actor('lion',-28,-60,[beat('handshake',4,'Welcome to my cafe!')]),actor('rowan',28,-60,[beat('handshake',4)])]),
 shot('6 The order',[actor('lion',90,40,[beat('carry_walk',5,distance_cm=200)])]),
 shot('7 Oops',[actor('lion',90,120,[beat('startle',3,'Whoa!'),beat('dodge',3)])]),
 shot('8 Laughing',[actor('lion',-60,60,[beat('laugh',4)],facing_yaw_deg=-90),actor('rowan',60,60,[beat('laugh',4)],facing_yaw_deg=90)]),
 shot('9 Farewell hug',[actor('lion',-27,60,[beat('hug',5)]),actor('rowan',27,60,[beat('hug',5)])]),
 shot('10 See you',[actor('lion',-60,-60,[beat('wave',4,'See you tomorrow!')],facing_yaw_deg=-20),actor('rowan',60,-60,[beat('wave',4)],facing_yaw_deg=20)]),
])
INSIDE=lambda:cam([0,300,140],[0,80,105],28)
DIRECTION=dict(auto_camera=True,sets=[dict(kind='village',origin_cm=CAFE)],shots={
 '1 Closed cafe':dict(origin_cm=CAFE,door_style='cafe',camera=cam([420,-330,150],[0,-60,120],28,[330,-200,150],[0,-30,120])),   # the door ends up centred on x=0 when Leo opens it from x=-63
 '2 Opening':dict(origin_cm=CAFE,door_style='cafe',camera=cam([170,-230,130],[-30,-40,115],34,[120,-160,125])),
 '3 Morning tea':dict(origin_cm=CAFE,offset_cm=[-100,150],door_style='cafe',camera=cam([170,60,125],[-100,200,70],36)),   # inside the room (x -191..191, y -4..316)
 '4 First customer':dict(origin_cm=CAFE,door_style='cafe',camera=cam([40,120,140],[40,-60,105],34)),
 '5 Welcome':dict(origin_cm=CAFE,door_style='cafe',camera=cam([300,-20,130],[0,-60,105],34)),
 '6 The order':dict(origin_cm=CAFE,door_style='cafe',camera=INSIDE()),
 '7 Oops':dict(origin_cm=CAFE,door_style='cafe',camera=INSIDE()),
 '8 Laughing':dict(origin_cm=CAFE,door_style='cafe',camera=cam([0,290,140],[0,60,105],30)),
 '9 Farewell hug':dict(origin_cm=CAFE,door_style='cafe',camera=cam([220,160,140],[0,60,105],34)),
 '10 See you':dict(origin_cm=CAFE,door_style='cafe',camera=cam([320,-60,140],[0,-60,105],32,[300,-20,140])),
})
