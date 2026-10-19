"""Blender script: 'The Spell Duel' - on a moonlit mage tower Leo and a rival mage trade five homing spells; Leo dodges two, the rival blocks one and dodges one, and Leo's shield turns the last spell back on the rival (about 40 s).

blender -b --disable-autoexec --python duel_scene.py -- <ship_assets_dir> <out.blend>

Technique: HOMING PROJECTILES AND A DODGE PLANNER. Each spell is simulated before anything is keyed: it leaves the caster's hand at 13 m/s and steers toward the target's current chest with a turn-rate limit of 2.2 rad/s.
For a dodge the planner tries start times (and, if needed, a longer sidestep) and keeps the one that gives the smallest miss of at least 0.75 m, so every dodge is a near miss and the timing is never hand-tuned. For a block the
shield disc is raised to meet the spell at the moment of impact; for the final exchange the spell is reflected from that point back at the caster with its own homing flight and hits. Casting is an IK arm thrust toward the target.
Audit: miss distances, block contact, the reflected hit, cast arm reach and grip, persistence, camera visibility. Clips: idle, dodge, block, fall, lie, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('duel');PI=math.pi;smooth=kit.smooth;MG=w2.MAGE;rnd=random.Random(30)
S.load_env('mage_tower')
LB=Vector((MG['leo'][0],MG['leo'][1],0));RB=Vector((MG['rival'][0],MG['rival'][1],0));CHEST=Vector((0,0,1.15))
V=13.;WMAX=2.2;DTS=1/48.
EX=[('R','dodge'),('L','shield'),('R','dodge'),('L','dodge'),('R','reflect')];T_CAST0=5.0;GAP=5.6
# ---------------------------------------------------------------------------------------------------------- state of the two fighters (dodges are planned below)
ACT={'L':[],'R':[]}    # sidesteps: (t0, dy)
def off(who,t):
 y=0.
 for (t0,dy) in ACT[who]:
  u=t-t0
  if u<0:continue
  if u<.5:y+=dy*smooth(u/.5)
  elif u<1.0:y+=dy
  elif u<1.8:y+=dy*(1-smooth((u-1.0)/.8))
 return y
HIT_FALL={'t':None}
def pos_of(who,t):
 base=LB if who=='L' else RB;p=Vector((base.x,base.y+off(who,t),0))
 if who=='R' and HIT_FALL['t'] is not None and t>HIT_FALL['t']:p.x+=.9*smooth((t-HIT_FALL['t'])/.6)
 return p
def chest(who,t):return pos_of(who,t)+CHEST
# ---------------------------------------------------------------------------------------------------------- spell flight
def fly(origin,t0,target_fn,speed=V,wmax=WMAX,hit_r=.55,tmax=2.6,stop_on_hit=True):
 pos=Vector(origin);d=(target_fn(t0)-pos).normalized();tr=[(t0,Vector(pos))];t=t0;best=(1e9,t0);hit=None
 while t<t0+tmax:
  want=(target_fn(t)-pos).normalized();ang=math.acos(max(-1,min(1,d.dot(want))))
  if ang>1e-6:
   k=min(1.,wmax*DTS/ang);d=(d*(1-k)+want*k).normalized()
  pos=pos+d*speed*DTS;t+=DTS;tr.append((t,Vector(pos)));dist=(pos-target_fn(t)).length
  if dist<best[0]:best=(dist,t)
  if dist<hit_r and stop_on_hit:hit=t;break
  if pos.length>MG['r']+3:break
 return tr,hit,best
cast_info=[];refl=None
for k,(who,kind) in enumerate(EX):
 tc=T_CAST0+GAP*k;d_,tg_='L' if who=='L' else 'R','R' if who=='L' else 'L'
 # the casting hand: shoulder (offset from the root) pushed along the aim
 cast_info.append(dict(k=k,caster=who,defender=tg_,t=tc,kind=kind))
SHOULDER_UP=1.13
def hand_origin(who,t,aim,thrust):
 p=pos_of(who,t);sh=p+Vector((0,-.24 if who=='L' else .24,SHOULDER_UP));return sh+aim*.42*thrust+Vector((0,0,.06))
for ci in cast_info:
 who,tg_,tc=ci['caster'],ci['defender'],ci['t']
 aim=(chest(tg_,tc)-(pos_of(who,tc)+Vector((0,0,SHOULDER_UP)))).normalized();ci['aim']=aim;origin=hand_origin(who,tc,aim,1.)
 if ci['kind']=='dodge':
  best=None
  for dyabs in (1.9,2.6):
   sgn=1 if ci['k']%2==0 else -1;dy=sgn*dyabs;ACT_save=list(ACT[tg_])
   for td in np.arange(tc+.05,tc+.95,.04):
    ACT[tg_]=ACT_save+[(td,dy)];tr,hit,bst=fly(origin,tc,lambda t,tg=tg_:chest(tg,t))
    if hit is None and bst[0]>=.75:
     score=bst[0]
     if best is None or score<best[0]:best=(score,td,dy)
   ACT[tg_]=ACT_save
   if best:break
  if best is None:print('NO DODGE for exchange',ci['k']);best=(0,tc+.3,1.9)
  ACT[tg_].append((best[1],best[2]));ci['dodge']=(best[1],best[2],best[0])
 tr,hit,bst=fly(origin,tc,lambda t,tg=tg_:chest(tg,t),stop_on_hit=(ci['kind']!='dodge'));ci['traj']=tr;ci['hit']=hit;ci['best']=bst;ci['origin']=origin
 ci['impact']=hit if hit is not None else bst[1]
 if ci['kind']=='reflect' and hit is not None:
  th=hit;ph=tr[-1][1];rt,rh,rb=fly(ph,th,lambda t:chest('R',t),speed=16.,wmax=4.0,hit_r=.5);ci['rtraj']=rt;ci['rhit']=rh;HIT_FALL['t']=rh
print('PLAN',[(ci['k'],ci['kind'],round(ci['t'],1),'hit' if ci['hit'] else 'miss %.2f'%ci['best'][0]) for ci in cast_info],'reflect hit at',HIT_FALL['t'])
T_END=(HIT_FALL['t'] or cast_info[-1]['impact'])+7.;S.clock(T_END);seconds=S.seconds
# ---------------------------------------------------------------------------------------------------------- characters
leo=S.character('Leo',S.params['hero_tint']);riv=S.character('Rival',(.55,.35,.7));CH={'L':leo,'R':riv}
IKs={};TGs={}
for who,ch in CH.items():IKs[who],TGs[who]=S.ik(ch)
CLIPS={'L':[],'R':[]}
for who in ('L','R'):
 segs=[];prev=0.
 events=[]
 for ci in cast_info:
  if ci['defender']==who:
   if ci['kind']=='dodge':td,dy,_=ci['dodge'];events.append((td-.15,td+1.3,'dodge'))
   else:events.append((ci['impact']-.5,ci['impact']+.9,'block'))
 if who=='R' and HIT_FALL['t']:events.append((HIT_FALL['t']-.05,HIT_FALL['t']+1.6,'fall'));events.append((HIT_FALL['t']+1.6,S.seconds,'lie'))
 if who=='L':events.append((HIT_FALL['t']+1.0,S.seconds,'cele'))
 events.sort();cur=0.
 for a,b,c in events:
  if a>cur+.1:segs.append((cur,a,'idle',1.))
  if b-a>.1:segs.append((a,b,c,1.))
  cur=max(cur,b)
 if cur<S.seconds:segs.append((cur,S.seconds,'idle',1.))
 S.play(CH[who],segs)
HEAD={'L':PI/2,'R':3*PI/2}
for f in S.keys():
 t=(f-1)/S.fps
 for who,ch in CH.items():
  p=pos_of(who,t);ch['root'].location=p;ch['root'].rotation_euler=(0,0,HEAD[who]);ch['root'].keyframe_insert('location',frame=f);ch['root'].keyframe_insert('rotation_euler',frame=f)
# casting arm: charge, thrust at the cast, relax
def thrust(ci,t):
 tc=ci['t'];return .3+.7*smooth((t-(tc-.45))/.4) if t<tc+.2 else 1.-.7*smooth((t-(tc+.4))/.5)
def cast_w(ci,t):tc=ci['t'];return smooth((t-(tc-.7))/.4)*(1-smooth((t-(tc+.7))/.5))
for f in S.keys():
 t=(f-1)/S.fps
 for who in ('L','R'):
  w=0.;tgt=None
  for ci in cast_info:
   if ci['caster']==who:
    cw=cast_w(ci,t)
    if cw>w:w=cw;tgt=hand_origin(who,t,ci['aim'],thrust(ci,t))
  if tgt is None:tgt=pos_of(who,t)+Vector((0,.24 if who=='R' else -.24,.9))
  TGs[who]['RH'].location=tgt;TGs[who]['RH'].keyframe_insert('location',frame=f);IKs[who]['RH'].influence=w;IKs[who]['RH'].keyframe_insert('influence',frame=f)
  TGs[who]['LH'].location=(0,0,0);IKs[who]['LH'].influence=0.;IKs[who]['LH'].keyframe_insert('influence',frame=f)
gaz={}
for who,ch in CH.items():
 gz=S.gaze(ch,(1,0,0) if who=='L' else (-1,0,0));gaz[who]=gz
 for f in S.keys():
  t=(f-1)/S.fps;o='R' if who=='L' else 'L';gz.location=chest(o,t)+Vector((0,0,.4));gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- spells, shields, bursts
def bolt_objects(name,color):
 core=S.prim('sphere','SparkBolt'+name,(0,0,0),color,scale=(.001,.001,.001),emit=9.,subdivisions=2);trail=[S.prim('sphere','SparkTrail%s_%d'%(name,i),(0,0,0),color,scale=(.001,.001,.001),emit=6.,subdivisions=1) for i in range(8)];return core,trail
def traj_at(tr,t):
 if t<tr[0][0] or t>tr[-1][0]:return None
 i=min(len(tr)-1,int((t-tr[0][0])/DTS));return tr[i][1]
RCOL=(.75,.3,1.);LCOL=(1.,.8,.3)
BOLTS=[]
for ci in cast_info:
 col=RCOL if ci['caster']=='R' else LCOL;core,trail=bolt_objects('%d'%ci['k'],col);BOLTS.append((ci['traj'],core,trail))
 if ci.get('rtraj'):c2,t2=bolt_objects('%dr'%ci['k'],(1,.95,.7));BOLTS.append((ci['rtraj'],c2,t2))
for tr,core,trail in BOLTS:
 for f in S.keys():
  t=(f-1)/S.fps;p=traj_at(tr,t)
  if p is None:core.location=tr[0][1];sc=.001
  else:
   core.location=p;u=(t-tr[0][0]);sc=.17*min(1,u*8)
  core.scale=(sc,sc,sc);core.keyframe_insert('location',frame=f);core.keyframe_insert('scale',frame=f)
  for i,tp in enumerate(trail):
   q=traj_at(tr,t-.03*(i+1))
   if q is None or p is None:tp.location=tr[0][1];ss=.001
   else:tp.location=q;ss=.15*(1-i/9.)
   tp.scale=(ss,ss,ss);tp.keyframe_insert('location',frame=f);tp.keyframe_insert('scale',frame=f)
BURST=[]
for ci in cast_info:
 tr=ci['traj'];b=S.prim('sphere','SparkBurst%d'%ci['k'],tr[-1][1],(1,.9,.7),scale=(.001,.001,.001),emit=8.,subdivisions=2);BURST.append((b,tr[-1][1],tr[-1][0]))
 if ci.get('rtraj'):b2=S.prim('sphere','SparkBurst%dr'%ci['k'],ci['rtraj'][-1][1],(1,.95,.7),scale=(.001,.001,.001),emit=9.,subdivisions=2);BURST.append((b2,ci['rtraj'][-1][1],ci['rtraj'][-1][0]))
for b,p,te in BURST:
 for f in S.keys():
  t=(f-1)/S.fps;u=(t-te)/.7;sc=(.001+1.1*smooth(min(1,u*2))*(1-smooth(max(0,u-.4)/.6))) if 0<=u<=1.0 else .001
  b.location=p;b.scale=(sc,sc,sc);b.keyframe_insert('scale',frame=f);b.keyframe_insert('location',frame=f)
SHIELD={}
for who in ('L','R'):SHIELD[who]=S.prim('sphere','SparkShield'+who,(0,0,0),(.4,.8,1.),scale=(.001,.001,.001),emit=2.5,subdivisions=2)
for who,sh in SHIELD.items():
 spans=[(ci['t']+.05,ci['impact']+.45,ci) for ci in cast_info if ci['defender']==who and ci['kind'] in ('shield','reflect')]
 for f in S.keys():
  t=(f-1)/S.fps;sc=.001;loc=chest(who,t)
  for (a,b,ci) in spans:
   if a<=t<=b:
    u=smooth((t-a)/.25)*(1-smooth((t-(b-.2))/.2));sc=max(sc,.001+u);d=(ci['origin']-chest(who,t)).normalized();loc=chest(who,t)+d*.8;sh.rotation_euler=d.to_track_quat('Z','Y').to_euler()
  sh.location=loc;sh.scale=(sc*.9,sc*.9,sc*.07);sh.keyframe_insert('location',frame=f);sh.keyframe_insert('scale',frame=f);sh.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('tower',0,T_CAST0-1.6,'wide')];last=cuts[0][2]
for ci in cast_info:
 tc=ci['t'];ti=ci['impact']
 for a,b,kind in ((tc-1.5,tc+.45,'cast%d'%ci['k']),(tc+.45,ti-.2,'bolt%d'%ci['k']),(ti-.2,ti+1.5,'react%d'%ci['k'])):
  a=max(a,last)
  if b-a<.35:continue
  cuts.append((kind,a,b,kind));last=b
if HIT_FALL['t'] and HIT_FALL['t']>last:cuts.append(('hit',last,HIT_FALL['t']+1.5,'hit'));last=HIT_FALL['t']+1.5
if S.seconds-last>.8:cuts.append(('victory',last,S.seconds,'end'))
def pos_(kind,t,u):
 pl=pos_of('L',t);pr=pos_of('R',t)
 if kind=='wide':return Vector((-3+4*u,-17,5.5)),Vector((0,0,1.5)),24
 if kind=='end':return Vector((-9,-6,2.2)),pl+Vector((.0,0,1.3)),32
 k=int(''.join(c for c in kind if c.isdigit())[:1] or 0);ci=cast_info[k];who=ci['caster'];df=ci['defender']
 if kind.startswith('cast'):
  c=pos_of(who,t);sgn=-1 if who=='L' else 1;return c+Vector((-2.4*sgn,-1.5,1.6)),chest(df,t),34
 if kind.startswith('bolt'):
  p=traj_at(ci['traj'],t) or ci['traj'][-1][1];return Vector((p.x*.2,-8.2,2.2)),p,30
 if kind.startswith('react'):
  d=pos_of(df,t);return d+Vector((0,-3.4,1.5)),chest(df,t),38
 if kind=='hit':return Vector((8.5,-5.5,1.8)),pr+Vector((0,0,1.0)),34
 return Vector((0,-9,3)),Vector((0,0,1.2)),28
S.cameras(cuts,pos_,('Spark','Shield'),cand=[(0,0,1.),(0,0,2.5),(0,2.5,0),(0,-2.5,0),(2.5,0,0),(-2.5,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
for ci in cast_info:
 if ci['kind']=='dodge':
  m=ci['best'][0]
  if ci['hit'] is not None or m<.7 or m>2.8:issues.append('AUDIT dodge: exchange %d misses by %.2f m (want 0.7-2.8)'%(ci['k']+1,m))
 else:
  if ci['hit'] is None:issues.append('AUDIT block: exchange %d never reaches the shield'%(ci['k']+1))
  else:
   p=ci['traj'][-1][1];dd=(p-chest(ci['defender'],ci['hit'])).length
   if dd>1.0:issues.append('AUDIT block: the spell bursts %.2f m from the defender (shield at 0.8 m)'%dd)
  if ci['kind']=='reflect' and not ci.get('rhit'):issues.append('AUDIT reflect: the reflected spell misses the rival')
rer=[];worst={}
for ci in cast_info:
 for f in range(S.F(ci['t']-.2),S.F(ci['t']+.5),3):
  t=(f-1)/S.fps;S.settle(f);ch=CH[ci['caster']];rig=ch['rig']
  sh=rig.matrix_world@rig.pose.bones['mixamorig:RightArm'].head;d=(TGs[ci['caster']]['RH'].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),ci['caster'],round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:RightForeArm'].tail-TGs[ci['caster']]['RH'].matrix_world.translation).length
  if g>worst.get(ci['caster'],(0,0))[0]:worst[ci['caster']]=(g,t)
if rer:issues.append('AUDIT reach: casting hand beyond arm reach %s (%d samples)'%(rer[:3],len(rer)))
for k_,(g,t) in worst.items():
 if g>.09:issues.append('AUDIT grip: %s casting hand misses its target by %.0f cm at %.1f s'%(k_,g*100,t))
print('DUEL',[(ci['kind'],round(ci['best'][0],2)) for ci in cast_info],'GRIP',{k:round(v[0]*100,1) for k,v in worst.items()},'REACH over',len(rer))
def snd(A):
 A.track('night wind',A.noise(A.N,25)*.35,.3);ct=A.buf()
 for ci in cast_info:
  A.at(ct,ci['t'],A.burst(.6,12,6.)*.8+A.tone(420,.6,5.,.4),1.);A.at(ct,ci['impact'],A.burst(.9,6,5.)+A.tone(210,.9,5.,.7),1.)
 if HIT_FALL['t']:A.at(ct,HIT_FALL['t'],A.burst(1.4,5,3.)+A.tone(90,1.4,3.,.9),1.)
 A.track('spells',ct,.8);hm=(np.sin(2*PI*55*A.t)+.5*np.sin(2*PI*110*A.t))*.1;A.track('rune hum',hm,.2)
 A.track('music',A.chords(((110,138.6,164.8),(98,123.5,146.8),(103.8,130.8,155.6),(92.5,116.5,138.6)),.22),.4)
S.audio(snd)
S.finish(issues,[leo['root']],world=(.015,.02,.05))
