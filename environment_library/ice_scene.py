"""Blender script: 'The Ice Cave' - Leo crosses a frozen cavern by leaping between drifting ice floes while stalactites crash down around him (about 50 s).

blender -b --disable-autoexec --python ice_scene.py -- <ship_assets_dir> <out.blend>

Technique: MOVING-PLATFORM HOP PLANNER. Nine floes drift on sine paths with different periods. For each hop the planner searches the earliest departure time at which the next floe will be within jump range when Leo lands
(measure-then-schedule: the landing point is the floe centre at the landing time), and Leo waits on the floe he rides until then. Floes dip and ring when he lands. Seven stalactites hang above his future route and drop on a timer
planned from his position, landing 1.6-3.0 m from him (a near miss, never a hit), shedding shards and a splash ring. Audit: hop distances within range, floes never overlap, stalactite near-miss distances, persistence, camera
visibility. Clips: idle, run, jump."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler
S=sb.Scene('ice');PI=math.pi;smooth=kit.smooth;I=w2.ICE;rnd=random.Random(9)
S.load_env('ice_cave')
FL=I['floes'];NF=len(FL)
def floe_xy(k,t):x0,y0,r,A,w,ph=FL[k];return Vector((x0,y0+A*math.sin(w*t+ph),0.))
ENDX=I['end_edge']+2.5;HOPT=.8;DMAX=7.4;REST=1.7
# ---------------------------------------------------------------------------------------------------------- the hop planner
START=Vector((4.3,0.,0.));plan=[];t=2.5;cur=('shelf',START)
def pos_of(st,tt):return st[1] if st[0]=='shelf' else floe_xy(st[1],tt)
stations=[('shelf',START)]+[('floe',k) for k in range(NF)]+[('shelf',Vector((ENDX,0.,0.)))]
warn=[]
for i in range(len(stations)-1):
 a,b=stations[i],stations[i+1];td=t
 while td<t+60:
  pa=pos_of(a,td);pb=pos_of(b,td+HOPT)
  if (pa-pb).length<=DMAX and (b[0]=='floe' or (pa-pb).length>=1.0):break
  td+=.05
 else:warn.append('no hop window from station %d'%i)
 pa=pos_of(a,td);pb=pos_of(b,td+HOPT)
 if b[0]=='shelf':pb=Vector((ENDX,pa.y*.4,0))
 plan.append(dict(i=i,a=a,b=b,td=td,tl=td+HOPT,pa=pa,pb=pb));t=td+HOPT+REST
T_RUN=t;T_END=T_RUN+4.5;S.clock(T_END+2.0);seconds=S.seconds
print('PLAN hops',len(plan),'ready at the far shelf %.1f s'%T_RUN,warn)
def state(tt):
 """(position, in_air, station index being ridden)"""
 if tt<plan[0]['td']:return START.copy(),False,0
 for h in plan:
  if h['td']<=tt<h['tl']:
   u=(tt-h['td'])/HOPT;p=h['pa'].lerp(h['pb'],u);p.z=4*(9.81*HOPT*HOPT/8)*u*(1-u)+0.;return p,True,h['i']
  nxt=plan[h['i']+1]['td'] if h['i']+1<len(plan) else 1e9
  if h['tl']<=tt<nxt:
   b=h['b']
   if b[0]=='floe':return floe_xy(b[1],tt),False,h['i']+1
   if tt<T_RUN:return h['pb'].copy(),False,h['i']+1
   u=smooth((tt-T_RUN)/3.5);return h['pb'].lerp(Vector((ENDX+9.,h['pb'].y,0)),u),False,h['i']+2
 return plan[-1]['pb'],False,len(plan)
def dip(k,tt):
 d=0.
 for h in plan:
  if h['b'][0]=='floe' and h['b'][1]==k and tt>=h['tl']:u=tt-h['tl'];d-=.28*math.exp(-u*2.6)*math.cos(2*PI*1.3*u)
 return d
# ---------------------------------------------------------------------------------------------------------- the floes
FLOES=[]
for k,(x0,y0,r,A,w,ph) in enumerate(FL):
 o=S.prim('cyl','Floe',(x0,y0,-.3),(.78,.9,1.),scale=(r,r,.3),vertices=9,radius=1,depth=2);FLOES.append(o)
 for j in range(3):
  a=rnd.uniform(0,6.28);S.prim('cone','FloeSpike',(math.cos(a)*.5,math.sin(a)*.5,1.5),(.85,.95,1.),scale=(.28/r,.28/r,1.0),vertices=5,radius1=1,depth=2,parent=o)
for f in S.keys():
 tt=(f-1)/S.fps
 for k,o in enumerate(FLOES):
  p=floe_xy(k,tt);o.location=(p.x,p.y,-.3+dip(k,tt));o.rotation_euler=(.03*math.sin(tt*.7+k),.03*math.cos(tt*.6+k),0);o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- stalactites planned from Leo's position
EV=[];hops_with_dwell=[h for h in plan if h['b'][0]=='floe']
for n,h in enumerate(hops_with_dwell[1:]):
 if n%1==0 and len(EV)<7 and n%1==0:
  t0=h['tl']+.2;t1=(plan[h['i']+1]['td'] if h['i']+1<len(plan) else T_RUN)-.2
  if t1-t0>=0.5 and n%1==0:EV.append(t0+(t1-t0)*.5)
EV=EV[::1][:7];print('stalactites at',[round(x,1) for x in EV])
FALL=1.7;ST=[]
for n,te in enumerate(EV):
 p,air,_=state(te);ang=rnd.uniform(0,6.28);d=rnd.uniform(1.8,2.8);ip=Vector((p.x+d*math.cos(ang),p.y+d*math.sin(ang),0))
 o=S.prim('cone','DustStalactite',(ip.x,ip.y,I['ceil']-2.2),(.78,.9,1.),scale=(.55,.55,1.6),rot=(PI,0,0),vertices=8,radius1=1,depth=2);ST.append(dict(o=o,te=te,ip=ip,miss=d))
 sh=[S.prim('cone','Splash%d_%d'%(n,j),(0,0,0),(.9,.97,1.),scale=(.001,.001,.001),vertices=5,radius1=1,depth=2) for j in range(6)]
 ring=S.prim('cyl','SplashRing%d'%n,(ip.x,ip.y,.0),(.75,.9,1.),scale=(.001,.001,.001),vertices=20,radius=1,depth=2)
 ST[-1].update(shards=sh,ring=ring,dirs=[(rnd.uniform(0,6.28),rnd.uniform(2.0,4.5),rnd.uniform(3.0,6.0)) for _ in sh])
for e in ST:
 o=e['o'];te=e['te'];h0=I['ceil']-2.2;h1=.9
 for f in S.keys():
  tt=(f-1)/S.fps;u=tt-(te-FALL)
  if u<0:z=h0+(.02*math.sin(tt*60) if u>-.7 else 0.);x=e['ip'].x+(.03*math.sin(tt*53) if u>-.7 else 0.)
  elif u<FALL:z=h0-(h0-h1)*(u/FALL)**2;x=e['ip'].x
  else:z=h1;x=e['ip'].x
  o.location=(x,e['ip'].y,z);o.keyframe_insert('location',frame=f)
  for (a,sp,vz),sh in zip(e['dirs'],e['shards']):
   v=tt-te
   if 0<=v<1.3:sh.location=(e['ip'].x+math.cos(a)*sp*v,e['ip'].y+math.sin(a)*sp*v,.3+vz*v-4.9*v*v);sc=.22*(1-smooth(v/1.3))+.001
   else:sh.location=(e['ip'].x,e['ip'].y,-1.);sc=.001
   sh.scale=(sc,sc,sc);sh.keyframe_insert('location',frame=f);sh.keyframe_insert('scale',frame=f)
  v=tt-te;rs=(.001+3.2*smooth(v/1.4)) if 0<=v<1.4 else .001;e['ring'].scale=(rs,rs,.02);e['ring'].keyframe_insert('scale',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root']
modes=[(0,plan[0]['td']-.25,'idle')]
for h in plan:
 modes.append((h['td']-.25,h['tl']+.25,'jump'))
 nxt=plan[h['i']+1]['td']-.25 if h['i']+1<len(plan) else T_RUN
 if nxt>h['tl']+.25:modes.append((h['tl']+.25,nxt,'idle'))
modes.append((T_RUN,T_RUN+3.6,'run'));modes.append((T_RUN+3.6,S.seconds,'idle'))
segs=[]
for a,b,m in modes:
 if b-a<.15:continue
 segs.append((a,b,m,.7 if m=='jump' else (.5 if m=='run' else 1.)))
S.play(leo,segs)
prevh=None;heads=[];posl=[]
for f in S.keys():
 tt=(f-1)/S.fps;p,air,idx=state(tt);posl.append(p)
 if idx<len(stations)-1:
  nxt=stations[idx+1] if not air else stations[idx+1]
  q=pos_of(nxt,tt);q=q if nxt[0]=='floe' else Vector((ENDX,0,0));hd=math.atan2(q.y-p.y,q.x-p.x)
 else:hd=0.
 heads.append(hd)
hs=np.unwrap(np.array(heads));k=7;hs=np.convolve(np.pad(hs,(k,k),mode='edge'),np.ones(2*k+1)/(2*k+1),mode='valid')
for n,f in enumerate(S.keys()):
 tt=(f-1)/S.fps;p=posl[n];k_=None
 st_k=state(tt)[2]
 z=0.
 if not state(tt)[1]:
  stn=stations[min(st_k,len(stations)-1)]
  if stn[0]=='floe':z=dip(stn[1],tt)
 root.location=(p.x,p.y,p.z+z);root.rotation_euler=(0,0,hs[n]+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 tt=(f-1)/S.fps;p,air,idx=state(tt);q=pos_of(stations[min(idx+1,len(stations)-1)],tt) if idx<len(stations)-1 else p+Vector((8,0,0));q=q if stations[min(idx+1,len(stations)-1)][0]=='floe' else Vector((ENDX,0,0))
 gz.location=(q.x,q.y,1.2);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
ev=[(plan[0]['td']-.9,plan[0]['tl']+.8,'hop0')]
for h in plan[1:]:ev.append((h['td']-.9,h['tl']+.8,'hop%d'%h['i']))
for n,e in enumerate(ST):ev.append((e['te']-1.5,e['te']+.9,'stal%d'%n))
ev.sort();cuts=[('cave',0,min(3.2,ev[0][0]),'wide')];last=cuts[0][2];alt=0
for a,b,kind in ev:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.2:
  n=max(1,int((a-last)//4.2));seg=(a-last)/n
  for j in range(n):cuts.append(('ride %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','side','low')[alt%3]));alt+=1
 cuts.append((kind,a,b,kind));last=b
cuts.append(('far shore',last,S.seconds,'end'))
def pos(kind,t,u):
 p,air,idx=state(t);head=Vector((1,0,0));lp=p+Vector((0,0,1.0))
 if kind=='wide':return Vector((-10,-9,7))+Vector((10*u,0,0)),Vector((25,0,2)),24
 if kind=='follow':return lp+Vector((-6,2.5,2.2)),lp+Vector((4,0,0))
 if kind=='side':return lp+Vector((1.5,-9,1.8)),lp,34
 if kind=='low':return lp+Vector((4,3.5,-.6)),lp+Vector((-1,0,.3)),30
 if kind.startswith('hop'):
  h=plan[int(kind[3:])];m=(h['pa']+h['pb'])*.5;return Vector((m.x-.5,m.y-8.5,1.6)),Vector((m.x+.5,m.y,1.6)),32
 if kind.startswith('stal'):
  e=ST[int(kind[4:])];return Vector((e['ip'].x-3.5,e['ip'].y-7.5,2.2)),Vector((e['ip'].x,e['ip'].y,5.5-2.5*smooth(min(1,max(0,(t-(e['te']-FALL))/FALL)))))
 return Vector((p.x-9,p.y-5,4)),lp,26
S.cameras(cuts,pos,('Floe','DustStalactite','Splash'))
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
for h in plan:
 d=(h['pa']-h['pb']).length
 if d>DMAX+.3:issues.append('AUDIT hop: hop %d spans %.1f m (limit %.1f)'%(h['i'],d,DMAX))
mn=1e9
for tt in np.arange(0,S.seconds,.2):
 for a in range(NF):
  for b in range(a+1,NF):mn=min(mn,(floe_xy(a,tt)-floe_xy(b,tt)).length-FL[a][2]-FL[b][2])
if mn<.4:issues.append('AUDIT floes: two floes come within %.2f m of each other'%mn)
miss=[e['miss'] for e in ST]
for e in ST:
 p,air,_=state(e['te']);d=math.hypot(p.x-e['ip'].x,p.y-e['ip'].y)
 if d<1.5 or d>3.2:issues.append('AUDIT stalactite: lands %.1f m from Leo (want 1.5-3.2)'%d)
print('ICE hops %d, min floe gap %.2f m, %d stalactites, near misses %s'%(len(plan),mn,len(ST),[round(x,1) for x in miss]))
def snd(A):
 wind=A.noise(A.N,14)*(.5+.3*np.sin(2*PI*.12*A.t));A.track('wind',wind,.4)
 cr=A.buf();ck=np.arange(int(1.2*A.SR))/A.SR;creak=np.sin(2*PI*(160+60*np.sin(2*PI*3*ck))*ck)*np.exp(-ck*3)*.5
 for h in plan:
  if h['b'][0]=='floe':A.at(cr,h['tl'],creak,.6)
 A.track('ice creaks',cr,.4)
 sp=A.buf();
 for h in plan:A.at(sp,h['tl'],A.burst(.5,5,7.),1.)
 A.track('landings',sp,.5)
 cs=A.buf()
 for e in ST:
  A.at(cs,e['te']-FALL-.3,A.burst(.7,40,3.)*.4,1.);A.at(cs,e['te'],A.burst(1.0,3,5.)+A.tone(1800,1.0,4.,.5),1.)
 A.track('stalactites',cs,.8);A.track('music',A.chords(((110,138.6,164.8),(98,123.5,146.8),(87.3,110,130.8),(98,123.5,146.8))),.35)
S.audio(snd)
S.finish(issues,[root],world=(.05,.08,.12))
