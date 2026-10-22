"""Film 9: 'The Clock Tower Key' - a village story told with real people (about 4 minutes, 5 scenes, 5 villagers of different heights and clothes).
The village clock stops at the wrong hour and keeper Nell has lost the winding key. Everyone searches the wrong places, until small Mina, playing by the stream, finds something shiny. Joss the farmer knows what it is. The key is carried to the tower, the clock chimes and the baker thanks the child.
The people are built on the Universal Animation Library skeleton (walk, jog, sit, talk, fall and dance clips), so each of them moves like a person: a tall farmer, a small child, an old woman.
python perf_movie.py films/village_clock_key.py out/clock_key --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='nell',name='Nell',species='person',height=1.7,posture='hurried',outfit='mayor',colors=[(.2,.35,.6),(.25,.22,.3),(.2,.12,.08)],description='the clock keeper, in a blue coat'),
 dict(id='pol',name='Pol',species='person',height=1.8,width=1.22,depth=1.15,posture='jaunty',outfit='cook',colors=[(.95,.95,.92),(.35,.3,.28),(.25,.18,.12)],description='the baker in a white apron'),
 dict(id='ada',name='Granny Ada',species='person',height=1.5,width=.92,depth=1.0,posture='hunched',outfit='villageress',colors=[(.7,.25,.3),(.4,.3,.35),(.3,.2,.12)],description='an old woman in a red shawl'),
 dict(id='joss',name='Farmer Joss',species='person',height=1.98,width=1.1,depth=1.05,posture='proud',outfit='farmer',colors=[(.25,.5,.3),(.5,.4,.25),(.3,.2,.1)],description='the tall farmer in a green shirt'),
 dict(id='mina',name='Mina',species='person',height=1.4,posture='neutral',outfit='child',colors=[(.9,.55,.2),(.3,.4,.7),(.4,.25,.15)],description='a small girl in an orange dress'),
]
KEYSTAND=lambda x,y,h=1.0:dict(kind='pedestal',at=[x,y],id='stand0',height=h,size=.4)
TOWER=dict(kind='tower',at=[0,12],id='clock_tower',size=1.2)
KEY=lambda x,y:prop('key','key',x,y,on='stand0',size=2.2)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the key is left behind
S.append(scene('rock','The key is left behind',loc('meadow',6,objects=[KEYSTAND(-1.0,-1.0)]),[at('nell',-5,-3.5,face=[-1,-1]),at('mina',8,4,face=[-1,-1])],props=[KEY(-1.0,-1.0)],steps=[
 par(go('nell',[-2.2,-2.0],gait='walk'),look('mina','nell',2)),
 take('nell','key'),
 convo([('nell','I must wind the clock at eight. First I will wash my hands in the stream.','warm','nell')]),
 put('nell',on='stand0'),
 par(sfx('bell',0.3),icon('nell','alarm',1.8),act('nell','startle')),
 convo([('nell','The bell! I am late for the tower!','concern','nell')]),
 go('nell',[-12,-6],gait='brisk'),
 par(look('mina','key',2.5),icon('mina','question',2.0)),
 wait(1.5),
],time='dawn',ambience='wind',music='mystery',fog=.05,intent='Nell sets her tower key on a rock to wash her hands, hears the bell, and hurries away without it.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the clock stops
S.append(scene('stopped','The clock stops',loc('village_square',4,objects=[TOWER]),[at('pol',-4,-3,face=[0,6]),at('ada',3,-3,face=[0,6]),at('nell',-10,-5,face=[0,4])],steps=[
 par(sfx('clang',0.2),icon('ada','question',1.8),icon('pol','alarm',1.8)),
 point('ada',[0,12,7],1.8),
 convo([('ada','Look at the tower. The clock has stopped!','concern','pol'),('pol','Nell winds it every morning. Where is she?','concern','ada')]),
 go('nell',[-1,-3.5],gait='walk'),
 convo([('nell','I cannot find my key! I had it when I washed my hands at the stream.','sad','pol'),('pol','Then it must still be at the stream.','warm','nell')]),
 par(point('pol',[-14,-8,1],1.6),icon('nell','idea',1.8)),
 convo([('ada','Go and look, Nell. We will wait here by the tower.','warm','nell')]),
 go('nell',[-12,-6],gait='brisk'),
],time='day',ambience='wind',music='mystery',intent='The clock stops. Nell has lost her key and sets off to look at the stream.'))
# 3 ---------------------------------------------------------------------------------------------------------------- Mina finds it
S.append(scene('found','Mina finds the key',loc('meadow',6,objects=[KEYSTAND(-1.0,-1.0)]),[at('mina',3,-1,face=[-1,-1]),at('joss',9,4,face=[-1,-1])],props=[KEY(-1.0,-1.0)],steps=[
 par(go('mina',[0.2,-1.6],gait='walk'),icon('mina','idea',1.6)),
 take('mina','key'),
 convo([('mina','A golden key! It was lying on the flat rock.','joy','joss')]),
 par(go('joss',[3.5,0.5],gait='walk'),icon('joss','question',1.8)),
 convo([('joss','Let me see. That is the key to the clock tower!','joy','mina'),('mina','The clock has stopped! Somebody is looking for it.','concern','joss')]),
 par(point('joss',[0,12,7],1.6),act('mina','nod')),
 convo([('joss','Come on, we will take it to the tower together.','warm','mina')]),
 par(go('mina',[12,2],gait='walk'),go('joss',[11,3],gait='walk')),
],time='day',ambience='wind',music='bright',intent='Mina finds the golden key on the rock. Joss knows it belongs to the clock tower.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the key comes home
S.append(scene('chime','The key comes home',loc('village_square',8,objects=[TOWER]),[at('nell',-3,-3,face=[0,6]),at('pol',-6,-4,face=[-3,-3]),at('ada',-1,-5,face=[-3,-3]),at('mina',9,-2,face=[-3,-3],holds='key'),at('joss',10.5,-3,face=[-3,-3])],props=[prop('key','key',9,-2,z=1.0,size=2.2)],steps=[
 convo([('nell','It was not at the stream. The clock will never run again.','sad','pol'),('pol','Do not give up, Nell. Somebody will find it.','warm','nell')]),
 par(go('mina',[-1.2,-3.0],gait='walk'),go('joss',[0.4,-3.6],gait='walk'),icon('nell','question',1.6)),
 give('mina','nell'),
 convo([('mina','Is this yours? It was on the flat rock by the stream.','joy','nell'),('nell','I left it on the rock! Thank you, Mina!','joy','mina')]),
 par(act('nell','cele'),emote('nell','smile',3)),
 go('nell',[0,8.5],gait='walk'),
 par(sfx('bell',0.2),sfx('bell',1.6),icon('pol','joy',2.0),icon('ada','joy',2.0)),
 par(act('pol','cele'),act('ada','cele'),act('mina','cele'),act('joss','laugh')),
],time='day',ambience='wind',music='epic',intent='Mina returns the key. Nell winds the clock and the bell rings.'))
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
OBJECTIVE={'rock':'Nell leaves her key behind','stopped':'The clock stops','found':'Mina finds a golden key','chime':'The key comes home','bun':'A bun for a hero'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='Nell the clock keeper leaves her key on a rock by the stream. The village clock stops, Nell searches in despair, and a little girl who found the key brings it home.'
THEME=dict(root=53,mode='major',tempo=100,motif=[(0,1),(4,.5),(7,.5),(12,1),(7,1)],motifs=dict(nell=[0,4,7],pol=[2,5,2],ada=[-3,0,-3],joss=[7,4,0],mina=[9,12,9]),palette=dict(pad=48,bass=41,pluck=46,hit=47))
FILM=dict(id='clock_key',title='The Clock Tower Key',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=4)
