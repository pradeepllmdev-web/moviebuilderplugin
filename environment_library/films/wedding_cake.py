"""Film 7: 'The Wobbly Cake' - a comedy about a wedding cake that has to cross a village in forty-five minutes (about 5 minutes, 8 scenes, 6 characters, 5 locations).
Built with the new pacing tools: characters talk while they walk (go ... talk=), lines overlap and interrupt (overlap_by), walks are short, and every scene has a visible clock ("Wedding at 4:00 - 45 minutes").
Beats: the cake leaves the bakery late; a cart wheel breaks; the cake is dropped (midpoint disaster); the baker despairs; the bride and groom - also late - turn it into the best part of their wedding.
python perf_movie.py films/wedding_cake.py out/cake --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='bettina',name='Bettina',species='badger',posture='hurried',outfit='cook',colors=[(.96,.96,.94),(.85,.35,.45),(.3,.3,.38),(.25,.18,.12)],description='the baker, flour to her elbows'),
 dict(id='dash',name='Dash',species='fox',posture='jaunty',outfit='child',colors=[(.25,.55,.7),(.95,.8,.25),(.35,.5,.35),(.4,.28,.2)],description='the baker’s bouncy apprentice'),
 dict(id='rufus',name='Rufus',species='ox',posture='angry',outfit='gentleman',colors=[(.25,.28,.4),(.8,.2,.25),(.2,.14,.1)],description='the best man in a borrowed suit'),
 dict(id='marcel',name='Marcel',species='heron',posture='tired',outfit='mayor',colors=[(.2,.3,.25),(.85,.8,.3),(.2,.15,.1)],description='the nervous, very tall groom'),
 dict(id='juno',name='Juno',species='mouse',posture='neutral',outfit='villageress',colors=[(.95,.92,.88),(.9,.7,.8),(.4,.3,.25)],description='the small, cheerful bride'),
 dict(id='elm',name='Granny Elm',species='elder',posture='hunched',outfit='mother',colors=[(.5,.4,.6),(.9,.88,.8),(.3,.22,.15)],description='the groom’s granny, who has opinions'),
]
CAKE=lambda x,y,on=None:prop('cake','barrel_small',x,y,on=on,size=1.2)
LOW=lambda i,x,y,h=.45:dict(kind='pedestal',at=[x,y],id='stand%d'%i,height=h,size=.4)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the bakery
S.append(scene('bakery','Cake day',loc('room',3,objects=[LOW(0,-1.0,-0.9)]),[at('bettina',-2.6,-2.6,face=[-1,-0.9]),at('dash',3.2,-3.0,face='bettina')],props=[CAKE(-1.0,-0.9,'stand0')],steps=[
 par(go('bettina',[-1.9,-1.5],gait='brisk'),go('dash',[1.2,-2.2],gait='bounce',talk=('Miss Bettina! The clock says three!','concern','bettina'))),
 convo([('bettina','Three?! The wedding is at four!','angry','dash'),('dash','And the chapel is on the far hill!','concern','bettina',dict(overlap_by=.5)),('bettina','Then we run. Take the left, I take the right.','serious','dash',dict(overlap_by=.4))]),
 point('dash',[12,-3],1.4),
 par(take('bettina','cake')),
 par(go('bettina',[0,-3.2],gait='brisk',talk=('Mind the icing! Mind the icing!','concern','dash')),go('dash',[1.2,-3.4],gait='bounce')),
],time='day',ambience='hall',music='comic',fog=0.,intent='Bettina and Dash realise the wedding cake is late. The wedding is at four.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the market
S.append(scene('market','Through the market',loc('market',3,objects=[LOW(1,-13.0,-2.4)]),[at('bettina',-13.0,-3.6,face=[-13.0,-2.4]),at('dash',-15,-3.8,face='bettina'),at('rufus',14,-8,face=[-5,-5])],props=[CAKE(-13.0,-2.4,'stand1')],steps=[
 take('bettina','cake'),
 par(go('bettina',[-2,-3.2],gait='brisk',talk=('Out of the way, please! Wedding cake coming through!','angry','dash')),go('dash',[-4.8,-5.0],gait='bounce')),
 par(go('rufus',[-0.8,-4.4],gait='stomp',talk=('Is that the cake? Give it here, I am the best man!','joy','bettina'))),
 convo([('bettina','You are the best man at what, exactly? Carrying?','concern','rufus'),('rufus','At everything! Hand it over!','joy','bettina',dict(overlap_by=.4)),('dash','He’s very big, Miss Bettina.','concern','bettina',dict(overlap_by=.3))]),
 point('bettina','rufus',1.2),
 give('bettina','rufus'),
 par(go('rufus',[14,-3.2],gait='stomp',talk=('Easy! Nothing could be easier!','joy','dash')),go('bettina',[8.6,-3.0],gait='brisk'),go('dash',[7.0,-5.8],gait='bounce')),
],time='day',ambience='market',music='comic',fog=0.,extras=crowd(6,[-12,-4,12,10],[0,-2],41),intent='The best man grabs the cake and strides off with it. 40 minutes left.'))
# 3 ---------------------------------------------------------------------------------------------------------------- the dropped cake
S.append(scene('drop','The wobble',loc('village_square',8,objects=[LOW(2,-9.0,-1.8,.7),LOW(3,6.0,-2.6,.7)]),[at('rufus',-9,-3.0,face=[-9,-1.8]),at('bettina',-8.2,-6.6,face='rufus'),at('dash',-9.8,-7.8,face='rufus')],props=[CAKE(-9.0,-1.8,'stand2')],steps=[
 take('rufus','cake'),
 par(go('rufus',[1.6,-3.0],gait='stomp',talk=('See? Steady as a rock. Not a wobble. Not one single wobble.','joy','dash')),go('bettina',[-5,-3.8],gait='brisk'),go('dash',[-6,-4.8],gait='bounce')),
 par(act('rufus','startle'),sfx('creak',0.1)),
 convo([('rufus','Wobble.','concern','bettina'),('bettina','Don’t you dare...','angry','rufus',dict(overlap_by=.3))]),
 put('rufus',on='stand3'),
 par(sfx('crash',0.1),act('bettina','fall')),
 par(act('dash','startle'),act('rufus','shrug')),
 point('dash','rufus',1.3,'L'),
 convo([('dash','The top tier...','sad','bettina')]),
],time='day',ambience='wind',music='sad',fog=0.,intent='Rufus wobbles and the cake drops. The top tier is ruined. 25 minutes left.'))
# 4 ---------------------------------------------------------------------------------------------------------------- despair
S.append(scene('despair','All is lost',loc('hilltop',4,objects=[dict(kind='bench',at=[-1.5,-1.0],id='bench0',yaw=0),LOW(4,3.0,-2.2,.45)]),[at('bettina',-2.8,-2.4,face=[3,-2.2]),at('dash',-0.4,-2.8,face='bettina'),at('rufus',1.4,-3.4,face='bettina')],props=[prop('smash','pie',3.0,-2.2,on='stand4',size=1.6)],steps=[
 par(go('bettina',[-1.5,-1.0],gait='shuffle')),
 sit('bettina','bench0.0',face=[3,-2.2]),
 convo([('bettina','Twenty years of baking, and the best cake of my life is a pancake.','sad','dash'),('rufus','It was a very good pancake.','concern','bettina'),('dash','Rufus!','angry','rufus',dict(overlap_by=.3))]),
 par(emote('bettina','sad',4),look('bettina',[3,-2.2],3)),
 point('rufus',[3,-2.2],1.2),
 wait(1.0),
],time='day',ambience='wind',music='sad',fog=0.,intent='Bettina sits on a bench, sure the wedding is ruined. 15 minutes left.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the bride arrives
S.append(scene('bride','Late, late, late',loc('hilltop',4,objects=[dict(kind='bench',at=[-1.5,-1.0],id='bench0',yaw=0),LOW(4,3.0,-2.2,.45)]),[at('bettina',-2.8,-2.4,face=[3,-2.2]),at('dash',-0.4,-2.8,face='bettina'),at('rufus',1.4,-3.4,face='bettina'),at('juno',-14,-5,face=[3,-2.2]),at('marcel',-18,-7,face=[3,-2.2]),at('elm',-12,-8,face=[3,-2.2])],props=[prop('smash','pie',3.0,-2.2,on='stand4',size=1.6)],steps=[
 sit('bettina','bench0.0',face=[3,-2.2]),
 par(go('juno',[0.4,-3.4],gait='brisk',talk=('Marcel, hurry! We are late for our own wedding!','joy','marcel')),go('marcel',[-5.4,-5.4],gait='shuffle'),go('elm',[-6,-7],gait='shuffle')),
 convo([('marcel','I know. I know. My legs are very long and very slow.','concern','juno'),('elm','In my day we ran to weddings.','serious','marcel',dict(overlap_by=.4))]),
 par(turn('juno','bettina'),emote('juno','brows',2)),
 convo([('juno','Bettina? Is that... the cake?','concern','bettina'),('bettina','It was. I am so sorry. It is ruined.','sad','juno')]),
 par(go('juno',[1.2,-2.2],gait='walk')),
],time='day',ambience='wind',music='mystery',fog=0.,intent='The bride and groom arrive, also late, and meet the despairing baker. 10 minutes left.'))
# 6 ---------------------------------------------------------------------------------------------------------------- the decision
S.append(scene('decision','The wobbliest cake',loc('hilltop',4,objects=[dict(kind='bench',at=[-1.5,-1.0],id='bench0',yaw=0),LOW(4,3.0,-2.2,.45)]),[at('juno',1.2,-2.2,face=[3,-2.2]),at('bettina',-2.8,-2.4,face='juno'),at('dash',-0.4,-2.8,face='juno'),at('rufus',1.4,-3.8,face='juno'),at('marcel',-4.4,-4.6,face='juno'),at('elm',-3,-6,face='juno')],props=[prop('smash','pie',3.0,-2.2,on='stand4',size=1.6)],steps=[
 sit('bettina','bench0.0',face='juno'),
 par(act('juno','think')),
 convo([('juno','Do you know what I want at my wedding? Friends. And something wobbly to laugh about.','warm','bettina'),('marcel','Wobbly is our whole family.','joy','juno',dict(overlap_by=.3)),('elm','And the cake is the best part.','warm','marcel',dict(overlap_by=.3))]),
 par(emote('bettina','smile',3),emote('dash','smile',3)),
 par(take('juno','smash')),
 go('juno',[8.0,2.6],gait='brisk',talk=('Everybody! To the chapel! With the wobbliest cake in history!','joy','bettina')),
],time='day',ambience='wind',music='warm',fog=0.,intent='The bride decides the wobbly cake is part of the wedding. 5 minutes left.'))
# 7 ---------------------------------------------------------------------------------------------------------------- the chapel
S.append(scene('chapel','Just in time',loc('courtyard',4,objects=[LOW(5,1.0,3.4,.45)]),[at('juno',-6,-6,face=[1,3.4]),at('marcel',-8,-7.4,face=[1,3.4]),at('bettina',-10,-5.6,face=[1,3.4]),at('dash',-11,-7.6,face=[1,3.4]),at('rufus',-12,-6,face=[1,3.4]),at('elm',-13,-7.4,face=[1,3.4])],props=[prop('smash','pie',1.0,3.4,on='stand5',size=1.6)],steps=[
 par(go('juno',[-1.2,1.2],gait='brisk'),go('marcel',[-2.4,0.4],gait='stomp'),go('bettina',[-3.6,1.6],gait='brisk'),go('dash',[-4.4,0.6],gait='bounce'),go('rufus',[-5.6,1.4],gait='stomp'),go('elm',[-6.4,0.4],gait='shuffle')),
 par(sfx('bell',0.2),sfx('bell',2.0)),
 convo([('marcel','Do you, Juno, take this cake, and also me?','joy','juno'),('juno','I do! Both! In that order!','joy','marcel',dict(overlap_by=.5))]),
 par(act('dash','joy'),act('rufus','joy'),act('bettina','joy'),act('elm','laugh')),
 par(sfx('chime',0.2),emote('juno','smile',3),emote('marcel','smile',3)),
],time='dusk',ambience='crowd',music='epic',fog=0.,extras=crowd(8,[-8,-8,8,-1],[0,3],91),intent='The wedding starts at four on the dot, wobbly cake and all.'))
# 8 ---------------------------------------------------------------------------------------------------------------- the party
S.append(scene('party','The best slice',loc('courtyard',4,objects=[LOW(5,1.0,3.4,.45)]),[at('juno',-1.5,1.2,face='marcel'),at('marcel',-0.2,1.0,face='juno'),at('bettina',-3.6,1.6,face='juno'),at('dash',-4.4,0.6,face='bettina'),at('rufus',-5.6,1.4,face='bettina'),at('elm',-2.6,-0.6,face='marcel')],props=[prop('smash','pie',1.0,3.4,on='stand5',size=1.6)],steps=[
 convo([('bettina','Next time I bake a cake, I am not letting anyone near it.','concern','juno'),('juno','Next time, bake two. One for eating, one for wobbling.','joy','bettina',dict(overlap_by=.3)),('dash','I will eat the wobbling one!','joy','bettina',dict(overlap_by=.3))]),
 par(act('rufus','laugh'),act('elm','laugh'),act('marcel','joy')),
 convo([('rufus','Best man. Worst carrier. Great cake.','joy','bettina')]),
 par(emote('bettina','smile',4),emote('juno','smile',4)),
 wait(2.0),
],time='dusk',ambience='crowd',music='bright',fog=0.,extras=crowd(10,[-8,-8,8,-1],[0,3],93),intent='Everyone celebrates with the wobbly cake.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'bakery':'Wedding at 4:00 - it is 3:00','market':'Wedding at 4:00 - 40 minutes','drop':'Wedding at 4:00 - 25 minutes','despair':'Wedding at 4:00 - 15 minutes','bride':'Wedding at 4:00 - 10 minutes','decision':'Wedding at 4:00 - 5 minutes','chapel':'4:00 - just in time','party':'The wobbliest cake in history'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A wedding cake has forty-five minutes to cross a village, and one disaster later, the wobbliest cake in history becomes the best part of the wedding.'
THEME=dict(root=60,mode='major',tempo=116,motif=[(0,1),(4,.5),(2,.5),(4,1),(7,1)],motifs=dict(bettina=[0,2,4],dash=[7,9,7],rufus=[0,0,-3],marcel=[2,0,-2],juno=[4,5,7],elm=[0,3,0]),palette=dict(pad=48,bass=45,pluck=54,hit=47))
for _c in CAST:_c.setdefault('pace',1.2)
FILM=dict(id='wedding_cake',title='The Wobbly Cake',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=4)
