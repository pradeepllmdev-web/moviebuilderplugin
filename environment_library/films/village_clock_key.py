"""Film 9: 'The Clock Tower Key' - a village story told with real people (about 3 minutes, 6 scenes, 5 villagers of different heights and clothes).
The village clock stops at the wrong hour and keeper Nell has lost the winding key. Everyone searches the wrong places, until small Mina, playing by the stream, finds something shiny. Joss the farmer knows what it is. The key is carried to the tower, the clock chimes and the baker thanks the child.
The people are built on the Universal Animation Library skeleton (walk, jog, sit, talk, fall and dance clips), so each of them moves like a person: a tall farmer, a small child, an old woman.
python perf_movie.py films/village_clock_key.py out/clock_key --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='nell',name='Nell',species='person',height=1.7,posture='hurried',outfit='mayor',colors=[(.2,.35,.6),(.25,.22,.3),(.2,.12,.08)],description='the clock keeper, in a blue coat'),
 dict(id='pol',name='Pol',species='person',height=1.8,posture='jaunty',outfit='cook',colors=[(.95,.95,.92),(.35,.3,.28),(.25,.18,.12)],description='the baker in a white apron'),
 dict(id='ada',name='Granny Ada',species='person',height=1.5,posture='hunched',outfit='villageress',colors=[(.7,.25,.3),(.4,.3,.35),(.3,.2,.12)],description='an old woman in a red shawl'),
 dict(id='joss',name='Farmer Joss',species='person',height=1.98,posture='proud',outfit='farmer',colors=[(.25,.5,.3),(.5,.4,.25),(.3,.2,.1)],description='the tall farmer in a green shirt'),
 dict(id='mina',name='Mina',species='person',height=1.25,posture='hurried',outfit='child',colors=[(.9,.55,.2),(.3,.4,.7),(.4,.25,.15)],description='a small girl in an orange dress'),
]
KEYSTAND=lambda x,y,h=.7:dict(kind='pedestal',at=[x,y],id='stand0',height=h,size=.4)
TOWER=dict(kind='tower',at=[0,12],id='clock_tower',size=1.2)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the clock stops
S.append(scene('stopped','The clock stops',loc('village_square',4,objects=[TOWER]),[at('pol',-5,-3,face=[0,6]),at('ada',3,-4,face=[0,6]),at('nell',7,3,face=[0,6])],steps=[
 convo([('pol','Half past six. Again. My bread will burn if I miss the bell.','concern','ada')]),
 par(sfx('clang',0.2),icon('ada','question',1.8)),
 point('ada',[0,12,7],1.8),
 convo([('ada','Look at the tower. The clock has stopped at the wrong hour.','concern','pol')]),
 par(run('nell',[1.5,-1.5]),icon('nell','alarm',1.6)),
 convo([('nell','The key! I have lost the winding key. It was on my belt this morning.','sad','pol'),('pol','Then we must find it before noon.','warm','nell')]),
],time='dawn',ambience='wind',music='mystery',fog=.05,intent='The village clock has stopped, and Nell the keeper has lost the winding key.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the search
S.append(scene('search','Looking in the wrong places',loc('market',5),[at('nell',-6,-3,face=[0,0]),at('pol',-2,-5,face=[0,0]),at('ada',4,-3,face=[0,0])],steps=[
 par(go('nell',[-1,-1],gait='brisk'),go('pol',[2,-3],gait='walk'),go('ada',[5,0],gait='walk')),
 par(look('nell',[-4,4],1.4),look('pol',[4,-5],1.4),look('ada',[0,5],1.4)),
 par(act('pol','shrug'),icon('pol','question',1.6)),
 convo([('pol','It is not in the bread baskets.','concern','nell'),('ada','Nor under the apples. I have checked three times.','concern','nell')]),
 par(act('nell','think'),emote('nell','sad',3)),
 convo([('nell','Without the key the whole village is out of time.','sad','pol')]),
],time='day',ambience='market',music='mystery',intent='Three villagers search the market and find nothing.'))
# 3 ---------------------------------------------------------------------------------------------------------------- the shiny thing
S.append(scene('stream','Something shiny',loc('meadow',6,objects=[KEYSTAND(-1.5,-1.0)]),[at('mina',-6,-4,face=[-1.5,-1]),at('joss',7,3,face=[-4,-3])],props=[prop('key','key',-1.5,-1.0,on='stand0',size=2.2)],steps=[
 par(go('mina',[-2.6,-2.0],gait='walk'),look('mina','key',2)),
 icon('mina','idea',1.6),
 take('mina','key'),
 convo([('mina','A golden key! Maybe it opens a treasure chest.','joy','joss')]),
 par(go('joss',[2,0],gait='walk'),icon('joss','question',1.8)),
 convo([('joss','Let me see that. Mina, that is the key to the clock tower!','joy','mina'),('mina','Then we have to take it back right now!','joy','joss')]),
 par(act('mina','cele'),act('joss','laugh')),
],time='day',ambience='wind',music='bright',intent='Mina finds a golden key by the stream. Joss knows what it opens.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the run
S.append(scene('run','A race to the tower',loc('meadow',7),[at('mina',-8,-2,face=[8,2]),at('joss',-9.5,-3,face=[8,2])],steps=[
 par(run('mina',[7,2]),go('joss',[2,0.5],gait='brisk')),
 convo([('joss','Mind the puddle, Mina!','warm','mina')]),
 par(run('mina',[16,4]),go('joss',[10,2.5],gait='brisk')),
 par(sfx('thud',0.2),act('joss','fall')),
 par(act('mina','startle'),icon('mina','alarm',1.6)),
 convo([('mina','Joss! Are you hurt?','concern','joss'),('joss','Only my pride. Go, go, I am right behind you!','warm','mina')]),
 run('mina',[20,5]),
],time='day',ambience='wind',music='epic',intent='Mina races toward the tower. Joss slips in the mud but sends her on.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the chime
S.append(scene('chime','The clock chimes',loc('village_square',8,objects=[TOWER]),[at('nell',-4,-3,face=[2,-2]),at('pol',-7,-5,face=[2,-2]),at('ada',-9,-3,face=[2,-2]),at('mina',9,2,face=[2,-2])],props=[],steps=[
 par(run('mina',[2.8,-1.2]),icon('nell','alarm',1.6)),
 convo([('mina','Nell! I found your key! It was in the grass by the stream!','joy','nell')]),
 par(act('nell','cele'),emote('nell','smile',3)),
 convo([('nell','You found it! Everyone, stand back. I will wind the clock.','joy','mina')]),
 par(go('nell',[0,4],gait='brisk'),act('mina','wave')),
 par(sfx('bell',0.2),sfx('bell',1.6),icon('pol','joy',2.0),icon('ada','joy',2.0)),
 par(act('pol','cele'),act('ada','cele'),act('mina','cele')),
],time='day',ambience='wind',music='epic',intent='Mina hands over the key. The keeper winds the clock and the bell rings.'))
# 6 ---------------------------------------------------------------------------------------------------------------- the bun
S.append(scene('bun','A bun for a hero',loc('village_square',9,objects=[dict(kind='bench',at=[0,-2.5],id='bench0',yaw=0),KEYSTAND(-4,2,1.15)]),[at('mina',-1.5,-4.5,face=[0,-2.5]),at('pol',-4,0,face=[0,-2.5]),at('ada',4,-1,face=[0,-2.5]),at('joss',7,-5,face=[0,-2.5]),at('nell',5,2,face=[0,-2.5])],props=[prop('bun','basket',-4,2,on='stand0',size=.55)],steps=[
 par(take('pol','bun'),look('mina','pol',2)),
 par(go('pol',[-1.6,-3.6],gait='walk'),go('joss',[1.8,-3.8],gait='walk'),icon('joss','joy',1.8)),
 give('pol','mina'),
 convo([('pol','For the girl who saved my bread. Warm from the oven.','warm','mina'),('mina','Thank you, Pol! It smells like the whole village.','joy','pol')]),
 par(sit('mina','bench0.0',face=[0,-8]),sit('joss','bench0.1',face=[0,-8])),
 convo([('joss','Pol, next time I carry the bun and Mina can watch!','joy','pol'),('ada','Noon, and not a minute wrong.','warm','nell')]),
 par(act('nell','laugh'),act('pol','laugh'),emote('mina','smile',3)),
 wait(1.5),
],time='dusk',ambience='wind',music='warm',intent='The villagers share a bun and laugh. The clock keeps perfect time.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'stopped':'The clock stops','search':'Where is the key?','stream':'A golden key','run':'Race to the tower','chime':'The clock chimes','bun':'A bun for a hero'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='The village clock stops and the keeper has lost her key; the whole village searches in vain, until a little girl finds it by the stream and races it to the tower.'
THEME=dict(root=53,mode='major',tempo=100,motif=[(0,1),(4,.5),(7,.5),(12,1),(7,1)],motifs=dict(nell=[0,4,7],pol=[2,5,2],ada=[-3,0,-3],joss=[7,4,0],mina=[9,12,9]),palette=dict(pad=48,bass=41,pluck=46,hit=47))
FILM=dict(id='clock_key',title='The Clock Tower Key',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=3)
