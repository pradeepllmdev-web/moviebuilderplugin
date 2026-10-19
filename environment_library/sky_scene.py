"""Blender script: 'The Sky City' - Leo crosses a floating city by riding and leaping between moving platforms (sliders, lifts, a rotating disc, an orbiting pad) to the tower (about 55 s).

blender -b --disable-autoexec --python sky_scene.py -- <ship_assets_dir> <out.blend>

Technique: HOP PLANNING IN 3D WITH RIDING. The platforms move on analytic paths (sine slide, lift, rotation, orbit); Leo is carried by the platform he stands on, including the point on the rotating disc he stands at.
For every hop the planner scans departure times until the departure point and the next platform's landing point (at departure + 0.9 s) are within 6.2 m horizontally and 2.0 m vertically, then flies him on an arc
whose height grows with the climb. On the disc the landing point is placed on the side he arrives from, and the next departure waits for the disc to carry him round to face the next platform. Platforms dip and ring on each landing.
Audit: hop reach, platform separation over the whole film, hands are not used, persistence, camera visibility. Clips: idle, jump, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('sky');PI=math.pi;smooth=kit.smooth;C=w2.SKYCITY;PL=C['plats'];NP=len(PL);rnd=random.Random(3);G_=9.81
S.load_env('sky_city')
HOPT=1.05;DMAX=8.4;DZMAX=2.0;REST=2.2;RO=2.4
def ppos(k,t):return Vector(w2.sky_pos(k,t))
def disc_alpha_state():return {}
ALPHA={}
def point_on(k,t,alpha=None):
 """Leo's standing point on platform k at time t (centre, or the riding point on the disc)"""
 p=ppos(k,t)
 if PL[k]['kind']=='deck':p=p+Vector((2.8 if k==0 else -2.5,0,0))
 if PL[k]['kind']=='disc':
  a=ALPHA[k]+PL[k]['w']*t;return p+Vector((RO*math.cos(a),RO*math.sin(a),0))
 return p
# ---------------------------------------------------------------------------------------------------------- planner
plan=[];t=3.0;warn=[]
for i in range(NP-1):
 td=t;found=False
 while td<t+60:
  pa=point_on(i,td)
  if PL[i+1]['kind']=='disc':
   c=ppos(i+1,td+HOPT);d=Vector((pa.x-c.x,pa.y-c.y,0)).normalized();pb=c+d*RO;alpha=math.atan2(d.y,d.x)-PL[i+1]['w']*(td+HOPT)
  else:pb=point_on(i+1,td+HOPT);alpha=None
  hd=math.hypot(pa.x-pb.x,pa.y-pb.y)
  if 1.0<=hd<=DMAX and abs(pb.z-pa.z)<=DZMAX:found=True;break
  td+=.05
 if not found:warn.append('no window for hop %d'%i)
 if PL[i+1]['kind']=='disc':ALPHA[i+1]=alpha
 plan.append(dict(i=i,td=td,tl=td+HOPT,pa=pa,pb=pb));t=td+HOPT+REST
T_RUN=t;S.clock(T_RUN+8.0);seconds=S.seconds
print('PLAN hops',len(plan),'last landing %.1f s'%plan[-1]['tl'],warn)
def leo_pos(tt):
 """(position, in_air, platform index ridden)"""
 if tt<plan[0]['td']:return point_on(0,tt),False,0
 for h in plan:
  i=h['i']
  if h['td']<=tt<h['tl']:
   u=(tt-h['td'])/HOPT;pa=h['pa'];pb=h['pb'];dz=pb.z-pa.z;A=G_*HOPT*HOPT/8+max(0,dz)*.35;p=pa.lerp(pb,u);p.z=pa.z+dz*u+4*A*u*(1-u);return p,True,i
  nxt=plan[i+1]['td'] if i+1<len(plan) else 1e9
  if h['tl']<=tt<nxt:return point_on(i+1,tt),False,i+1
 return point_on(NP-1,tt),False,NP-1
def dip(k,tt):
 d=0.
 for h in plan:
  if h['i']+1==k and tt>=h['tl']:u=tt-h['tl'];d-=.25*math.exp(-u*2.5)*math.cos(2*PI*1.4*u)
 return d
