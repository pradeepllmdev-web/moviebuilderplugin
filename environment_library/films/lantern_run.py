"""Film 5: 'The Lantern Run' - a foggy night, a stolen lantern and a chase with a heart (about 5 minutes, 9 scenes, 6 characters, 3 locations).
The village's Great Lantern is to light the festival, but fog has trapped the fishing fleet at sea and the harbour beacon is broken. Dot, a fisherman's daughter, steals the lantern while the guard sleeps. The village chases her through the market to the quay, where the reason comes out - and the whole village lights the harbour instead.
Every scene has a single visible goal (guard it, steal it, chase it, explain it, light it, welcome the boats home), action instead of talking, and the clue to Dot's motive is shown before she acts.
python perf_movie.py films/lantern_run.py out/lantern --plan-only   (seconds)   or without --plan-only to build it in Blender."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from perf_dsl import *
CAST=[
 dict(id='rue',name='Captain Rue',species='bear',posture='tired',outfit='fisherman',colors=[(.2,.35,.6),(.95,.75,.12),(.2,.27,.38)],description='a worried fishing captain'),
 dict(id='pim',name='Mayor Pim',species='badger',posture='proud',outfit='mayor',colors=[(.5,.12,.2),(.9,.8,.3),(.22,.15,.1)],description='the mayor in a plum suit and top hat'),
 dict(id='dot',name='Dot',species='fox',posture='hurried',outfit='child',colors=[(.9,.55,.2),(.3,.6,.6),(.3,.3,.45),(.4,.28,.2)],description='the captain’s brave daughter'),
 dict(id='sal',name='Sal',species='wolf',posture='angry',outfit='cowboy',colors=[(.55,.2,.2),(.4,.3,.18),(.3,.38,.55),(.28,.18,.1),(.8,.6,.3)],description='the market trader, quick to shout'),
 dict(id='nell',name='Nell',species='rabbit',posture='neutral',outfit='villageress',colors=[(.3,.5,.4),(.93,.9,.85),(.42,.27,.17)],description='the baker, who wants everyone fed'),
 dict(id='ferris',name='Brother Ferris',species='heron',posture='tired',outfit='monk',colors=[(.5,.38,.25)],description='the tall guard monk who falls asleep'),
]
LANTERN=lambda x,y,on:prop('lantern','lantern',x,y,on=on,size=2.0)
STAND=lambda i,x,y,h=.8:dict(kind='pedestal',at=[x,y],id='stand%d'%i,height=h,size=.5)
S=[]
# 1 ---------------------------------------------------------------------------------------------------------------- the great lantern
S.append(scene('great_lantern','The Great Lantern',loc('village_square',9,objects=[STAND(0,2.5,-1.0)]),[at('pim',-3,1.5,face=[2.5,-1]),at('nell',-6,-3,face=[2.5,-1]),at('sal',7,2,face=[2.5,-1]),at('ferris',-8,-6,face=[2.5,-1]),at('dot',5,-6,face=[2.5,-1])],props=[LANTERN(2.5,-1.0,'stand0')],steps=[
 convo([('pim','Neighbours! Tonight the Great Lantern lights our festival!','joy','nell'),('sal','Brightest lamp in the county.','warm','pim')]),
 par(act('nell','cele'),act('sal','nod')),
 par(look('dot',[0,-25],3),emote('dot','sad',3)),
 convo([('pim','Brother Ferris, guard it until the feast.','serious','ferris'),('ferris','I never sleep on duty.','serious','pim')]),
 par(go('pim',[-16,2],gait='strut'),go('nell',[-16,-4],gait='walk'),go('sal',[16,3],gait='stomp'),go('dot',[16,-8],gait='shuffle')),
 go('ferris',[3.6,-2.8],gait='shuffle'),
],time='dusk',ambience='wind',music='warm',extras=crowd(4,[-14,-8,14,8],[2.5,-1],31),intent='The mayor will light the Great Lantern tonight. Brother Ferris guards it.'))
# 2 ---------------------------------------------------------------------------------------------------------------- the fog
S.append(scene('fog','Fog at sea',loc('harbor',4),[at('rue',-8,-3.0,face=[0,-20]),at('dot',8,-2.4,face='rue')],steps=[
 par(look('rue',[0,-22],3),emote('rue','sad',3)),
 run('dot',[-5.6,-3.0]),
 convo([('dot','Papa! The fog is thick. The boats cannot see the harbour!','concern','rue'),('rue','The old beacon cracked last week. Nothing bright enough.','sad','dot')]),
 par(emote('dot','brows',2),look('dot',[10,10],2)),
 convo([('dot','What about the Great Lantern?','concern','rue'),('rue','It belongs to the village, Dot. Not to us.','serious','dot')]),
 par(emote('dot','sad',3),look('dot',[0,-22],3)),
],time='overcast',ambience='sea',music='sad',intent='Fog traps the fishing boats. Captain Rue says the broken beacon cannot be replaced.'))
# 3 ---------------------------------------------------------------------------------------------------------------- the taking
S.append(scene('taking','Asleep on duty',loc('village_square',9,objects=[STAND(0,2.5,-1.0)]),[at('ferris',3.8,-2.6,face=[2.5,-1]),at('dot',-12,5,face=[2.5,-1])],props=[LANTERN(2.5,-1.0,'stand0')],steps=[
 par(act('ferris','fall'),sfx('thud',0.5)),
 wait(1.5),
 par(go('dot',[-2,1.6],gait='sneak'),look('dot',[3.8,-2.6],2)),
 take('dot','lantern'),
 par(act('ferris','getup')),
 convo([('ferris','Wha? Thief! Stop! Somebody stop that child!','angry','dot')]),
 run('dot',[-14,-1]),
],time='night',ambience='night',music='tense',intent='While the guard sleeps, Dot takes the lantern and runs. Ferris wakes too late.'))
# 4 ---------------------------------------------------------------------------------------------------------------- the chase
S.append(scene('chase','Stop that thief!',loc('market',6,objects=[STAND(1,-9,-1.0)]),[at('dot',-9,-2.7,face=[-9,-1]),at('sal',-20,-4.5,face=[8,-2]),at('nell',-22,-1.6,face=[8,-2]),at('ferris',-21,-7,face=[8,-2])],props=[LANTERN(-9,-1.0,'stand1')],steps=[
 take('dot','lantern'),
 par(run('dot',[2,-3.2]),run('sal',[-8,-4.2]),run('nell',[-12,-2.4]),run('ferris',[-13,-6.4])),
 convo([('sal','Stop right there, little thief!','angry','dot')]),
 par(act('nell','fall'),sfx('crash',0.4)),
 par(run('dot',[13,-3.6]),run('sal',[3,-4.2]),act('nell','getup'),run('ferris',[-3,-6])),
 convo([('nell','My cakes! Somebody catch her!','angry','sal')]),
],time='night',ambience='market',music='epic',intent='The village chases Dot through the market. Nell trips over a crate.'))
# 5 ---------------------------------------------------------------------------------------------------------------- the quay
S.append(scene('quay','Cornered on the quay',loc('harbor',4,objects=[STAND(2,9.4,-2.4)]),[at('dot',8,-3.4,face=[9.4,-2.4]),at('sal',-14,-3.8,face=[10,-3]),at('nell',-16,-2.4,face=[10,-3]),at('pim',-18,-3.2,face=[10,-3])],props=[LANTERN(9.4,-2.4,'stand2')],steps=[
 take('dot','lantern'),
 par(go('dot',[12.5,-3.6],gait='brisk'),go('sal',[2,-3.6],gait='stomp'),go('nell',[0,-2.4],gait='brisk'),go('pim',[-2,-3.0],gait='stomp')),
 convo([('sal','Give it back, child!','angry','dot'),('dot','I cannot. Not yet.','sad','sal')]),
 par(go('pim',[7.6,-3.0],gait='stomp')),
 convo([('pim','Dot! That is the village lantern! Explain yourself!','angry','dot')]),
],time='night',ambience='sea',music='tense',intent='The chase ends at the quay. Dot holds the lantern and will not give it up.'))
# 6 ---------------------------------------------------------------------------------------------------------------- the reason
S.append(scene('reason','The reason',loc('harbor',4,objects=[STAND(2,9.4,-2.4)]),[at('dot',12.2,-3.5,face=[3,-3]),at('pim',7.4,-3.0,face='dot'),at('sal',5.4,-3.6,face='dot'),at('nell',2.4,-3.8,face='dot'),at('rue',-12,-3.4,face='dot')],props=[LANTERN(11.2,-3.0,'stand2')],steps=[
 run('rue',[2.2,-3.0]),
 convo([('rue','Dot! What have you done?','concern','dot'),('dot','The boats are lost in the fog, Papa. I wanted them to see a light.','sad','rue')]),
 par(look('pim',[0,-22],3),emote('pim','concern',3)),
 convo([('pim','Fog over the whole bay. And fourteen boats out there.','concern','rue'),('nell','Oh, the poor sailors.','sad','pim')]),
 par(emote('sal','concern',2.5),act('sal','shrug')),
],time='overcast',ambience='sea',music='sad',intent='Dot explains: she took the lantern to guide the fishing boats home through the fog.'))
# 7 ---------------------------------------------------------------------------------------------------------------- lighting the harbour
S.append(scene('light','Light the harbour',loc('harbor',4,objects=[STAND(2,9.4,-2.4),STAND(3,14.5,-3.4,.7)]),[at('dot',12.2,-3.4,face=[14.5,-3.4]),at('pim',8,-3.0,face='dot'),at('rue',5,-3.4,face='dot'),at('sal',2.6,-3.9,face='dot'),at('nell',0.4,-3.8,face='dot')],props=[LANTERN(9.4,-2.4,'stand2')],steps=[
 convo([('pim','A lantern belongs where it is needed. Dot, put it on the quay stand.','warm','dot')]),
 par(take('dot','lantern')),
 par(go('dot',[13.2,-3.6],gait='shuffle')),
 put('dot',on='stand3'),
 par(sfx('chime',0.3),sfx('bell',1.4),emote('rue','smile',3),emote('pim','smile',3)),
 convo([('sal','Look at that glow. Like a small sun.','warm','dot')]),
 par(look('rue',[-4,-22],3),look('nell',[-4,-22],3),look('sal',[-4,-22],3)),
 wait(1.5),
],time='night',ambience='sea',music='warm',intent='Everyone agrees to place the lantern at the quay to guide the boats.'))
# 8 ---------------------------------------------------------------------------------------------------------------- the boats come home
S.append(scene('boats','The boats come home',loc('harbor',4,objects=[STAND(3,14.5,-3.4,.7)]),[at('rue',9,-3.0,face=[-4,-22]),at('dot',12,-3.5,face=[-4,-22]),at('pim',7,-2.4,face=[-4,-22]),at('nell',5.2,-3.6,face=[-4,-22]),at('sal',3.2,-2.6,face=[-4,-22])],props=[LANTERN(14.5,-3.4,'stand3')],steps=[
 par(look('rue',[-4,-22],3),look('dot',[-4,-22],3)),
 sfx('bell',0.4),
 convo([('dot','Papa! Look! A mast!','joy','rue'),('rue','Fourteen boats, and every one of them following that light!','joy','dot')]),
 par(act('rue','cele'),act('dot','cele'),act('nell','cele'),act('sal','cele'),act('pim','cele')),
 sfx('bell',0.4),
 wait(1.5),
],time='night',ambience='sea',music='epic',extras=crowd(8,[-4,-10,16,-1],[0,-6],81),intent='The fishing fleet follows the lantern into the harbour. Everyone is saved.'))
# 9 ---------------------------------------------------------------------------------------------------------------- festival at the quay
S.append(scene('festival','Festival at the quay',loc('harbor',4,objects=[STAND(3,14.5,-3.4,.7)]),[at('pim',8,-3.0,face='dot'),at('dot',12,-3.4,face='rue'),at('rue',10,-2.4,face='dot'),at('nell',4.8,-3.6,face='pim'),at('sal',3,-2.6,face='pim'),at('ferris',-3,-3.2,face='pim')],props=[LANTERN(14.5,-3.4,'stand3')],steps=[
 par(go('ferris',[5.6,-2.6],gait='brisk')),
 convo([('pim','Neighbours! The festival is moved to the quay tonight!','joy','nell'),('nell','I will fetch every cake in the village.','joy','pim')]),
 convo([('pim','To Dot, who stole the lantern and saved the fleet!','joy','dot'),('ferris','And to me, who was asleep for all of it.','joy','pim'),('sal','Especially you.','joy','ferris')]),
 par(act('dot','cele'),act('rue','laugh'),act('nell','cele')),
 par(emote('dot','smile',4),emote('rue','smile',4)),
 wait(2.5),
],time='night',ambience='crowd',music='bright',extras=crowd(10,[-4,-10,16,-1],[2,-4],91),intent='The village celebrates at the harbour. Everyone toasts Dot.'))
INTENT={s['id']:s['intent'] for s in S}
OBJECTIVE={'great_lantern':'The Great Lantern lights the festival','fog':'The boats are lost in the fog','taking':'Who will take the lantern?','chase':'Stop that thief!','quay':'Cornered on the quay','reason':'Why did she take it?','light':'Light the harbour','boats':'Will the boats find the way?','festival':'Home safe'}
for _s in S:_s['objective']=OBJECTIVE[_s['id']]
LOGLINE='A fisherman’s daughter steals the village’s Great Lantern during a foggy festival night, and the chase that follows lights the way home for fourteen lost boats.'
THEME=dict(root=50,mode='dorian',tempo=104,motif=[(0,1),(3,1),(4,.5),(3,.5),(7,1.5)],motifs=dict(rue=[0,-3,0],pim=[0,4,7],dot=[7,6,4],sal=[0,0,-2],nell=[4,5,4],ferris=[-3,-5,-3]),palette=dict(pad=48,bass=43,pluck=52,hit=47))
for _c in CAST:_c.setdefault('pace',1.2)
FILM=dict(id='lantern_run',title='The Lantern Run',cast=CAST,scenes=S,logline=LOGLINE,theme=THEME,target_minutes=5)
