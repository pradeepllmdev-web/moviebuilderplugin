"""Film 9: 'The Clock Tower Key' - a village story told with real people (about 5 minutes, 5 scenes, 5 villagers of different heights and clothes).
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
S.append(scene('rock','The key is left behind',loc('meadow',6,objects=[KEYSTAND(-1.0,-1.0)]),[at('nell',-6,-4,face=[-1,-1],holds='key')],props=[prop('key','key',-6,-4,z=1.0,size=2.2)],steps=[
 go('nell',[-2.4,-2.1],gait='walk',talk=('Eight o’clock sharp. The whole village sets its day by my clock.','warm','nell')),
 par(look('nell',[-1,-1],1.2),emote('nell','smile',2)),
 convo([('nell','Cold stream water first. A clock keeper needs clean hands.','warm','nell')]),
 put('nell',on='stand0'),
 par(sfx('bell',0.3),icon('nell','alarm',1.8),act('nell','startle')),
 convo([('nell','That was the quarter bell already? Oh, I am late!','concern','nell')]),
 go('nell',[-13,-7],gait='brisk'),
 wait(1.2),
],time='dawn',ambience='wind',music='mystery',fog=.05,intent='Nell sets her tower key on a flat rock to wash her hands, hears the bell and hurries away without it.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the clock stops
S.append(scene('stopped','The clock stops',loc('village_square',4,objects=[TOWER]),[at('pol',-4,-3,face=[0,6]),at('ada',3,-3,face=[0,6]),at('nell',-11,-5,face=[0,4])],steps=[
 par(sfx('clang',0.2),icon('ada','question',1.8)),
 convo([('pol','Granny Ada, look at the tower. The clock still says half past six.','concern','ada'),('ada','It is nearly nine, Pol. Your customers will think it is dawn all day.','warm','pol')]),
 point('ada',[0,12,7],1.8),
 convo([('pol','Nell winds it every morning. That is not like her.','concern','ada')]),
 go('nell',[-1,-3.5],gait='walk'),
 convo([('nell','I did not forget! I only... oh no. My key is not on my belt.','sad','pol'),('ada','Where did you last have it, dear?','warm','nell'),('nell','At the stream. I set it on the flat rock while I washed my hands.','concern','ada')]),
 par(point('pol',[-14,-8,1],1.6),icon('nell','idea',1.8)),
 convo([('pol','Then the rock is where we start. Go, we will keep the village calm.','warm','nell')]),
 go('nell',[-12,-6],gait='brisk'),
],time='day',ambience='wind',music='mystery',intent='The clock stops. Nell has lost her key and sets off to look at the stream.'))
# 3 ---------------------------------------------------------------------------------------------------------------- Mina finds it
S.append(scene('found','Mina finds the key',loc('meadow',6,objects=[KEYSTAND(-1.0,-1.0)]),[at('mina',3,-1,face=[-1,-1]),at('joss',9,4,face=[-1,-1])],props=[KEY(-1.0,-1.0)],steps=[
 par(go('mina',[0.2,-1.6],gait='walk'),icon('mina','idea',1.6)),
 take('mina','key'),
 convo([('mina','A golden key, lying on the flat rock. Maybe it opens a treasure chest!','joy','mina')]),
 par(go('joss',[3.5,0.5],gait='walk'),icon('joss','question',1.8)),
 convo([('joss','Mina! That is no toy. That is the key to the clock tower.','concern','mina'),('mina','The clock stopped this morning. Somebody must be so worried!','concern','joss')]),
 par(point('joss',[0,12,7],1.6),act('mina','nod')),
 convo([('joss','We will take it back together.','warm','mina'),('mina','I will carry it. I found it!','joy','joss'),('joss','Quite right. You found it, you carry it.','warm','mina')]),
 par(go('mina',[12,2],gait='walk'),go('joss',[11,3],gait='walk')),
],time='day',ambience='wind',music='bright',intent='Mina finds the golden key on the rock. Joss knows it belongs to the clock tower.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the key comes home
S.append(scene('chime','The key comes home',loc('village_square',8,objects=[TOWER]),[at('nell',-3,-3,face=[0,6]),at('pol',-6,-4,face=[-3,-3]),at('ada',-1,-5,face=[-3,-3]),at('mina',9,-2,face=[-3,-3],holds='key'),at('joss',10.5,-3,face=[-3,-3])],props=[prop('key','key',9,-2,z=1.0,size=2.2)],steps=[
 convo([('nell','Nothing. The rock was bare, and the stream has washed away my footprints.','sad','pol'),('pol','Perhaps an honest soul picked it up. We have a few of those.','warm','nell'),('ada','Or a magpie. They do love anything shiny.','warm','nell')]),
 par(go('mina',[-1.2,-3.0],gait='walk'),go('joss',[0.4,-3.6],gait='walk'),icon('nell','question',1.6)),
 give('mina','nell'),
 convo([('mina','Miss Nell? Is this what you are looking for? It was on the flat rock.','joy','nell'),('nell','My key! Mina, you wonderful girl. I thought the whole village was lost to time.','joy','mina'),('joss','She would not let me carry it once.','joy','nell')]),
 par(act('nell','cele'),emote('nell','smile',3)),
 convo([('nell','Stand back, everyone. Time to wake up the clock.','warm','pol')]),
 go('nell',[0,8.5],gait='walk'),
 par(sfx('bell',0.2),sfx('bell',1.6),icon('pol','joy',2.0),icon('ada','joy',2.0)),
 convo([('pol','Right on time. My bread thanks you, Nell!','joy','nell')]),
],time='day',ambience='wind',music='epic',intent='Mina returns the key. Nell winds the clock and the bell rings.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the bun
S.append(scene('bun','A bun for a hero',loc('village_square',9,objects=[dict(kind='bench',at=[0,-2.5],id='bench0',yaw=0),KEYSTAND(-4,2,1.15)]),[at('mina',-1.5,-4.5,face=[0,-2.5]),at('pol',-4,0,face=[0,-2.5]),at('ada',4,-1,face=[0,-2.5]),at('joss',7,-5,face=[0,-2.5]),at('nell',5,2,face=[0,-2.5],holds='key')],props=[prop('bun','basket',-4,2,on='stand0',size=.55),prop('key','key',5,2,z=1.0,size=2.2)],steps=[
 par(take('pol','bun'),look('mina','pol',2)),
 par(go('pol',[-1.6,-3.6],gait='walk'),go('joss',[1.8,-3.8],gait='walk'),icon('joss','joy',1.8)),
 give('pol','mina'),
 convo([('pol','This one is for you, Mina. Still warm from the oven.','warm','mina'),('mina','For me? It smells like cinnamon. Thank you, Pol!','joy','pol')]),
 par(sit('mina','bench0.0',face=[0,-8]),sit('joss','bench0.1',face=[0,-8])),
 convo([('joss','Not a bad morning, Pol. Mina found a key, and I found a bench.','joy','pol'),('pol','And I found a reason to bake a bigger batch tomorrow.','warm','joss')]),
 convo([('ada','Noon on the dot, Nell. It was almost worth the fright.','warm','nell'),('nell','Never again. Tonight I tie that key to my belt with a double knot.','joy','ada')]),
 par(act('nell','laugh'),act('pol','laugh'),emote('mina','smile',3)),
 wait(.8),
],time='dusk',ambience='wind',music='warm',intent='The villagers share a bun and laugh. The clock keeps perfect time.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'rock':'Nell leaves her key behind','stopped':'The clock stops','found':'Mina finds a golden key','chime':'The key comes home','bun':'A bun for a hero'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='Nell the clock keeper leaves her key on a rock by the stream. The village clock stops, Nell searches in despair, and a little girl who found the key brings it home.'
THEME=dict(root=53,mode='major',tempo=100,motif=[(0,1),(4,.5),(7,.5),(12,1),(7,1)],motifs=dict(nell=[0,4,7],pol=[2,5,2],ada=[-3,0,-3],joss=[7,4,0],mina=[9,12,9]),palette=dict(pad=48,bass=41,pluck=46,hit=47))
FILM=dict(id='clock_key',title='The Clock Tower Key',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=4.5)