# ---------------------------------------------------------------------------------------------------------- platforms
PROOT=[]
for k in range(NP):
 P=PL[k];r=P['r'];root=bpy.data.objects.new('Plat%d'%k,None);S.link(root);PROOT.append(root)
 if P['kind'] in ('deck',):continue
 S.prim('cyl','PlatSlab',(0,0,-.25),(.78,.76,.7),scale=(r,r,.25),vertices=20,radius=1,depth=2,parent=root);S.prim('cyl','PlatRim',(0,0,-.02),(.3,.8,1.),scale=(r+.04,r+.04,.03),vertices=20,radius=1,depth=2,emit=3.,parent=root)
 S.prim('cone','PlatRock',(0,0,-1.5),(.42,.4,.36),scale=(r*.8,r*.8,1.0),rot=(PI,0,0),vertices=9,radius1=1,depth=2,parent=root)
 if P['kind']=='disc':
  for a in range(4):S.prim('cube','DiscStripe',(math.cos(a*PI/2)*r*.5,math.sin(a*PI/2)*r*.5,.01),(1,.8,.2),scale=(r*.4,.12,.01),rot=(0,0,a*PI/2),parent=root)
for f in S.keys():
 tt=(f-1)/S.fps
 for k,root in enumerate(PROOT):
  if PL[k]['kind']=='deck':continue
  p=ppos(k,tt);root.location=(p.x,p.y,p.z+dip(k,tt));root.rotation_euler=(.025*math.sin(tt*.9+k),.025*math.cos(tt*.8+k),(PL[k]['w']*tt if PL[k]['kind']=='disc' else 0.));root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
# distant wind turbines and an airship
TURB=[]
for (x,y,z) in ((14,32,-2),(40,-38,4),(78,34,6)):
 base=bpy.data.objects.new('Turbine',None);S.link(base);base.location=(x,y,z);S.prim('cyl','TurbinePole',(0,0,5),(.85,.85,.9),scale=(.25,.25,5),vertices=8,radius=1,depth=2,parent=base)
 rotor=bpy.data.objects.new('TurbineRotor',None);S.link(rotor);rotor.parent=base;rotor.location=(0,-.4,10)
 for a in range(3):S.prim('cube','TurbineBlade',(0,0,2.2),(.95,.95,.98),scale=(.12,.04,2.2),rot=(0,0,0),parent=rotor).rotation_euler=(0,a*2*PI/3,0)
 TURB.append((rotor,rnd.uniform(.5,1.1)))
for f in S.keys():
 tt=(f-1)/S.fps
 for rotor,w in TURB:rotor.rotation_euler=(0,w*tt,0);rotor.keyframe_insert('rotation_euler',frame=f)
ship=bpy.data.objects.new('Airship',None);S.link(ship);S.prim('sphere','AirshipHull',(0,0,0),(.8,.78,.7),scale=(6,1.8,1.8),subdivisions=2,parent=ship);S.prim('cube','AirshipCabin',(0,0,-2.2),(.5,.35,.2),scale=(1.6,.7,.5),parent=ship);S.prim('cube','AirshipFin',(-5.6,0,.9),(.7,.2,.2),scale=(.7,.1,1.2),parent=ship)
for f in S.keys():
 tt=(f-1)/S.fps;ship.location=(-30+2.6*tt,40,16+.6*math.sin(tt*.4));ship.rotation_euler=(0,0,0);ship.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root']
modes=[(0,plan[0]['td']-.25,'idle')]
for h in plan:
 modes.append((h['td']-.25,h['tl']+.25,'jump'))
 nxt=plan[h['i']+1]['td']-.25 if h['i']+1<len(plan) else T_RUN
 if nxt>h['tl']+.25:modes.append((h['tl']+.25,nxt,'idle'))
modes.append((T_RUN,S.seconds,'cele'))
S.play(leo,[(a,b,m,.7 if m=='jump' else 1.) for a,b,m in modes if b-a>.15])
heads=[];posl=[]
for f in S.keys():
 tt=(f-1)/S.fps;p,air,idx=leo_pos(tt);posl.append(p);nx=ppos(min(idx+1,NP-1),tt);hd=math.atan2(nx.y-p.y,nx.x-p.x) if idx<NP-1 else 0.;heads.append(hd)
