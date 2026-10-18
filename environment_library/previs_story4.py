"""Story 4: 'The Lost Cub' (about 65 s, 12 shots, 4 places). Leo follows tiny paw prints through forest, river and mountains to a hut.
Written against story_lint.py: every new place starts with a wide shot of Leo arriving, the paw prints and scenery stay for the whole place,
the door has real walls and a lit window (built automatically), and the speakers look down at the cub.
  python quick_review.py previs --plan previs_story4:STORY --direction previs_story4:DIRECTION"""
from previs_story import beat,actor,shot,cam
FOREST,RIVER,MOUNTAIN,HUT=[0,0],[6000,0],[12000,0],[18000,0]
DOWN=dict(look_pitch_deg=-8)
STORY=dict(version=1,title='The Lost Cub',unsupported=[],shots=[
 shot('1 Dawn',[actor('lion',0,0,[beat('sleep',4),beat('get_up',3)])]),
 shot('2 Footprints',[actor('lion',0,-100,[beat('look_around',3),beat('think',4,'Tiny paw prints. Someone is lost.',**DOWN)])],'medium'),
 shot('3 Following',[actor('lion',0,-100,[beat('walk',5,distance_cm=260)])]),
 shot('4 River bank',[actor('lion',0,-150,[beat('walk',4,distance_cm=240)])]),
 shot('5 The bridge',[actor('lion',0,100,[beat('walk',6,distance_cm=330)])]),
 shot('6 Mountain path',[actor('lion',0,-250,[beat('walk',4,distance_cm=140)])]),
 shot('7 The climb',[actor('lion',0,-100,[beat('climb_stairs',6,distance_cm=220)])]),
 shot('8 The hut',[actor('lion',-63,-150,[beat('walk',3,distance_cm=90)])]),
 shot('9 The door',[actor('lion',-63,-60,[beat('open_door',5),beat('stunned',3,'A light inside?')])]),
 shot('10 Found',[actor('lion',-70,150,[beat('celebrate',4,**DOWN)],facing_yaw_deg=-90),actor('rowan',70,150,[beat('wave',4,'I found the little one!',**DOWN)],facing_yaw_deg=90)]),
 shot('11 Hug',[actor('lion',-27,150,[beat('hug',5)]),actor('rowan',27,150,[beat('hug',5)])]),
 shot('12 Home',[actor('lion',-60,150,[beat('wave',4,'Goodbye, little one!',**DOWN)],facing_yaw_deg=-20),actor('rowan',60,150,[beat('wave',4,'Safe travels!')],facing_yaw_deg=20)]),
])
def prints():
 """Alternating paw prints along the forest trail (world cm); part of the forest for every shot there."""
 return [dict(shape='cylinder',center_cm=[(-7 if i%2 else 7)+FOREST[0],-130+i*22,.4],size_cm=[5,.8],color=[.22,.15,.08],name='Paw',place=FOREST) for i in range(16)]
def cub(origin):
 """A small round lion cub in the hut, between the two actors, for every shot at the hut."""
 x,y=origin[0]+8,origin[1]+150;c=[.92,.62,.26]
 return [dict(shape='sphere',center_cm=[x,y,14],size_cm=[13],color=c,name='Cub',scale=(1,1.2,.9),place=HUT),
  dict(shape='sphere',center_cm=[x,y-12,28],size_cm=[10],color=c,name='CubHead',place=HUT),
  dict(shape='sphere',center_cm=[x-7,y-12,37],size_cm=[3.5],color=[.7,.4,.15],name='CubEar',place=HUT),
  dict(shape='sphere',center_cm=[x+7,y-12,37],size_cm=[3.5],color=[.7,.4,.15],name='CubEar',place=HUT)]
INSIDE=lambda:cam([0,290,150],[0,150,90],28)
DIRECTION=dict(auto_camera=True,sets=[dict(kind='forest',origin_cm=FOREST),dict(kind='river',origin_cm=RIVER),dict(kind='mountains',origin_cm=MOUNTAIN),dict(kind='village',origin_cm=HUT)],
 props=prints()+cub(HUT),
 shots={
  '1 Dawn':dict(origin_cm=FOREST,camera=cam([320,380,170],[0,0,50],32,[250,300,110],[0,0,80])),
  '2 Footprints':dict(origin_cm=FOREST,camera=cam([220,120,150],[0,-100,60],40)),
  '3 Following':dict(origin_cm=FOREST,camera=cam([380,-200,120],[0,-100,90],32,[380,100,120],[0,150,90])),
  '4 River bank':dict(origin_cm=RIVER,camera=cam([520,-300,260],[0,100,40],26,[480,-200,240],[0,150,40])),
  '5 The bridge':dict(origin_cm=RIVER,camera=cam([400,100,140],[0,150,80],32,[400,420,140],[0,430,80])),
  '6 Mountain path':dict(origin_cm=MOUNTAIN,camera=cam([520,-350,260],[0,-60,60],26,[460,-250,240],[0,-20,60])),
  '7 The climb':dict(origin_cm=MOUNTAIN,camera=cam([380,-60,100],[0,-20,40],32,[330,40,110],[0,10,60])),
  '8 The hut':dict(origin_cm=HUT,camera=cam([520,-300,260],[0,60,100],26,[450,-200,230],[0,60,100])),
  '9 The door':dict(origin_cm=HUT,camera=cam([200,-200,130],[-30,-40,110],32,[140,-140,125])),   # outside, side-on; the door is centred on x=0 when Leo opens it from x=-63
  '10 Found':dict(origin_cm=HUT,camera=INSIDE()),
  '11 Hug':dict(origin_cm=HUT,camera=cam([0,290,150],[0,150,100],34)),
  '12 Home':dict(origin_cm=HUT,camera=cam([0,290,150],[0,150,105],30)),
 })
