"""Blender script: 'The Reef' - Leo dives through a coral reef full of fish, takes a pearl from a giant clam and escapes a shark into a crevice (about 55 s).

blender -b --disable-autoexec --python reef_scene.py -- <ship_assets_dir> <out.blend>

Technique: UNDERWATER LOCOMOTION AND A SCHOOL. Leo swims horizontally (body axis along the path, pitched from the path slope; the run clip is the flutter kick) and stands to open the clam; 100 fish are simulated as boids
(separation, alignment, cohesion, a moving goal, avoidance of Leo, of the shark and of the rocks) so the school parts around him and bursts away from the shark. The shark is a chain of segments trailing its head; before the chase
it patrols a circle, then its head follows Leo's own path a distance d(t) behind that shrinks from 14 m to 2.6 m (the pursuit is tuned by construction) until the crevice, where Leo turns in and the shark overshoots. The clam
lid opens, both hands take the pearl (IK) and carry it at the chest. Audit: shark-Leo closest approach, fish never inside Leo, hands within reach of the pearl, crevice entry, persistence, camera visibility.
Clips: idle, run."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('reef');PI=math.pi;smooth=kit.smooth;RF=w2.REEF;rnd=random.Random(6)
S.load_env('reef')
FLOOR=RF['floor'];CX,CY,CZ=RF['clam'];CRX,CRY,CRZ=RF['crevice'];HC=.85
# ---------------------------------------------------------------------------------------------------------- paths and profiles
P1=sb.Path([(0,0,-1.5),(14,0,-6),(30,3,-8.5),(52,-5,-8),(66,3,-9.5),(74,-1.0,-10.6),(78,-1.1,FLOOR+HC)])
P2=sb.Path([(78,-1.1,FLOOR+HC),(92,3,-9),(110,-3,-9),(128,3,-10),(143,-1,-10.8),(150,-3,FLOOR+1.0),(158,-3,FLOOR+1.0)])
V=4.2
def prof(t,t0,L,v,acc=1.0,dec_d=0.):
 tau=t-t0
 if tau<=0:return 0.
 da=.5*v*acc
 s=.5*(v/acc)*tau*tau if tau<acc else da+v*(tau-acc)
 if dec_d>0:
  s0=L-dec_d;tt=s0 and None
  if s>=L-dec_d:
   ts=acc+(L-dec_d-da)/v if L-dec_d>da else 0.;ta=tau-ts;a=v*v/(2*dec_d);s=L-dec_d+v*ta-.5*a*ta*ta
   if ta>v/a:s=L
 return min(s,L)
T0=1.5;t_a=T0+(P1.length-4.)/V+1.9+.9;T_OPEN=t_a+.3;T_REACH=t_a+1.3;T_GRAB=t_a+2.4;T_LIFT=T_GRAB+1.0;T_DEP=T_GRAB+1.8
T_J=T_DEP+3.0;s_c=P2.s_of(5)
def s1(t):return prof(t,T0,P1.length,V,1.0,4.0)
def s2(t):return prof(t,T_DEP,P2.length,V,1.0,0.)
t_c=T_DEP;
while s2(t_c)<s_c and t_c<T_DEP+80:t_c+=.02
T_END=t_c+(P2.length-s_c)/V+1.0+6.0;S.clock(T_END);seconds=S.seconds
print('TIMES arrive clam %.1f, depart %.1f, shark joins %.1f, crevice %.1f, end %.1f'%(t_a,T_DEP,T_J,t_c,T_END))
def lerp_ang(a,b,u):return a+((b-a+PI)%(2*PI)-PI)*u
def tang_h(P,s):t=P.tangent(s);return math.atan2(t.y,t.x),math.asin(max(-1,min(1,t.z)))
def leo_state(t):
 """(center, heading, pitch from vertical, mode) of Leo at time t."""
 if t<T_DEP-1.2:
  s=s1(t);c=P1.at(s);h,al=tang_h(P1,s)
  near=smooth((s-(P1.length-3.5))/3.5)
  h=lerp_ang(h,PI/2,near);p=lerp_ang(PI/2-al,0.,near)
  return c,h,p,('swim' if near<.95 else 'stand')
 if t<T_DEP:u=smooth((t-(T_DEP-1.2))/1.2);h0,al0=tang_h(P2,.5);return P2.at(0.),lerp_ang(PI/2,h0,u),lerp_ang(0.,PI/2-al0,u),'stand' if u<.4 else 'swim'
 s=s2(t);c=P2.at(s);h,al=tang_h(P2,s);return c,h,PI/2-al,'swim'
def xform(t):
 c,h,p,mode=leo_state(t);lat=Vector((-math.sin(h),math.cos(h),0));R=Matrix.Rotation(p,3,lat)@Matrix.Rotation(h+PI/2,3,'Z');return c-R@Vector((0,0,HC)),R,mode,c
# ---------------------------------------------------------------------------------------------------------- the shark (patrol, then follows Leo's path)
SEGR=[.5,.65,.72,.68,.58,.47,.36,.26,.17];SPC=.8;NSH=len(SEGR)
def patrol(t):a=.4+t*(4.5/20.);return Vector((100+20*math.cos(a),32+20*math.sin(a),-14+1.2*math.sin(t*.4)))
def d_of(t):
 u=min(1.,max(0.,(t-T_J)/(t_c-T_J)));return 14.-(14.-3.4)*u**1.5
SH_V=5.2
def shark_follow(t):
 if t<=t_c:s=s2(t)-d_of(t)
 else:s=s2(t_c)-d_of(t_c)+SH_V*(t-t_c)
 if s<=s_c:return P2.at(max(0.,s))
 tc=P2.tangent(s_c-8);d=s-s_c;return P2.at(s_c)+tc*d+Vector((0,.09*d*d,.03*d*d))
def shark_head(t):
 if t<T_J-2.5:return patrol(t)
 u=smooth((t-(T_J-2.5))/2.5);return patrol(t).lerp(shark_follow(t),u) if t<T_J else shark_follow(t)
DT=1/48.;TS=np.arange(-6.,T_END+.01,DT);HP=np.array([list(shark_head(t)) for t in TS]);CUMH=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(HP,axis=0),axis=1))])
def arc_back(i,k):
 """position on the head's history k*SPC metres behind the head at sample i"""
 target=CUMH[i]-k*SPC
 if target<=0:return Vector(HP[0])
 j=int(np.searchsorted(CUMH,target,side='right')-1);u=(target-CUMH[j])/max(1e-9,CUMH[j+1]-CUMH[j]);return Vector(HP[j]*(1-u)+HP[j+1]*u)