hs=np.unwrap(np.array(heads));k=7;hs=np.convolve(np.pad(hs,(k,k),mode='edge'),np.ones(2*k+1)/(2*k+1),mode='valid')
for n,f in enumerate(S.keys()):
 tt=(f-1)/S.fps;p=posl[n];air=leo_pos(tt)[1];idx=leo_pos(tt)[2];z=0. if air else dip(idx,tt)
 root.location=(p.x,p.y,p.z+z);root.rotation_euler=(0,0,hs[n]+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 tt=(f-1)/S.fps;p,air,idx=leo_pos(tt);nx=ppos(min(idx+1,NP-1),tt);gz.location=(nx.x,nx.y,nx.z+1.3);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
ev=[(h['td']-.9,h['tl']+.8,'hop%d'%h['i']) for h in plan];cuts=[('city',0,plan[0]['td']-.9,'wide')];last=cuts[0][2];alt=0
for a,b,kind in ev:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.2:
  n=max(1,int((a-last)//4.5));seg=(a-last)/n
  for j in range(n):cuts.append(('ride %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','side','ahead')[alt%3]));alt+=1
 cuts.append((kind,a,b,kind));last=b
cuts.append(('tower',last,S.seconds,'end'))
def pos_(kind,t,u):
 p,air,idx=leo_pos(t);lp=p+Vector((0,0,1.0));nx=ppos(min(idx+1,NP-1),t)
 if kind=='wide':return Vector((-12+10*u,-16,8)),Vector((22,0,3)),22
 if kind=='follow':return lp+Vector((-6,3,2.4)),lp+Vector((3,0,0)),30
 if kind=='side':return lp+Vector((1,-10,1.5)),lp,34
 if kind=='ahead':return nx+Vector((3.5,-4.5,1.8)),lp,32
 if kind.startswith('hop'):
  h=plan[int(kind[3:])];m=(h['pa']+h['pb'])*.5;return Vector((m.x,m.y-11,m.z+1.8)),m+Vector((0,0,1.0)),32
 return Vector((PL[-1]['x']-1,-9,PL[-1]['z']+2.5)),Vector((PL[-1]['x']+8,0,PL[-1]['z']+3.5)),26
S.cameras(cuts,pos_,('Plat','Airship','Turbine','Disc'))
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
for h in plan:
 hd=math.hypot(h['pa'].x-h['pb'].x,h['pa'].y-h['pb'].y);dz=h['pb'].z-h['pa'].z
 if hd>DMAX+.1 or abs(dz)>DZMAX+.1:issues.append('AUDIT hop: hop %d spans %.1f m horizontally and %.1f m vertically'%(h['i'],hd,dz))
mn=1e9
for tt in np.arange(0,S.seconds,.25):
 for a in range(NP):
  for b in range(a+1,NP):mn=min(mn,(ppos(a,tt)-ppos(b,tt)).length-PL[a]['r']-PL[b]['r'])
if mn<.4:issues.append('AUDIT platforms: two platforms come within %.2f m'%mn)
print('SKY hops %d, last landing %.1f s, min platform gap %.2f m'%(len(plan),plan[-1]['tl'],mn))
def snd(A):
 A.track('wind',A.noise(A.N,12)*(.5+.3*np.sin(2*PI*.1*A.t)),.4)
 hm=A.buf()
 for k_,P in enumerate(PL):
  if P['kind']!='deck':hm+=np.sin(2*PI*(80+25*k_)*A.t[:1].repeat(1))[0]*0 if False else 0
 A.track('hum',(np.sin(2*PI*70*A.t)+.4*np.sin(2*PI*140*A.t))*.15,.2)
 jp=A.buf()
 for h in plan:A.at(jp,h['td'],A.burst(.5,30,4.)*.6,.7);A.at(jp,h['tl'],A.burst(.4,6,8.)+A.tone(130,.4,8.,.5),.9)
 A.track('jumps',jp,.7);A.track('music',A.chords(((196,246.9,293.7),(174.6,220,261.6),(220,277.2,329.6),(164.8,207.7,246.9)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.55,.72,.95))
