"""Blender script: 'The Night Market' - Leo chases a thief through a crowded lantern market; the thief topples crate stacks behind him, Leo vaults each one, and corners him at a dead-end gate to take back the sack (about 45 s).

blender -b --disable-autoexec --python market_scene.py -- <ship_assets_dir> <out.blend>

Technique: PURSUIT ON A PATH THROUGH A STEERED CROWD. The thief runs a Catmull-Rom street path (S-bends around the island stalls); Leo runs the same path a distance d behind that closes from 10 m to 0.9 m (a function of the
thief's progress, kept above 2.6 m until the last crate so every crate has fallen before he arrives). 60 bystanders walk on their own errands: steered by separation, by repulsion from every stall rectangle and by
a strong repulsion from the two runners, so the crowd parts around the chase. Crates topple about their base edge when the thief passes and Leo's jump windows are derived from where they land. The thief turns, holds out the sack;
Leo's hand takes it (IK) and carries it at the chest. Audit: distance to bystanders and stalls, jump clearance over each crate, the sack hand-off, hands within reach, persistence, camera visibility.
Clips: idle, run, jump, startle."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('market');PI=math.pi;smooth=kit.smooth;M=w2.MARKET;rnd=random.Random(15);G_=9.81
S.load_env('night_market')
PATH=sb.Path([(x,y,0.) for x,y in M['path']]);LEN=PATH.length;VT=5.0;T0=2.6;S0=10.;S_END=LEN-3.0
def crate_s(x):
 i=int(np.argmin(np.abs(PATH.pts[:,0]-x)));return float(PATH.cum[i])
SC=[crate_s(x) for x in M['crates']]
def sT(t):
 tau=t-T0
 if tau<=0:return S0
 e=min(1.,tau);ease=.5*e*e  # one second of acceleration
 s=S0+VT*(ease+max(0,tau-1.))
 return min(s,S_END)
t_stop=T0+1.+(S_END-S0-VT*.5)/VT
def d_of_s(s):
 s_last=SC[-1]+8.
 if s<=S0:return 10.
 if s<=s_last:return 10.-(10.-3.6)*(s-S0)/(s_last-S0)
 return 3.6-(3.6-.9)*smooth((s-s_last)/(S_END-s_last))
def sL(t):s=sT(t);return s-d_of_s(s)
T_HAND=t_stop+.5;T_TAKE=t_stop+1.5;T_CARRY=T_TAKE+.7;T_END=T_CARRY+5.0;S.clock(T_END);seconds=S.seconds
print('TIMES thief stops %.1f s at s=%.0f of %.0f, Leo d=%.2f m'%(t_stop,S_END,LEN,d_of_s(S_END)))
def time_of(fn,s,t_lo=0.,t_hi=200.):
 lo,hi=t_lo,t_hi
 for _ in range(50):
  mid=(lo+hi)/2
  if fn(mid)<s:lo=mid
  else:hi=mid
 return (lo+hi)/2
def pos_s(s):return PATH.at(s)
def head_s(s):tg=PATH.tangent(s+1.5);return math.atan2(tg.y,tg.x)
# ---------------------------------------------------------------------------------------------------------- crates
CR=[];JUMPS=[]
for k,sc in enumerate(SC):
 side=1 if k%2==0 else -1;p=pos_s(sc);tg=PATH.tangent(sc);lat=Vector((-tg.y,tg.x,0))*side;pivot=p+lat*1.25;root=bpy.data.objects.new('CrateStack%d'%k,None);S.link(root);root.location=pivot
 S.prim('cube','CrateA',(lat.x*.45,lat.y*.45,.45),(.55,.4,.2),scale=(.45,.45,.45),parent=root);S.prim('cube','CrateB',(lat.x*.45,lat.y*.45,1.15),(.5,.36,.18),scale=(.4,.4,.35),parent=root)
 t_pass=time_of(sT,sc-.5);ax=tg  # axis along the path; fall toward the lane
 CR.append(dict(root=root,pivot=pivot,lat=lat,tg=tg,t_fall=t_pass,s=sc,side=side))
 ta=time_of(sL,sc-2.2);tb=time_of(sL,sc+1.8);JUMPS.append((ta,tb,sc))
for c in CR:
 for f in S.keys():
  t=(f-1)/S.fps;th=min(PI/2,.5*7.0*max(0,t-c['t_fall'])**2)
  # rotate about the axis along the path, tipping toward the lane centre: sign from the lateral side
  ang=-th*c['side'] if abs(c['tg'].x)>=abs(c['tg'].y) else th
  c['root'].rotation_euler=(0,0,0);ax=c['tg'];R=Matrix.Rotation(-th*c['side']*(1 if True else 1),3,ax)
  c['root'].rotation_euler=R.to_euler();c['root'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- bystanders
N=60;rng=np.random.default_rng(5);RECTS=np.array([[x,y,w/2+.7,d/2+.7] for (x,y,w,d) in M['mid']+M['edge']])
pos=np.column_stack([rng.uniform(4,128,N),rng.uniform(-9,9,N)]);
for i in range(N):
 while any(abs(pos[i,0]-r[0])<r[2] and abs(pos[i,1]-r[1])<r[3] for r in RECTS) or (abs(pos[i,1]-PATH.at(min(LEN-1,max(0,pos[i,0]*1.02)))[1])<1.2 and pos[i,0]<18):pos[i]=[rng.uniform(4,128),rng.uniform(-9,9)]
goalp=np.column_stack([rng.uniform(4,128,N),rng.uniform(-9,9,N)]);spd=rng.uniform(1.0,1.6,N);FPOS={}
def nearest_rect(P):
 dx=np.clip(P[:,None,0]-RECTS[None,:,0],-RECTS[None,:,2],RECTS[None,:,2]);dy=np.clip(P[:,None,1]-RECTS[None,:,1],-RECTS[None,:,3],RECTS[None,:,3]);return dx,dy
for fi in range(1,S.frames+1):
 t=(fi-1)/S.fps;a=np.array(list(pos_s(sT(t)).xy));b=np.array(list(pos_s(sL(t)).xy))
 g=goalp-pos;gd=np.linalg.norm(g,axis=1,keepdims=True);new=gd[:,0]<2.0;goalp[new]=np.column_stack([rng.uniform(4,128,new.sum()),rng.uniform(-9,9,new.sum())])
 v=g/(gd+1e-6)
 d=pos[:,None,:]-pos[None,:,:];dist=np.linalg.norm(d,axis=2)+np.eye(N)*99;sep=(d/(dist[...,None]**2+1e-3)*(dist[...,None]<1.1)).sum(1)*.6
 dxr,dyr=nearest_rect(pos);ox=pos[:,None,0]-RECTS[None,:,0]-dxr;oy=pos[:,None,1]-RECTS[None,:,1]-dyr;inside=(np.abs(ox)<1e-6)&(np.abs(oy)<1e-6)
 rep=np.stack([ox,oy],axis=2);rn=np.linalg.norm(rep,axis=2)+1e-6;near=(rn<1.0)&(~inside);avr=(rep/rn[...,None]*((1.0-rn)[...,None])*near[...,None]).sum(1)*3.
 av=np.zeros((N,2))
 for q in (a,b):
  r=pos-q;rn2=np.linalg.norm(r,axis=1,keepdims=True)+1e-6;av+=r/rn2*np.clip((4.0-rn2)/4.0,0,1)*7.
 vel=v*spd[:,None]+sep+avr+av;vn=np.linalg.norm(vel,axis=1,keepdims=True);vel=vel/(vn+1e-6)*np.clip(vn,0,3.0);pos=pos+vel/S.fps
 FPOS[fi]=(pos.copy(),vel.copy())
cols=[(.7,.25,.2),(.2,.4,.7),(.75,.6,.2),(.3,.55,.3),(.6,.3,.55),(.8,.8,.75),(.5,.35,.2)]
PEOPLE=[]
for i in range(N):
 r=bpy.data.objects.new('Passer%d'%i,None);S.link(r);sc=.85+rnd.random()*.2;c=cols[i%len(cols)]
 S.prim('cone','PasserBody',(0,0,.55*sc),c,scale=(.26*sc,.26*sc,.55*sc),vertices=10,radius1=1,depth=2,parent=r);S.prim('sphere','PasserHead',(0,0,1.22*sc),(.82,.62,.46),scale=(.13*sc,.13*sc,.13*sc),subdivisions=1,parent=r);PEOPLE.append(r)
prevy=[None]*N
for f in S.keys():
 for i,r in enumerate(PEOPLE):
  p,vl=FPOS[f];sp=np.linalg.norm(vl[i]);yaw=math.atan2(vl[i][1],vl[i][0]) if sp>.05 else 0.;ph=f/S.fps*6+i;r.location=(p[i,0],p[i,1],.05*abs(math.sin(ph)) if sp>.1 else 0.);e=Euler((0,0,yaw))
  if prevy[i] is not None:e.make_compatible(prevy[i])
  prevy[i]=e.copy();r.rotation_euler=e;r.keyframe_insert('location',frame=f);r.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- the two runners
leo=S.character('Leo',S.params['hero_tint']);thief=S.character('Thief',(.32,.32,.4))
def t_state(t):
 s=sT(t);p=pos_s(s);h=head_s(s)
 if t>t_stop+.1:h=lerp_ang(h,head_s(S_END)+PI,smooth((t-t_stop-.1)/.5))
 return Vector((p.x,p.y,0)),h
def lerp_ang(a,b,u):return a+((b-a+PI)%(2*PI)-PI)*u
def l_state(t):
 s=sL(t);p=pos_s(s);h=head_s(s);z=0.
 for (ta,tb,sc) in JUMPS:
  if ta<=t<=tb:u=(t-ta)/(tb-ta);T=tb-ta;A=G_*T*T/8+.35;z=4*A*u*(1-u)
 return Vector((p.x,p.y,z)),h
S.play(leo,[(0,T0+.3,'idle',1.),(T0+.3,t_stop,'run',.55),(t_stop,S.seconds,'idle',1.)])
S.play(thief,[(0,T0-.2,'idle',1.),(T0-.2,t_stop,'run',.6),(t_stop,S.seconds,'startle',1.)])
# jump windows replace the run clip for Leo
for (ta,tb,sc) in JUMPS:pass
for f in S.keys():
 t=(f-1)/S.fps
 for ch,fn in ((leo,l_state),(thief,t_state)):
  p,h=fn(t);ch['root'].location=p;ch['root'].rotation_euler=(0,0,h+PI/2);ch['root'].keyframe_insert('location',frame=f);ch['root'].keyframe_insert('rotation_euler',frame=f)
IKL,TGL=S.ik(leo);IKT,TGT=S.ik(thief)
def fl(h):return Vector((math.cos(h),math.sin(h),0)),Vector((-math.sin(h),math.cos(h),0))
SACK=S.prim('sphere','Sack',(0,0,0),(.55,.42,.25),scale=(.17,.17,.2),subdivisions=2)
def sack_pos(t):
 p,h=t_state(t);f,l=fl(h);carry=p+f*.3+l*(-.28)+Vector((0,0,.95))
 if t<T_HAND:return carry
 ext=p+f*.5+Vector((0,0,1.15))
 if t<T_TAKE:return carry.lerp(ext,smooth((t-T_HAND)/.6))
 pl,hl=l_state(t);fl_,ll=fl(hl);chest=pl+fl_*.3+ll*.12+Vector((0,0,1.05))
 return ext.lerp(chest,smooth((t-T_TAKE)/(T_CARRY-T_TAKE))) if t<T_CARRY else chest
for f in S.keys():
 t=(f-1)/S.fps;sp=sack_pos(t);SACK.location=sp;SACK.keyframe_insert('location',frame=f)
 # thief's right hand holds the sack until Leo takes it; Leo's left hand takes it
 wt=smooth((t-.5)/.6)*(1-smooth((t-(T_TAKE+.3))/.5));wl=smooth((t-(T_HAND+.2))/.6)
 TGT['RH'].location=sp+Vector((0,0,0));TGT['RH'].keyframe_insert('location',frame=f);IKT['RH'].influence=wt;IKT['RH'].keyframe_insert('influence',frame=f)
 TGL['LH'].location=sp;TGL['LH'].keyframe_insert('location',frame=f);IKL['LH'].influence=wl;IKL['LH'].keyframe_insert('influence',frame=f)
 TGL['RH'].location=(0,0,0);IKL['RH'].influence=0.;IKL['RH'].keyframe_insert('influence',frame=f);TGT['LH'].location=(0,0,0);IKT['LH'].influence=0.;IKT['LH'].keyframe_insert('influence',frame=f)
gzl=S.gaze(leo,(1,0,0));gzt=S.gaze(thief,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;pt,ht=t_state(t);pl,hl=l_state(t)
 gzl.location=pt+Vector((0,0,1.4));gzl.keyframe_insert('location',frame=f);gzt.location=(pl+Vector((0,0,1.4))) if t>t_stop else (pt+fl(ht)[0]*6+Vector((0,0,1.2)));gzt.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('market',0,T0+.8,'wide')];last=T0+.8;alt=0;evs=sorted([(ta-.8,tb+.9,'jump%d'%k) for k,(ta,tb,sc) in enumerate(JUMPS)]+[(t_stop-2.0,T_TAKE+.3,'cornered'),(T_TAKE+.3,T_END,'end')])
for a,b,kind in evs:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.2:
  n=max(1,int((a-last)//4.3));seg=(a-last)/n
  for j in range(n):cuts.append(('chase %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','front','top','side')[alt%4]));alt+=1
 cuts.append((kind,a,b,kind));last=b
if S.seconds-last>.8:cuts.append(('end',last,S.seconds,'end'))
def pos_(kind,t,u):
 pl,hl=l_state(t);pt,ht=t_state(t);f,l=fl(hl);lp=pl+Vector((0,0,1.0))
 if kind=='wide':return Vector((-6+8*u,-9,5.5)),Vector((18,0,1.5)),24
 if kind=='follow':return lp-f*5.0+l*1.2+Vector((0,0,2.0)),lp+f*2,30
 if kind=='front':return pt+fl(ht)[0]*5.5+Vector((0,1.0,1.4)),(pl+pt)/2+Vector((0,0,1.0)),30
 if kind=='top':return lp+Vector((-1.5,-1.5,5.0)),lp,32
 if kind=='side':return lp+l*5.0+Vector((0,0,1.3)),lp,34
 if kind.startswith('jump'):
  k=int(kind[4:]);c=CR[k];return c['pivot']+Vector((0,0,.0))+c['tg']*-4.0+c['lat']*-1.5+Vector((0,0,1.0)),c['pivot']+c['lat']*-1.0+Vector((0,0,.7)),32
 if kind=='cornered':return (pl+pt)/2+l*3.2+Vector((0,0,1.4)),(pl+pt)/2+Vector((0,0,1.1)),34
 return (pl+pt)/2+l*2.4+Vector((0,0,1.5)),(pl+pt)/2+Vector((0,0,1.2)),44
S.cameras(cuts,pos_,('CrateStack','Crate','Sack','Passer'),cand=[(0,0,1.),(0,0,2.5),(0,2.,.5),(0,-2.,.5),(2.,0,.5),(-2.,0,.5)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
mind_t=min((l_state(t)[0]-t_state(t)[0]).length for t in np.arange(T0+2,t_stop,.1))
if mind_t<.85:issues.append('AUDIT chase: Leo closes to %.2f m of the thief before the end'%mind_t)
bys=1e9
for fi in range(1,S.frames+1,3):
 t=(fi-1)/S.fps;P=FPOS[fi][0]
 for q in (l_state(t)[0],t_state(t)[0]):bys=min(bys,np.min(np.linalg.norm(P-np.array([q.x,q.y]),axis=1)))
if bys<.45:issues.append('AUDIT crowd: a bystander comes within %.2f m of a runner'%bys)
stall=1e9
for s in np.arange(0,LEN,.5):
 p=pos_s(s)
 for (x,y,w,d) in M['mid']+M['edge']:
  dx=max(abs(p.x-x)-w/2,0);dy=max(abs(p.y-y)-d/2,0);stall=min(stall,math.hypot(dx,dy))
if stall<1.0:issues.append('AUDIT stalls: the street path passes %.2f m from a stall'%stall)
for k,(ta,tb,sc) in enumerate(JUMPS):
 c=CR[k];tm=time_of(sL,sc);T=tb-ta;A=G_*T*T/8+.35
 if t_state(0)[0] is None:pass
 if tm<c['t_fall']+.82:issues.append('AUDIT crate: Leo reaches crate %d only %.2f s after the thief starts it falling'%(k+1,tm-c['t_fall']))
 if A<.9:issues.append('AUDIT jump: crate %d apex %.2f m is too low'%(k+1,A))
print('MARKET thief-Leo min %.2f m, bystander min %.2f m, stalls min %.2f m, jumps %d, apex %.2f m'%(mind_t,bys,stall,len(JUMPS),G_*(JUMPS[0][1]-JUMPS[0][0])**2/8+.35))
rer=[];worst={}
for f in range(S.F(T_HAND),S.F(T_CARRY+1),3):
 t=(f-1)/S.fps;S.settle(f)
 for ch,l_,b,a_,IKX,TGX in ((leo,'LH','LeftForeArm','LeftArm',IKL,TGL),(thief,'RH','RightForeArm','RightArm',IKT,TGT)):
  if IKX[l_].influence<.99:continue
  rig=ch['rig'];sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TGX[l_].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),ch['tag'],round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TGX[l_].matrix_world.translation).length
  if g>worst.get(ch['tag'],(0,0))[0]:worst[ch['tag']]=(g,t)
if rer:issues.append('AUDIT reach: sack hand-off beyond arm reach %s (%d samples)'%(rer[:3],len(rer)))
for k_,(g,t) in worst.items():
 if g>.09:issues.append('AUDIT grip: %s misses the sack by %.0f cm at %.1f s'%(k_,g*100,t))
print('HANDOFF GRIP',{k:round(v[0]*100,1) for k,v in worst.items()},'REACH over',len(rer))
def snd(A):
 A.track('crowd',A.noise(A.N,5)*(.5+.3*np.sin(2*PI*.3*A.t))*.5+A.noise(A.N,40)*.2,.35)
 st=A.buf();k=A.burst(.1,5,40.)
 for t in np.arange(T0,t_stop,.24):A.at(st,t,k,.6);A.at(st,t+.02,k,.35)
 A.track('steps',st,.5);cr=A.buf()
 for c in CR:A.at(cr,c['t_fall']+.45,A.burst(.8,6,6.)+A.tone(110,.8,6.,.6),.9)
 for (ta,tb,sc) in JUMPS:A.at(cr,tb,A.burst(.3,6,10.),.5)
 A.track('crates',cr,.8);A.track('music',A.chords(((146.8,185,220),(130.8,164.8,196),(123.5,155.6,185),(138.6,174.6,207.7)),.18),.35)
S.audio(snd)
S.finish(issues,[leo['root']],world=(.04,.05,.1))
