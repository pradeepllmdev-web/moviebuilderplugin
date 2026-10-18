"""Story 4: 'The Lost Cub' (about 52 s, 9 shots, 4 places). Leo follows tiny paw prints through forest, river and mountains to a hut.
  python quick_review.py previs --plan previs_story4:STORY --direction previs_story4:DIRECTION"""
from previs_story import beat,actor,shot,cam
FOREST,RIVER,MOUNTAIN,HUT=[0,0],[6000,0],[12000,0],[18000,0]
STORY=dict(version=1,title='The Lost Cub',unsupported=[],shots=[
 shot('1 Dawn',[actor('lion',0,0,[beat('sleep',4),beat('get_up',3)])]),
 shot('2 Footprints',[actor('lion',0,-100,[beat('look_around',3),beat('think',4,'Tiny paw prints. Someone is lost.')])],'medium'),
 shot('3 Following',[actor('lion',0,-100,[beat('walk',5,distance_cm=260)])]),
 shot('4 The bridge',[actor('lion',0,100,[beat('walk',6,distance_cm=330)])]),
 shot('5 The climb',[actor('lion',0,-100,[beat('climb_stairs',6,distance_cm=220)])]),
 shot('6 The hut',[actor('lion',0,-60,[beat('open_door',5),beat('stunned',3,'A light inside?')])]),
 shot('7 Found',[actor('lion',-70,0,[beat('celebrate',4)],facing_yaw_deg=-90),actor('rowan',70,0,[beat('wave',4,'I found the little one!')],facing_yaw_deg=90)]),
 shot('8 Hug',[actor('lion',-27,0,[beat('hug',5)]),actor('rowan',27,0,[beat('hug',5)])]),
 shot('9 Home',[actor('lion',-60,0,[beat('wave',4,'Goodbye, little one!')]),actor('rowan',60,0,[beat('wave',4,'Safe travels!')])]),
])
def prints():
 """Alternating paw prints along the forest trail (world cm), only there for the first shots."""
 return [dict(shape='cylinder',center_cm=[(-7 if i%2 else 7)+FOREST[0],-130+i*22,.4],size_cm=[5,.8],color=[.22,.15,.08],name='Paw',only_in=['2 Footprints','3 Following']) for i in range(16)]
def cub(origin):
 """A small round lion cub standing between the two actors in the last shots."""
 x,y=origin[0]+8,origin[1];c=[.92,.62,.26];late=['7 Found','8 Hug','9 Home']
 return [dict(shape='sphere',center_cm=[x,y,14],size_cm=[13],color=c,name='Cub',scale=(1,1.2,.9),only_in=late),
  dict(shape='sphere',center_cm=[x,y-12,28],size_cm=[10],color=c,name='CubHead',only_in=late),
  dict(shape='sphere',center_cm=[x-7,y-12,37],size_cm=[3.5],color=[.7,.4,.15],name='CubEar',only_in=late),
  dict(shape='sphere',center_cm=[x+7,y-12,37],size_cm=[3.5],color=[.7,.4,.15],name='CubEar',only_in=late)]
DIRECTION=dict(sets=[dict(kind='forest',origin_cm=FOREST),dict(kind='river',origin_cm=RIVER),dict(kind='mountains',origin_cm=MOUNTAIN),dict(kind='village',origin_cm=HUT)],
 props=prints()+cub(HUT),
 shots={
  '1 Dawn':dict(origin_cm=FOREST,camera=cam([320,380,170],[0,0,50],32,[250,300,110],[0,0,80])),
  '2 Footprints':dict(origin_cm=FOREST,camera=cam([220,120,150],[0,-100,60],40)),
  '3 Following':dict(origin_cm=FOREST,camera=cam([380,-200,120],[0,-100,90],32,[380,100,120],[0,150,90])),
  '4 The bridge':dict(origin_cm=RIVER,camera=cam([400,100,140],[0,150,80],32,[400,420,140],[0,430,80])),
  '5 The climb':dict(origin_cm=MOUNTAIN,camera=cam([380,-60,100],[0,-20,40],32,[330,40,110],[0,10,60])),
  '6 The hut':dict(origin_cm=HUT,camera=cam([220,260,130],[0,-20,100],32,[160,200,120],[0,0,100])),
  '7 Found':dict(origin_cm=HUT,camera=cam([0,330,130],[0,0,90],32)),
  '8 Hug':dict(origin_cm=HUT,camera=cam([0,260,140],[0,0,105],38)),
  '9 Home':dict(origin_cm=HUT,camera=cam([0,330,150],[0,0,105],30,[0,260,150])),
 })