def shark_pose(t):
 i=int(round((t+6.)/DT));return [arc_back(i,k) for k in range(NSH+1)]
SHK=[]
for k,r in enumerate(SEGR):SHK.append(S.prim('sphere','Shark%d'%k,(0,0,0),(.45,.5,.56) if k%2 else (.5,.55,.6),scale=(r*1.7,r*.9,r*.8),subdivisions=2))
fin=S.prim('cone','SharkFin',(0,0,0),(.4,.44,.5),scale=(.5,.08,.8),vertices=4,radius1=1,depth=2);tailf=S.prim('cone','SharkTail',(0,0,0),(.4,.44,.5),scale=(.15,.08,.8),vertices=4,radius1=1,depth=2)
for f in S.keys():
 t=(f-1)/S.fps;pp=shark_pose(t)
 for k,o in enumerate(SHK):
  a=pp[k];b=pp[k+1];d=a-b;d=d if d.length>1e-6 else Vector((1,0,0));q=d.to_track_quat('X','Z');o.location=(a+b)/2;o.rotation_euler=q.to_euler();o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
 d=pp[2]-pp[3];q=d.to_track_quat('X','Z');fin.location=pp[2]+Vector((0,0,.7));fin.rotation_euler=q.to_euler();fin.keyframe_insert('location',frame=f);fin.keyframe_insert('rotation_euler',frame=f)
 d=pp[NSH-1]-pp[NSH];q=d.to_track_quat('X','Z');tailf.location=pp[NSH]+d.normalized()*-.2;tailf.rotation_euler=(q.to_euler().x,q.to_euler().y,q.to_euler().z+.35*math.sin(t*4));tailf.keyframe_insert('location',frame=f);tailf.keyframe_insert('rotation_euler',frame=f)
