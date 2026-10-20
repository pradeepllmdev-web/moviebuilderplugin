"""Film 2: 'The Ember Road' - a caravan carries the last coal of a failing lighthouse across the hills to relight a dead beacon before the winter fog (about 15 minutes, 20 scenes, 7 characters, 9 locations).
An overland adventure for the performance engine (perf_dsl): a lion captain, a boar cook, a rabbit scout, a heron navigator, a wolf who knows the road, a stowaway mouse and a badger harbour master.
python perf_movie.py films/ember_road.py out/ember --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='sera',name='Captain Sera',species='lion',posture='proud',accessories=['cape','sword','belt'],tint=[1.0,.82,.6],description='the caravan captain, certain until she is not'),
 dict(id='dorn',name='Dorn',species='boar',posture='tired',accessories=['apron','backpack'],description='the cook, who carries everyone’s opinions'),
 dict(id='kit',name='Kit',species='rabbit',posture='hurried',accessories=['hat_cap','satchel'],description='the scout, first to run and first to stop'),
 dict(id='moss',name='Moss',species='heron',posture='proud',accessories=['glasses','staff'],description='the navigator, tall, vague and usually right'),
 dict(id='thorne',name='Thorne',species='wolf',posture='tense',accessories=['scarf','belt'],tint=[.45,.5,.58],description='a road guide with a debt he does not mention'),
 dict(id='wick',name='Wick',species='mouse',posture='hurried',accessories=['backpack'],tint=[.8,.75,.7],description='a stowaway who wants to see a beacon'),
 dict(id='brant',name='Harbour Master Brant',species='badger',posture='angry',accessories=['hat_cap','medals'],description='the harbour master, gruff and worried'),
]
EMBER=lambda x,y,on=None,z=None:prop('ember','lantern',x,y,on=on,z=z)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the failing light
S.append(scene('failing_light','The failing light',loc('harbor',2,objects=[dict(kind='pedestal',at=[2.0,-1.0],id='stand0',height=1.0,size=.7)]),[at('moss',0,0,face=[2,-1]),at('brant',7,1,face=[3,-1]),at('sera',10,-1,face=[0,0])],props=[EMBER(2.0,-1.0,on='stand0')],steps=[
 look('brant','moss',2),
 take('moss','ember'),
 convo([('moss','Look at it, Brant. It sneezes. It has not held a steady flame since Tuesday.','concern','brant'),('brant','The last coal from the Cape Tern beacon. Forty winters it fed our lighthouse.','sad','moss')]),
 par(go('brant',[1.5,0.6],gait='walk'),go('sera',[2.4,-0.2],gait='walk')),
 convo([('brant','Captain Sera! Good. Tell her, Moss. Tell her what the stars said.','angry','sera'),('moss','The fog comes in three days. Thick as wool, until spring.','serious','sera'),
  ('sera','Then the ships stay home. We have done it before.','serious','moss'),('brant','Not without a light, Captain. Not with the Cape Tern beacon dead for years.','angry','sera')]),
 convo([('moss','The coal is the last of its fire. Take it back, and the old beacon wakes.','serious','sera'),('sera','Across the hills in three days, with a coal that sneezes.','concern','moss')]),
],time='dusk',ambience='sea',music='mystery',extras=crowd(5,[-12,-4,12,5],[2,-1],11)))
# 2 ---------------------------------------------------------------------------------------------------------------- the council
S.append(scene('council','The council of ash',loc('hall',3),[at('sera',-3,-6.5,face=[0,5]),at('moss',3,-6.8,face=[0,5]),at('brant',0,-7.5,face=[0,5]),at('dorn',-6,-7.2,face=[0,5])],props=[prop('chart','map',1.0,-.45,on='table')],steps=[
 par(go('sera',[-1.2,-2.6],gait='strut'),go('moss',[1.6,-2.6],gait='strut'),go('brant',[-3.0,-2.2],gait='stomp'),go('dorn',[3.5,-2.0],gait='walk')),
 take('sera','chart'),
 convo([('brant','Three days over the Hollow Hills. No road. Only moss and cliffs and one old guide, if he lives.','angry','sera'),('moss','I have walked it. In my head. Many times. The map is mostly correct.','serious','sera')]),
 convo([('sera','Mostly.','concern','moss'),('dorn','Mostly is what we say about my soup and nobody has died.','joy','sera'),('sera','Dorn. You are coming. We will need food and morale and a large pot.','warm','dorn'),
  ('dorn','Morale is in the pot.','warm','sera')]),
 wait(.5),
 convo([('brant','The harbour gives you the cart, the ember, and every prayer it has left.','serious','sera'),('sera','Then we leave at dawn. Everyone sleeps. Nobody argues.','serious','brant')]),
 sfx('gong',0.3),
],time='day',ambience='hall',music='epic',extras=crowd(5,[-10,-7,10,7],[0,0],12)))
# 3 ---------------------------------------------------------------------------------------------------------------- loading the cart
S.append(scene('loading','Loading the cart',loc('harbor',4),[at('dorn',-6.5,0.5,face=[-4.4,-2]),at('kit',4,1.5,face=[0,0]),at('wick',6,2.5,face=[0,0])],props=[prop('flour','crate',-4.5,-1.5,z=.25)],steps=[
 par(go('kit',[-1,0.5],gait='brisk'),push('dorn','flour',dist=2.0,dir=0)),
 convo([('kit','The north road is clear and the moon is up. I counted four owls and one very rude cat.','joy','dorn'),('dorn','You counted a cat as a threat?','concern','kit'),('kit','It looked at me like I owed it money.','concern','dorn')]),
 par(go('wick',[1.5,0.2],gait='brisk'),look('dorn','wick',1)),
 sfx('knock',0.2),
 par(act('kit','startle'),act('dorn','startle')),
 convo([('dorn','Did the barrel just move?','concern','kit'),('kit','Barrels do not move. Barrels are loyal.','serious','dorn'),('wick','I am not a barrel!','concern','kit')]),
 par(go('kit','wick',stop=1.2,gait='brisk'),go('dorn','wick',stop=1.8,gait='walk')),
 convo([('dorn','A stowaway! A very small stowaway! Who are you?','angry','wick'),('wick','Wick. I want to see the beacon light up. I have a snack. I have two snacks.','concern','dorn'),('kit','He is smaller than the cat.','joy','dorn')]),
],time='night',ambience='sea',music='bright',extras=crowd(4,[-10,-3,10,5],[-4,-2],13)))
# 4 ---------------------------------------------------------------------------------------------------------------- the departure
S.append(scene('departure','Departure at dawn',loc('meadow',2),[at('sera',-8,-6,face=[0,0]),at('moss',-10,-7,face=[0,0]),at('dorn',-12,-5,face=[0,0]),at('kit',-9,-9,face=[0,0]),at('wick',-13,-8,face=[0,0])],steps=[
 par(go('sera',[-1,0],gait='strut'),go('moss',[-3,-1.8],gait='strut'),go('dorn',[-5,1],gait='walk'),go('kit',[0,2.5],gait='brisk'),go('wick',[-4,3],gait='brisk')),
 convo([('sera','One more look at the sea. After this, only hills.','serious','moss'),('moss','Hills are just waves that forgot to move.','serious','sera'),('dorn','And I have forgotten my second pot.','concern','sera')]),
 par(emote('wick','smile',2)),
 convo([('kit','Captain, the road is empty and golden and nobody is following us.','joy','sera'),('sera','Good. Keep it that way, scout.','warm','kit')]),
 par(go('kit',[12,6],gait='run'),go('sera',[10,3],gait='strut'),go('moss',[8,0],gait='strut'),go('dorn',[7,-3],gait='walk'),go('wick',[6,2.5],gait='brisk')),
],time='dawn',ambience='wind',music='bright',extras=crowd(6,[-14,-10,-6,0],[-1,0],14)))
# 5 ---------------------------------------------------------------------------------------------------------------- first fire
S.append(scene('first_fire','The first fire',loc('campfire_night',3),[at('dorn',-5,3,face=[0,0]),at('sera',4,5,face=[0,0]),at('moss',-3,-6,face=[0,0]),at('kit',6,-3,face=[0,0]),at('wick',-8,-2,face=[0,0])],steps=[
 par(sit('sera','log_e.0',face=[0,0]),sit('moss','log_w.0',face=[0,0]),go('dorn',[-1.8,1.9],gait='walk')),
 par(go('kit',[-2.2,-1.2],gait='brisk'),go('wick',[-3.4,-3.4],gait='brisk')),
 convo([('dorn','Stew. Honest stew. Everything in it is what it says it is.','warm','moss'),('moss','What does it say it is?','concern','dorn'),('dorn','Stew.','serious','moss')]),
 sfx('thud',0.5),
 act('wick','startle'),
 convo([('sera','Who sneezed?','angry','kit'),('kit','The stowaway.','serious','sera'),('sera','The stowaway sneezed at my fire. Bring him here.','angry','kit')]),
 par(go('wick',[-1.0,-1.5],gait='walk'),),
 convo([('wick','I am very quiet and I have been useful. I found the second pot.','concern','sera'),('sera','He found the second pot.','concern','dorn'),('dorn','Captain, I think I love him.','joy','sera')]),
 emote('sera','smile',3),
],time='night',ambience='fire',music='warm'))
# 6 ---------------------------------------------------------------------------------------------------------------- a stranger
S.append(scene('stranger','A stranger on the road',loc('forest_clearing',6),[at('sera',-6,0,face=[1,0]),at('kit',-7,2,face=[1,0]),at('thorne',8,-3,face=[-1,0]),at('moss',-9,-1,face=[1,0])],steps=[
 par(go('thorne',[3.5,0.2],gait='walk'),go('kit',[-3.5,1.8],gait='sneak'),go('sera',[-3.5,-1],gait='strut')),
 convo([('thorne','Easy. I carry a lantern, not a sword. It is the lantern that has opinions.','serious','sera'),('sera','Name.','serious','thorne'),('thorne','Thorne. I guide caravans through the Hollow Hills. For a fair price.','warm','sera')]),
 par(go('moss','sera',stop=1.9,gait='strut'),look('thorne','moss',1.5)),
 convo([('moss','The old guide was called Thorne. He disappeared nine winters ago.','concern','sera'),('thorne','I was away. Business.','serious','moss'),('kit','He looks hungry. And honest, mostly.','warm','sera')]),
 convo([('sera','We have three days and a map that says mostly. Walk beside me, not behind me.','serious','thorne'),('thorne','That is how I like it. Both sides see more.','warm','sera')]),
 par(go('thorne',[-3,-3.6],gait='walk'),go('sera',[-4,-2],gait='strut')),
],time='dusk',ambience='wind',music='mystery'))
# 7 ---------------------------------------------------------------------------------------------------------------- market trouble
S.append(scene('market_trouble','Market trouble',loc('market',4),[at('wick',-2,-6,face=[0,3]),at('dorn',-5,-4,face=[0,3]),at('kit',-2,-11,face=[0,3]),at('sera',6,-9,face=[0,3])],steps=[
 par(go('dorn','stall1',stop=2.2,gait='walk'),go('wick',[0.5,-1],gait='brisk')),
 convo([('dorn','Four sacks of oats, a barrel of salt, and whatever you call this vegetable.','warm','sera'),('sera','Dorn, that is a hat.','concern','dorn'),('dorn','It will taste like a hat. But the price is honest.','serious','sera')]),
 sfx('crash',0.2),
 par(act('kit','startle'),act('sera','startle')),
 convo([('kit','Wick took an apple! He took an apple from the fruit stall and ran!','angry','sera')]),
 par(run('wick',[10,-8]),run('kit',[4,-8])),
 par(go('sera',[8,-5],gait='brisk'),go('dorn',[2,-2],gait='walk')),
 act('wick','fall'),act('wick','getup'),
 convo([('wick','It was a small apple. Everyone said we need to be careful with weight.','concern','kit'),('kit','You are tiny and your conscience is bigger than your head. We pay for it.','warm','wick'),('sera','You pay, Wick. Out of your two snacks.','serious','wick')]),
],time='day',ambience='market',music='comic',extras=crowd(10,[-14,-12,14,10],[0,-2],15)))
# 8 ---------------------------------------------------------------------------------------------------------------- the fog line
S.append(scene('fog_line','The fog line',loc('hilltop',4),[at('moss',-2,-2,face=[8,12]),at('thorne',-4,-3,face=[8,12]),at('wick',-1,-4,face=[8,12])],steps=[
 par(look('moss',[10,14],4),look('thorne',[10,14],4),emote('wick','concern',3)),
 convo([('moss','There. The grey edge on the horizon. That is the fog, walking inland.','serious','thorne'),('wick','It looks like a wall.','concern','moss'),('thorne','It is a wall, little one. Nothing inside it is where you left it.','serious','wick')]),
 par(go('thorne',[-1,-1],gait='walk'),turn('moss','thorne')),
 convo([('thorne','I kept the Cape Tern beacon once. My father before me. We fed it oil from the northern wells.','sad','moss'),('moss','Then why did it go dark?','concern','thorne'),('thorne','Because I left. And a light with no keeper is only a tall candle.','sad','moss')]),
 emote('wick','sad',2),
 convo([('wick','I will keep it.','warm','thorne'),('thorne','You are the size of a doorknob.','joy','wick'),('wick','Doorknobs are very important to doors.','serious','thorne')]),
],time='dusk',ambience='wind',music='sad'))
# 9 ---------------------------------------------------------------------------------------------------------------- storm in the ruins
S.append(scene('storm_ruins','Shelter from the storm',loc('ruins',3,objects=[dict(kind='pedestal',at=[-2.5,1.5],id='shrine',height=.85,size=.7)]),[at('sera',-6,-4,face=[0,0]),at('dorn',-7,-6,face=[0,0]),at('kit',-9,-5,face=[0,0]),at('moss',-8,-8,face=[0,0])],props=[EMBER(-2.5,1.5,on='shrine')],steps=[
 par(go('sera',[-1.5,-1.8],gait='run'),go('dorn',[-2.8,-2.6],gait='walk'),go('kit',[1.8,-2.4],gait='run'),go('moss',[-0.2,-3.2],gait='strut')),
 sfx('thunder',0.2),
 par(act('kit','startle'),act('dorn','startle')),
 take('sera','ember'),
 convo([('sera','Get behind the wall! Everyone, now!','angry','kit'),('dorn','I am behind the wall! The wall is not very behind!','concern','sera')]),
 sfx('thunder',0.5),
 convo([('moss','Captain, the flame.','concern','sera'),('sera','I see it. I am shielding it with my cape.','serious','moss'),('kit','It is so small. It is only a blue bead.','sad','sera')]),
 emote('sera','concern',3),
 convo([('sera','Burn. Please burn. Three more days. That is all I am asking.','sad','sera'),('dorn','It burns, Captain. I can hear it. It is humming.','warm','sera')]),
 sfx('chime',0.3),
 emote('sera','smile',2),
],time='night',ambience='rain',music='tense'))
# 10 --------------------------------------------------------------------------------------------------------------- the murals
S.append(scene('murals','The painted cave',loc('cave',3,objects=[dict(kind='pedestal',at=[3,-1],id='plinth',height=.7,size=.6)]),[at('kit',0,-5,face=[0,0]),at('wick',1,-6,face=[0,0])],props=[prop('chart2','map',3,-1,on='plinth')],steps=[
 par(go('kit',[0.5,-3],gait='brisk'),go('wick',[1.6,-4.2],gait='brisk')),
 convo([('wick','It is enormous. The ceiling is painted. Those are stars. Those are boats.','joy','kit'),('kit','And that is a beacon. A tall one. With rays coming out like a hedgehog.','joy','wick')]),
 par(go('kit',[2.2,-.8],gait='walk'),go('wick',[1.0,-1.6],gait='walk')),
 take('kit','chart2'),
 convo([('kit','A map. Drawn by someone who knew the hills. There is a path under the cliffs.','serious','wick'),('wick','The captain is going over the top. That path is a day shorter.','concern','kit')]),
 act('wick','cele'),
 convo([('kit','Quiet! It is a sacred place. We do not cheer in sacred places.','concern','wick'),('wick','I am not cheering. I am vibrating respectfully.','joy','kit')]),
],time='night',ambience='cave',music='mystery'))
# 11 --------------------------------------------------------------------------------------------------------------- the collapse
S.append(scene('collapse','The collapse',loc('cave',4),[at('kit',-4,-3,face=[0,0]),at('wick',-3,-4.5,face=[0,0]),at('sera',-3,-9,face=[0,0]),at('dorn',-5,-9.5,face=[0,0])],props=[prop('rockfall','boulder',3.5,-2.0,z=.5)],steps=[
 par(go('kit',[3.8,-3.8],gait='brisk'),go('wick',[1.8,-4.4],gait='brisk')),
 sfx('crash',0.2),
 par(act('kit','startle'),act('wick','fall')),
 convo([('wick','Kit! Kit! The ceiling is making noises!','concern','kit'),('kit','That is the ceiling saying goodbye. Run!','angry','wick')]),
 par(act('wick','getup'),go('sera',[0,-5],gait='run'),go('dorn',[-1.5,-6],gait='run')),
 convo([('sera','The way out is blocked. Dorn, the boulder.','angry','dorn'),('dorn','I am a cook, not a bulldozer!','angry','sera'),('sera','You are both. Push!','angry','dorn')]),
 push('dorn','rockfall',dist=2.4,dir=0),
 par(act('sera','cele'),act('kit','laugh')),
 convo([('dorn','It moved! I moved a boulder! Write that down.','joy','sera')]),
],time='night',ambience='cave',music='epic'))
# 12 --------------------------------------------------------------------------------------------------------------- morning talk
S.append(scene('morning','Morning on the moor',loc('meadow',6,objects=[dict(kind='log',at=[0,0],id='logb',w=2.4)]),[at('dorn',-4,-2,face=[0,0]),at('sera',4,-2,face=[0,0])],steps=[
 par(sit('dorn','logb.0',face=[3,-3]),sit('sera','logb.2',face=[-3,-3])),
 convo([('sera','You never ask for anything, Dorn. Why do you come?','serious','dorn'),('dorn','My mother said a fire needs a cook. I said it needs a captain. She said it needs both and a bit of luck.','warm','sera'),
  ('sera','What was your luck?','serious','dorn'),('dorn','I ate it. It was a Thursday.','joy','sera')]),
 emote('sera','smile',3),
 convo([('sera','I am afraid, Dorn. Not of the hills. Of arriving and finding I carried a dead coal for nothing.','sad','dorn'),('dorn','Captain, a coal that survives a storm and a stowaway and my cooking is not dead.','warm','sera')]),
 wait(2),
],time='dawn',ambience='wind',music='calm'))
# 13 --------------------------------------------------------------------------------------------------------------- the confession
S.append(scene('confession','The confession',loc('campfire_night',5),[at('thorne',0,-3.3,face=[0,0]),at('sera',5,3.5,face=[0,0]),at('moss',-5,3,face=[0,0])],steps=[
 sit('thorne','log_s.0',face=[0,0]),
 par(go('sera',[-1.6,1.4],gait='walk'),go('moss',[1.8,1.0],gait='walk')),
 convo([('thorne','I sold the northern oil, Captain. Nine winters ago. A man paid me enough to leave. The beacon starved the week after.','sad','sera'),('sera','You let ships break so you could sleep in a bed.','angry','thorne'),
  ('thorne','I let a light die. Yes. I have been walking back to it ever since.','sad','sera')]),
 par(act('sera','argue'),emote('moss','concern',3)),
 convo([('sera','And you did not say a word.','angry','thorne'),('moss','He said it now, Captain. In the hardest place to say it.','serious','sera'),('thorne','If you want me gone, I go. The map is yours.','sad','sera')]),
 go('thorne',[-6,-6],gait='walk'),
 emote('sera','sad',3),
],time='night',ambience='fire',music='sad'))
# 14 --------------------------------------------------------------------------------------------------------------- the lesson
S.append(scene('lesson','The star lesson',loc('hilltop',5),[at('moss',-3,-2,face=[0,12]),at('wick',-1.5,-3.5,face='moss')],steps=[
 par(look('moss',[0,16],3),look('wick',[0,16],3)),
 convo([('moss','Three stars in a row. The belt. Follow the belt and it points to the cape.','serious','wick'),('wick','Which star?','concern','moss'),('moss','The one that is not a cloud.','serious','wick'),('wick','Moss, they are all not clouds.','concern','moss')]),
 convo([('moss','Fair. I have never been entirely certain about clouds.','warm','wick'),('wick','The belt. Three stars. Up.','joy','moss')]),
 par(look('wick',[0,16],3),emote('wick','smile',3)),
 convo([('moss','Good. Now you are a navigator. Please do not tell anyone how I do it.','warm','wick'),('wick','I will say you taught me everything.','joy','moss'),('moss','Everything is rather too much. Say something.','serious','wick')]),
],time='night',ambience='wind',music='calm'))
# 15 --------------------------------------------------------------------------------------------------------------- tracking
S.append(scene('tracking','On the trail',loc('forest_clearing',7),[at('kit',-9,2,face=[0,0]),at('sera',-11,0,face=[0,0])],steps=[
 par(go('kit',[-3,2],gait='brisk'),go('sera',[-5,-0.4],gait='strut')),
 convo([('kit','Fresh tracks. Boots, one pair, going north. He did not even hide them.','serious','sera'),('sera','He wanted to be followed. Or he wanted to be wrong.','concern','kit')]),
 par(go('kit',[2,4],gait='brisk'),go('sera',[0,2],gait='strut')),
 look('kit',[6,6],2),
 convo([('kit','There. A glove. And the trail drops off the edge.','concern','sera'),('sera','Then we climb down. Quietly. Quickly.','serious','kit')]),
 par(go('kit',[6,5],gait='run'),go('sera',[4,3.5],gait='run')),
],time='day',ambience='wind',music='tense'))
# 16 --------------------------------------------------------------------------------------------------------------- the ledge
S.append(scene('ledge','The ledge',loc('ruins',5),[at('thorne',0,5.5,face=[0,0]),at('kit',-6,-2,face=[0,0]),at('sera',-8,-3,face=[0,0])],steps=[
 act('thorne','fall'),
 par(go('kit',[-1,3.8],gait='run'),go('sera',[-2.5,3.0],gait='run')),
 convo([('kit','He is breathing. His leg is bent wrong.','concern','sera'),('thorne','Go. The map is in the pocket. I am slow and you are not.','sad','sera')]),
 act('sera','kneel'),
 convo([('sera','I have a coal, a cook and a guide. I am not losing the guide.','angry','thorne'),('thorne','I sold the oil, Captain.','sad','sera'),('sera','And you walked nine years back. That is the thing I am keeping.','warm','thorne')]),
 par(act('thorne','getup'),act('kit','cele')),
 convo([('kit','He is up! He is up and a bit crooked!','joy','sera'),('thorne','Crooked and grateful. I will lead from the front.','warm','sera')]),
],time='day',ambience='wind',music='warm'))
# 17 --------------------------------------------------------------------------------------------------------------- Cape Tern
S.append(scene('cape_tern','Cape Tern',loc('courtyard',4),[at('sera',-12,-8,face=[0,0]),at('thorne',-11,-7,face=[0,0]),at('moss',-10,-8.5,face=[0,0]),at('dorn',-9,-8,face=[0,0]),at('kit',-8,-8,face=[0,0]),at('wick',-8,-9,face=[0,0])],steps=[
 par(go('sera',[-3,-3],gait='strut'),go('thorne',[-5,-2],gait='walk'),go('moss',[-1,-5],gait='strut'),go('dorn',[-6,-5],gait='walk'),go('kit',[3,-3],gait='brisk'),go('wick',[-3.2,-6],gait='brisk')),
 par(look('thorne',[0,0],3),look('sera',[0,0],3)),
 convo([('thorne','There she is. The lens is cracked and the stairs are gone. But the iron is sound.','sad','sera'),('sera','Can it burn?','serious','thorne'),('thorne','It has been waiting nine winters. I think it has opinions.','warm','sera')]),
 convo([('wick','I will keep it. I said I would.','warm','thorne'),('dorn','Wick, you will have to be forty feet taller.','concern','wick'),('wick','I will use a ladder.','serious','dorn')]),
],time='dusk',ambience='sea',music='epic'))
# 18 --------------------------------------------------------------------------------------------------------------- the repair
S.append(scene('lens_repair','The night repair',loc('courtyard',5,objects=[dict(kind='pedestal',at=[6,2],id='bench1',height=.8,size=.7)]),[at('thorne',-1,-3,face='statue'),at('dorn',-5,-5,face='statue'),at('kit',5,-6,face=[0,0]),at('wick',-3,2,face=[0,0])],props=[prop('tool1','tool',6.0,2.0,on='bench1')],steps=[
 par(go('thorne',[3.5,0.5],gait='walk'),go('kit',[8,.8],gait='brisk')),
 take('thorne','tool1'),
 convo([('thorne','Hold the frame. Kit, hands steady. Wick, pass the cloth.','serious','kit'),('kit','My hands are made of jelly and enthusiasm.','joy','thorne')]),
 give('thorne','kit'),
 par(go('dorn','statue',stop=2.4,gait='walk'),go('wick',[5.5,0.2],gait='brisk')),
 convo([('dorn','Soup for the brave. Hot, dark and slightly wise.','warm','thorne'),('thorne','It tastes like a hat.','joy','dorn'),('dorn','It is a hat. Thank you for noticing.','joy','thorne')]),
 par(act('kit','cele'),sfx('chime',0.2)),
],time='night',ambience='night',music='warm'))
# 19 --------------------------------------------------------------------------------------------------------------- relight
S.append(scene('relight','The relighting',loc('courtyard',6,objects=[dict(kind='pedestal',at=[-3.4,-4.2],id='stand1',height=.8,size=.7),dict(kind='pedestal',at=[4.5,3.0],id='stand2',height=.8,size=.7)]),[at('sera',-3,-5,face='statue'),at('moss',-6,-3,face='statue'),at('thorne',-4,-7,face='statue'),at('dorn',-8,-5,face='statue'),at('wick',-5,-8,face='statue'),at('kit',-7,-8,face='statue')],props=[EMBER(-3.4,-4.2,on='stand1')],steps=[
 par(take('sera','ember'),look('moss','sera',3)),
 convo([('sera','Nine winters dark. Three days of road. Let us see if the old girl remembers.','serious','thorne')]),
 par(go('sera',[5.8,2.2],gait='strut'),go('thorne',[4.4,3.5],gait='walk'),go('moss',[3,2],gait='strut'),go('wick',[2.5,4],gait='brisk')),
 put('sera',on='stand2'),
 par(sfx('chime',0.2),sfx('bell',0.8),emote('sera','smile',3)),
 convo([('wick','It is warming. It is humming. It is the colour of tea.','joy','sera'),('moss','It is catching on the lens. Look at the walls. Look!','joy','thorne')]),
 par(act('kit','cele'),act('dorn','laugh'),act('wick','cele')),
 convo([('thorne','Every ship on this coast can see that.','warm','sera'),('sera','Every ship on this coast will thank a mouse, a cook and a crooked wolf.','warm','thorne')]),
],time='night',ambience='sea',music='epic'))
# 20 --------------------------------------------------------------------------------------------------------------- sunrise
S.append(scene('sunrise','Sunrise on the cape',loc('hilltop',6),[at('sera',-2,-2,face=[8,12]),at('thorne',-4,-3,face=[8,12]),at('wick',-1,-4,face=[8,12]),at('moss',-6,-2,face=[8,12]),at('dorn',-5,-5,face=[8,12]),at('kit',-3,-5.5,face=[8,12])],steps=[
 par(look('sera',[10,14],4),look('thorne',[10,14],4),emote('wick','smile',3)),
 convo([('sera','Whatever the fog does tonight, there is a light behind it.','warm','thorne'),('thorne','Nine winters. I thought I had walked to nothing.','sad','sera'),('sera','You walked to a keeper. That is something.','warm','thorne')]),
 convo([('wick','Keeper. Hear that? I am the assistant keeper. Of the doorknob.','joy','moss'),('moss','Assistant of the doorknob. It is a very senior post.','warm','wick'),('dorn','I will bring soup every winter. Hat flavoured.','joy','wick')]),
 par(act('dorn','laugh')),
 convo([('sera','Home, then. By the shorter path.','warm','kit'),('kit','Under the cliffs. The painted way. I know the map.','joy','sera')]),
 wait(3),
],time='dawn',ambience='wind',music='warm'))
INTENT={
 'failing_light':'Dusk at the harbour. The lighthouse coal is dying and the winter fog is three days away.',
 'council':'Captain Sera takes the mission: carry the coal over the hills to the dead beacon at Cape Tern.',
 'loading':'Night. The cart is loaded, and a stowaway mouse is found.',
 'departure':'Dawn. The caravan leaves the sea behind.',
 'first_fire':'First camp. The stowaway is welcomed.',
 'stranger':'A guide named Thorne offers to lead them through the Hollow Hills.',
 'market_trouble':'Resupply in a hill market. Wick steals an apple and they chase him.',
 'fog_line':'From a hilltop they see the fog coming. Thorne once kept the Cape Tern beacon.',
 'storm_ruins':'A storm. Sera shields the failing coal in the ruins.',
 'murals':'Kit and Wick find a painted cave and a map of a shorter path.',
 'collapse':'The cave ceiling falls. A boulder blocks the way out.',
 'morning':'Morning. Sera confesses her fear to Dorn.',
 'confession':'Thorne confesses: he sold the beacon oil and let it die.',
 'lesson':'Moss teaches Wick to find the way by the stars.',
 'tracking':'Thorne has gone. Kit and Sera follow his tracks.',
 'ledge':'They find Thorne hurt in the ruins and take him back.',
 'cape_tern':'The party reaches Cape Tern: a dark tower with a cracked lens.',
 'lens_repair':'Night. Thorne repairs the lens with everyone helping.',
 'relight':'The coal is set in the beacon, and it catches.',
 'sunrise':'Sunrise. The light shines, and Thorne has found his way back.',
}
for _s in S:_s['intent']=INTENT[_s['id']]
OBJECTIVE={}
for _id in ('failing_light','council'):OBJECTIVE[_id]='Goal: save the lighthouse coal'
for _id in ('loading','departure','first_fire','stranger','market_trouble'):OBJECTIVE[_id]='Day 1 of 3: carry the coal to Cape Tern'
for _id in ('fog_line','storm_ruins','murals','collapse'):OBJECTIVE[_id]='Day 2 of 3: carry the coal to Cape Tern'
for _id in ('morning','confession','lesson','tracking','ledge'):OBJECTIVE[_id]='Day 3 of 3: carry the coal to Cape Tern'
for _id in ('cape_tern','lens_repair','relight'):OBJECTIVE[_id]='Goal: relight the beacon'
OBJECTIVE['sunrise']='The beacon burns'
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A caravan carries the last coal of a failing lighthouse over the hills to relight a dead beacon before the winter fog.'
THEME=dict(root=52,mode='dorian',tempo=92,motif=[(0,1),(4,1),(3,.5),(2,.5),(0,1)],motifs=dict(sera=[0,4,7],moss=[2,1,0],kit=[4,6,4,7],dorn=[0,0,-1],thorne=[0,3,2,0],wick=[7,6,7],brant=[0,-1,0]),palette=dict(pad=48,bass=43,pluck=46,hit=47))
for _c in CAST:_c.setdefault('pace',1.25)   # film pacing: a brisker cadence on every gait (strides and planted feet unchanged)
FILM=dict(id='ember_road',title='The Ember Road',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=15)
