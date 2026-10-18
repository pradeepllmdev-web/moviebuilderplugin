"""Story 6: 'The Birthday Surprise' (about 60 s, 11 shots, 4 places), written with named anchors (see previs_anchors.py).
Leo plans a surprise, carries a cup of tea over the river and up the mountain steps, sneaks into Rowan's hut while Rowan sleeps, and wakes
him with a cheer; Rowan startles, laughs, they toast and hug.
  python quick_review.py previs --plan previs_story6:STORY --direction previs_story6:DIRECTION --strict"""
from previs_story5 import beat,actor,shot
STORY=dict(version=1,title='The Birthday Surprise',unsupported=[],shots=[
 shot('1 The plan',[actor('lion','clearing',[beat('think',4,'A surprise for Rowan!'),beat('nod',3)])],'medium'),
 shot('2 Setting out',[actor('lion','trail_start',[beat('walk',4,distance_cm=160)])]),
 shot('3 The river',[actor('lion','south_bank',[beat('walk',4,distance_cm=240)])]),
 shot('4 The bridge',[actor('lion','bridge_start',[beat('carry_walk',6,distance_cm=360)])]),
 shot('5 The steps',[actor('lion','stairs_bottom',[beat('climb_stairs',6,distance_cm=220)])]),
 shot('6 Quietly',[actor('lion','door_front',[beat('open_door',5,'Shh, quietly now.'),beat('nod',3)])]),
 shot('7 Asleep',[actor('lion',('inside_center','left'),[beat('look_around',6)]),actor('rowan',('inside_center','right'),[beat('sleep',6)])]),
 shot('8 Surprise',[actor('lion',('inside_center','left'),[beat('celebrate',4,'Surprise!')]),actor('rowan',('inside_center','right'),[beat('get_up',4)])]),
 shot('9 Startled',[actor('lion',('inside_center','left'),[beat('laugh',6)]),actor('rowan',('inside_center','right'),[beat('startle',3),beat('laugh',3)])]),
 shot('10 Toast',[actor('lion',('inside_near','left'),[beat('celebrate',4)]),actor('rowan',('inside_near','right'),[beat('celebrate',4,'Best birthday ever!')])]),
 shot('11 Hug',[actor('lion',('inside_near','left'),[beat('hug',5)]),actor('rowan',('inside_near','right'),[beat('hug',5)])]),
])
DIRECTION=dict(
 sets=[dict(name='forest',kind='forest',origin_cm=[0,0]),dict(name='river',kind='river',origin_cm=[6000,0]),dict(name='mountain',kind='mountains',origin_cm=[12000,0]),dict(name='hut',kind='village',origin_cm=[18000,0])],
 shots={'1 The plan':dict(place='forest'),'2 Setting out':dict(place='forest'),'3 The river':dict(place='river'),'4 The bridge':dict(place='river'),'5 The steps':dict(place='mountain'),
  '6 Quietly':dict(place='hut',door_style='cafe'),'7 Asleep':dict(place='hut',door_style='cafe'),'8 Surprise':dict(place='hut',door_style='cafe'),'9 Startled':dict(place='hut',door_style='cafe'),
  '10 Toast':dict(place='hut',door_style='cafe'),'11 Hug':dict(place='hut',door_style='cafe')})