def shark_nose(t):return shark_pose(t)[0]
# ---------------------------------------------------------------------------------------------------------- the school (boids)
N=100;rr=np.random.default_rng(3);pos=np.column_stack([rr.normal(24,2.5,N),rr.normal(0,2.5,N),rr.normal(-7,1.2,N)]);vel=np.column_stack([rr.normal(2,.4,N),rr.normal(0,.4,N),rr.normal(0,.2,N)])
ROCKS=np.array([[x,y,z,r] for (x,y,z,r) in RF['rocks']])
def goal(t):return np.array([24+2.3*t,10*math.sin(t*.22),-7+1.8*math.sin(t*.31)])
FPOS={};FVEL={};dtb=1/S.fps
for fi in range(1,S.frames+1):
 t=(fi-1)/S.fps;leo=np.array(list(leo_state(t)[0]));sk=np.array(list(shark_nose(t)))
 for _ in range(2):
  d=pos[:,None,:]-pos[None,:,:];dist=np.linalg.norm(d,axis=2)+np.eye(N)*99
  sep=(d/(dist[...,None]**2+1e-3)*(dist[...,None]<1.0)).sum(1)
  nb=(dist<4.5)[...,None];cnt=nb.sum(1)+1e-6;ali=((vel[None,:,:]*nb).sum(1)/cnt-vel);coh=((pos[None,:,:]*nb).sum(1)/cnt-pos)*(cnt>1)
  g=goal(t)-pos;g=g/(np.linalg.norm(g,axis=1,keepdims=True)+1e-6)
  al=pos-leo;ad=np.linalg.norm(al,axis=1,keepdims=True);avl=al/(ad+1e-6)*np.clip((4.5-ad)/4.5,0,1)*7
  as_=pos-sk;sd=np.linalg.norm(as_,axis=1,keepdims=True);avs=as_/(sd+1e-6)*np.clip((11-sd)/11,0,1)*11
  avr=np.zeros_like(pos)
  for (rx,ry,rz,rad) in ROCKS:
   v_=pos-np.array([rx,ry,rz]);dd=np.linalg.norm(v_,axis=1,keepdims=True);avr+=v_/(dd+1e-6)*np.clip((rad+2.0-dd)/2.0,0,1)*8
  bnd=np.zeros_like(pos);bnd[:,2]+=np.clip(FLOOR+1.2-pos[:,2],0,3)*3-np.clip(pos[:,2]+1.5,0,3)*3
  acc=1.6*sep+.7*ali+.45*coh+1.3*g+avl+avs+avr+bnd;vel=vel+acc*dtb*.5;sp=np.linalg.norm(vel,axis=1,keepdims=True);vmax=np.where(sd<11,6.5,4.0);vel=vel/(sp+1e-6)*np.clip(sp,2.0,vmax);pos=pos+vel*dtb*.5
 FPOS[fi]=pos.copy();FVEL[fi]=vel.copy()
FISH=[S.prim('cone','DustFish%d'%i,(0,0,0),(.9,.5,.2) if i%3==0 else ((.3,.6,.9) if i%3==1 else (.95,.85,.3)),scale=(.09,.09,.3),rot=(0,0,0),vertices=6,radius1=1,depth=2) for i in range(N)]
for f in S.keys():
 for i,o in enumerate(FISH):
  v=Vector(FVEL[f][i]);q=v.to_track_quat('Z','Y') if v.length>1e-6 else Euler((0,0,0)).to_quaternion()
  o.location=tuple(FPOS[f][i]);o.rotation_euler=q.to_euler();o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- the clam and the pearl
