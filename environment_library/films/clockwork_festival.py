"""Film 1: 'Twelve Strikes' - the key to the great town clock vanishes the night before the harvest festival (about 15 minutes, 20 scenes, 7 characters, 8 locations).

A village comedy-drama written for the performance engine (perf_dsl): a bear clockmaker, a fox courier, a mouse apprentice, an ox guard captain, an owl mayor, a cat baker and a wolf who is not the thief he seems.
Everything is data: python perf_movie.py films/clockwork_festival.py out/clockwork --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='bram',name='Bram',species='bear',posture='tired',accessories=['glasses','apron','cane'],description='the old clockmaker, gentle and stubborn'),
 dict(id='mara',name='Mara',species='fox',posture='jaunty',accessories=['hat_cap','satchel'],voice_pitch=205,description='a quick courier who talks faster than she runs'),
 dict(id='pip',name='Pip',species='mouse',posture='hurried',accessories=['scarf'],description="Bram's apprentice, small and brave"),
 dict(id='odo',name='Captain Odo',species='ox',posture='proud',accessories=['helmet','medals','sword'],description='captain of the town guard, loud and fair'),
 dict(id='wren',name='Mayor Wren',species='owl',posture='hunched',accessories=['hat_top','bowtie'],description='the mayor, who dislikes surprises'),
 dict(id='tilda',name='Tilda',species='cat',posture='angry',accessories=['apron','scarf'],tint=[.95,.7,.45],description='the baker with opinions about everything'),
 dict(id='rook',name='Rook',species='wolf',posture='tense',accessories=['cape','eyepatch'],description='a quiet stranger who knows the clock better than the town'),
]
TOWER=dict(kind='tower',at=[0,17],id='clocktower',size=1.4)
def square(seed=2):return loc('village_square',seed,objects=[TOWER],markers=dict(clock=[0,12.5]))
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the silent clock
S.append(scene('silent_clock','The silent clock',square(),[at('bram',0,11.5,face=[0,17]),at('wren',6,5,face=[0,11]),at('pip',-3,10,face=[0,17])],[
 par(look('bram',[0,17],3),emote('bram','sad',3),look('pip','bram',2)),
 par(go('wren','bram',stop=1.7,gait='walk'),turn('pip','wren')),
 convo([('wren','Bram, the festival begins at noon. Why is my clock silent?','concern','bram'),('bram','Because it cannot be wound, Mayor. The great key is gone.','sad','wren'),('wren','Gone? Keys do not simply walk away!','angry','bram'),
  ('pip','He locked it in the glass case last night. I watched him do it.','concern','wren'),('bram','And this morning the case is open and the key is not in it.','sad','wren')]),
 act('wren','shrug'),sfx('bell',0.2),
 convo([('wren','Then we have until noon to find it, or twelve strikes become twelve rumours.','serious','bram')]),
 par(go('wren',[6,5],gait='walk'),act('bram','think',dur=3)),
 convo([('pip','I will search every corner of the workshop. Every drawer, every cog, every crumb.','joy','bram')]),
 par(go('pip',[-8,5],gait='run'),look('bram','pip',3)),
],time='dawn',ambience='wind',music='mystery'))
# 2 ---------------------------------------------------------------------------------------------------------------- the captain accuses
S.append(scene('accusation','The captain accuses',square(3),[at('odo',-8,-3,face=[0,0]),at('bram',2,3,face=[-8,-3]),at('tilda',-6,6,face=[0,0]),at('pip',4,5,face=[0,0])],steps=[
 go('odo','bram',stop=2.4,gait='stomp'),
 convo([('odo','Clockmaker! A key does not vanish from a locked room. Who else holds a copy?','angry','bram'),('bram','No one, Captain. I made one key and I kept it close.','serious','odo'),
  ('odo','Then close is not close enough. I will have my guards search your workshop.','angry','bram'),('pip','You cannot! He has been fixing that clock for forty years!','angry','odo')]),
 par(go('tilda','odo',stop=2.0,gait='stomp'),look('bram','odo',2)),
 convo([('tilda','Forty years and never once on time. Odo, leave the old bear be, my bread is rising.','angry','odo'),('tilda','Rising bread is my concern when the festival has no clock to start it and no bread to end it.','angry','odo')]),
 act('odo','shrug'),
 convo([('odo','Very well. Until sunset. Then I search, and I do not ask twice.','serious','bram'),('bram','You will not need to. My door is open to anyone who can find a key in a clock.','sad','odo')]),
 par(go('odo',[-7,-5],gait='stomp'),emote('bram','sad',3)),
 convo([('pip','We need a detective. Not a captain.','concern','bram')]),
 act('tilda','wave'),
],time='day',ambience='market',music='tense'))
# 3 ---------------------------------------------------------------------------------------------------------------- the empty case
S.append(scene('empty_case','The empty case',loc('workshop',2),[at('bram',-1.5,-1.0,face='table'),at('pip',2.8,1.8,face='table')],props=[prop('scrap','letter',1.6,0.2,on='table')],steps=[
 par(go('pip',[1.0,-1.3],gait='brisk'),look('bram','table',2)),
 convo([('pip','Here! The latch was lifted, not broken. Whoever came knew the case.','concern','bram'),('bram','A thief who knew the case. That narrows it to everyone I ever taught.','sad','pip')]),
 take('pip','scrap'),
 convo([('pip','And this was caught on the hinge. Half a letter, torn.','serious','bram')]),
 give('pip','bram'),
 par(act('bram','think',dur=3),look('pip','bram',3)),
 convo([('bram','A careful hand. Round letters, like a clerk or a courier.','serious','pip'),('pip','Courier. Mara carries every letter in town.','concern','bram'),('bram','Then we ask her before she leaves for the hills.','serious','pip')]),
 put('bram',on='table'),
 par(act('pip','wave'),sfx('door',1.0)),
 convo([('pip','I will run. You will see. Faster than a clock.','joy','bram'),('bram','Faster than this clock, yes. That is not a high bar.','warm','pip')]),
 go('pip',[1.5,-3.5],gait='run'),
],time='day',ambience='fire',music='mystery'))
# 4 ---------------------------------------------------------------------------------------------------------------- the courier
S.append(scene('courier','The courier',square(4),[at('mara',-12,-3,face=[0,0]),at('pip',6,6,face=[-3,-3]),at('tilda',-9,6,face=[0,0])],steps=[
 run('mara','well',stop=2.5),
 act('mara','fall'),act('mara','getup'),
 par(go('pip','mara',stop=1.4,gait='run'),look('mara','pip',2)),
 convo([('mara','Do not look at me. The cobbles moved.','joy','pip'),('pip','Mara, someone stole the clock key. We found half a letter and we think it is yours.','concern','mara'),
  ('mara','Mine? I have delivered nine hundred letters this year and written four.','serious','pip')]),
 act('mara','think'),
 convo([('mara','Round, careful... that is Rook. He writes like a man ironing shirts. He buys lamp oil from Tilda every night.','serious','pip')]),
 par(go('mara','tilda',stop=2.0,gait='brisk'),go('pip','tilda',stop=2.0,gait='brisk')),
 convo([('mara','Tilda, did a wolf buy oil from you last night?','concern','tilda'),('tilda','Three bottles and a candle. Said he wanted to read.','angry','mara'),('tilda','At midnight. Who reads at midnight?','angry','pip'),
  ('mara','Someone who does not want to be seen.','serious','tilda')]),
 say('pip','Then we follow the oil.','joy','mara'),
],time='day',ambience='market',music='bright'))
# 5 ---------------------------------------------------------------------------------------------------------------- the market
S.append(scene('market_trail','The oil trail',loc('market',3),[at('mara',-7,-6,face=[0,3]),at('pip',-5.5,-6.5,face=[0,3]),at('tilda',-3,2,face=[0,-2])],steps=[
 par(go('mara','tilda',stop=2.2,gait='brisk'),go('pip','tilda',stop=2.2,gait='brisk')),
 convo([('tilda','Looking for oil? Fresh barrel, cheap, and no one asks questions.','warm','mara'),('mara','Where did the wolf go with his three bottles?','concern','tilda'),
  ('tilda','Out through the north road, toward the old orchard.','serious','mara'),('pip','Then so do we.','serious','tilda')]),
 par(go('mara',[5,-4],gait='brisk'),go('pip',[7.5,-5.5],gait='brisk'),act('tilda','wave')),
 convo([('tilda','Bring me the key and I will bake you a cake the size of the bell!','joy','mara'),('mara','Is she serious?','concern','pip'),('pip','She is always serious. That is why the cakes are good.','warm','mara')]),
 par(go('mara',[6,-10.5],gait='run'),go('pip',[10,-8],gait='run')),
],time='day',ambience='market',music='bright'))
# 6 ---------------------------------------------------------------------------------------------------------------- the council
S.append(scene('council','The council',loc('hall',2),[at('wren',0,6.2,face=[0,-4]),at('odo',-2.5,-6.5,face=[0,5]),at('bram',2.5,-6.8,face=[0,5])],steps=[
 par(go('odo',[-2,-2.6],gait='stomp'),go('bram',[2,-2.6],gait='walk')),
 sit('wren','throne.0',face=[0,-4]),
 convo([('wren','Captain, Bram, you both look as if the roof has fallen on you.','serious','odo'),('odo','Mayor, the clock key is stolen and I want to search his workshop. He refuses.','angry','wren'),
  ('bram','I welcome a search. I only ask that the captain does not touch the pendulum.','serious','wren'),('odo','I have never touched a pendulum in my life.','angry','bram')]),
 emote('wren','concern',2),
 convo([('wren','Then neither of you will begin a quarrel before noon. Odo, watch the north gate. Bram, find your key.','serious','odo'),('odo','And if he does not?','concern','wren'),
  ('wren','Then we ring the festival with a handbell and I will apologise to the whole town myself.','sad','odo')]),
 par(go('odo',[-2.5,-6.5],gait='stomp'),go('bram',[2.5,-6.8],gait='walk')),
 emote('wren','sad',3),
],time='day',ambience='hall',music='tense'))
# 7 ---------------------------------------------------------------------------------------------------------------- the orchard
S.append(scene('orchard','The old orchard',loc('forest_clearing',5,objects=[dict(kind='tree',at=[-4,3],id='apple1'),dict(kind='tree',at=[4,-3],id='apple2'),dict(kind='log',at=[0,-5],id='trunk')]),[at('mara',-5,-1,face=[0,0]),at('pip',-6,-2,face=[0,0])],steps=[
 par(go('mara',[-3,0],gait='walk'),go('pip',[-4,-1.5],gait='walk')),
 convo([('pip','Mara? I am scared of orchards.','concern','mara'),('mara','Nobody is scared of orchards. It is only trees standing in rows.','serious','pip'),
  ('pip','Rows watching us.','concern','mara')]),
 sfx('knock',0.5),
 par(act('mara','startle'),act('pip','startle')),
 convo([('mara','That was a branch.','concern','pip'),('pip','Branches do not knock twice.','concern','mara')]),
 par(go('mara',[0.5,2],gait='walk'),go('pip',[-.5,.4],gait='walk')),
 look('mara',[6,6],2),
 convo([('mara','There. Smoke behind the tool shed. He is camping.','serious','pip'),('pip','Whatever he is, he is not hiding very well.','concern','mara')]),
 par(go('mara',[3,4],gait='walk'),go('pip',[2,2.6],gait='walk')),
],time='dusk',ambience='night',music='mystery'))
# 8 ---------------------------------------------------------------------------------------------------------------- rook's camp
S.append(scene('rook_camp',"Rook's camp",loc('campfire_night',2),[at('rook',0,-3.3,face=[0,0]),at('mara',-6,5,face=[0,0]),at('pip',-7,6,face=[0,0])],steps=[
 sit('rook','log_s.0',face=[0,0]),
 par(look('rook',[0,0],2),emote('rook','concern',3)),
 convo([('rook','Thirty teeth on the escape wheel. Two cracked. One more winding and it shatters.','sad','rook')]),
 act('rook','think') if False else emote('rook','sad',2),
 convo([('rook','And nobody listens to a wolf who says the tower will fall.','sad','rook')]),
 par(go('mara',[-4,3],gait='walk'),go('pip',[-5,4],gait='walk'),look('rook',[-5,5],2)),
 convo([('rook','Someone is there. I can hear two sets of paws, and one of them is arguing with a root.','concern','rook'),('pip','It is not arguing! It tripped!','concern','rook')]),
 par(go('mara',[-3.2,1.6],gait='walk'),go('pip',[-4,2.6],gait='walk'),emote('rook','smile',2)),
 convo([('rook','Come to the fire. I will not bite. I have not had the energy since breakfast.','warm','mara'),('mara','You are Rook. You stole the key.','angry','rook'),('rook','I borrowed it. For the tower.','serious','mara')]),
],time='night',ambience='fire',music='sad'))
# 9 ---------------------------------------------------------------------------------------------------------------- chase
S.append(scene('chase','The chase',loc('meadow',4),[at('rook',-2,0,face=[8,0]),at('mara',-10,-1,face=[0,0]),at('pip',-11,2,face=[0,0])],steps=[
 par(go('mara','rook',stop=2.4,gait='brisk'),go('pip','rook',stop=2.4,gait='brisk')),
 convo([('mara','Rook! The key! Give it back!','angry','rook'),('rook','I have it and I am keeping it. Not for me, for the tower!','angry','mara')]),
 par(run('rook',[16,8]),turn('mara',[16,8])),
 par(run('mara',[14,6]),run('pip',[12,9])),
 act('rook','jump'),
 par(act('rook','fall'),act('mara','startle')),
 par(act('rook','getup'),go('pip',[13,7],gait='brisk'),go('mara',[11.5,4.5],gait='brisk')),
 convo([('rook','Enough. I am too old to run and too tired to win. Listen to me, please.','sad','mara'),('mara','You have thirty seconds and one cake.','serious','rook')]),
],time='day',ambience='wind',music='epic'))
# 10 --------------------------------------------------------------------------------------------------------------- the confession
S.append(scene('confession','The confession',loc('meadow',5,objects=[dict(kind='log',at=[0,0],id='seat1',w=2.4)]),[at('rook',-2,-1.5,face=[0,0]),at('mara',2.5,-1.5,face=[0,0]),at('pip',0,-4,face=[0,0])],steps=[
 sit('rook','seat1.0',face='pip'),
 par(sit('mara','seat1.1',face='pip'),look('pip','rook',2)),
 convo([('rook','I was Bram’s first apprentice. Then I left, and I thought I had forgotten everything.','sad','pip'),('rook','But last month I came back to hear the clock, and heard a gear grinding like a sick horse.','sad','pip'),
  ('pip','So you took the key so nobody could wind it.','concern','rook'),('rook','Yes. I tried telling the Captain. He said he did not listen to men who wore eyepatches.','angry','pip')]),
 emote('mara','smile',2),
 convo([('mara','He told me the same thing last week, and I do not even wear one.','joy','pip'),('rook','I will show Bram the crack. If he says I am wrong, I will return the key and leave.','serious','pip'),
  ('mara','Deal. And you walk in front, so we can see your tail.','warm','pip')]),
 par(stand('rook'),stand('mara')),
 convo([('pip','I knew it. A bad wolf would never read in an orchard.','joy','rook')]),
],time='dusk',ambience='wind',music='sad'))
# 11 --------------------------------------------------------------------------------------------------------------- the crack
S.append(scene('the_crack','The crack',loc('workshop',3),[at('bram',-1.2,-1.2,face='table'),at('rook',-0.4,-3.0,face=[0,0]),at('mara',3,-1.6,face=[0,0]),at('pip',3.3,-2.5,face=[0,0])],props=[prop('key','key',1.2,0.15,on='table')],steps=[
 par(go('rook',[0.8,-1.9],gait='walk'),turn('bram','rook')),
 convo([('bram','Rook. I thought you were a story the apprentices told each other.','sad','rook'),('rook','I am a story that came back to say sorry. And to say the gear is cracked.','serious','bram')]),
 take('rook','key'),
 give('rook','bram'),
 go('rook',[2.6,-2.8],gait='walk'),
 par(act('bram','think',dur=3),emote('bram','concern',3)),
 convo([('bram','Thirty years I oiled that gear. I would have felt it.','sad','rook'),('rook','You oiled it. You never turned it by hand with a lantern behind it.','serious','bram')]),
 put('bram',on='table'),
 par(go('mara','bram',stop=1.9,gait='walk'),go('pip','bram',stop=1.9,gait='brisk')),
 convo([('pip','Then we need to see it. Tonight.','concern','bram'),('bram','Tonight, and tomorrow before noon, we repair it or stop the festival. Both are hard.','sad','pip')]),
 act('bram','nod'),
],time='dusk',ambience='fire',music='warm'))
# 12 --------------------------------------------------------------------------------------------------------------- the announcement
S.append(scene('announcement','The announcement',square(6),[at('wren',3,-4,face=[0,0]),at('odo',-6,-3,face=[0,0]),at('bram',-2,1,face=[3,-4]),at('rook',1,2,face=[3,-4]),at('tilda',-8,4,face=[0,0])],steps=[
 par(go('bram',[1.0,-1.6],gait='walk'),go('rook',[5.3,-2.0],gait='walk'),go('odo',[-1.6,-5.0],gait='stomp')),
 convo([('odo','That wolf is the thief! Seize him!','angry','rook')]),
 par(act('rook','startle'),act('bram','block')),
 convo([('bram','Captain, he is not the thief. He is the one person who listened to the clock.','angry','odo'),('rook','The gear is cracked, sir. Come and look.','serious','odo')]),
 par(go('tilda','odo',stop=2.2,gait='stomp'),look('wren','rook',2)),
 convo([('tilda','Odo, you said you do not ask twice. Ask once. Ask him politely.','angry','odo'),('odo','Politely... Show me the crack, wolf.','serious','rook')]),
 act('odo','nod'),
 convo([('wren','Then the festival waits a day. Tilda, tell the town the clock needs rest.','serious','tilda'),('tilda','A clock that needs rest. I have been saying that about myself for years.','warm','wren')]),
 emote('wren','smile',2),
],time='dusk',ambience='crowd',music='calm'))
# 13 --------------------------------------------------------------------------------------------------------------- repair at night
S.append(scene('repair','The night repair',loc('workshop',4),[at('bram',-1.5,-1.0,face='table'),at('rook',3.0,-1.8,face='table'),at('pip',-3.5,-2.2,face=[0,0])],props=[prop('wrench','tool',1.0,-.2,on='table'),prop('crate_gear','crate',3.6,-2.9,z=.35),prop('lamp2','lantern',2.2,.3,on='table')],steps=[
 par(go('pip',[2.7,-2.9],gait='brisk'),look('bram','table',2)),
 convo([('bram','Rook, the lantern. And Pip, the new escape wheel from the crate.','serious','rook')]),
 par(take('rook','lamp2'),act('pip','nod')),
 push('pip','crate_gear',dist=1.4,dir=180),
 convo([('pip','It is heavy. Gears are heavier than gossip.','joy','bram'),('bram','Nothing is heavier than gossip, Pip. Gears at least stay where you put them.','warm','pip')]),
 take('bram','wrench'),
 par(act('bram','hips'),sfx('clang',0.5)),
 convo([('rook','Hold the wheel steady. I will turn the arbor.','serious','bram'),('bram','Your hands remember it better than mine do.','warm','rook')]),
 put('bram',on='table'),
 par(act('pip','cele'),sfx('chime',0.2)),
],time='night',ambience='fire',music='warm'))
# 14 --------------------------------------------------------------------------------------------------------------- bread at midnight
S.append(scene('bread','Bread at midnight',loc('courtyard',3),[at('odo',-4,-2,face=[0,0]),at('tilda',-9,4,face=[0,0])],steps=[
 sit('odo','bench_a.0',face=[0,0]),
 par(go('tilda','odo',stop=2.2,gait='stomp'),look('odo','tilda',2)),
 convo([('tilda','You sit like a sack of apples. Eat.','angry','odo'),('odo','I am on watch.','serious','tilda'),('tilda','A guard who faints is not on watch. Eat.','angry','odo')]),
 emote('odo','smile',2),
 convo([('odo','I was wrong about the wolf. I was loud before I was right.','sad','tilda'),('tilda','You are always loud first. It is a gift, mostly.','warm','odo')]),
 sit('tilda','bench_a.1',face='odo'),
 convo([('odo','If that tower falls on the festival, I will not forgive myself.','sad','tilda'),('tilda','Then we make sure it does not. You hold the ladder, I hold the bread.','warm','odo'),('odo','That is the best plan anyone has had today.','warm','tilda')]),
 emote('tilda','smile',3),
],time='night',ambience='night',music='warm'))
# 15 --------------------------------------------------------------------------------------------------------------- dawn
S.append(scene('dawn_square','The morning crowd',square(7),[at('wren',-2,-3,face=[0,6]),at('mara',6,-6,face=[0,0]),at('tilda',-8,3,face=[0,0]),at('odo',3,-2,face=[0,8])],steps=[
 par(go('mara','wren',stop=1.8,gait='run'),act('tilda','wave')),
 convo([('mara','Mayor! They are still inside the tower. Bram says the wheel is in and the key is cut.','joy','wren'),('wren','Then I must write a speech. I have had one for twelve years but it begins with an apology.','concern','mara')]),
 par(go('tilda','wren',stop=2.2,gait='stomp')),
 convo([('tilda','Do not apologise. Say what happened. A cracked gear and a clever wolf and an old bear who is not too proud.','warm','wren'),('wren','Too long for a speech.','serious','tilda'),('tilda','Then keep it short and shout the last bit.','warm','wren')]),
 act('wren','think'),
 par(go('odo','wren',stop=2.2,gait='stomp')),
 convo([('odo','Mayor, the guard stands ready. Nobody climbs the tower but the repair crew.','serious','wren')]),
 act('wren','nod'),
 convo([('wren','Then we begin at noon. Mara, run and tell them the clock is back and so are we.','warm','mara')]),
 go('mara',[14,-2],gait='run'),
],time='dawn',ambience='market',music='bright'))
# 16 --------------------------------------------------------------------------------------------------------------- twelve strikes
S.append(scene('twelve_strikes','Twelve strikes',square(8),[at('wren',0,-4,face=[0,12]),at('bram',-3,7,face=[0,17]),at('rook',3,7,face=[0,17]),at('pip',0,6,face=[0,17]),at('mara',-6,-1,face=[0,17]),at('tilda',-9,3,face=[0,17]),at('odo',7,-1,face=[0,17])],steps=[
 par(act('wren','talk',dur=3),look('bram',[0,17],4)),
 convo([('wren','Friends! The clock needed rest, and tonight it has had it. Now we ask it to speak.','warm','bram'),('bram','Gently, Rook. Wind her gently.','serious','rook')]),
 par(act('bram','nod'),act('rook','nod'),sfx('bell',0.5)),
 par(sfx('bell',0.5),sfx('bell',2.5),sfx('bell',4.5),act('pip','cele'),act('mara','cele'),act('tilda','laugh')),
 par(sfx('bell',0.5),sfx('bell',2.5),sfx('bell',4.5),act('odo','cele'),act('wren','laugh')),
 par(sfx('bell',0.5),sfx('bell',2.5),sfx('gong',4.5),act('bram','laugh'),act('rook','laugh'),act('pip','wave')),
 convo([('pip','Twelve! It counted twelve!','joy','mara'),('mara','And not a minute late!','joy','pip'),('tilda','Cake in the square! Come while it is warm!','joy','odo')]),
 par(act('odo','cele'),act('mara','wave')),
],time='day',ambience='crowd',music='bright'))
# 17 --------------------------------------------------------------------------------------------------------------- an apology
S.append(scene('apology','An apology',square(9),[at('odo',-4,-2,face=[0,0]),at('rook',4,-3,face=[0,0])],steps=[
 par(go('odo','rook',stop=1.9,gait='walk'),look('rook','odo',2)),
 convo([('odo','Rook. I called you a thief in front of the whole town.','serious','rook'),('rook','You called me many things. Most of them were fair.','warm','odo'),
  ('odo','The eyepatch was not one of them. I owe you an apology and a job.','warm','rook')]),
 act('rook','startle'),
 convo([('rook','A job?','concern','odo'),('odo','Keeper of the clock tower. Someone who listens to gears. The pay is bad, the stairs are steep.','warm','rook'),('rook','I accept. I like steep stairs. They keep my tail in shape.','joy','odo')]),
 par(act('odo','laugh'),act('rook','laugh')),
 convo([('odo','Come, the baker is handing out cake the size of a bell.','warm','rook'),('rook','Then lead on, Captain. I will walk behind you, so I can see your helmet.','warm','odo')]),
],time='day',ambience='market',music='warm'))
# 18 --------------------------------------------------------------------------------------------------------------- farewell
S.append(scene('farewell','The farewell',loc('hilltop',3),[at('mara',-1,-1,face=[8,6]),at('pip',-2.5,-1.5,face='mara')],steps=[
 par(look('mara',[10,12],3),act('pip','wave')),
 convo([('pip','You are leaving again.','sad','mara'),('mara','The hills do not deliver themselves. But I will be back for the next festival.','warm','pip'),('pip','Bram wants you to take this.','warm','mara')]),
 act('pip','pick'),
 convo([('mara','A brass key. Not the clock’s.','joy','pip'),('pip','The workshop door. He says couriers need somewhere to be late to.','joy','mara')]),
 act('mara','laugh'),
 convo([('mara','Tell him I will be late to everything. Especially the cake.','joy','pip'),('pip','Be careful on the road. And do not fall in the orchard.','warm','mara')]),
 par(go('mara',[8,10],gait='run'),act('pip','wave')),
 convo([('pip','Run! Be late to everything!','joy','mara')]),
],time='day',ambience='wind',music='warm'))
# 19 --------------------------------------------------------------------------------------------------------------- tea
S.append(scene('tea','Tea in the workshop',loc('workshop',5),[at('bram',-1.5,-2.5,face='table'),at('rook',3.5,-2.0,face='table')],props=[prop('cup1','cup',0.9,0.2,on='table'),prop('cup2','cup',1.6,-0.1,on='table')],steps=[
 par(take('bram','cup1'),take('rook','cup2')),
 par(sit('rook','stool_b.0',face=[0.8,0]),sit('bram','stool_a.0',face=[1,0.5])),
 convo([('bram','Forty years, and the wolf who fixed it did it in one night.','warm','rook'),('rook','You oiled it for forty. I only listened for one.','warm','bram'),
  ('bram','Teach me to listen.','serious','rook'),('rook','Teach me to be patient.','serious','bram')]),
 par(emote('bram','smile',3),emote('rook','smile',3)),
 convo([('bram','To the clock.','warm','rook'),('rook','To the clock.','warm','bram')]),
 sfx('chime',0.5),
 wait(3),
],time='dusk',ambience='fire',music='warm'))
# 20 --------------------------------------------------------------------------------------------------------------- evening
S.append(scene('evening','The evening strike',square(10),[at('wren',-3,-4,face=[0,12]),at('tilda',3,-4,face=[0,12]),at('odo',0,-6,face=[0,12]),at('pip',1,2,face=[0,12]),at('mara',-6,-1,face=[0,12]),at('bram',-1,5,face=[0,12]),at('rook',1.5,5,face=[0,12])],steps=[
 par(look('wren',[0,17],3),emote('tilda','smile',3)),
 convo([('tilda','Cake for everyone! The tall bell-shaped kind!','joy','odo')]),
 par(act('odo','laugh'),act('pip','cele'),act('mara','wave')),
 par(sfx('bell',0.3),sfx('bell',2.3),sfx('bell',4.3),look('bram',[0,17],4),look('rook',[0,17],4),act('wren','nod')),
 convo([('bram','Six strikes. Right on the hour.','warm','rook'),('rook','Right on the hour.','warm','bram')]),
 par(go('pip','bram',stop=1.2,gait='brisk'),go('mara','pip',stop=1.4)),
 convo([('pip','Can we do it again tomorrow?','joy','bram'),('bram','Every day, Pip. That is the whole secret of a clock.','warm','pip')]),
 wait(3),
],time='dusk',ambience='crowd',music='calm'))
FILM=dict(id='clockwork_festival',title='Twelve Strikes',cast=CAST,scenes=S,target_minutes=15)
