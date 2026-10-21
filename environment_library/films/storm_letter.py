"""Film 6: 'The Storm Letter' - a race against sunset (about 6 minutes, 9 scenes, 6 characters, 4 locations).
A scholar reads a storm in her barometer and sends the young courier Pepper to warn the ferry captain before sunset. Everything is built on one clock (the sky darkens and the fog thickens scene by scene), a rule that gets broken for a good reason (Pepper "never stops" - and stops to help old Mo), a midpoint reversal (the letter is snatched by the stylish Vesper), a twist (Vesper was racing to warn the ferry too), a payoff (Mo's gratitude pays the toll) and a last-second finish.
Setups: Pepper's promise, the toll keeper's apple, the broken bridge, the ferry's three bells. Payoffs: she stops for Mo, Mo pays the toll, the two rivals carry the letter together, the storm breaks right after the ferry stays.
python perf_movie.py films/storm_letter.py out/storm --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='pepper',name='Pepper',species='fox',posture='hurried',outfit='child',colors=[(.2,.5,.7),(.95,.75,.2),(.35,.5,.35),(.4,.28,.2)],description='a small, fast courier who never stops'),
 dict(id='vesper',name='Vesper',species='rabbit',posture='proud',outfit='gentleman',colors=[(.22,.12,.3),(.8,.15,.3),(.15,.1,.1)],description='a stylish rival in a purple suit'),
 dict(id='odile',name='Odile',species='owl',posture='neutral',outfit='scholar',colors=[(.3,.4,.5),(.9,.85,.6)],description='the tall weather scholar'),
 dict(id='tobias',name='Captain Tobias',species='wolf',posture='tired',outfit='fisherman',colors=[(.2,.3,.55),(.95,.75,.15),(.22,.27,.36)],description='the ferry captain in a yellow coat'),
 dict(id='grub',name='Grub',species='ox',posture='angry',outfit='innkeeper',colors=[(.75,.7,.6),(.5,.25,.15),(.85,.8,.7),(.3,.25,.2)],description='the toll keeper who counts apples'),
 dict(id='mo',name='Old Mo',species='elder',posture='hunched',outfit='shepherd',colors=[(.55,.45,.3),(.65,.25,.2),(.35,.28,.2),(.25,.18,.1)],description='an old farmer with a stuck cart'),
]
LETTER=lambda x,y,on=None:prop('letter','letter',x,y,on=on,size=1.6)
LOW=lambda i,x,y,h=.7:dict(kind='pedestal',at=[x,y],id='stand%d'%i,height=h,size=.4)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the warning
S.append(scene('warning','Storm by sunset',loc('room',3),[at('odile',-2.6,-2.6,face='table'),at('pepper',3.4,-3.0,face='odile')],props=[LETTER(1.0,-.45,'table')],steps=[
 go('odile',[0.6,-1.4],gait='walk'),
 act('odile','think'),
 sfx('sting',0.4),
 take('odile','letter'),
 run('pepper',[2.0,-2.2]),
 convo([('odile','My barometer is falling like a stone. A great storm by sunset.','serious','pepper'),('odile','The ferry sails at sunset. Captain Tobias must read this letter. Do not stop for anything.','serious','pepper'),('pepper','I never stop!','joy','odile')]),
 give('odile','pepper'),
 par(act('pepper','cele'),sfx('thunder',0.3)),
 run('pepper',[0.2,-3.3]),
],time='day',ambience='wind',music='mystery',fog=.1,intent='Odile gives Pepper a storm warning for the ferry captain. The ferry sails at sunset.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the square
S.append(scene('square','Vesper notices',loc('village_square',5),[at('pepper',-9,-1.5,face=[14,-2]),at('vesper',2,-1.5,face=[-6,-3]),at('mo',13,6,face=[4,6])],props=[prop('cart','cart_load',9,6,z=None)],steps=[
 run('pepper',[-2,-2.8]),
 par(turn('vesper','pepper'),emote('vesper','brows',2)),
 convo([('vesper','Where is the little courier going in such a hurry?','warm','pepper'),('pepper','Secret ferry business!','joy','vesper'),('vesper','Ferry business is my business.','serious','pepper')]),
 par(act('pepper','dodge'),sfx('whoosh',0.1)),
 run('pepper',[16,-4]),
 par(look('vesper',[16,-4],2),emote('vesper','smile',2.5)),
],time='day',ambience='wind',music='bright',fog=.15,intent='Vesper spots the letter and seems curious. Pepper dodges her and runs on.'))
# 3 ---------------------------------------------------------------------------------------------------------------- Old Mo's cart
S.append(scene('cart','Never stop... except',loc('market',6,objects=[LOW(0,-9.6,-3.2),LOW(1,-1.6,-2.2,.7)]),[at('pepper',-9.6,-4.4,face=[-9.6,-3.2]),at('mo',-2.4,-4.4,face=[-1,-4.4]),at('vesper',3.5,-7.6,face=[-2,-4])],props=[prop('cart','cart_load',-1.0,-4.6),LETTER(-9.6,-3.2,'stand0')],steps=[
 take('pepper','letter'),
 run('pepper',[-5.8,-3.8]),
 par(act('mo','argue'),sfx('creak',0.2)),
 convo([('mo','Stuck! Stuck again! These old wheels hate me!','sad','pepper')]),
 par(look('pepper',[20,-4],1.5),emote('pepper','concern',2.5)),
 convo([('pepper','I never stop. I never stop. ...Oh, bother.','concern','mo')]),
 par(go('pepper',[-2.6,-2.2],gait='brisk')),
 put('pepper',on='stand1'),
 push('pepper','cart',dist=3.0,dir=0),
 par(sfx('thud',0.2),act('mo','cele')),
 convo([('mo','Bless you, child! Now run!','joy','pepper')]),
 par(go('vesper',[-1.6,-3.0],gait='brisk')),
 take('vesper','letter'),
 sfx('sting',0.1),
 par(act('pepper','startle'),run('vesper',[16,-4.4])),
 convo([('pepper','Vesper! My letter!','angry','vesper')]),
],time='dusk',ambience='market',music='tense',fog=.28,extras=crowd(3,[-12,-4,12,10],[0,-4],41),intent='Pepper breaks her promise to help Old Mo. While her back is turned, Vesper takes the letter and runs.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the chase
S.append(scene('chase','The chase',loc('market',6),[at('vesper',-17,-6,face=[16,-6]),at('pepper',-20,-5,face=[16,-6]),at('grub',-1,-1.5,face=[-1,-6])],steps=[
 par(sfx('whoosh',0.1),run('vesper',[2,-6.2]),run('pepper',[-4,-6.0])),
 par(act('grub','startle'),emote('grub','concern',2)),
 convo([('grub','No running in my market!','angry','pepper')]),
 par(sfx('whoosh',0.1),run('vesper',[17,-6.0]),run('pepper',[8,-5.8]),act('grub','dodge')),
 sfx('crash',0.2),
],time='dusk',ambience='market',music='epic',fog=.3,intent='Pepper races after Vesper through the market and past an angry toll keeper.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the broken bridge
S.append(scene('bridge','The broken bridge',loc('harbor',5,water=[-5,-9,5,3],objects=[dict(kind='platform',at=[-12,-3.5],w=14,d=5,height=.05,id='bank_w',color=(.55,.5,.45)),dict(kind='platform',at=[12,-3.5],w=14,d=5,height=.05,id='bank_e',color=(.55,.5,.45)),LOW(2,-8.6,-2.4,.7),dict(kind='pedestal',at=[0,-3.5],id='stand4',height=.58,size=.3)]),[at('vesper',-6.6,-3.6,face=[5,-3.6]),at('pepper',-20,-3.6,face=[-6.6,-3.6])],props=[prop('plank','plank',-8.6,-2.4,on='stand2',size=3.5)],steps=[
 run('pepper',[-9.4,-3.6]),
 convo([('pepper','Give it back, Vesper!','angry','vesper'),('vesper','I read it. A storm! I was taking it to Tobias myself. You were too slow.','serious','pepper')]),
 par(act('pepper','startle'),sfx('thunder',0.2)),
 convo([('pepper','You were warning him?','concern','vesper'),('vesper','But the bridge is out. We cannot cross.','sad','pepper')]),
 par(take('pepper','plank')),
 par(go('pepper',[-5.6,-3.4],gait='brisk')),
 put('pepper',on='stand4'),
 par(act('vesper','cele'),emote('pepper','smile',2.5)),
],time='dusk',ambience='sea',music='mystery',fog=.35,intent='Vesper reveals she was racing to warn the ferry too. Together they bridge the gap with a plank.'))
# 6 ---------------------------------------------------------------------------------------------------------------- the toll
S.append(scene('toll','The toll',loc('harbor',5,water=[-5,-9,5,3],objects=[dict(kind='platform',at=[-12,-3.5],w=14,d=5,height=.05,id='bank_w',color=(.55,.5,.45)),dict(kind='platform',at=[12,-3.5],w=14,d=5,height=.05,id='bank_e',color=(.55,.5,.45)),LOW(3,-9.6,-0.6,.7)]),[at('grub',9,-3.2,face=[-6,-3.4]),at('pepper',-8,-3.4,face=[8,-3.4]),at('vesper',-10,-3.8,face=[8,-3.4]),at('mo',-11.4,-1.4,face=[8,-3.4])],props=[prop('apple','apple',-9.6,-0.6,on='stand3')],steps=[
 par(go('pepper',[5.2,-3.6],gait='brisk'),go('vesper',[4.2,-4.2],gait='strut')),
 convo([('grub','Toll bridge. One apple each. No apple, no crossing.','angry','pepper'),('vesper','We have no apples. A storm is coming!','concern','grub'),('grub','No apple, no crossing.','angry','vesper')]),
 par(sfx('thunder',0.2),emote('pepper','sad',2.5)),
 take('mo','apple'),
 convo([('mo','These two children helped me with my cart. Grub, take mine.','warm','grub')]),
 give('mo','grub'),
 par(emote('grub','smile',2.5),act('grub','shrug')),
 convo([('grub','...Fine. Cross. But mind the thunder.','concern','pepper')]),
 par(run('pepper',[18,-3.6]),run('vesper',[17,-4.4])),
],time='dusk',ambience='sea',music='comic',fog=.4,intent='The toll keeper blocks the way until Old Mo pays with an apple, to repay Pepper’s kindness.'))
# 7 ---------------------------------------------------------------------------------------------------------------- the ferry
S.append(scene('ferry','Last bell',loc('harbor',7,objects=[LOW(5,-17.6,-3.0)]),[at('tobias',11.6,-3.4,face=[-14,-3.2]),at('pepper',-17.6,-4.2,face=[-17.6,-3.0]),at('vesper',-19.4,-4.6,face=[9,-3.2])],props=[LETTER(-17.6,-3.0,'stand5')],steps=[
 take('pepper','letter'),
 par(sfx('bell',0.2),sfx('bell',2.8),sfx('bell',5.4),run('pepper',[-3,-3.4]),run('vesper',[-5,-4.2])),
 par(act('pepper','fall'),sfx('thud',0.2)),
 par(act('pepper','getup'),go('vesper',[-6.0,-4.4],gait='run')),
 par(act('vesper','nod'),emote('pepper','smile',1.5)),
 par(run('pepper',[8.2,-3.4]),run('vesper',[7.0,-4.6])),
 convo([('pepper','Captain! A letter from Odile! A storm is coming!','concern','tobias')]),
 par(act('tobias','think'),sfx('sting',0.2)),
],time='dusk',ambience='sea',music='epic',fog=.45,extras=crowd(8,[4,-9,18,-1],[11,-5],71),intent='At the last bell Pepper trips, Vesper helps her up, and they run the last steps together to hand over the letter.'))
# 8 ---------------------------------------------------------------------------------------------------------------- the storm breaks
S.append(scene('storm','The storm breaks',loc('harbor',7),[at('tobias',9,-3.2,face='pepper'),at('pepper',5.4,-3.6,face='tobias'),at('vesper',4.2,-4.4,face='tobias')],steps=[
 convo([('tobias','A storm by sunset... Odile is never wrong.','serious','pepper')]),
 par(sfx('thunder',0.2),act('tobias','startle')),
 convo([('tobias','Everybody off the ferry! Passengers to shelter! Now!','angry','pepper')]),
 par(run('tobias',[13.5,-3.0]),act('pepper','cele'),act('vesper','cele')),
 sfx('thunder',0.5),
 convo([('tobias','Fastest courier on the coast. And the best rival she will ever have.','warm','vesper')]),
],time='night',ambience='rain',music='tense',fog=.6,extras=crowd(8,[4,-9,18,-1],[11,-5],71),intent='Tobias reads the letter, cancels the sailing, and the storm breaks over the empty ferry.'))
# 9 ---------------------------------------------------------------------------------------------------------------- the inn
S.append(scene('inn','Soup and thunder',loc('room',3),[at('odile',-2.4,-2.6,face='pepper'),at('pepper',0,-1.8,face='odile'),at('vesper',2.6,-2.4,face='pepper'),at('grub',3.4,-0.6,face='pepper'),at('mo',-3.2,1.4,face='pepper'),at('tobias',-1,1.8,face='pepper')],steps=[
 convo([('odile','Fourteen families would have sailed into that.','serious','pepper'),('tobias','Thanks to a small fox who never stops. Almost never.','warm','pepper')]),
 par(act('mo','laugh'),act('grub','laugh'),act('pepper','cele')),
 convo([('vesper','Pepper, partner? The Harbour Couriers need a fast fox and a stylish cat.','joy','pepper'),('pepper','Deal. But I get to wear the cap.','joy','vesper')]),
 sfx('thunder',0.5),
 par(emote('pepper','smile',4),emote('vesper','smile',4)),
 wait(2.0),
],time='night',ambience='rain',music='warm',fog=.0,intent='Everybody shelters at the inn. The rivals become partners.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'warning':'Sunset: warn the ferry in 3 hours','square':'2 hours to sunset','cart':'Pepper never stops...','chase':'The letter is stolen! 1 hour left','bridge':'The bridge is broken','toll':'No apple, no crossing','ferry':'The last bell: 5 minutes','storm':'The storm breaks','inn':'Safe'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A courier who never stops breaks her promise once, for a good reason, and it saves a ferry full of families from a storm.'
THEME=dict(root=53,mode='dorian',tempo=108,motif=[(0,1),(2,1),(4,.5),(3,.5),(7,1.5)],motifs=dict(pepper=[7,6,4],vesper=[0,3,5],odile=[2,0,-2],tobias=[-5,-3,-5],grub=[0,0,-3],mo=[2,1,-1]),palette=dict(pad=48,bass=43,pluck=52,hit=47))
for _c in CAST:_c.setdefault('pace',1.2)
FILM=dict(id='storm_letter',title='The Storm Letter',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=5)
