"""Blender script: 'The Swamp' - Leo poles a punt through a mangrove swamp at night; four crocodiles lunge from their lairs as he passes and he fends two of them off with the pole (about 55 s).

blender -b --disable-autoexec --python swamp_scene.py -- <ship_assets_dir> <out.blend>

Technique: POLING PHYSICS AND AMBUSH TIMING. The pole is planted on the bed during the push and its tip stays fixed in the world while the boat moves: the boat's advance is exactly the change in the pole's lean
((hand height - bed) * tan(angle)) so the tip never slips; between pushes the pole is lifted and swung forward. Each crocodile lunges so that it snaps at the boat just as the boat passes its lair (the head arcs from the lair
to a point 1.1-1.7 m off the hull, never touching it); for two of them Leo swings the pole round and the tip meets the snout before the jaws close, so the stroke schedule has to give way to a poke (the timeline is solved
iteratively: boat motion decides the croc times, croc times decide the pokes, pokes change the boat motion). The body of each croc trails its head along the head's own path. Audit: tip slip while planted, croc to Leo and to the
hull, pole-tip contact on the pokes, hands within reach of the pole, persistence, camera visibility. Clips: idle."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('swamp');PI=math.pi;smooth=kit.smooth;SW=w2.SWAMP;rnd=random.Random(20)
S.load_env('swamp')
PATH=sb.Path([(x,y,0.) for x,y in SW['path']]);BED=SW['bed'];XH,ZH=.08,1.2;TP=1.7;LP=3.8;T0=2.0;S_START=2.0;DRIFT=.2
def smooth_(x):return smooth(x)
def stroke_pose(u):
 """(phi, tip height, planted) at stroke phase u in [0,1)"""
 PHI0,PHI1=-.63,.35
 if u<.22:return PHI1+(PHI0-PHI1)*smooth(u/.30),.5,False
 if u<.32:v=(u-.22)/.10;return PHI1+(PHI0-PHI1)*smooth(u/.30),.5+(BED-.5)*smooth(v),False
 if u<.88:return PHI0+(PHI1-PHI0)*smooth((u-.32)/.56),BED,True
 return PHI1,BED+(.5-BED)*smooth((u-.88)/.12),False
def stroke_phi_planted(u):return stroke_pose(u)[0]
DT=1/48.;SIMT=np.arange(0,70,DT)
def simulate(poke_s):
 """boat arc length, pole lean and tip height, planted flag, poke blend and stroke phase over time"""
 s=S_START;tk=T0;out={'s':[],'phi':[],'tz':[],'pl':[],'wp':[]};phi_prev=None;fired=[False]*len(poke_s);wins=[];last=(.35,.5,False);active=None
 for t in SIMT:
  wp=0.
  for q,ps in enumerate(poke_s):
   if not fired[q] and s>=ps:fired[q]=True;wins.append((t,t+1.8))
  active=None
  for (a,b) in wins:
   if a<=t<b:active=(a,b)
  if active:
   a,b=active;wp=smooth((t-a)/.3)*(1-smooth((t-(b-.3))/.3));ph,tz,pl=last;tk=b
  else:
   if t<T0:u=0.
   else:
    u=((t-tk)/TP)
    while u>=1.:tk+=TP;u=((t-tk)/TP)
   ph,tz,pl=stroke_pose(u);last=(ph,tz,pl)
  if pl and phi_prev is not None and not active:s+=(ZH-BED)*(math.tan(ph)-math.tan(phi_prev))
  s+=DRIFT*DT if t>=T0 else 0.
  phi_prev=ph if pl else None
  out['s'].append(s);out['phi'].append(ph);out['tz'].append(tz);out['pl'].append(pl);out['wp'].append(wp)
 res={k:np.array(v) for k,v in out.items()};res['wins']=wins;return res
def idx(t):return min(len(SIMT)-1,max(0,int(round(t/DT))))
def sb_(sim,t):return float(sim['s'][idx(t)])
def time_of_s(sim,s):
 i=int(np.searchsorted(sim['s'],s));return SIMT[min(i,len(SIMT)-1)]
# ---------------------------------------------------------------------------------------------------------- iterate boat / croc / poke
LAIRS=SW['lairs'];CROC=[]
def s_of_x(x):return float(PATH.cum[int(np.argmin(np.abs(PATH.pts[:,0]-x)))])
poke_s=[s_of_x(lx)-1.0 for k,(lx,ly,sd) in enumerate(LAIRS) if k%2==1]
sim=simulate(poke_s);wins=sim['wins'];wi=0
for k,(lx,ly,sd) in enumerate(LAIRS):
 side=1 if ly>0 else -1
 if k%2==1:
  a,b=wins[wi];wi+=1;t_hit=a+1.2;CROC.append(dict(k=k,lair=None,side=side,t_hit=t_hit,poked=True,dist=1.15))
 else:
  CROC.append(dict(k=k,lair=Vector((lx,ly,-.12)),side=side,t_hit=time_of_s(sim,s_of_x(lx)+.3),poked=False,dist=1.7))
pokes=wins
T_ARR=time_of_s(sim,PATH.length-6.);T_END=T_ARR+7.;S.clock(T_END);seconds=S.seconds
def boat(t):
 s=sb_(sim,t);p=PATH.at(s);tg=PATH.tangent(s+1.0);h=math.atan2(tg.y,tg.x);return Vector((p.x,p.y,0)),h,s
def bframe(t):
 p,h,s=boat(t);bob=.03*math.sin(t*1.3);roll=.03*math.sin(t*.9+1);R=Matrix.Rotation(h,3,'Z')@Matrix.Rotation(roll,3,'X');m=R.to_4x4();m.translation=p+Vector((0,0,bob));return m
for e in CROC:
 if e['lair'] is None:
  bm=bframe(e['t_hit']);e['lair']=bm.translation+bm.to_3x3()@Vector((-.5,e['side']*5.4,0))+Vector((0,0,-.12))
# ---------------------------------------------------------------------------------------------------------- crocodiles
SEGR=[.30,.36,.40,.38,.33,.27,.20,.13];SPCE=.5;NS=len(SEGR)
def croc_head(e,t):
 L0=e['lair'];tb=bframe(e['t_hit']);fwd=tb.to_3x3()@Vector((1,0,0));lat=tb.to_3x3()@Vector((0,1,0))*e['side']*-1.0
 tgt=tb.translation+lat*-1.0*0+(tb.to_3x3()@Vector((0,e['side']*e['dist'],0)))+Vector((0,0,.1));tgt.z=.1
 t0=e['t_hit']-.9
 rec=e['t_hit']-.1 if e['poked'] else e['t_hit']+.1
 if t<t0:return L0.copy(),0.
 if t<=e['t_hit']-.1+0.0 if e['poked'] else t<=e['t_hit']:
  u=(t-t0)/(e['t_hit']-t0-(.1 if e['poked'] else 0.));u=min(1.,u);return L0.lerp(tgt,1-(1-u)**2)+Vector((0,0,.2*math.sin(PI*u*.5))),u
 if t<rec+1.3:u=smooth((t-rec)/1.3);cur=tgt;return cur.lerp(L0,u)+Vector((0,0,.0)),1.-u
 return L0.copy(),0.
def croc_jaw(e,t):
 th=e['t_hit'];o0=th-.55;
 if e['poked']:
  if t<o0:return 0.
  if t<th-.3:return .9*smooth((t-o0)/.25)
  if t<th-.2:return .9*(1-smooth((t-(th-.3))/.1))
  return 0.
 if t<o0:return 0.
 if t<th-.1:return .9*smooth((t-o0)/.45)
 if t<th+.05:return .9*(1-smooth((t-(th-.1))/.15))
 return 0.
CH=[]
for e in CROC:
 L0=e['lair'];tb=bframe(e['t_hit']);tgt=tb.translation+tb.to_3x3()@Vector((0,e['side']*e['dist'],0));fdir=Vector((tgt.x-L0.x,tgt.y-L0.y,0)).normalized();e['fdir']=fdir
 pre=[L0-fdir*(NS*SPCE+1.0)+fdir*(i*.1) for i in range(int((NS*SPCE+1.0)/.1))]
 hp=[];hist=[]
 for t in SIMT[:int(T_END/DT)+2:1]:hp.append(croc_head(e,t)[0])
 H=np.array([list(p) for p in pre]+[list(p) for p in hp]);cum=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(H,axis=0),axis=1))]);e['H']=H;e['cum']=cum;e['npre']=len(pre)
 segs=[S.prim('sphere','Croc%d_%d'%(e['k'],i),(0,0,0),(.2,.32,.16) if i%2 else (.25,.38,.2),scale=(SEGR[i]*1.4,SEGR[i],SEGR[i]*.75),subdivisions=2) for i in range(NS)]
 hroot=bpy.data.objects.new('CrocHead%d'%e['k'],None);S.link(hroot)
 S.prim('cube','CrocUpperJaw',(.42,0,.02),(.24,.4,.18),scale=(.42,.13,.05),parent=hroot);S.prim('sphere','CrocSkull',(0,0,.04),(.22,.36,.17),scale=(.28,.2,.12),subdivisions=1,parent=hroot)
 hinge=bpy.data.objects.new('CrocHinge%d'%e['k'],None);S.link(hinge);hinge.parent=hroot;hinge.location=(.0,0,-.03);S.prim('cube','CrocLowerJaw',(.38,0,0),(.2,.33,.14),scale=(.38,.11,.035),parent=hinge)
 for sy in (-1,1):S.prim('sphere','CrocEye',(.22,sy*.13,.14),(1,.75,.1),scale=(.05,.05,.05),emit=3.,subdivisions=1,parent=hroot)
 e.update(segs=segs,hroot=hroot,hinge=hinge)
def arc_pos(e,i,k):
 target=e['cum'][e['npre']+i]-k*SPCE;H=e['H'];cum=e['cum']
 if target<=0:return Vector(H[0])
 j=int(np.searchsorted(cum,target,side='right')-1);j=min(j,len(H)-2);u=(target-cum[j])/max(1e-9,cum[j+1]-cum[j]);return Vector(H[j]*(1-u)+H[j+1]*u)
for f in S.keys():
 t=(f-1)/S.fps;i=int(round(t/DT))
 for e in CROC:
  pp=[arc_pos(e,i,k) for k in range(NS+1)]
  for k,o in enumerate(e['segs']):
   a=pp[k];b=pp[k+1];d=a-b;d=d if d.length>1e-6 else e['fdir'];o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('X','Z').to_euler();o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
  hd=pp[0];d=(pp[0]-pp[1]);d=d if d.length>1e-6 else e['fdir'];d=Vector((d.x,d.y,d.z*.0+0.)).normalized() if abs(d.x)+abs(d.y)>1e-6 else e['fdir']
  e['hroot'].location=hd+Vector((0,0,.0));e['hroot'].rotation_euler=d.to_track_quat('X','Z').to_euler();e['hroot'].keyframe_insert('location',frame=f);e['hroot'].keyframe_insert('rotation_euler',frame=f)
  e['hinge'].rotation_euler=(0,croc_jaw(e,t),0);e['hinge'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- the boat, the pole, Leo
bt=bpy.data.objects.new('Boat',None);S.link(bt)
S.prim('cube','BoatHull',(0,0,.08),(.3,.2,.12),scale=(1.9,.62,.14),parent=bt)
for sy in (-1,1):S.prim('cube','BoatSide',(0,sy*.58,.3),(.32,.22,.13),scale=(1.9,.05,.18),parent=bt)
S.prim('cube','BoatBow',(1.95,0,.22),(.3,.2,.12),scale=(.18,.5,.2),parent=bt)
lantern=S.prim('sphere','BoatLantern',(1.6,0,.55),(1,.75,.35),scale=(.12,.12,.12),emit=6.,parent=bt,subdivisions=1)
leo=S.character('Leo',S.params['hero_tint'],parent=bt);leo['root'].location=(-.25,0,.22);leo['root'].rotation_euler=(0,0,PI/2)
IK,TG=S.ik(leo);S.play(leo,[(0,S.seconds,'idle',1.)])
pole=bpy.data.objects.new('Pole',None);S.link(pole);S.prim('cyl','PoleShaft',(0,0,LP/2),(.4,.3,.15),scale=(.028,.028,LP/2),vertices=6,radius=1,depth=2,parent=pole)
Hb=Vector((XH,0,ZH))
def pole_pose_b(t):
 """pole direction (u) and grip distance from the tip (s_g) in the boat frame, blended with the poke"""
 i=idx(t);ph=sim['phi'][i];tz=sim['tz'][i];wp=sim['wp'][i];u=Vector((math.sin(ph),0,math.cos(ph)));sg=(ZH-tz)/math.cos(ph)
 if wp>0:
  for e in CROC:
   if e['poked'] and e['t_hit']-1.2<=t<e['t_hit']+.6:
    tc=e['t_hit']-.3;pt,_=croc_head(e,min(t,tc));tb=bframe(t).inverted();hb=tb@(pt);hb.z=max(hb.z,.2)
    up=(Hb-hb).normalized();sgp=(Hb-hb).length;u=(u*(1-wp)+up*wp).normalized();sg=sg*(1-wp)+sgp*wp
 return u,sg
for f in S.keys():
 t=(f-1)/S.fps;M=bframe(t);bt.matrix_world=M;bt.location=M.translation;bt.rotation_euler=M.to_3x3().to_euler();bt.keyframe_insert('location',frame=f);bt.keyframe_insert('rotation_euler',frame=f)
 u,sg=pole_pose_b(t);tip=Hb-u*sg;pole.location=M@tip;pole.rotation_euler=(M.to_3x3()@u).to_track_quat('Z','Y').to_euler();pole.keyframe_insert('location',frame=f);pole.keyframe_insert('rotation_euler',frame=f)
 TG['RH'].location=M@Hb;TG['LH'].location=M@(Hb+u*.3);w=smooth((t-1.0)/.8)
 for l in ('LH','RH'):TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;M=bframe(t);ahead=None
 act=[e for e in CROC if e['t_hit']-1.6<=t<=e['t_hit']+.8]
 gz.location=(croc_head(act[0],t)[0]+Vector((0,0,.1))) if act else M@Vector((8,0,.9));gz.keyframe_insert('location',frame=f)
# fireflies
FF=[]
for i in range(50):
 c=Vector((rnd.uniform(0,66),rnd.uniform(-8,8),rnd.uniform(1,4)));ph=(rnd.uniform(0,6),rnd.uniform(0,6),rnd.uniform(0,6));o=S.prim('sphere','SparkFly%d'%i,c,(.8,1,.4),scale=(.05,.05,.05),emit=8.,subdivisions=1);FF.append((o,c,ph))
for f in S.keys():
 t=(f-1)/S.fps
 for o,c,ph in FF:o.location=c+Vector((1.2*math.sin(t*.7+ph[0]),1.2*math.sin(t*.5+ph[1]),.5*math.sin(t*.9+ph[2])));o.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
evs=sorted([(e['t_hit']-1.7,e['t_hit']+1.0,'croc%d'%e['k']) for e in CROC]);cuts=[('swamp',0,T0+1.8,'wide')];last=T0+1.8;alt=0
for a,b,kind in evs:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.2:
  n=max(1,int((a-last)//4.3));seg=(a-last)/n
  for j in range(n):cuts.append(('poling %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','front','pole','side')[alt%4]));alt+=1
 cuts.append((kind,a,b,kind));last=b
if S.seconds-last>.8:cuts.append(('dock',last,S.seconds,'end'))
def pos_(kind,t,u):
 M=bframe(t);fw=M.to_3x3()@Vector((1,0,0));lt=M.to_3x3()@Vector((0,1,0));c=M.translation;lp=c+Vector((0,0,1.1))
 if kind=='wide':return Vector((-10+6*u,-4,6.5)),Vector((20,0,1)),22
 if kind=='follow':return c-fw*6.5+Vector((0,0,1.5))+lt*1.0,lp+fw*2,30
 if kind=='front':return c+fw*5.5+lt*1.6+Vector((0,0,1.0)),lp,30
 if kind=='pole':return c+fw*2.6-lt*1.0+Vector((0,0,1.4)),lp,36
 if kind=='side':return c+lt*6.5+Vector((0,0,1.5)),lp,34
 if kind.startswith('croc'):
  e=CROC[int(kind[4:])];h,_=croc_head(e,t);return c-fw*3.0-lt*e['side']*2.2*-1+Vector((0,0,.8)),h+Vector((0,0,.3)),34
 return c-fw*7+Vector((0,3,2.5)),c+fw*4+Vector((0,0,1.2)),26
S.cameras(cuts,pos_,('Boat','Pole','Croc','SparkFly'),cand=[(0,0,.8),(0,0,2.),(0,2.,0),(0,-2.,0),(2.,0,0),(-2.,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
slip=0.
for t in np.arange(T0+.5,T_ARR,.05):
 i=idx(t)
 if sim['pl'][i] and sim['wp'][i]<=.01:
  M=bframe(t);u=Vector((math.sin(sim['phi'][i]),0,math.cos(sim['phi'][i])));sg=(ZH-sim['tz'][i])/math.cos(sim['phi'][i]);tip=M@(Hb-u*sg)
  j=idx(t+.05)
  if sim['pl'][j] and sim['wp'][j]<=.01:
   M2=bframe(t+.05);u2=Vector((math.sin(sim['phi'][j]),0,math.cos(sim['phi'][j])));sg2=(ZH-sim['tz'][j])/math.cos(sim['phi'][j]);tip2=M2@(Hb-u2*sg2);slip=max(slip,(tip2-tip).length)
if slip>.07:issues.append('AUDIT pole: the planted tip slips %.2f m in 0.05 s (should stay fixed in the water bed)'%slip)
dl=1e9;dh=1e9
for e in CROC:
 for t in np.arange(e['t_hit']-1.2,e['t_hit']+1.5,.02):
  h,_=croc_head(e,t);M=bframe(t);loc=M.inverted()@h;dl=min(dl,math.hypot(loc.x+.25,loc.y));
  hx=max(abs(loc.x)-1.9,0);hy=max(abs(loc.y)-.6,0);dh=min(dh,math.hypot(hx,hy))
if dl<.9:issues.append('AUDIT croc: a head comes within %.2f m of Leo'%dl)
if dh<.45:issues.append('AUDIT croc: a head comes within %.2f m of the hull'%dh)
for e in CROC:
 if e['poked']:
  tc=e['t_hit']-.3;i=idx(tc);M=bframe(tc);u,sg=pole_pose_b(tc);tip=M@(Hb-u*sg);h,_=croc_head(e,tc);d=(tip-h).length
  if d>.35:issues.append('AUDIT poke: the pole tip is %.2f m from the snout of croc %d at the contact'%(d,e['k']+1))
rer=[];worst={}
for f in range(S.F(T0+1.0),S.F(T_ARR),6):
 t=(f-1)/S.fps;S.settle(f);rig=leo['rig']
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.5:rer.append((round(d-.44,3),l,round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,t)
if rer:issues.append('AUDIT reach: hand target beyond reach of the pole %s (%d samples)'%(rer[:3],len(rer)))
for l,(g,t) in worst.items():
 if g>.09:issues.append('AUDIT grip: %s misses the pole by %.0f cm at %.1f s'%(l,g*100,t))
print('SWAMP slip %.3f m, croc-Leo %.2f m, croc-hull %.2f m, GRIP %s, REACH over %d'%(slip,dl,dh,{k:round(v[0]*100,1) for k,v in worst.items()},len(rer)))
def snd(A):
 A.track('swamp',A.noise(A.N,40)*.35+A.noise(A.N,3)*.03,.35)
 fr=A.buf();k=np.arange(int(.25*A.SR))/A.SR;chirp=np.sin(2*PI*(2500+500*np.sin(k*60))*k)*np.exp(-k*14)
 for t in np.arange(1,S.seconds,.7):
  if rnd.random()<.6:A.at(fr,t+rnd.random()*.4,chirp*.3,1.)
 A.track('frogs and insects',fr,.25)
 sp=A.buf()
 for t in np.arange(T0,T_ARR,TP):A.at(sp,t+.4,A.burst(.4,10,8.)*.5,1.);A.at(sp,t+.7,A.burst(.8,30,4.)*.4,1.)
 A.track('pole and water',sp,.5);cr=A.buf()
 for e in CROC:
  A.at(cr,e['t_hit']-.8,A.burst(.7,25,5.)*.7,1.);A.at(cr,e['t_hit']-.05 if not e['poked'] else e['t_hit']-.2,A.burst(.25,3,18.)+A.tone(120,.25,10.,.8),1.)
 A.track('crocs',cr,.8);A.track('music',A.chords(((98,116.5,146.8),(87.3,103.8,130.8),(92.5,110,138.6),(82.4,98,123.5)),.2),.35)
S.audio(snd)
S.finish(issues,[leo['root']],world=(.05,.09,.08))
