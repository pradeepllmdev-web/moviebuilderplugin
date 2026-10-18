"""Story 8: 'A Friend's Visit' (about 46 s, 8 shots, one place, 'home' theme with fireplace, bed, bookshelf, table and lamp).
Written against every rule so far: Leo walks up, opens the door (push, then it swings on), walks through the doorway into the room, Rowan
is already inside, they greet with an angled handshake, toast, hug, and Leo has tea by the fire facing the room. No gesture without a
line or purpose, idle beats hold still, nobody teleports through a wall, scenery is permanent.
  python quick_review.py previs --plan previs_story8:STORY --direction previs_story8:DIRECTION --strict"""
from previs_story5 import beat,actor,shot
STORY=dict(version=1,title="A Friend's Visit",unsupported=[],shots=[
 shot('1 Evening street',[actor('lion','street',[beat('walk',4,distance_cm=230)])]),
 shot('2 The door',[actor('lion','door_front',[beat('open_door',5,'Anybody home?'),beat('idle',3)])]),
 shot('3 Coming in',[actor('lion','doorway',[beat('walk',5,distance_cm=260)])]),
 shot('4 Who is it',[actor('lion','room_entry',[beat('walk',4,distance_cm=150)]),actor('rowan','inside_back',[beat('think',4,'Who could that be?')])]),
 shot('5 Greeting',[actor('lion',('inside_center','left'),[beat('handshake',4,'Good evening, Rowan!')]),actor('rowan',('inside_center','right'),[beat('handshake',4)])]),
 shot('6 Toast',[actor('lion',('inside_center','left'),[beat('celebrate',4,'To good friends!')]),actor('rowan',('inside_center','right'),[beat('nod',4,purpose='agrees with the toast')])]),
 shot('7 Stay a while',[actor('lion',('inside_center','left'),[beat('hug',5)]),actor('rowan',('inside_center','right'),[beat('hug',5,'Stay a while, my friend.')])]),
 shot('8 By the fire',[actor('lion','seat_inside',[beat('sit_down',3),beat('drink',6),beat('sit',3,'What a perfect evening.')],face='toward:inside_center')]),
])
DIRECTION=dict(
 sets=[dict(name='home',kind='village',origin_cm=[0,0])],
 shots={t:dict(place='home') for t in ['1 Evening street','2 The door','3 Coming in','4 Who is it','5 Greeting','6 Toast','7 Stay a while','8 By the fire']})
