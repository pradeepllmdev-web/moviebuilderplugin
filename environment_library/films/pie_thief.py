"""Film 3: 'The Pie Thief' - a short, easy-to-follow village story (about 7 minutes, 12 scenes, 6 characters, 4 locations).
Tilda the baker brings a giant cherry pie to the village contest. It vanishes. Everyone blames the blacksmith until small footprints lead to a shepherd's hill, where a boy has given the pie to his starving grandfather. The baker forgives, the village shares a feast, and the boy becomes her apprentice.
One goal per scene, big readable actions (carry, hide, point, follow, hand over, hug) and a printed objective on every scene, so the plot is clear with the sound off.
python perf_movie.py films/pie_thief.py out/pie --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='tilda',name='Tilda',species='lion',posture='jaunty',outfit='cook',colors=[(.96,.96,.94),(.85,.35,.4),(.3,.3,.38),(.25,.18,.12)],description='the baker, proud of her cherry pie'),
 dict(id='orin',name='Mayor Orin',species='wolf',posture='proud',outfit='mayor',colors=[(.14,.17,.32),(.75,.1,.12),(.25,.15,.1)],description='the mayor in a blue suit and top hat'),
 dict(id='gus',name='Gus',species='boar',posture='angry',outfit='blacksmith',colors=[(.6,.6,.62),(.38,.24,.12),(.25,.2,.15),(.3,.3,.36)],description='the big blacksmith, always hungry'),
 dict(id='pip',name='Pip',species='mouse',posture='hurried',outfit='child',colors=[(.3,.55,.85),(.95,.8,.3),(.4,.6,.4),(.45,.3,.2)],description='a small boy with a secret'),
 dict(id='fen',name='Old Fen',species='elder',posture='hunched',outfit='shepherd',colors=[(.55,.45,.32),(.7,.2,.2),(.38,.3,.22),(.25,.18,.1)],description='Pip’s grandfather, a thin old shepherd'),
 dict(id='rosa',name='Rosa',species='rabbit',posture='neutral',outfit='villageress',colors=[(.75,.3,.3),(.93,.9,.85),(.42,.27,.17)],description='the baker’s friend, who notices small things'),
]
PIE=lambda x,y,on=None,z=None:prop('pie','pie',x,y,on=on,z=z)
STAND=lambda x,y:dict(kind='pedestal',at=[x,y],id='stand0',height=.7,size=.4)
LOW=lambda i,x,y,h=.8:dict(kind='pedestal',at=[x,y],id='stand%d'%i,height=h,size=.4)
BENCH=dict(kind='bench',at=[-1.5,-1.0],id='bench0',yaw=0)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the pie
S.append(scene('bakery','The giant pie',loc('room',2),[at('tilda',-3,-2.6,face='table'),at('rosa',3.3,-2.4,face='table')],props=[PIE(1.0,-.45,on='table')],steps=[
 par(go('tilda',[1.0,-1.2],gait='walk'),look('rosa','table',2)),
 take('tilda','pie'),
 convo([('rosa','Tilda! It is the biggest pie I have ever seen!','joy','tilda'),('tilda','Cherries and cream. Three days of baking.','warm','rosa'),
  ('rosa','And today the mayor tastes it?','joy','tilda'),('tilda','At noon. And I will win the Golden Spoon!','joy','rosa')]),
 par(act('tilda','joy'),emote('rosa','smile',3)),
 par(go('tilda',[0,-3.2],gait='strut'),go('rosa',[1.2,-3.2],gait='walk')),
],time='day',ambience='hall',music='bright',intent='A baker proudly shows her giant cherry pie. Today she will try to win the Golden Spoon.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the contest
S.append(scene('contest','The contest table',loc('village_square',3,objects=[STAND(2.5,-1.0),LOW(1,-8,-4.4)]),[at('orin',-4,1.5,face=[2.5,-1]),at('gus',9,3,face=[2.5,-1]),at('tilda',-9,-5,face=[2.5,-1]),at('rosa',-7.5,-6,face=[2.5,-1])],props=[PIE(-8,-4.4,on='stand1')],steps=[
 par(take('tilda','pie'),look('orin','tilda',2)),
 convo([('orin','Friends of Applewick! At noon the Golden Spoon goes to the finest pie.','joy','gus'),('gus','Finest pie, finest pie. My stomach has been rumbling since breakfast.','concern','orin')]),
 par(go('tilda',[1.2,-2.6],gait='strut'),go('rosa',[0,-3],gait='walk')),
 put('tilda',on='stand0'),
 convo([('orin','Magnificent! Nobody touch it until noon.','warm','gus'),('gus','Who, me? I would never.','concern','orin')]),
],time='day',ambience='wind',music='bright',extras=crowd(6,[-14,-8,14,8],[2.5,-1],21),intent='The pie is displayed in the village square. Everyone must wait until noon.'))
# 3 ---------------------------------------------------------------------------------------------------------------- left alone
S.append(scene('alone','Alone with the pie',loc('village_square',3,objects=[STAND(2.5,-1.0)]),[at('tilda',0.5,-2.0,face=[2.5,-1]),at('rosa',-1.5,-3.2,face=[2.5,-1]),at('gus',5.5,0.8,face=[2.5,-1]),at('orin',-4,2,face=[0,0])],props=[PIE(2.5,-1.0,on='stand0')],steps=[
 convo([('tilda','Oh no. I forgot the red ribbon! I will be back in a moment.','concern','rosa'),('orin','Rosa! I need help with the judges chairs.','serious','rosa')]),
 par(run('tilda',[-10,-8]),go('rosa',[-5,3],gait='brisk'),go('orin',[-9,5],gait='walk')),
 par(go('gus',[3.6,-0.6],gait='walk'),emote('gus','smile',3)),
 convo([('gus','Cherries. Warm cherries. Just one little sniff.','warm','gus')]),
 sfx('clang',0.2),
 convo([('orin','Gus! Your anvil is ringing! Customers!','angry','gus')]),
 act('gus','shrug'),
 go('gus',[12,2],gait='stomp'),
 wait(1.0),
],time='day',ambience='wind',music='mystery',intent='Everyone leaves the pie alone for a moment. Gus is tempted, but his anvil calls him away.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the taking
S.append(scene('taking','A small thief',loc('village_square',3,objects=[STAND(2.5,-1.0)]),[at('pip',-6,5,face=[2.5,-1])],props=[PIE(2.5,-1.0,on='stand0')],steps=[
 convo([('pip','Grandfather has not eaten for two days. Forgive me, Tilda.','sad','pip')]),
 par(go('pip',[0,1.5],gait='sneak'),look('pip',[-3,0],1)),
 par(look('pip',[6,0],1.2),look('pip',[-4,-4],1.2)),
 take('pip','pie'),
 par(look('pip',[-8,2],1),act('pip','startle')),
 run('pip',[14,-3]),
],time='day',ambience='wind',music='tense',intent='Little Pip secretly takes the pie. He has a reason: his grandfather is hungry.'))
# 5 ---------------------------------------------------------------------------------------------------------------- gone
S.append(scene('gone','The pie is gone',loc('village_square',3,objects=[STAND(2.5,-1.0)]),[at('tilda',-10,-8,face=[2.5,-1])],props=[],steps=[
 par(run('tilda',[1.6,-2.6])),
 par(act('tilda','startle'),emote('tilda','sad',3)),
 convo([('tilda','No. No, no, no. My pie! My Golden Spoon pie!','sad','tilda')]),
 go('tilda',[2.4,-1.8],gait='shuffle'),
 act('tilda','argue'),
 convo([('tilda','Help! Somebody took my pie!','angry','tilda')]),
],time='day',ambience='wind',music='sad',intent='Tilda returns with the ribbon. The pie has vanished.'))
# 6 ---------------------------------------------------------------------------------------------------------------- blame
S.append(scene('blame','Who took it?',loc('village_square',4,objects=[STAND(2.5,-1.0)]),[at('tilda',1.0,-2.5,face=[2.5,-1]),at('rosa',-5,-3,face='tilda'),at('orin',-6,2,face='tilda'),at('gus',10,3,face=[2.5,-1])],steps=[
 par(go('rosa',[0,-3],gait='brisk'),go('orin',[-1,0.5],gait='walk')),
 convo([('orin','Gus! You were sniffing the pie. I heard it from the anvil.','angry','gus'),('gus','I only sniffed! I would never take it.','angry','orin')]),
 par(go('gus',[4.5,-0.5],gait='stomp')),
 convo([('tilda','Nobody else loves pie like you, Gus.','sad','gus'),('gus','This is a terrible thing to say about a blacksmith!','angry','tilda')]),
 par(go('rosa',[2.8,-1.6],gait='walk'),look('rosa',[2.5,-2.4],2)),
 point('rosa',[2.5,-2.4],1.4),
 convo([('rosa','Wait. Look. Small footprints in the dust. Little ones. Going east.','concern','orin'),('gus','Small! Do I look small?','concern','rosa'),
  ('orin','Follow them! The contest is at noon.','serious','tilda')]),
],time='day',ambience='wind',music='tense',intent='Everyone blames Gus, until Rosa notices small footprints leading away.',extras=crowd(4,[-14,-8,14,8],[2.5,-1],7)))
# 7 ---------------------------------------------------------------------------------------------------------------- tracking
S.append(scene('tracking','Following the footprints',loc('meadow',5),[at('rosa',-8,-6,face=[8,4]),at('tilda',-10,-7.5,face=[8,4]),at('orin',-12,-6,face=[8,4]),at('gus',-13,-8,face=[8,4])],steps=[
 par(go('rosa',[-2,-2],gait='walk'),go('tilda',[-4,-3.5],gait='brisk'),go('orin',[-5,-2],gait='walk'),go('gus',[-6.5,-3.5],gait='stomp')),
 point('rosa',[-1,-1],1.3),
 par(look('tilda',[-3,-2],2)),
 convo([('rosa','Here. A cherry crumb.','concern','tilda'),('tilda','He ate my pie on the way?','angry','rosa'),('orin','A thief with small feet and a big appetite.','serious','tilda')]),
 par(go('rosa',[5,3],gait='brisk'),go('tilda',[4,2],gait='brisk'),go('orin',[3,3.5],gait='walk'),go('gus',[2,2],gait='stomp')),
 convo([('gus','Hungry thieves go uphill. I would.','warm','orin'),('rosa','The prints climb the shepherd’s hill.','serious','tilda')]),
],time='day',ambience='wind',music='mystery',intent='The four follow the footprints and cherry crumbs out of the village and toward the shepherd’s hill.'))
# 8 ---------------------------------------------------------------------------------------------------------------- the hungry grandfather
S.append(scene('hill','Grandfather’s hill',loc('hilltop',3,objects=[BENCH,LOW(2,4.2,3.6,.7)]),[at('fen',-4,-3,face=[-1.5,-1]),at('pip',5,4,face=[-4,-3])],props=[PIE(4.2,3.6,on='stand2')],steps=[
 par(take('pip','pie'),go('fen',[-1.5,-1.0],gait='shuffle')),
 sit('fen','bench0.0',face='pip'),
 par(go('pip',[0.2,-1.0],gait='brisk')),
 give('pip','fen'),
 convo([('pip','Grandfather, eat. It is a cherry pie.','warm','fen'),('fen','Pip. Where did you get such a beautiful pie?','concern','pip')]),
 par(emote('pip','sad',3),act('pip','kneel')),
 convo([('pip','From the village. It was for the contest. You were so hungry.','sad','fen'),('fen','Oh, little one. A hungry belly does not make a pie ours.','serious','pip')]),
],time='day',ambience='wind',music='sad',intent='Pip gives the pie to his hungry grandfather, who realises it belongs to someone else.'))
# 9 ---------------------------------------------------------------------------------------------------------------- caught
S.append(scene('caught','Caught',loc('hilltop',3,objects=[BENCH]),[at('fen',-2.8,-2.2,face=[6,6]),at('pip',-1.2,-2.8,face=[6,6]),at('tilda',9,7,face=[0,0]),at('rosa',11,6,face=[0,0]),at('orin',12,8,face=[0,0]),at('gus',10,9,face=[0,0])],steps=[
 par(go('tilda',[3.4,2.4],gait='stomp'),go('rosa',[4.4,3.4],gait='brisk'),go('orin',[5.4,3.6],gait='walk'),go('gus',[6.4,4.2],gait='stomp')),
 par(act('pip','startle'),emote('fen','concern',3)),
 point('tilda','pip',1.3),
 convo([('tilda','My pie! Who took my Golden Spoon pie?','angry','pip')]),
 par(go('pip',[-1.0,-0.2],gait='walk'),turn('fen','tilda')),
 convo([('pip','It was me. I am sorry.','sad','tilda'),('fen','He took it for me. I have eaten nothing for three days. My sheep ran off and I could not leave the hill.','sad','tilda')]),
 par(act('gus','shrug'),emote('tilda','concern',3)),
 convo([('gus','And I was nearly arrested for pie.','concern','orin')]),
],time='day',ambience='wind',music='sad',intent='The searchers arrive. Pip admits it, and old Fen explains he has been starving.'))
# 10 --------------------------------------------------------------------------------------------------------------- forgiveness
S.append(scene('forgive','Forgiveness',loc('hilltop',3,objects=[BENCH]),[at('fen',-2.8,-2.2,face='tilda'),at('pip',-1.2,-2.8,face='tilda'),at('tilda',2.8,2.0,face='pip'),at('rosa',4.2,2.8,face='tilda'),at('orin',5.2,3.2,face='tilda'),at('gus',6.2,3.8,face='fen')],steps=[
 par(go('tilda',[0.8,-0.5],gait='shuffle'),emote('tilda','sad',3)),
 convo([('tilda','Three days without food. And you still left half for the sheep.','warm','fen'),('fen','Only half. The rest is for Pip.','warm','tilda')]),
 par(act('tilda','kneel'),emote('pip','smile',3)),
 convo([('tilda','Pip, a pie is for eating. Next time, just ask.','warm','pip'),('pip','Yes, Miss Tilda.','joy','tilda')]),
 par(act('rosa','joy'),act('orin','nod')),
 convo([('gus','I will fetch your sheep, old man. They are afraid of nothing but my hammer.','joy','fen'),('orin','Then come to the square, everyone! The contest goes on!','joy','tilda')]),
],time='day',ambience='wind',music='warm',intent='Tilda forgives Pip. Gus offers to find Fen’s sheep, and everyone invites Fen to the square.'))
# 11 --------------------------------------------------------------------------------------------------------------- the feast
S.append(scene('feast','The Golden Spoon',loc('village_square',3,objects=[STAND(2.5,-1.0)]),[at('orin',-3,-1,face=[2.5,-1]),at('tilda',0.2,-3.2,face='orin'),at('pip',-1.2,-4.4,face='orin'),at('fen',-1,-4,face='orin'),at('rosa',-4.5,-5.2,face='orin'),at('gus',-6,-2,face='orin')],props=[PIE(2.5,-1.0,on='stand0')],steps=[
 par(go('orin',[4.6,-4.6],gait='strut')),
 convo([('orin','Neighbours! This year the Golden Spoon does not go to the biggest pie.','joy','tilda'),('orin','It goes to the kindest baker. Tilda, who forgave a hungry boy.','joy','tilda')]),
 par(act('tilda','bow'),act('pip','joy'),act('rosa','joy'),act('gus','laugh')),
 convo([('gus','And I get the first slice, because I was blamed!','joy','orin'),('tilda','The first slice is for Old Fen.','warm','gus')]),
 par(go('fen',[2.0,-1.8],gait='shuffle'),emote('fen','smile',3)),
],time='day',ambience='wind',music='bright',extras=crowd(8,[-14,-8,14,8],[2.5,-1],31),intent='The mayor gives the Golden Spoon to Tilda for her kindness, and Old Fen is served the first slice.'))
# 12 --------------------------------------------------------------------------------------------------------------- apprentice
S.append(scene('apprentice','A new apprentice',loc('village_square',6,objects=[dict(kind='bench',at=[-4,-3.5],id='bench_x')]),[at('tilda',-1.5,-1.5,face='pip'),at('pip',0.8,-1.2,face='tilda'),at('fen',-5.6,-2.4,face='pip'),at('rosa',4,-3,face='pip'),at('gus',7,-1,face='pip')],steps=[
 convo([('tilda','Pip, I need a helper in the bakery. The ovens are warm and the cherries are free.','warm','pip'),('pip','Me? An apprentice baker?','joy','tilda'),('tilda','Every day. And the first lesson: always share.','warm','pip')]),
 par(act('pip','joy'),act('fen','laugh'),act('rosa','joy')),
 convo([('fen','Now that is a pie worth stealing.','joy','tilda'),('gus','Never again. I am keeping my nose to the anvil.','joy','fen')]),
 par(emote('tilda','smile',4),emote('pip','smile',4)),
 wait(2.5),
],time='dusk',ambience='wind',music='warm',intent='Tilda makes Pip her apprentice. The village is happy again.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'bakery':'Today: win the Golden Spoon','contest':'Today: win the Golden Spoon','alone':'Noon is near','taking':'Who took the pie?','gone':'Who took the pie?','blame':'Who took the pie?','tracking':'Follow the footprints','hill':'Why was it taken?','caught':'Why was it taken?','forgive':'Forgive or punish?','feast':'The Golden Spoon','apprentice':'A new beginning'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A baker’s giant pie vanishes before the village contest, and the trail of small footprints leads to a very different kind of thief.'
THEME=dict(root=57,mode='major',tempo=96,motif=[(0,1),(2,1),(4,1),(2,.5),(0,1.5)],motifs=dict(tilda=[0,2,4],orin=[0,4,7],gus=[0,-3,0],pip=[7,6,4],fen=[2,0,-1],rosa=[4,5,4]),palette=dict(pad=48,bass=45,pluck=52,hit=47))
for _c in CAST:_c.setdefault('pace',1.15)
FILM=dict(id='pie_thief',title='The Pie Thief',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=6.5)
