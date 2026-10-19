"""Blender script: 'The Vine Swings' - Leo crosses a jungle ravine by swinging from vine to vine between stone platforms to a temple (about 38 s).

blender -b --disable-autoexec --python jungle_scene.py -- <ship_assets_dir> <out.blend>

Technique: PENDULUM + RELEASE SOLVER. Each vine is a real pendulum (length 12 m, amplitude 24.6 deg, period from sqrt(L/g)); its phase is set so that it is at the back extreme exactly when Leo is ready on the platform. Leo hangs from the
vine (hands by IK on the rope, body tilted with the rope), and the planner scans release times: the centre of mass leaves with the pendulum's velocity, flies on a ballistic arc, and the release that lands the feet closest to the
next vine's grab point is chosen (measure-then-schedule), so he lands exactly where the next vine will be waiting. Audit: landing error, flight timing, hands within reach of the rope, persistence, camera visibility.
Clips: idle, run, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('jungle');PI=math.pi;smooth=kit.smooth;J=w2.JUNGLE;rnd=random.Random(2);G_=9.81
S.load_env('jungle_temple')
PX,PZ,LB,TH=J['px'],J['pz'],J['LB'],J['TH'];AN=J['anchors'];OM=math.sqrt(G_/LB);HALF=PI/OM;NV=len(AN);COMH=.7;GRIPH=.55;WALK=1.1;DROP=J['DROP'];HOP=.45
def theta(t,tg):return -TH*math.cos(OM*(t-tg))
def com(k,t,tg):
 th=theta(t,tg);ax,az=AN[k];return Vector((ax+LB*math.sin(th),0,az-LB*math.cos(th)))
def vel(k,t,tg):
 th=theta(t,tg);thd=TH*OM*math.sin(OM*(t-tg));return Vector((LB*thd*math.cos(th),0,LB*thd*math.sin(th)))
def flight(c0,v0,zc,t0):
 """ballistic centre of mass from (c0,v0) until its z reaches zc going down; returns (landing time, landing com)."""
 a=-.5*G_;b=v0.z;c=c0.z-zc;disc=b*b-4*a*c
 if disc<0:return None
 T=max((-b+math.sqrt(disc))/(2*a),(-b-math.sqrt(disc))/(2*a));return t0+T,Vector((c0.x+v0.x*T,0,zc))
# ---------------------------------------------------------------------------------------------------------- the planner
plan=[];tg=3.0;warns=[]
for k in range(NV):
 target=Vector((PX[k+1]-1.2,0,PZ[k+1]+COMH));best=None
 for tr in np.arange(tg+HALF-1.8,tg+HALF+.02,.02):
  c0=com(k,tr,tg);v0=vel(k,tr,tg);r=flight(c0,v0,PZ[k+1]+COMH,tr)
  if r is None:continue
  err=abs(r[1].x-target.x)
  if best is None or err<best[0]:best=(err,tr,r[0],r[1])
 if best is None:warns.append('no release for vine %d'%k);best=(9,tg+HALF,tg+HALF+1,target)
 err,tr,tl,pl=best;plan.append(dict(k=k,tg=tg,tr=tr,tl=tl,land=pl,err=err));tg=tl+2.4
T_RUN=plan[-1]['tl']+.8;T_END=T_RUN+3.0+3.5;S.clock(T_END);print('PLAN',[(round(p['tg'],1),round(p['tr'],1),round(p['tl'],1),round(p['err'],2)) for p in plan],warns)
def rope_theta(k,t):return theta(t,plan[k]['tg'])
def leo_com(t):
 """(centre of mass, mode, k) of Leo at time t."""
 if t<plan[0]['tg']-HOP:return Vector((PX[0]+2.0,0,PZ[0]+COMH)),'stand',0
 for p in plan:
  k=p['k']
  if p['tg']-HOP<=t<p['tg']:
   u=(t-p['tg']+HOP)/HOP;b0=Vector((PX[k]+2.0,0,PZ[k]+COMH));return Vector((b0.x,0,b0.z+DROP*smooth(u)+4*.35*u*(1-u))),'swing',k
  if p['tg']<=t<p['tr']:return com(k,t,p['tg']),'swing',k
  if p['tr']<=t<p['tl']:
   u=t-p['tr'];c0=com(k,p['tr'],p['tg']);v0=vel(k,p['tr'],p['tg']);return Vector((c0.x+v0.x*u,0,c0.z+v0.z*u-.5*G_*u*u)),'fly',k
  nxt=plan[k+1]['tg']-HOP if k+1<NV else T_RUN
  if p['tl']<=t<nxt:
   gx=PX[k+1]+2.0 if k+1<NV else p['land'].x
   if t<p['tl']+.3 or gx==p['land'].x:return Vector((p['land'].x,0,p['land'].z)),'stand',k+1
   u=smooth((t-p['tl']-.3)/WALK);return Vector((p['land'].x+(gx-p['land'].x)*min(1.,u),0,p['land'].z)),('walk' if u<1 else 'stand'),k+1
 if t<T_RUN+3.0:
  u=smooth((t-T_RUN)/3.0);x=plan[-1]['land'].x+u*(82.-plan[-1]['land'].x);return Vector((x,0,.7)),'run',NV
 return Vector((82.,0,.7)),'cele',NV
# ---------------------------------------------------------------------------------------------------------- vines
ROPE=[S.prim('cyl','Rope',(0,0,0),(.45,.36,.18),scale=(.05,.05,1),vertices=6,radius=1,depth=2) for k in range(NV)]
for f in S.keys():
 t=(f-1)/S.fps
 for k,r in enumerate(ROPE):
  th=rope_theta(k,t);ax,az=AN[k];d=Vector((math.sin(th),0,-math.cos(th)));L=LB-GRIPH+.5;mid=Vector((ax,0,az))+d*(L/2)
  r.location=mid;r.scale=(.05,.05,L/2);r.rotation_euler=(-d).to_track_quat('Z','Y').to_euler();r.keyframe_insert('location',frame=f);r.keyframe_insert('scale',frame=f);r.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root'];IK,TG=S.ik(leo)
segs=[(0,plan[0]['tg']-.6,'idle',1.)]
for i,p in enumerate(plan):
 segs.append((p['tg']-.6,p['tl']+.15,'idle',1.))
 nxt=plan[i+1]['tg']-.6 if i+1<NV else T_RUN
 if nxt>p['tl']+.15:segs.append((p['tl']+.15,nxt,'idle',1.))
segs+=[(T_RUN,T_RUN+3.0,'run',.5),(T_RUN+3.0,S.seconds,'cele',1.)]
S.play(leo,segs)
for f in S.keys():
 t=(f-1)/S.fps;c,mode,k=leo_com(t);tilt=0.
 if mode=='swing':tilt=-rope_theta(k,t)*(smooth((t-(plan[k]['tg']-HOP))/HOP) if t<plan[k]['tg'] else 1.)
 elif mode=='fly':p=plan[k];tilt=-rope_theta(k,p['tr'])*(1-smooth((t-p['tr'])/(p['tl']-p['tr'])))
 R_=Matrix.Rotation(tilt,3,'Y')@Matrix.Rotation(PI/2,3,'Z')
 root.location=c-Vector((0,0,COMH));root.rotation_euler=R_.to_euler();root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
def hand_w(t):
 w=0.
 for p in plan:w=max(w,smooth((t-(p['tg']-.6))/.5)*(1-smooth((t-p['tr'])/.35)))
 return w
for f in S.keys():
 t=(f-1)/S.fps;c,mode,k=leo_com(t);k_=min(k,NV-1);w=hand_w(t)
 for p in plan:
  if p['tg']-.7<=t<p['tr']+.4:k_=p['k']
 th=rope_theta(k_,t);ax,az=AN[k_];d=Vector((math.sin(th),0,-math.cos(th)));grip=Vector((ax,0,az))+d*(LB-GRIPH)
 for l,sg in (('LH',1),('RH',-1)):
  TG[l].location=grip+Vector((0,.11*sg,.08*sg));TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;c,mode,k=leo_com(t);j=min(k+1,len(PX)-1);gz.location=(PX[j]+1.5,0,PZ[j]+1.6);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- the idol's eyes light up when he arrives
eyes=[S.prim('sphere','IdolEye',(J['temple_x']+5.9,sy*.45,5.3),(1,.75,.1),scale=(.16,.16,.16),emit=0.,subdivisions=1) for sy in (-1,1)]
for e in eyes:
 m=e.data.materials[0].copy();e.data.materials[0]=m;b=m.node_tree.nodes.get('Principled BSDF')
 if b and 'Emission Strength' in b.inputs:
  for f in range(1,S.frames+1,3):b.inputs['Emission Strength'].default_value=12. if (f-1)/S.fps>=T_RUN+2.2 else 0.;b.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('ravine',0,plan[0]['tg']-.7,'wide')];alt=0
for p in plan:
 a=p['tg']-.7;cuts.append(('swing %d'%(p['k']+1),a,p['tr']-.1,('side','ahead','low')[alt%3]));alt+=1
 cuts.append(('release %d'%(p['k']+1),p['tr']-.1,p['tl']+.8,'release'))
 nxt=plan[p['k']+1]['tg']-.7 if p['k']+1<NV else T_RUN
 if nxt-(p['tl']+.8)>.7:cuts.append(('landing %d'%(p['k']+1),p['tl']+.8,nxt,'land%d'%p['k']))
cuts.append(('temple',T_RUN,S.seconds,'end'))
for i in range(len(cuts)-1):
 if cuts[i][2]!=cuts[i+1][1]:cuts[i]=(cuts[i][0],cuts[i][1],cuts[i+1][1],cuts[i][3])
cuts=[c for c in cuts if c[2]-c[1]>.5]
def pos(kind,t,u):
 c,mode,k=leo_com(t);lp=c+Vector((0,0,.3));k=min(k,NV-1)
 if kind=='wide':return Vector((8+10*u,-19,8)),Vector((28,0,3)),22
 if kind=='side':return Vector((c.x+.5,-14,c.z+1.5)),lp,30
 if kind=='ahead':return Vector((PX[min(k+1,len(PX)-1)]+4,-6,PZ[min(k+1,len(PX)-1)]+2.4)),lp,34
 if kind=='low':return Vector((c.x-6,-7,1.2)),lp,26
 if kind=='release':return Vector((c.x-3,-12,c.z+3.0)),lp+Vector((2,0,0)),36
 if kind.startswith('land'):
  j=int(kind[4:])+1;return Vector((PX[j]+5,-4,PZ[j]+1.5)),Vector((PX[j]+1.5,0,PZ[j]+1.2)),36
 return Vector((70,-9,2.5)),Vector((80,0,2.5)),26
S.cameras(cuts,pos,('Rope','IdolEye'))
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
for p in plan:
 if p['err']>.6:issues.append('AUDIT landing: vine %d lands %.2f m from the next grab point'%(p['k']+1,p['err']))
per=2*PI/OM
rer=[];worst={}
for f in range(S.F(plan[0]['tg']),S.F(plan[-1]['tr']),6):
 t=(f-1)/S.fps
 if hand_w(t)<.99:continue
 S.settle(f);rig=leo['rig']
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),l,round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,t)
if rer:issues.append('AUDIT reach: hands beyond reach of the rope %s (%d samples)'%(rer[:3],len(rer)))
for l,(g,t) in worst.items():
 if g>.08:issues.append('AUDIT grip: %s misses the rope by %.0f cm at %.1f s'%(l,g*100,t))
print('JUNGLE vines %d, period %.1f s, landing errors %s m, GRIP %s, REACH over %d'%(NV,per,[round(p['err'],2) for p in plan],{k:round(v[0]*100,1) for k,v in worst.items()},len(rer)))
def snd(A):
 A.track('jungle',A.noise(A.N,30)*.3+A.noise(A.N,4)*.05,.35)
 b=A.buf()
 for t in np.arange(1,S.seconds,.9):
  f0=float(A.rng.choice((2400,2900,3300,1800)));A.at(b,t+A.rng.random()*.5,A.tone(f0,.25,12.,.3)*(A.rng.random()>.5),1.)
 A.track('birds',b,.25)
 w=A.buf()
 for p in plan:
  A.at(w,p['tg']+HALF*.5-.4,A.burst(1.2,60,2.)*np.sin(np.linspace(0,PI,int(1.2*A.SR)))**2,.8);A.at(w,p['tl'],A.burst(.4,5,8.)+A.tone(90,.4,8.,.6),.9)
 A.track('swings',w,.7);A.track('music',A.chords(((130.8,164.8,196),(110,138.6,164.8),(123.5,155.6,185),(98,123.5,146.8)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.3,.45,.3))
