"""Story 9: 'Tea for a Sick Friend' (about 66 s, 11 shots, 4 places), written against every rule so far and with the anchors system.
Leo picks up a cup in town, carries it over the river bridge, climbs the mountain steps and opens Rowan's door (push, then it swings on),
walks through the doorway and across the cosy room to Rowan, who is unwell by the fire; they talk, shake hands (turned toward each other)
and Leo has tea by the fire facing the room. Every gesture has a line or a purpose, listeners hold still, nobody crosses a wall, the
scenery is permanent.
  python quick_review.py previs --plan previs_story9:STORY --direction previs_story9:DIRECTION --strict"""
from previs_story5 import beat,actor,shot
STORY=dict(version=1,title='Tea for a Sick Friend',unsupported=[],shots=[
 shot('1 The cup',[actor('lion','street_near',[beat('pick_up',5,purpose='takes the steaming cup for Rowan'),beat('idle',3)])]),
 shot('2 Setting out',[actor('lion','street',[beat('carry_walk',5,distance_cm=110)])]),
 shot('3 Over the river',[actor('lion','bridge_start',[beat('carry_walk',6,distance_cm=360)])]),
 shot('4 Up the steps',[actor('lion','stairs_bottom',[beat('climb_stairs',6,distance_cm=220)])]),
 shot('5 The door',[actor('lion','door_front',[beat('open_door',5,'Rowan? It is Leo.'),beat('idle',3)])]),
 shot('6 Coming in',[actor('lion','doorway',[beat('walk',5,distance_cm=260)])]),
 shot('7 By the fire',[actor('lion','room_entry',[beat('walk',4,'Poor Rowan, I brought tea.',distance_cm=150)]),actor('rowan','inside_back',[beat('headache',4,purpose='is unwell, holding his head')])]),
 shot('8 Tea for you',[actor('lion',('inside_center','left'),[beat('talk',4,'I brought your tea.')]),actor('rowan',('inside_center','right'),[beat('idle',4)])]),
 shot('9 Thank you',[actor('lion',('inside_center','left'),[beat('idle',4)]),actor('rowan',('inside_center','right'),[beat('talk',4,'That is so kind, Leo.')])]),
 shot('10 Get well soon',[actor('lion',('inside_center','left'),[beat('handshake',4,'Get well soon, friend.')]),actor('rowan',('inside_center','right'),[beat('handshake',4)])]),
 shot('11 Fireside',[actor('lion','seat_inside',[beat('sit_down',3),beat('drink',6),beat('sit',3,'Now we rest.')],face='toward:inside_center')]),
])
DIRECTION=dict(
 sets=[dict(name='town',kind='village',origin_cm=[0,0]),dict(name='river',kind='river',origin_cm=[6000,0]),dict(name='mountain',kind='mountains',origin_cm=[12000,0]),dict(name='hut',kind='village',origin_cm=[18000,0])],
 shots={'1 The cup':dict(place='town'),'2 Setting out':dict(place='town'),'3 Over the river':dict(place='river'),'4 Up the steps':dict(place='mountain'),
  **{t:dict(place='hut') for t in ['5 The door','6 Coming in','7 By the fire','8 Tea for you','9 Thank you','10 Get well soon','11 Fireside']}})
