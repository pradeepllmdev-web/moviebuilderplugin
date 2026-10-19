"""Blender script: 'The Rope Bridge' - Leo sprints across a rotten rope bridge over a gorge while the planks drop away behind him; he vaults two gaps and makes the last leap to the cliff as the bridge goes down (about 28 s).

blender -b --disable-autoexec --python bridge_scene.py -- <ship_assets_dir> <out.blend>

Technique: A COLLAPSE WAVE AND A ROPE SIMULATION. The failure time of plank k is tw + k*d; d is bisected so the nearest failed plank never gets closer than 1.4 m to Leo's rear foot (pursuit tuning, as for the boulder). The ropes are a
Verlet chain (one-sided distance constraints, 4 % slack): each node is pinned at its plank while the plank is intact and released when it fails, so the ropes hang and sag by themselves as the bridge empties (the handrails
follow the same nodes). Failed planks fall ballistically with tumble. Leo vaults the three missing planks on arcs derived from the plank positions and leaps to the cliff from plank 26. Audit: closest failed plank, plank under Leo
intact at every frame, takeoff and landing planks intact, jump apex, rope sanity, persistence, camera visibility. Clips: idle, run, jump."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('bridge');PI=math.pi;smooth=kit.smooth;B=w2.BRIDGE;rnd=random.Random(5);G_=9.81
S.load_env('gorge_bridge')
N=B['n'];XK=[B['x0']+B['dx']*k for k in range(N)];MISS=set(B['missing']);HW=B['hw'];VL=6.0;T0=3.0;XS=-3.0;X_STOP=52.;LAST=26;XL_FAR=B['cliff_far']+1.6
def x_leo(t):return min(XS+VL*(t-T0),X_STOP) if t>=T0 else XS
def t_at_x(x):return T0+(x-XS)/VL
# the jump list: (takeoff plank, landing plank or the cliff)
JUMPS=[(7,10),(16,18),(LAST,'cliff')]
def jump_window(j):
 a,b=j;xa=XK[a];xb=XK[b] if b!='cliff' else XL_FAR;ta=t_at_x(xa);tb=t_at_x(xb);return ta,tb,xa,xb
JW=[jump_window(j) for j in JUMPS]
def leo_z(t):
 for (ta,tb,xa,xb) in JW:
  if ta<=t<=tb:u=(t-ta)/(tb-ta);T=tb-ta;A=G_*T*T/8+.25;return 4*A*u*(1-u)
 return 0.
# ---------------------------------------------------------------------------------------------------------- the collapse wave (bisect the spacing)
WALK=[k for k in range(N) if k not in MISS and k<=LAST]
tw=t_at_x(XK[0])+.8
def fail_times(d):
 ft={}
 for k in range(N):
  if k in MISS:continue
  if k<=LAST:ft[k]=tw+k*d
 ft[LAST+1]=t_at_x(XK[22])+.2;ft[LAST+2]=t_at_x(XK[22])+.55
 return ft
def min_gap(d):
 ft=fail_times(d);g=1e9;t_end=JW[-1][1]
 for t in np.arange(tw,t_end,.02):
  failed=[XK[k] for k in ft if ft[k]<=t and k<=LAST]
  if failed:g=min(g,(x_leo(t)-.25)-max(failed))
 return g
lo,hi=.05,.6
for _ in range(40):
 mid=(lo+hi)/2
 if min_gap(mid)<1.4:lo=mid
 else:hi=mid
DWAVE=(lo+hi)/2;FT=fail_times(DWAVE);print('WAVE spacing %.3f s per plank, closest approach %.2f m'%(DWAVE,min_gap(DWAVE)))
T_LAND=JW[-1][1];S.clock(T_LAND+9.0);seconds=S.seconds
# ---------------------------------------------------------------------------------------------------------- the rope (Verlet)
M_=N+2;A0=B['anchors'][0];REST=B['dx']*1.04;X0=np.array([A0+i*B['dx'] for i in range(M_)]);Z0=np.full(M_,.05)
pos=np.column_stack([X0,Z0]);prev=pos.copy();ROPE_STATE={}
def pinned(i,t):
 if i==0 or i==M_-1:return True
 k=i-1;return (k not in MISS) and (k not in FT or t<FT[k])
dt=1/48.;frame_of_step=0
for step in range(int(S.seconds*48)+2):
 t=step*dt;pin=np.array([pinned(i,t) for i in range(M_)]);new=pos+(pos-prev)*.995+np.array([0,-G_*dt*dt]);new[pin]=np.column_stack([X0,Z0])[pin];prev=pos;pos=new
 for it in range(12):
  for i in range(M_-1):
   d=pos[i+1]-pos[i];l=np.linalg.norm(d)
   if l>REST:
    c=d/l*(l-REST)
    if pin[i] and pin[i+1]:continue
    if pin[i]:pos[i+1]-=c
    elif pin[i+1]:pos[i]+=c
    else:pos[i]+=c*.5;pos[i+1]-=c*.5
 if step%2==0:ROPE_STATE[step//2+1]=pos.copy()
minz=min(float(v[:,1].min()) for v in ROPE_STATE.values());print('ROPE lowest node %.1f m'%minz)
CH=[]
for (y,dz) in ((-HW,0.),(HW,0.),(-HW,1.0),(HW,1.0)):
 CH.append((y,dz,[S.prim('cyl','Rope',(0,0,0),(.45,.36,.2),scale=(.03,.03,1),vertices=5,radius=1,depth=2) for _ in range(M_-1)]))
for f in S.keys():
 P=ROPE_STATE.get(f,ROPE_STATE[max(ROPE_STATE)])
 for (y,dz,segs) in CH:
  for i,o in enumerate(segs):
   a=Vector((P[i,0],y,P[i,1]+dz));b=Vector((P[i+1,0],y,P[i+1,1]+dz));d=b-a;o.location=(a+b)/2;o.scale=(.03,.03,max(1e-3,d.length/2));o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.keyframe_insert('location',frame=f);o.keyframe_insert('scale',frame=f);o.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- planks
PL=[]
for k in range(N):
 r=bpy.data.objects.new('Plank%d'%k,None);S.link(r);S.prim('cube','PlankBoard',(0,0,0),(.55,.38,.2),scale=(.24,HW+.1,.03),parent=r)
 for sy in (-1,1):S.prim('cyl','PlankPost',(0,sy*HW,.5),(.4,.3,.18),scale=(.025,.025,.5),vertices=5,radius=1,depth=2,parent=r)
 PL.append(dict(root=r,k=k,vx=rnd.uniform(-.4,.4),vy=rnd.uniform(-.5,.5),spin=rnd.uniform(-3.5,3.5),spin2=rnd.uniform(-2,2)))
RIV=B['river_z']+.5
def plank_state(p,t):
 k=p['k'];x=XK[k]
 if k in MISS:return Vector((x+.6,rnd_y[k],RIV+.2)),(.3*k,.2,k*.7)
 ft=FT.get(k,1e9)
 if t<ft:return Vector((x,0,.05)),(0,0,0)
 u=t-ft;z=.05-.5*G_*u*u;h=Vector((x+p['vx']*u,p['vy']*u,z))
 if h.z<RIV:h.z=RIV+rnd.uniform(0,.0)+.05*(k%3);return h,(p['spin']*3,p['spin2']*2,p['spin']*u*0+k*.4)
 return h,(p['spin2']*u*.8,p['spin']*u,p['spin']*u*.3)
rnd_y={k:rnd.uniform(-8,8) for k in range(N)}
rest_pose={}
for p in PL:
 for f in S.keys():
  t=(f-1)/S.fps;loc,rot=plank_state(p,t)
  if p['k']<=LAST and p['k'] not in MISS:
   # a small dip when Leo's foot is on the plank
   lx=x_leo(t);dxl=abs(lx-XK[p['k']])
   if dxl<.7 and leo_z(t)<.05 and t<FT.get(p['k'],1e9):loc=Vector((loc.x,loc.y,loc.z-.035*(1-dxl/.7)))
  if 'frozen' in rest_pose.get(p['k'],{}) and t>FT.get(p['k'],1e9)+4:loc,rot=rest_pose[p['k']]['frozen']
  if p['k'] in FT and loc.z<=RIV+.06 and p['k'] not in rest_pose:rest_pose[p['k']]={'frozen':(Vector(loc),rot)}
  p['root'].location=loc;p['root'].rotation_euler=rot;p['root'].keyframe_insert('location',frame=f);p['root'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root']
segs=[(0,T0-.15,'idle',1.)];cur=T0-.15
for (ta,tb,xa,xb) in JW:
 segs.append((cur,ta-.2,'run',.5));segs.append((ta-.2,tb+.25,'jump',.7));cur=tb+.25
t_stop=T0+(X_STOP-XS)/VL;segs.append((cur,t_stop,'run',.5));segs.append((t_stop,S.seconds,'idle',1.))
S.play(leo,[s for s in segs if s[1]-s[0]>.12])
for f in S.keys():
 t=(f-1)/S.fps;x=x_leo(t);yaw=PI/2*0+PI/2
 if t>t_stop:yaw=PI/2+PI*smooth((t-t_stop)/.9)
 root.location=(x,0,leo_z(t));root.rotation_euler=(0,0,yaw);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;x=x_leo(t);gz.location=((x+12,0,1.2) if t<t_stop else (XK[14],0,-2.));gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
ev=[(ta-1.0,tb+.9,'jump%d'%i) for i,(ta,tb,xa,xb) in enumerate(JW)];cuts=[('gorge',0,T0+.8,'wide')];last=T0+.8;alt=0
for a,b,kind in ev:
 a=max(a,last)
 if b-a<.8:continue
 if a-last>1.2:
  n=max(1,int((a-last)//3.6));seg=(a-last)/n
  for j in range(n):cuts.append(('run %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','front','below','side')[alt%4]));alt+=1
 cuts.append((kind,a,b,kind));last=b
cuts.append(('collapse',last,S.seconds,'end'))
def pos_(kind,t,u):
 x=x_leo(t);z=leo_z(t);lp=Vector((x,0,z+1.0))
 if kind=='wide':return Vector((20+4*u,-15,4)),Vector((20,0,0)),17
 if kind=='follow':return Vector((x-5.2,-1.4,2.3)),lp+Vector((3,0,0)),30
 if kind=='front':return Vector((x+5.5,1.3,1.5)),Vector((x-3.5,0,.4)),28
 if kind=='below':return Vector((x-5,-2.5,-11)),Vector((x-1,0,1.0)),24
 if kind=='side':return Vector((x+.5,-9.5,1.4)),lp,32
 if kind.startswith('jump'):
  ta,tb,xa,xb=JW[int(kind[4:])];m=(xa+xb)/2;return Vector((m-2.5,-5.5,2.2)),Vector((m+.5,0,1.1)),28
 return Vector((X_STOP+2.0,-4.0,1.9)),Vector((XK[20],0,-1.0)),26
S.cameras(cuts,pos_,('Plank','Rope'),cand=[(0,0,1.),(0,0,2.5),(0,2.5,0),(0,-2.5,0),(2.5,0,0),(-2.5,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
mg=min_gap(DWAVE)
if mg<1.2 or mg>1.7:issues.append('AUDIT pursuit: closest failed plank %.2f m behind Leo (want 1.2-1.7)'%mg)
bad=0
for t in np.arange(T0,T_LAND,.03):
 x=x_leo(t)
 if leo_z(t)>.02:continue
 under=[k for k in range(N) if abs(x-XK[k])<=.55]
 if x>=0 and x<=B['anchors'][1] and not under:continue
 for k in under:
  if k in MISS or t>=FT.get(k,1e9)+0.:bad+=1
if bad:issues.append('AUDIT footing: Leo stands over a missing or failed plank at %d sampled instants'%bad)
for i,(ta,tb,xa,xb) in enumerate(JW):
 a=JUMPS[i][0];b=JUMPS[i][1]
 if a in MISS or FT.get(a,1e9)<ta-.25:issues.append('AUDIT jump: takeoff plank %d of jump %d has already failed'%(a,i+1))
 if b!='cliff' and (b in MISS or FT.get(b,1e9)<tb):issues.append('AUDIT jump: landing plank %d of jump %d has failed'%(b,i+1))
 T=tb-ta;A=G_*T*T/8+.25
 if A<.5:issues.append('AUDIT jump: jump %d apex %.2f m is too low'%(i+1,A))
if minz<-52:issues.append('AUDIT rope: a rope node falls below the river (%.1f m)'%minz)
print('BRIDGE gap %.2f m, jumps %s, lowest rope %.1f m'%(mg,[(round(ta,1),round(tb,1)) for ta,tb,_,_ in JW],minz))
def snd(A):
 A.track('wind',A.noise(A.N,15)*(.5+.3*np.sin(2*PI*.2*A.t)),.4)
 sn=A.buf();k=np.arange(int(.3*A.SR))/A.SR;crack=A.noise(len(k),3)*np.exp(-k*25)+np.sin(2*PI*180*k)*np.exp(-k*18)*.4
 for kk,t in sorted(FT.items()):A.at(sn,t,crack*(.5+.5*A.rng.random()),.8)
 A.track('planks',sn,.7);st=A.buf();k2=A.burst(.1,5,40.)
 for t in np.arange(T0,t_stop,.17):A.at(st,t,k2,.5)
 A.track('steps',st,.4);cr=np.zeros(A.N+A.SR)
 A.at(A.buf(),0,k2*0)
 A.track('creaks',(np.sin(2*PI*(110+30*np.sin(A.t*3))*A.t)*.1)*np.clip((A.t-T0)/2,0,1)*np.clip((T_LAND+4-A.t)/4,0,1),.2)
 A.track('music',A.chords(((130.8,155.6,196),(116.5,146.8,174.6),(103.8,130.8,155.6),(110,138.6,164.8)),.22),.4)
S.audio(snd)
S.finish(issues,[root],world=(.55,.7,.9))
