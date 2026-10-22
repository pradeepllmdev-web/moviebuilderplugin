"""Film 4: 'The Silent Bell' - a village festival whose bell has vanished (about 4.5 minutes, 9 scenes, 6 new characters, 5 locations).
Marta finds the festival bell's stand empty at noon. A search party follows clues from the harbour to the market to the smithy, where gruff Otto has secretly mended the cracked bell as a gift. They carry it home, hang it and ring it at sunset.
Built for easy viewing: every scene has one goal shown on screen, the clues are things you can see (tracks, a painting, a cloth-covered bell), and every line is also captioned.
python perf_movie.py films/silent_bell.py out/bell --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='marta',name='Marta',species='cat',posture='hurried',outfit='innkeeper',colors=[(.92,.88,.8),(.55,.2,.25),(.88,.8,.6),(.3,.25,.2)],description='the innkeeper who runs the festival'),
 dict(id='hugo',name='Mayor Hugo',species='ox',posture='proud',outfit='gentleman',colors=[(.3,.3,.34),(.6,.1,.15),(.2,.14,.1)],description='the grumpy mayor in a grey suit'),
 dict(id='finn',name='Finn',species='fox',posture='jaunty',outfit='fisherman',colors=[(.25,.4,.65),(.95,.78,.15),(.25,.3,.4)],description='a cheerful fisherman in a yellow coat'),
 dict(id='lulu',name='Lulu',species='owl',posture='neutral',outfit='artist',colors=[(.85,.35,.3),(.25,.35,.65),(.65,.25,.5),(.95,.8,.25)],description='a painter who notices everything'),
 dict(id='otto',name='Otto',species='bear',posture='tired',outfit='blacksmith',colors=[(.5,.5,.55),(.4,.26,.14),(.22,.18,.14),(.3,.3,.36)],description='the big quiet blacksmith'),
 dict(id='bea',name='Bea',species='rabbit',posture='hurried',outfit='child',colors=[(.9,.5,.6),(.95,.85,.4),(.35,.55,.4),(.4,.28,.2)],description='a curious child who follows the clues'),
]
STAND=dict(kind='pedestal',at=[3.0,-1.2],id='stand0',height=.8,size=.5)
BELL=lambda x,y,on=None:prop('bell','bell',x,y,on=on,size=1.6)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the empty stand
S.append(scene('empty_stand','The empty stand',loc('village_square',7,objects=[STAND]),[at('marta',-8,-3.6,face=[3,-1.2]),at('hugo',-10,3,face=[3,-1.2]),at('bea',8,-6,face=[3,-1.2])],steps=[
 par(go('marta',[1.2,-2.6],gait='brisk'),look('hugo','marta',2)),
 act('marta','startle'),
 convo([('marta','Hugo! The festival bell is gone!','sad','hugo')]),
 point('marta','stand0',1.4),
 par(go('hugo',[-1.4,-1.0],gait='stomp'),go('bea',[5.0,-2.8],gait='brisk')),
 convo([('hugo','Gone? It must ring at sunset. That is five hours away!','angry','marta'),('bea','There are wheel tracks in the dust. Big ones.','concern','hugo'),('hugo','Then everyone looks. Everyone!','angry','marta')]),
],time='day',ambience='wind',music='tense',intent='The festival bell has vanished from its stand. It must ring at sunset.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the plan
S.append(scene('plan','Splitting up',loc('village_square',7,objects=[STAND]),[at('hugo',-2,-1,face='marta'),at('marta',0.5,-2.5,face='hugo'),at('finn',-9,-5,face='hugo'),at('lulu',9,-6,face='hugo')],steps=[
 par(go('finn',[-4.0,-2.6],gait='bounce'),go('lulu',[3.8,-4.6],gait='walk')),
 convo([('hugo','Finn, search the harbour. Lulu, the market. Marta and I will ask around here.','serious','finn'),('finn','Aye. A bell cannot hide from a fisherman.','joy','hugo'),('lulu','I will look carefully. I always do.','warm','hugo')]),
 par(go('finn',[-16,-2],gait='bounce'),go('lulu',[16,-3],gait='walk'),act('hugo','cut')),
 wait(1.0),
],time='day',ambience='wind',music='mystery',intent='The mayor sends the villagers to search the harbour and the market.'))
# 3 ---------------------------------------------------------------------------------------------------------------- harbour
S.append(scene('harbor','Clue one: the harbour',loc('harbor',4),[at('finn',-10,-2.6,face=[0,-3]),at('bea',-12,-3.2,face=[0,-3])],steps=[
 par(go('finn',[-3,-1.0],gait='bounce'),go('bea',[-5,0.2],gait='brisk')),
 convo([('finn','No bell in the boats. No bell in the nets. Only fish.','concern','bea')]),
 point('bea',[-1,1.8],1.4),
 par(look('bea',[-1,1.8],1.5),act('bea','kneel')),
 convo([('bea','Finn, look! Wheel marks. Deep ones, like something heavy.','concern','finn'),('finn','Heavy and heading up the hill road. Toward the smithy!','serious','bea')]),
 par(act('finn','cut'),act('bea','joy')),
],time='day',ambience='sea',music='mystery',intent='At the harbour, Finn and Bea find deep wheel marks leading toward the smithy.'))
# 4 ---------------------------------------------------------------------------------------------------------------- market
S.append(scene('market','Clue two: the painting',loc('market',5,objects=[dict(kind='pedestal',at=[-1.5,-2.2],id='crate_p',height=.7,size=.4)]),[at('lulu',-7,-5,face=[-1.5,-2.2]),at('marta',9,-7,face='lulu'),at('hugo',11,-8,face='lulu')],props=[prop('painting','scroll',-1.5,-2.2,on='crate_p')],steps=[
 par(take('lulu','painting'),go('marta',[3.0,-3.4],gait='brisk'),go('hugo',[4.6,-3.8],gait='stomp')),
 convo([('lulu','I painted the square at dawn. Look what is in the corner.','warm','marta')]),
 give('lulu','marta'),
 convo([('marta','A cart. With a big shape under a blanket.','concern','hugo'),('hugo','Whose cart is that?','angry','lulu'),('lulu','Otto the blacksmith. He rolled it up the hill road before breakfast.','serious','hugo')]),
],time='day',ambience='market',music='mystery',extras=crowd(5,[-12,-4,12,10],[0,-2],41),intent='Lulu’s painting shows a covered cart belonging to Otto the blacksmith.'))
# 5 ---------------------------------------------------------------------------------------------------------------- march
S.append(scene('march','To the smithy',loc('meadow',3),[at('hugo',-10,-6,face=[8,4]),at('marta',-12,-7.5,face=[8,4]),at('finn',-13,-5,face=[8,4]),at('bea',-14,-7,face=[8,4]),at('lulu',-15,-5.5,face=[8,4])],steps=[
 par(go('hugo',[-2,-2],gait='stomp'),go('marta',[-4,-3.4],gait='brisk'),go('finn',[-5,-1.4],gait='bounce'),go('bea',[-6.4,-3.2],gait='brisk'),go('lulu',[-7.6,-2],gait='walk')),
 convo([('hugo','The blacksmith hates noise. He took the bell to silence it!','angry','marta'),('marta','Otto would never.','concern','hugo'),('finn','We will see. The smithy is just over the hill.','serious','hugo')]),
 par(go('hugo',[6,3],gait='stomp'),go('marta',[4.2,2.2],gait='brisk'),go('finn',[3,3.8],gait='bounce'),go('bea',[2,2.4],gait='brisk'),go('lulu',[1,3.6],gait='walk')),
],time='day',ambience='wind',music='tense',intent='The search party marches to the smithy. The mayor thinks Otto took the bell.'))
# 6 ---------------------------------------------------------------------------------------------------------------- the smithy
S.append(scene('smithy','The smithy',loc('workshop',2),[at('otto',-1.6,-2.4,face=[-3,-1]),at('hugo',0,-3.2,face='otto'),at('marta',1.4,-3.2,face='otto'),at('bea',2.6,-2.9,face='otto')],props=[BELL(1.0,-.45,on='table')],steps=[
 par(act('otto','hit'),sfx('clang',0.3)),
 par(go('hugo',[-0.2,-1.2],gait='stomp'),go('marta',[1.1,-1.8],gait='brisk'),go('bea',[2.6,-1.6],gait='brisk')),
 convo([('hugo','Otto! You took our festival bell!','angry','otto')]),
 point('hugo','otto',1.2),
 par(emote('otto','concern',2.5),act('otto','shrug')),
 convo([('otto','It cracked at the last festival. I mended it at dawn. A gift. I wanted no fuss.','warm','hugo'),('marta','Otto. It is perfect.','joy','otto'),('hugo','Ahem. I may have shouted a little too early.','concern','otto')]),
 par(act('bea','joy'),emote('marta','smile',3)),
],time='day',ambience='fire',music='warm',intent='In the smithy, Otto reveals he secretly mended the cracked bell as a gift.'))
# 7 ---------------------------------------------------------------------------------------------------------------- procession
S.append(scene('procession','Bringing it home',loc('village_square',7,objects=[STAND,dict(kind='pedestal',at=[-5.0,-4.6],id='stand1',height=.8,size=.5)]),[at('otto',-8.5,-5.6,face=[-5,-4.6]),at('bea',-9.5,-8.2,face='otto'),at('marta',-9.2,-1.6,face='otto'),at('hugo',-7.4,-9,face='otto')],props=[BELL(-5.0,-4.6,on='stand1')],steps=[
 par(take('otto','bell'),go('bea',[-6.8,-6.2],gait='brisk')),
 convo([('bea','Careful, Otto. It rings if you sneeze.','joy','otto'),('otto','I never sneeze.','warm','bea')]),
 par(go('otto',[1.2,-2.4],gait='shuffle'),go('bea',[-0.6,-3.4],gait='brisk'),go('marta',[-1.6,-1.6],gait='walk'),go('hugo',[-3.6,-0.8],gait='strut')),
],time='dusk',ambience='wind',music='warm',extras=crowd(6,[-14,-8,14,9],[3,-1.2],51),intent='Otto carries the mended bell back to the village square.'))
# 8 ---------------------------------------------------------------------------------------------------------------- hanging the bell
S.append(scene('ring','The bell rings',loc('village_square',7,objects=[STAND,dict(kind='pedestal',at=[-1.0,-2.0],id='stand1',height=.8,size=.5)]),[at('otto',-3.0,-3.2,face=[-1,-2]),at('bea',-5.0,-4.6,face=[3,-1.2]),at('marta',-6.2,-2.4,face=[3,-1.2]),at('hugo',-7.4,-4.4,face=[3,-1.2])],props=[BELL(-1.0,-2.0,on='stand1')],steps=[
 par(take('otto','bell')),
 put('otto',on='stand0'),
 par(emote('marta','smile',3),act('bea','joy')),
 convo([('hugo','Citizens of the village! The festival bell rings again!','joy','marta')]),
 par(sfx('bell',0.3),sfx('bell',1.6),sfx('bell',2.9),act('bea','joy'),act('marta','joy'),act('hugo','bow')),
 wait(2.0),
],time='dusk',ambience='wind',music='epic',extras=crowd(8,[-14,-8,14,9],[3,-1.2],61),intent='The bell is back on its stand and rings at sunset.'))
# 9 ---------------------------------------------------------------------------------------------------------------- festival night
S.append(scene('festival','Festival night',loc('village_square',7,objects=[STAND]),[at('marta',-1.5,-3.0,face='otto'),at('otto',1.0,-3.6,face='marta'),at('bea',-3.0,-4.4,face='otto'),at('hugo',-5,-2,face='otto'),at('finn',-7,-4.5,face='otto'),at('lulu',5,-4,face='otto')],steps=[
 convo([('marta','Otto, the first dance is yours. And the first bowl of soup.','warm','otto'),('otto','I do not dance. But I will take the soup.','warm','marta')]),
 par(act('finn','joy'),act('lulu','joy'),act('bea','joy')),
 convo([('hugo','From now on, the smithy is not the quiet house. It is the house of the bell.','joy','otto'),('bea','Next year I will ring it myself!','joy','otto')]),
 par(emote('otto','smile',4),emote('marta','smile',4)),
 wait(2.5),
],time='night',ambience='crowd',music='warm',extras=crowd(10,[-14,-8,14,9],[0,-3],71),intent='The village celebrates with a feast. Otto is thanked.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'empty_stand':'The festival bell is missing!','plan':'Find the bell before sunset','harbor':'Clue 1: heavy wheel marks','market':'Clue 2: a painting','march':'Follow the clues to the smithy','smithy':'Who took the bell?','procession':'Bring the bell home','ring':'Ring the bell at sunset','festival':'The festival'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='The festival bell vanishes hours before sunset, and a trail of clues leads a village search party to a surprising gift.'
THEME=dict(root=55,mode='dorian',tempo=100,motif=[(0,1),(4,1),(2,.5),(4,.5),(7,1.5)],motifs=dict(marta=[0,4,2],hugo=[0,0,-3],finn=[4,6,4],lulu=[2,4,7],otto=[-5,-3,-5],bea=[7,9,7]),palette=dict(pad=48,bass=43,pluck=52,hit=47))
for _c in CAST:_c.setdefault('pace',1.15)
FILM=dict(id='silent_bell',title='The Silent Bell',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=4)
