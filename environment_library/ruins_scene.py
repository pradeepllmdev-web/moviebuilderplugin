"""Blender script: 'The Boulder Trap' - a giant boulder is released in a desert temple corridor; Leo outruns it, jumps a pit and slides under a closing stone door (about 40 s).

blender -b --disable-autoexec --python ruins_scene.py -- <ship_assets_dir> <out.blend>

Technique: PURSUIT TUNING. The boulder accelerates then holds a top speed; the planner bisects that top speed so the closest approach between the boulder's front and Leo's back is a chosen 2.2 m (dramatic but not a hit), and
the door's closing start is solved so that its lower edge is 1.0 m above the floor exactly when Leo slides under. The boulder rolls without slipping (roll angle = distance / radius), smashes the ten statues it grazes
(they topple forward about their bases at the moment of contact) and jams in the pit. Audit: closest approach, jump clear of the pit, door gap at the crossing, statue contact times, persistence, camera visibility.
Clips: startle, run, jump, crawl, idle, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler
S=sb.Scene('ruins');PI=math.pi;smooth=kit.smooth;D=w2.DESERT;rnd=random.Random(4)
S.load_env('desert_ruins')
PX0,PX1,PD=D['pit'];R=3.2;LEO_V=6.5;T_B=1.5;T0=2.7;XS=6.;AC=2.8;TARGET=2.2;XT=PX0-.8;JT=.8;XL=PX1+.8
# ---------------------------------------------------------------------------------------------------------- Leo's line (constant speed, jump, crawl)
XC=114.5;CR=2.4;XDOOR=D['door_x']
def leo_x(t):
 if t<T0:return XS
 tj=T0+(XT-XS)/LEO_V
 if t<tj:return XS+LEO_V*(t-T0)
 if t<tj+JT:return XT+(XL-XT)*(t-tj)/JT
 t2=tj+JT;tc=t2+(XC-XL)/LEO_V
 if t<tc:return XL+LEO_V*(t-t2)
 tx=tc+(XDOOR+3.4-XC)/CR
 if t<tx:return XC+CR*(t-tc)
 return min(XDOOR+3.4+LEO_V*.6*(t-tx),XDOOR+9.)
tj=T0+(XT-XS)/LEO_V;t_land=tj+JT;t_cr0=t_land+(XC-XL)/LEO_V;t_cross=t_cr0+(XDOOR-XC)/CR;t_cr1=t_cr0+(XDOOR+3.4-XC)/CR
def leo_z(t):
 if tj<=t<=tj+JT:u=(t-tj)/JT;return 4*(9.81*JT*JT/8)*u*(1-u)
 return 0.
# ---------------------------------------------------------------------------------------------------------- the boulder: bisect the top speed for the target closest approach
def boulder_run(vmax,fps=48):
 xs=[-14.];v=0.;t=T_B;ts=[T_B];xpit=(PX0+PX1)/2;fallt=None
 while t<T0+40:
  v=min(vmax,v+AC/fps) if fallt is None else max(0.,v-vmax*3.0/fps);x=xs[-1]+v/fps;xs.append(x);t+=1/fps;ts.append(t)
  if fallt is None and x>=xpit:fallt=t
  if fallt is not None and v<=0:break
 return np.array(ts),np.array(xs),fallt
def min_gap(vmax):
 ts,xs,fallt=boulder_run(vmax);g=1e9
 for t,x in zip(ts,xs):
  if fallt is not None and t>fallt:break
  g=min(g,(leo_x(t)-.3)-(x+R))
 return g
lo,hi=LEO_V+.05,14.
for _ in range(30):
 mid=(lo+hi)/2
 if min_gap(mid)>TARGET:lo=mid
 else:hi=mid
VMAX=(lo+hi)/2;BT,BX,T_FALL=boulder_run(VMAX);print('VMAX %.2f m/s -> closest approach %.2f m'%(VMAX,min_gap(VMAX)))
def bx(t):
 if t<=BT[0]:return BX[0]
 return float(np.interp(t,BT,BX))
# the door: close so that its lower edge is 1.0 m up when Leo is under it
DUR=3.5;H0=6.5
lo_,hi_=0.,1.
for _ in range(40):
 u=(lo_+hi_)/2
 if H0*(1-smooth(u))>1.0:lo_=u
 else:hi_=u
T_DC=t_cross-(lo_+hi_)/2*DUR
def door_bottom(t):return H0*(1-smooth((t-T_DC)/DUR))
S.clock(t_cr1+6.0);seconds=S.seconds
# ---------------------------------------------------------------------------------------------------------- scenery that moves
BOUL=S.prim('sphere','Boulder',(0,0,R),(.62,.5,.34),scale=(R,R,R),subdivisions=3)
for k in range(18):
 a=rnd.uniform(0,6.28);b=rnd.uniform(-1.2,1.2);v=Vector((math.cos(a)*math.cos(b),math.sin(a)*math.cos(b),math.sin(b)))*.97
 S.prim('sphere','BoulderRock',v,(.55,.45,.3),scale=(.17,.17,.14),subdivisions=1,parent=BOUL)
for f in S.keys():
 t=(f-1)/S.fps;x=bx(t);z=R;rolling=T_FALL is None or t<=T_FALL
 if T_FALL is not None and t>T_FALL:u=min(1.,(t-T_FALL)/.7);z=R-1.5*smooth(u);x=bx(T_FALL)
 BOUL.location=(x,0,z);BOUL.rotation_euler=(0,x/R,.0);BOUL.keyframe_insert('location',frame=f);BOUL.keyframe_insert('rotation_euler',frame=f)
ST=[]
for (x,sy) in D['statues']:
 y=sy*3.3;root=bpy.data.objects.new('Statue',None);S.link(root);root.location=(x,y,0)
 S.prim('cube','StatueBase',(0,0,.35),(.62,.5,.3),scale=(.5,.5,.35),parent=root);S.prim('cube','StatueBody',(0,0,1.7),(.7,.58,.36),scale=(.38,.34,1.0),parent=root);S.prim('sphere','StatueHead',(0,0,3.0),(.72,.6,.38),scale=(.3,.3,.35),subdivisions=1,parent=root)
 # contact: the first moment the boulder's surface reaches the statue's inner face
 th=None
 for t,xx in zip(BT,BX):
  if xx>=x-math.sqrt(max(0,R*R-(abs(y)-.5)**2))*.6:th=t;break
 ST.append(dict(o=root,x=x,y=y,th=th))
for e in ST:
 for f in S.keys():
  t=(f-1)/S.fps;ang=0.
  if e['th'] is not None and t>e['th']:u=t-e['th'];ang=min(PI*.47,.5*5.0*u*u)
  e['o'].rotation_euler=(0,ang,0);e['o'].keyframe_insert('rotation_euler',frame=f)
door=S.prim('cube','StoneDoor',(XDOOR,0,0),(.58,.46,.3),scale=(.9,D['hw']+.4,3.3));DS=[]
for f in S.keys():
 t=(f-1)/S.fps;door.location=(XDOOR,0,door_bottom(t)+3.3);door.keyframe_insert('location',frame=f)
PUFF=[]
def puff(name,x,y,t0,size):
 p=S.prim('sphere','DustPuff'+name,(x,y,1.),(.78,.68,.5),scale=(.001,.001,.001),subdivisions=1);PUFF.append((p,x,y,t0,size))
for k,e in enumerate(ST):
 if e['th'] is not None:puff('S%d'%k,e['x'],e['y'],e['th'],2.2)
puff('Pit',(PX0+PX1)/2,0,T_FALL,4.0);puff('Door',XDOOR-1,0,t_cross-.2,1.8)
for p,x,y,t0,size in PUFF:
 for f in S.keys():
  t=(f-1)/S.fps;u=(t-t0)/1.6;sc=.001+size*smooth(min(1,max(0,u)))*(1-smooth(min(1,max(0,(u-.6)/.4)))) if 0<=u<=1 else .001
  p.scale=(sc,sc,sc*.7);p.location=(x,y,.6+1.2*max(0,u));p.keyframe_insert('scale',frame=f);p.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root']
S.play(leo,[(0,T_B+1.0,'idle'),(T_B+1.0,T0,'startle',1.),(T0,tj-.15,'run',.5),(tj-.15,t_land+.2,'jump',.7),(t_land+.2,t_cr0,'run',.5),(t_cr0,t_cr1,'crawl',.75),(t_cr1,t_cr1+1.2,'run',.5),(t_cr1+1.2,S.seconds,'cele',1.)])
for f in S.keys():
 t=(f-1)/S.fps;root.location=(leo_x(t),0,leo_z(t));root.rotation_euler=(0,0,PI/2*0+PI/2 if t>=T0-.2 else PI/2+PI*(1-smooth((t-(T_B+1.0))/1.2))*.0);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
# before T0 Leo looks back at the boulder: turn him back then forward
for f in S.keys():
 t=(f-1)/S.fps;h=PI+(0 if True else 0)
 if t<T_B+.6:yaw=PI/2+PI
 elif t<T0:yaw=PI/2+PI*(1-smooth((t-(T_B+.6))/(T0-T_B-.6)))
 else:yaw=PI/2
 root.rotation_euler=(0,0,yaw);root.keyframe_insert('rotation_euler',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;gz.location=((bx(t)+R*.3,0,2.) if t<T0 else (leo_x(t)+10,0,1.2));gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
ev=[(e['th']-.8,e['th']+1.0,'stat%d'%k) for k,e in enumerate(ST[:6]) if e['th'] and e['th']>T0+1]+[(tj-1.6,tj+1.8,'pit'),(T_FALL-.5,T_FALL+2.2,'fall'),(t_cross-2.2,t_cross+1.2,'door')]
ev.sort();cuts=[('temple',0,T0+.3,'wide')];last=T0+.3;alt=0
for a,b,kind in ev:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.0:
  n=max(1,int((a-last)//4.0));seg=(a-last)/n
  for j in range(n):cuts.append(('chase %d'%len(cuts),last+j*seg,last+(j+1)*seg,('front','side','boulder')[alt%3]));alt+=1
 cuts.append((kind,a,b,kind));last=b
cuts.append(('safe',last,S.seconds,'end'))
def cl(y,lim=4.3):return max(-lim,min(lim,y))
def pos(kind,t,u):
 lx=leo_x(t);lp=Vector((lx,0,leo_z(t)+1.0));b=bx(t)
 if kind=='wide':return Vector((-12+14*u,-4.2,5.5)),Vector((14,0,1.5)),24
 if kind=='front':return Vector((lx+7,.8,1.5)),Vector(((lx+b)/2+1,0,1.6)),30
 if kind=='side':return Vector((lx+1.5,-4.6,4.4)),lp,34
 if kind=='boulder':return Vector((b+11,-4.4,1.6)),Vector((b,0,R*.8)),30
 if kind.startswith('stat'):e=ST[int(kind[4:])];return Vector((e['x']+8,cl(-e['y']*.9,4.3)*(1),1.8)),Vector((e['x'],e['y'],1.8)),30
 if kind=='pit':return Vector((PX1+6.5,-4.3,2.0)),Vector((PX0+.5,0,1.4)),28
 if kind=='fall':return Vector((PX1+8,-3.5,2.6)),Vector((PX0+1.5,0,1.0)),26
 if kind=='door':return Vector((XDOOR+7,-3.2,.8)),Vector((XDOOR-1.5,0,1.0)),30
 return Vector((XDOOR+10,-4.2,3.0)),lp,26
print('CUTS',[(c[0],round(c[1],1),round(c[2],1),c[3]) for c in cuts])
S.cameras(cuts,pos,('Boulder','Statue','StoneDoor','DustPuff'))
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
gap=min((leo_x(t)-.3)-(bx(t)+R) for t in np.arange(T_B,T_FALL,.02))
if gap<1.4 or gap>3.2:issues.append('AUDIT pursuit: closest approach %.2f m (want 1.4-3.2)'%gap)
if not (tj+.05<t_land and leo_x(tj)<PX0-.3 and leo_x(t_land)>PX1+.3):issues.append('AUDIT jump: take-off %.1f / landing %.1f do not clear the pit %.1f-%.1f'%(leo_x(tj),leo_x(t_land),PX0,PX1))
dg=door_bottom(t_cross)
if dg<.8 or dg>1.3:issues.append('AUDIT door: lower edge %.2f m above the floor when Leo passes (want 0.8-1.3)'%dg)
miss=[k for k,e in enumerate(ST) if e['th'] is None]
if miss:issues.append('AUDIT statues: the boulder never reaches statues %s'%miss)
print('RUINS gap %.2f m, VMAX %.1f, boulder falls at %.1f s, door edge %.2f m at the crossing, %d statues smashed'%(gap,VMAX,T_FALL,dg,len(ST)-len(miss)))
def snd(A):
 dist=np.maximum(2.,np.abs(np.array([leo_x(t) for t in A.t[::441]])-np.array([bx(t) for t in A.t[::441]])));env=np.interp(A.t,A.t[::441],np.clip(7./dist,0,1.))*np.minimum(np.maximum(A.t-T_B,0)/1.5,1)
 rum=A.noise(A.N,16)*env;A.track('rumble',rum,.85)
 hits=A.buf()
 for e in ST:
  if e['th']:A.at(hits,e['th'],A.burst(1.0,4,5.)+A.tone(180,1.0,4.,.5),.9)
 A.at(hits,T_FALL,A.burst(1.6,25,3.)*.9+A.tone(60,1.6,2.5,.7),1.);A.track('impacts',hits,.8)
 st=A.buf();k=A.burst(.1,5,40.)
 for t in np.arange(T0,t_cr0,.27):A.at(st,t,k,.6)
 A.at(st,tj,A.burst(.3,5,12.),.5);A.at(st,t_land,A.burst(.35,5,10.),.8);A.track('steps',st,.5)
 dr=A.buf();gk=np.arange(int(DUR*A.SR))/A.SR;A.at(dr,T_DC,A.noise(len(gk),40)*np.sin(PI*gk/DUR)**.5,.8);A.track('door',dr,.6)
 A.track('torches',A.noise(A.N,3)*(.5+.5*A.noise(A.N,3000)),.12);A.track('music',A.chords(((110,130.8,164.8),(98,123.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.55,.6,.8))
