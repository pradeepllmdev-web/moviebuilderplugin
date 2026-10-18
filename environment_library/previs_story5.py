"""Story 5: 'Leo's Delivery' (about 50 s, 8 shots, 4 places), written with named anchors instead of coordinates (see previs_anchors.py).
Leo picks up a cup in town, carries it over the river bridge, climbs the mountain steps, opens Rowan's door and hands over the tea.
  python quick_review.py previs --plan previs_story5:STORY --direction previs_story5:DIRECTION --strict"""
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
def actor(character,at,segments,**extra):return dict(character=character,at=at,position_cm=[0,0],segments=segments,**extra)
def shot(title,actors,camera='full'):
 return dict(version=1,title=title,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='golden_hour',lookdev='soft_portrait',camera=camera,unsupported=[],notes=[],actors=actors)
STORY=dict(version=1,title="Leo's Delivery",unsupported=[],shots=[
 shot('1 Order up',[actor('lion','street_near',[beat('pick_up',5),beat('nod',3,'Order up!')])]),
 shot('2 On the road',[actor('lion','street',[beat('carry_walk',5,distance_cm=110)])]),
 shot('3 The bridge',[actor('lion','bridge_start',[beat('carry_walk',6,distance_cm=360)])]),
 shot('4 The steps',[actor('lion','stairs_bottom',[beat('climb_stairs',6,distance_cm=220)])]),
 shot('5 The door',[actor('lion','door_front',[beat('open_door',5,'Special delivery!'),beat('stunned',3)])]),
 shot('6 Thank you',[actor('lion',('inside_center','left'),[beat('wave',4)]),actor('rowan',('inside_center','right'),[beat('wave',4,'Thank you, Leo!')])]),
 shot('7 Cheers',[actor('lion',('inside_near','left'),[beat('celebrate',4)]),actor('rowan',('inside_near','right'),[beat('celebrate',4)])]),
 shot('8 Hug',[actor('lion',('inside_near','left'),[beat('hug',5)]),actor('rowan',('inside_near','right'),[beat('hug',5)])]),
])
DIRECTION=dict(
 sets=[dict(name='town',kind='village',origin_cm=[0,0]),dict(name='river',kind='river',origin_cm=[6000,0]),dict(name='mountain',kind='mountains',origin_cm=[12000,0]),dict(name='hut',kind='village',origin_cm=[18000,0])],
 shots={'1 Order up':dict(place='town'),'2 On the road':dict(place='town'),'3 The bridge':dict(place='river'),'4 The steps':dict(place='mountain'),
  '5 The door':dict(place='hut',door_style='cafe'),'6 Thank you':dict(place='hut',door_style='cafe'),'7 Cheers':dict(place='hut',door_style='cafe'),'8 Hug':dict(place='hut',door_style='cafe')})
