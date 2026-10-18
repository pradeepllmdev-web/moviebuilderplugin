"""Story 7: 'The Morning Bakery' (about 55 s, 10 shots, one place), written with anchors and the new rules:
no limb movement without a purpose (idle beats hold still; every gesture has a line or a stated purpose), a large themed bakery
(counter with glass top, oven with fire, bread shelves, flour sacks, awning, lamp posts, barrels, flower boxes, a cart).
Leo walks up in the lamp light, unlocks the bakery, brings the first tray, greets Rowan, they shake hands, have tea and a toast, and hug.
  python quick_review.py previs --plan previs_story7:STORY --direction previs_story7:DIRECTION --strict"""
from previs_story5 import beat,actor,shot
STORY=dict(version=1,title='The Morning Bakery',unsupported=[],shots=[
 shot('1 Lamp light',[actor('lion','street',[beat('walk',4,distance_cm=230)])]),
 shot('2 Unlocking',[actor('lion','door_front',[beat('open_door',5,'Time to bake the bread!'),beat('idle',3)])]),
 shot('3 First tray',[actor('lion','inside_near',[beat('pick_up',5,purpose='takes the first tray from the table'),beat('idle',3)])]),
 shot('4 To the counter',[actor('lion','inside_center',[beat('carry_walk',5,distance_cm=150)])]),
 shot('5 Tea break',[actor('lion','seat_inside',[beat('sit_down',3),beat('drink',6),beat('stand_up',3)])]),
 shot('6 Good morning',[actor('lion',('entrance','left'),[beat('idle',4)]),actor('rowan',('entrance','right'),[beat('wave',4,'Good morning, Leo!')])]),
 shot('7 Fresh bread',[actor('lion',('entrance','left'),[beat('talk',4,'Fresh bread, just baked!')]),actor('rowan',('entrance','right'),[beat('idle',4)])]),
 shot('8 Welcome',[actor('lion',('entrance','left'),[beat('handshake',4,'Welcome to my bakery!')]),actor('rowan',('entrance','right'),[beat('handshake',4)])]),
 shot('9 Toast',[actor('lion',('inside_center','left'),[beat('celebrate',4,'To fresh bread!')]),actor('rowan',('inside_center','right'),[beat('nod',4,purpose='agrees with the toast')])]),
 shot('10 Thank you',[actor('lion',('inside_center','left'),[beat('hug',5)]),actor('rowan',('inside_center','right'),[beat('hug',5,'Thank you, my friend.')])]),
])
DIRECTION=dict(
 sets=[dict(name='bakery',kind='village',origin_cm=[0,0])],
 shots={t:dict(place='bakery',door_style='bakery') for t in ['1 Lamp light','2 Unlocking','3 First tray','4 To the counter','5 Tea break','6 Good morning','7 Fresh bread','8 Welcome','9 Toast','10 Thank you']})