clam=S.prim('sphere','ClamBase',(CX,CY,FLOOR+.5),(.55,.35,.5),scale=(1.0,.8,.55),subdivisions=2)
hinge=bpy.data.objects.new('ClamHinge',None);S.link(hinge);hinge.location=(CX,CY+.8,FLOOR+1.0);S.prim('sphere','ClamLid',(0,-.8,0),(.6,.42,.5),scale=(1.0,.8,.3),subdivisions=2,parent=hinge)
PEARL0=Vector((CX,-.75,FLOOR+1.02));pearl=S.prim('sphere','Pearl',PEARL0,(1,1,.95),scale=(.09,.09,.09),emit=2.5,subdivisions=2)
for f in S.keys():
 t=(f-1)/S.fps;op=smooth((t-T_OPEN)/1.5)*.95;hinge.rotation_euler=(-op,0,0);hinge.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root'];IK,TG=S.ik(leo)
S.play(leo,[(0,T0-.3,'idle',1.),(T0-.3,t_a-2.2,'run',.8),(t_a-2.2,T_DEP-1.2,'idle',1.),(T_DEP-1.2,S.seconds,'run',.8)])
HW=lambda t:smooth((t-(T_REACH-.6))/.6)
for f in S.keys():
 t=(f-1)/S.fps;loc,R,mode,c=xform(t);root.location=loc;root.rotation_euler=R.to_euler();root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 chest=loc+R@Vector((0,-.25,.95))
 if t<T_GRAB:pp=PEARL0
 elif t<T_LIFT:pp=PEARL0.lerp(chest,smooth((t-T_GRAB)/(T_LIFT-T_GRAB)))
 else:pp=chest
 pearl.location=pp;pearl.keyframe_insert('location',frame=f)
 w=HW(t);lat=R@Vector((1,0,0))
 for l,sg in (('LH',1),('RH',-1)):
  TG[l].location=pp+lat*(-.1*sg);TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(0,1,0))
for f in S.keys():
 t=(f-1)/S.fps;c,h,p,mode=leo_state(t);gz.location=(c+Vector((math.cos(h),math.sin(h),0))*6) if mode=='swim' else Vector(PEARL0)+Vector((0,.3,0));gz.keyframe_insert('location',frame=f)
