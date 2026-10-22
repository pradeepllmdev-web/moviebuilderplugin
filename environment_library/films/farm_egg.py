"""Film 8: 'The Egg on the Farm' - a farm, a giant egg and a very lost baby dinosaur (about 4 minutes, 7 scenes, 2 people and 7 animals and dinosaurs).
Mostly pantomime: the animals (pig, cow, sheep, pug, horse, a baby raptor and a T-rex) are creatures with their own low-poly bodies and animations; they tell the story with movement and sounds, while a farmer and a child say only the few lines the story needs.
A child finds an egg, it hatches into a baby raptor who panics the farm, the child calms him with an apple, and the thunder of footsteps turns out to be his mother.
python perf_movie.py films/farm_egg.py out/egg --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='hazel',name='Farmer Hazel',species='boar',posture='tired',outfit='farmer',colors=[(.25,.4,.7),(.85,.7,.3),(.3,.2,.1)],description='the farmer in blue overalls and a straw hat'),
 dict(id='moss',name='Moss',species='cat',posture='hurried',outfit='child',colors=[(.9,.5,.3),(.95,.85,.4),(.35,.55,.4),(.4,.28,.2)],description='a small, brave child'),
 dict(id='percy',name='Percy',species='pig',posture='neutral',tint=[1.,.78,.78],description='the farm pig'),
 dict(id='clara',name='Clara',species='cow',posture='neutral',description='the farm cow'),
 dict(id='dolly',name='Dolly',species='sheep',posture='jaunty',description='a skittish sheep'),
 dict(id='biscuit',name='Biscuit',species='pug',posture='hurried',tint=[.9,.78,.55],description='the farm pug, always barking'),
 dict(id='bolt',name='Bolt',species='horse',posture='proud',description='the proud horse'),
 dict(id='zip',name='Zip',species='raptor',posture='hurried',tint=[.7,1.,.55],description='a baby raptor, hatched this morning'),
 dict(id='mama',name='Mama',species='trex',posture='tired',pace=.5,description='a very large mother'),
]
EGG=lambda x,y:prop('egg','egg',x,y,size=3.2)
STAND=lambda i,x,y,h=.45:dict(kind='pedestal',at=[x,y],id='stand%d'%i,height=h,size=.4)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- dawn on the farm
S.append(scene('dawn','A strange egg',loc('meadow',7),[at('hazel',-7,-2.6,face=[2,2]),at('moss',-9,-4.6,face=[-1.5,-6.4]),at('clara',2,3.5,face=[-6,-3]),at('percy',5.5,0.5,face=[-6,-3]),at('dolly',8,-3.2,face=[-6,-3]),at('biscuit',-4.5,-6,face=[-6,-3]),at('bolt',10,-6,face=[-6,-3])],props=[EGG(-1.5,-6.6)],steps=[
 par(sfx('moo',0.3,who='clara'),sfx('oink',0.9,who='percy'),sfx('baa',1.5,who='dolly')),
 convo([('hazel','Morning, everyone! Breakfast soon!','joy','moss')]),
 par(go('moss',[-3.2,-5.4],gait='run'),sfx('bark',0.3,who='biscuit')),
 point('moss','egg',1.6),
 par(go('hazel',[-4.6,-4.0],gait='walk')),
 convo([('moss','Farmer Hazel! Look! An egg!','joy','hazel'),('hazel','That is no hen’s egg. That is a very big egg.','concern','moss')]),
 par(sfx('sting',0.2),act('hazel','startle')),
],time='dawn',ambience='wind',music='mystery',fog=.1,extras=[],intent='Moss finds a giant egg in the field. Farmer Hazel has never seen one like it.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the egg hatches
S.append(scene('hatch','It hatched!',loc('meadow',7),[at('zip',-1.5,-6.6,face=[-1,3]),at('moss',-4.2,-4.6,face='zip'),at('hazel',-6,-2.6,face='zip'),at('clara',2,3.5,face='zip'),at('percy',5.5,0.5,face='zip'),at('dolly',8,-3.2,face=[16,-8]),at('biscuit',-3.6,-7.2,face='zip'),at('bolt',10,-6,face='zip')],props=[EGG(-0.2,-7.6)],steps=[
 par(sfx('thud',0.2),sfx('crash',0.8)),
 par(act('moss','startle'),act('hazel','startle'),act('clara','startle'),act('percy','startle')),
 par(sfx('roar',0.2,who='zip'),act('zip','jump')),
 par(run('percy',[12,8]),run('dolly',[13,-7]),run('clara',[7,7.2]),sfx('oink',0.2,who='percy'),sfx('baa',0.6,who='dolly')),
 convo([('hazel','It hatched! It is a... what is it?','concern','moss'),('moss','He is a baby dinosaur!','joy','hazel')]),
],time='day',ambience='wind',music='comic',fog=0.,intent='The egg hatches into a baby raptor. The farm animals panic.'))
# 3 ---------------------------------------------------------------------------------------------------------------- chaos
S.append(scene('chaos','Chaos on the farm',loc('meadow',7),[at('zip',-1.0,-5.6,face=[8,0]),at('percy',9.5,5.5,face='zip'),at('dolly',11,-5.8,face=[18,-8]),at('clara',9.5,4.5,face='zip'),at('biscuit',-3.2,-6.4,face='zip'),at('bolt',10,-6,face='zip'),at('hazel',-5.6,-3.0,face='zip'),at('moss',-3.4,-4.4,face='zip')],steps=[
 par(run('zip',[7,2]),run('biscuit',[3,0]),sfx('bark',0.2,who='biscuit'),sfx('roar',0.6,who='zip')),
 par(run('percy',[-8,5]),run('clara',[-10,3]),run('dolly',[-8,-3]),sfx('oink',0.1,who='percy'),sfx('moo',0.3,who='clara'),sfx('baa',0.5,who='dolly')),
 par(run('zip',[-6,4]),act('bolt','jump'),sfx('neigh',0.2,who='bolt'),run('biscuit',[-2,3])),
 par(run('zip',[-1,-4]),run('percy',[6,-2]),run('dolly',[2,6]),run('clara',[4,-4])),
 convo([('hazel','Stop! Everybody stop!','angry','moss')]),
 par(sfx('crash',0.2),act('hazel','fall')),
],time='day',ambience='wind',music='epic',fog=0.,intent='The baby raptor runs through the farm and every animal scatters. Hazel falls.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the apple
S.append(scene('apple','Just hungry',loc('meadow',8,objects=[dict(kind='pedestal',at=[-6.0,-3.0],id='stand0',height=.6,size=.25),STAND(1,2.0,-2.0,.6)]),[at('moss',-6.0,-4.2,face=[-6,-3]),at('zip',6,1,face='moss'),at('hazel',-9,-6,face='moss'),at('biscuit',-9.5,-4,face='zip')],props=[prop('apple','apple',-6.0,-3.0,on='stand0',size=1.4)],steps=[
 take('moss','apple'),
 par(look('moss','zip',1.5),emote('moss','smile',2)),
 convo([('moss','Shh. It’s okay. He is not angry. He is just hungry.','warm','hazel')]),
 par(go('moss',[1.0,-2.4],gait='walk'),go('zip',[4,-0.6],gait='walk')),
 put('moss',on='stand1'),
 par(go('moss',[-1.4,-3.4],gait='walk')),
 par(go('zip',[2.8,-1.4],gait='walk'),sfx('chomp',1.0,who='zip')),
 par(act('zip','jump'),sfx('roar',0.2,who='zip'),emote('moss','smile',3)),
 convo([('hazel','Well, I never. He is only a baby.','warm','moss'),('moss','He wants his mother.','sad','hazel')]),
],time='day',ambience='wind',music='warm',fog=0.,intent='Moss calms the baby raptor with an apple. He is just hungry, and lost.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the thunder
S.append(scene('thunder','The ground shakes',loc('hilltop',3),[at('moss',-2.8,-2.4,face=[-16,10]),at('zip',-1.6,-3.6,face=[-16,10]),at('hazel',-5,-4,face=[-16,10]),at('clara',6,-3,face=[-16,10]),at('percy',4,4,face=[-16,10]),at('mama',-22,12,face='moss')],steps=[
 par(sfx('thunder',0.2),act('hazel','startle'),act('clara','startle')),
 par(go('mama',[-12,8],gait='walk',),sfx('thunder',1.2)),
 par(run('percy',[10,6]),run('clara',[12,-4]),sfx('oink',0.1,who='percy'),sfx('moo',0.4,who='clara')),
 convo([('hazel','Run! Something big is coming!','angry','moss')]),
 par(go('mama',[-7,6],gait='walk'),sfx('roar',0.6,who='mama')),
 par(look('moss',[-7,6],2),point('hazel',[-7,6],1.2)),
],time='dusk',ambience='wind',music='tense',fog=.15,intent='The ground shakes. Something enormous walks toward the farm.'))
# 6 ---------------------------------------------------------------------------------------------------------------- reunion
S.append(scene('reunion','Mama',loc('hilltop',3),[at('moss',-2.8,-2.4,face='mama'),at('zip',-1.6,-3.6,face='mama'),at('hazel',-5.2,-4.6,face='mama'),at('mama',-8,6.4,face='moss')],steps=[
 convo([('moss','Don’t be scared, Hazel. Look at Zip.','warm','hazel')]),
 par(go('zip',[-6,5],gait='run'),sfx('roar',0.2,who='zip')),
 par(sfx('roar',0.1,who='mama'),act('mama','startle')),
 act('zip','jump'),
 go('zip',[-5.0,3.6],gait='walk'),
 par(act('moss','wave'),sfx('chime',0.5)),
 convo([('hazel','Mothers. They always find you.','warm','moss')]),
],time='dusk',ambience='wind',music='warm',fog=.1,intent='Zip runs to his mother. The farmer and the child watch them reunite.'))
# 7 ---------------------------------------------------------------------------------------------------------------- goodbye
S.append(scene('goodbye','Over the hill',loc('hilltop',3),[at('moss',-2.8,-2.4,face='mama'),at('hazel',-5.2,-4.6,face='mama'),at('mama',-8,6.4,face=[-20,14]),at('zip',-7.4,5.4,face=[-20,14]),at('percy',6,2,face='moss'),at('clara',8,-2,face='moss'),at('dolly',3,5,face='moss')],steps=[
 par(go('mama',[-24,16],gait='walk'),go('zip',[-16,9],gait='run')),
 par(act('moss','wave'),sfx('roar',0.8,who='mama')),
 par(go('percy',[-1.5,0.5],gait='walk'),go('clara',[-3.5,-1.6],gait='walk'),go('dolly',[-0.2,-1.8],gait='walk')),
 convo([('hazel','Best egg we ever had.','joy','moss'),('moss','Can we have another one?','joy','hazel')]),
 par(act('hazel','laugh'),sfx('moo',0.4,who='clara'),sfx('oink',0.8,who='percy')),
 wait(2.0),
],time='dusk',ambience='wind',music='warm',fog=0.,intent='The dinosaurs go home. The farm animals come back and the farm is quiet again.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'dawn':'A strange egg in the field','hatch':'The egg hatches!','chaos':'Chaos on the farm','apple':'A hungry baby','thunder':'Something big is coming','reunion':'Mama','goodbye':'Home'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A child finds a giant egg on the farm; it hatches into a baby raptor who panics the animals, until an apple, a lot of thunder and a very large mother bring everyone home.'
THEME=dict(root=55,mode='dorian',tempo=104,motif=[(0,1),(2,.5),(4,.5),(7,1),(4,1)],motifs=dict(hazel=[0,-3,0],moss=[4,6,4],zip=[7,6,7],mama=[-5,-7,-5]),palette=dict(pad=48,bass=43,pluck=46,hit=47))
for _c in CAST:_c.setdefault('pace',1.2)
FILM=dict(id='farm_egg',title='The Egg on the Farm',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=3.5)