# bubbles from his mouth
BUB=[S.prim('sphere','DustBubble%d'%i,(0,0,0),(.85,.95,1.),scale=(.001,.001,.001),subdivisions=1) for i in range(60)]
for i,b in enumerate(BUB):
 te=1.0+i*(seconds-2)/60;
 for f in S.keys():
  t=(f-1)/S.fps;u=t-te
  if 0<=u<4.5:
   loc,R,mode,c=xform(te);hp=loc+R@Vector((0,-.25,1.55));b.location=(hp.x+.2*math.sin(u*3+i),hp.y+.2*math.cos(u*2+i),hp.z+.9*u);sc=.07*min(1,u*2)*(1-smooth((u-3.8)/.7))+.001
  else:b.location=(0,0,5.);sc=.001
  b.scale=(sc,sc,sc);b.keyframe_insert('location',frame=f);b.keyframe_insert('scale',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
ev=[(T_OPEN-1.2,T_LIFT+.8,'clam'),(T_J-1.2,T_J+3.2,'chase'),(t_c-3.5,t_c-.8,'chase2')]
cuts=[('dive',0,min(5.0,ev[0][0]),'wide')];last=cuts[0][2];alt=0
for a,b,kind in ev:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.5:
  n=max(1,int((a-last)//4.5));seg=(a-last)/n
  for j in range(n):cuts.append(('swim %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','side','front')[alt%3]));alt+=1
 cuts.append((kind,a,b,kind));last=b
cuts.append(('safe',last,S.seconds,'end'))
def pos_(kind,t,u):
 r=pos_raw(kind,t,u);P=Vector(r[0]);P.z=max(FLOOR+.9,min(P.z,.5));return (P,)+tuple(r[1:])
def pos_raw(kind,t,u):
 loc,R,mode,c=xform(t);fw=R@Vector((0,-1,0));lat=R@Vector((1,0,0));sh=shark_nose(t)
 if kind=='wide':return Vector((10+25*u,-14,3)),Vector((32,0,-8)),24
 if kind=='follow':return c-fw*4.5+Vector((0,0,1.4))+lat*1.0,c+fw*2,30
 if kind=='side':return c+lat*4.5+Vector((0,0,.8)),c,32
 if kind=='front':return c+fw*5.0+Vector((0,0,.5)),c,30
 if kind=='clam':return Vector((CX+3.2,-3.4,FLOOR+2.6)),Vector((CX,-.4,FLOOR+1.0)),40
 if kind=='chase':return (c+sh)/2+Vector((0,-9,2)),(c+sh)/2,30
 if kind=='chase2':return c-fw*3.2+Vector((0,2.4,1.2)),(c+sh)/2,30
 if kind=='crev':return Vector((CRX-7,CRY-.0,FLOOR+1.9)),(sh*.4+Vector((CRX+4,CRY,CRZ+.6))*.6),28
 return Vector((CRX-6,CRY,FLOOR+1.6)),Vector((CRX+6,CRY,FLOOR+1.0)),30
S.cameras(cuts,pos_,('Shark','DustFish','DustBubble','Pearl','Clam'),cand=[(0,0,.8),(0,2.5,0),(0,-2.5,0),(2.5,0,0),(-2.5,0,0),(0,0,-.8)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
mind=min((Vector(leo_state(t)[0])-shark_nose(t)).length for t in np.arange(T_J,T_END,.04))
if mind<1.6:issues.append('AUDIT shark: closest approach %.2f m (want 1.6 or more)'%mind)
if mind>4.5:issues.append('AUDIT shark: closest approach %.2f m is not dramatic (want 4.5 or less)'%mind)
inside=0
for fi in range(1,S.frames+1,6):
 c=np.array(list(leo_state((fi-1)/S.fps)[0]));
 if (np.linalg.norm(FPOS[fi]-c,axis=1)<.55).any():inside+=1
if inside:issues.append('AUDIT fish: fish inside Leo at %d sampled frames'%inside)
rer=[];worst={}
for f in range(S.F(T_REACH),S.F(T_END-6),6):
 t=(f-1)/S.fps;S.settle(f);rig=leo['rig']
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),l,round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,t)
if rer:issues.append('AUDIT reach: hands beyond reach of the pearl %s (%d samples)'%(rer[:3],len(rer)))
for l,(g,t) in worst.items():
 if g>.08:issues.append('AUDIT grip: %s misses the pearl by %.0f cm at %.1f s'%(l,g*100,t))
ce=Vector(leo_state(T_END-4)[0]);print('REEF shark closest %.2f m, fish %d, crevice end at (%.0f,%.0f,%.0f), GRIP %s, REACH over %d'%(mind,N,ce.x,ce.y,ce.z,{k:round(v[0]*100,1) for k,v in worst.items()},len(rer)))
def snd(A):
 A.track('underwater',A.noise(A.N,50)*.5+A.noise(A.N,6)*.05,.4)
 b=A.buf()
 for i in range(60):
  te=1.0+i*(seconds-2)/60;A.at(b,te,A.burst(.25,3,15.)*.5+A.tone(900+30*i%400,.25,20.,.3),1.)
 A.track('bubbles',b,.3)
 sk=A.buf();dist=np.array([max(1.,(Vector(leo_state(t)[0])-shark_nose(t)).length) for t in A.t[::441]]);env=np.interp(A.t,A.t[::441],np.clip(5./dist,0,1))*np.clip((A.t-T_J+2)/2,0,1)
 A.track('shark',(np.sin(2*PI*48*A.t)+.4*np.sin(2*PI*96*A.t))*env,.7)
 hb=A.buf();k=np.arange(int(.2*A.SR))/A.SR;beat=np.sin(2*PI*60*k)*np.exp(-k*20)
 for t in np.arange(T_J,t_c+1,.55-.2*np.clip(1,0,1)):A.at(hb,t,beat,.8);A.at(hb,t+.18,beat*.6,.8)
 A.track('heartbeat',hb,.5)
 cl=A.buf();A.at(cl,T_OPEN,A.noise(int(1.5*A.SR),40)*np.sin(np.linspace(0,PI,int(1.5*A.SR))),.8);A.at(cl,T_GRAB,A.tone(1300,1.5,3.,.6),1.);A.track('clam',cl,.5)
 A.track('music',A.chords(((98,123.5,146.8),(87.3,110,130.8),(110,138.6,164.8),(92.5,116.5,138.6)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.04,.2,.32))
