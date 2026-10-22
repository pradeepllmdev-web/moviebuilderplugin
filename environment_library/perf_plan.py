"""Performance planner (pure Python + numpy, no Blender): compiles a declarative scene spec into per-frame motion, clips, speech, hand reaches and prop tracks, and audits the result.

    plan=perf_plan.compile(spec, registry)        # spec: see below; registry: cast_registry.Registry (or {id: look})
    plan.frames, plan.actors[id].X/Y/H (per frame), .clips, .hands, plan.lines, plan.events, plan.props, plan.audit()

Spec (all plain data, JSON-able):
    dict(id='s01', title=.., location=dict(preset='village_square', seed=2, objects=[..]), time='day'|'dusk'|'night'|'dawn'|'overcast', ambience='wind', music='calm',
         cast=[dict(id='mara', at=[x,y], face=[x,y]|'id'), ...], props=[dict(id='lantern1', kind='lantern', at=[x,y], on='table1'|z=..)],
         steps=[beat | [beat, beat, ...], ...])        # a step is one beat or a list of beats that run at the same time; steps run one after another
Beats (who = character id):
    go      who, to (point | character | prop | marker | object | seat), gait ('walk'|'run'|gait name, default from posture), stop (m before a character/prop target), face (point/id after arriving), via [points], pace
    turn    who, to                         face a point or character
    say     who, text, mood (serious|angry|warm|concern|sad|joy), to    a spoken line with lip sync, eye lines, the listener's reaction and body turns
    act     who, clip, dur, to, scale       any library clip in place (wave, nod, shrug, laugh, push, kick, bow, startle, think, talk, argue, cele, hit, punch, block, dodge, jump, fall, getup, kneel, look, hips, cut)
    react   who, kind, to                   a reaction clip (startle, nod, laugh, think, shrug, wave, cele, block, dodge, hit, bow) turned towards what it reacts to
    look    who, at, dur                    eyes and head only
    emote   who, kind (smile|frown|concern|sad|brows), dur
    wait    dur                             everybody holds
    take    who, prop, hand ('R'|'L'|'both')            walks to the prop, reaches with IK, carries it
    put     who, prop, at (point) | on (object id)      carries it to the place and lets go
    give    who, to, prop                   hands a carried prop to another character
    push    who, prop, dist, dir            pushes a prop with both hands (the prop slides while the hands stay on it)
    sit     who, on (seat id like 'bench1.0'), face      walks to the seat, turns, sits;   stand  who
    sfx     name, at (offset s)             a sound event (door, thud, clang, splash, bell, gong, crash, thunder, chime, knock)
    cam     size ('wide'|'medium'|'close'|'insert'), subject, mode ('follow'|'static'|'high'|'low'|'track')   hint for the camera director
Everything is simulated at 24 fps; the planter never hides or removes anything. Heading is the world direction a character faces (radians); the Blender root rotation is heading+pi/2 (the rig faces -Y).
Planted feet: a walk's ground speed comes from the gait table and the character's size, and the clip's play scale is derived from it, never tuned by hand."""
import math,random
import numpy as np
import dialogue as dg,gaits,perf_locations as pl
FPS=24
CLIP_FRAMES=dict(argue=96,block=72,bow=72,cele=120,climb=96,crawl=96,cut=72,dodge=72,fall=72,getup=72,hips=72,hit=72,idle=96,jump=72,kick=72,kneel=96,laugh=96,lie=96,look=144,nod=72,pick=120,punch=72,push=72,run=48,shrug=72,sit=216,startle=72,talk=96,think=96,wave=72)
for _g,_v in gaits.GAITS.items():CLIP_FRAMES.setdefault(_v['clip'],_v['cycle'])
ACT_CLIPS=('climb','pick','argue','block','bow','cele','cut','dodge','fall','getup','hips','hit','jump','kick','kneel','laugh','lie','look','nod','punch','push','shrug','startle','talk','think','wave','idle')
QUICK=dict(nod=.7,shrug=.75,wave=.75,startle=.8,think=.75,laugh=.7,cele=.7,block=.8,bow=.8,argue=.7,talk=.8,hips=.8,pick=.8)   # gestures play a little quicker than the library clip (the film is short)
SEATED_OK=('look','emote','say')
MOODS=dg.MOODS
SIT_DOWN=(1,110)             # frames of the sit clip: standing -> seated (hips down by frame 97), then held
SIT_HIPS_FWD=.11             # seated hips are this far in front of the root (x size)
REACH_STAND=.46              # distance (x size) the actor stands from something it takes
CARRY={'R':[(-.34,-.4,.78)],'L':[(.34,-.4,.78)],'both':[(-.2,-.44,.8),(.2,-.44,.8)]}
DURATION_PROVIDER=None   # fn(voice, text, mood) -> seconds of the recorded line or None; perf_movie / perf_scene set it so lines last as long as the real voice
class SpecError(ValueError):pass
def wrap(a):
 while a>math.pi:a-=2*math.pi
 while a<-math.pi:a+=2*math.pi
 return a
def lerp_angle(a,b,u):return a+wrap(b-a)*u
def ease(u):u=max(0.,min(1.,u));return u*u*(3-2*u)
def _segdist(p0,p1,c):
 dx,dy=p1[0]-p0[0],p1[1]-p0[1];L2=dx*dx+dy*dy
 t=0. if L2<1e-9 else max(0.,min(1.,((c[0]-p0[0])*dx+(c[1]-p0[1])*dy)/L2));return math.hypot(p0[0]+dx*t-c[0],p0[1]+dy*t-c[1]),t
class Router:
 """grid A* around circular obstacles (x,y,r): cells inside an obstacle grown by `margin` are blocked, the start and goal discs are freed, the path is pulled straight where it can be"""
 def __init__(s,obst,half,margin=.4,cell=.25):
  s.cell=cell;s.hx,s.hy=half[0]+6,half[1]+6;s.nx,s.ny=int(2*s.hx/cell)+1,int(2*s.hy/cell)+1;s.margin=margin
  xs=np.arange(s.nx)*cell-s.hx;ys=np.arange(s.ny)*cell-s.hy;X,Y=np.meshgrid(xs,ys,indexing='ij');m=np.zeros((s.nx,s.ny),bool)
  for c in obst:m|=(X-c[0])**2+(Y-c[1])**2<(c[2]+margin)**2
  s.blocked=m
 def cellof(s,p):return (min(s.nx-1,max(0,int(round((p[0]+s.hx)/s.cell)))),min(s.ny-1,max(0,int(round((p[1]+s.hy)/s.cell)))))
 def clear(s,p,q,free,mask=None,extra=None):
  mask=s.blocked if mask is None else mask;n=max(2,int(math.hypot(q[0]-p[0],q[1]-p[1])/(s.cell*.5)))
  for i in range(n+1):
   x=p[0]+(q[0]-p[0])*i/n;y=p[1]+(q[1]-p[1])*i/n;c=s.cellof((x,y))
   if extra is not None and extra[c]:return False
   if mask[c] and not any(math.hypot(x-f[0],y-f[1])<f[2] for f in free):return False
  return True
 def route(s,p0,p1,free_r=.7,extra=(),start_r=.7):
  free=[(p0[0],p0[1],start_r),(p1[0],p1[1],free_r)];emask=None
  if extra:
   emask=np.zeros_like(s.blocked)
   for (ex,ey,er) in extra:
    c=s.cellof((ex,ey));r=int((er+s.margin)/s.cell)+1
    for i in range(max(0,c[0]-r),min(s.nx,c[0]+r+1)):
     for j in range(max(0,c[1]-r),min(s.ny,c[1]+r+1)):
      if math.hypot((i-c[0])*s.cell,(j-c[1])*s.cell)<er+s.margin:emask[i,j]=True
  if s.clear(p0,p1,free,s.blocked,emask):return [tuple(p0),tuple(p1)]
  import heapq
  a,b=s.cellof(p0),s.cellof(p1);blocked=s.blocked.copy()
  for f in free:
   c=s.cellof(f);r=int(f[2]/s.cell)+1
   for i in range(max(0,c[0]-r),min(s.nx,c[0]+r+1)):
    for j in range(max(0,c[1]-r),min(s.ny,c[1]+r+1)):
     if math.hypot((i-c[0])*s.cell,(j-c[1])*s.cell)<f[2]:blocked[i,j]=False
  if emask is not None:
   blocked|=emask
   for f in free:     # the cells right at the start and at the goal are always walkable
    c=s.cellof(f);r=int(.4/s.cell)+1
    for i in range(max(0,c[0]-r),min(s.nx,c[0]+r+1)):
     for j in range(max(0,c[1]-r),min(s.ny,c[1]+r+1)):
      if math.hypot((i-c[0])*s.cell,(j-c[1])*s.cell)<.4:blocked[i,j]=False
  g={a:0.};prev={};h=[(0.,a)];done=set();N=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
  while h:
   _,c=heapq.heappop(h)
   if c in done:continue
   done.add(c)
   if c==b:break
   for d in N:
    n=(c[0]+d[0],c[1]+d[1])
    if not (0<=n[0]<s.nx and 0<=n[1]<s.ny) or blocked[n]:continue
    if d[0] and d[1] and (blocked[c[0]+d[0],c[1]] or blocked[c[0],c[1]+d[1]]):continue
    ng=g[c]+(1.414 if d[0] and d[1] else 1.)
    if ng<g.get(n,1e9):g[n]=ng;prev[n]=c;heapq.heappush(h,(ng+math.hypot(n[0]-b[0],n[1]-b[1]),n))
  if b not in prev and a!=b:return s.route(p0,p1,free_r,(),start_r) if extra else [tuple(p0),tuple(p1)]   # no way round the characters: ignore them, keep the solids
  cells=[b]
  while cells[-1]!=a:cells.append(prev[cells[-1]])
  pts=[tuple(p0)]+[(c[0]*s.cell-s.hx,c[1]*s.cell-s.hy) for c in reversed(cells[1:-1])]+[tuple(p1)]
  out=[pts[0]];i=0
  while i<len(pts)-1:   # string pulling
   j=len(pts)-1
   while j>i+1 and not s.clear(pts[i],pts[j],free,s.blocked,emask):j-=1
   out.append(pts[j]);i=j
  return out
def route(p0,p1,obst,half=(30,30),margin=.4):return Router(obst,half,margin).route(p0,p1)
def round_corners(pts,r,n=6):
 """polyline with every interior corner replaced by a quadratic curve of about radius r (people do not turn on the spot while walking)"""
 pts=[tuple(p) for p in pts]
 if len(pts)<3 or r<=.05:return pts
 out=[pts[0]]
 for i in range(1,len(pts)-1):
  p0,p1,p2=pts[i-1],pts[i],pts[i+1];d0=math.hypot(p0[0]-p1[0],p0[1]-p1[1]);d1=math.hypot(p2[0]-p1[0],p2[1]-p1[1]);k=min(r,d0*.45,d1*.45)
  if k<.05 or d0<1e-6 or d1<1e-6:out.append(p1);continue
  a=(p1[0]+(p0[0]-p1[0])/d0*k,p1[1]+(p0[1]-p1[1])/d0*k);b=(p1[0]+(p2[0]-p1[0])/d1*k,p1[1]+(p2[1]-p1[1])/d1*k)
  for j in range(n+1):
   u=j/n;out.append(((1-u)**2*a[0]+2*u*(1-u)*p1[0]+u*u*b[0],(1-u)**2*a[1]+2*u*(1-u)*p1[1]+u*u*b[1]))
 out.append(pts[-1]);return out
def polyline_samples(points,speed,dt=1./FPS):
 """positions along a polyline at constant speed: list of (x,y,raw_heading); the last sample is the end point"""
 pts=[tuple(p) for p in points];segs=[(a,b,math.hypot(b[0]-a[0],b[1]-a[1])) for a,b in zip(pts,pts[1:])];segs=[s for s in segs if s[2]>1e-6]
 if not segs:return [(pts[0][0],pts[0][1],None)]
 total=sum(s[2] for s in segs);n=max(1,int(round(total/speed/dt)));out=[];k=0;acc=0.
 for i in range(n+1):
  s=min(total,total*i/n)
  while k<len(segs)-1 and s>acc+segs[k][2]+1e-9:acc+=segs[k][2];k+=1
  a,b,L=segs[k];u=min(1.,(s-acc)/L);out.append((a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u,math.atan2(b[1]-a[1],b[0]-a[0])))
 return out
EXTRA_SPECIES=('rabbit','cat','badger','boar','mouse','fox','owl','bear','ox','heron','wolf','elder')
EXTRA_ACC=('hat_cap','hat_straw','scarf','satchel','backpack','apron','bowtie','cane','flower','glasses')
EXTRA_POSTURES=('neutral','proud','tired','jaunty','hunched')
def make_extras(spec,layout,starts):
  """background characters of a scene (spec 'extras': dict(n, area=[x0,y0,x1,y1], focus=[x,y], seed, species)): deterministic looks and places that avoid solids and the cast, all turned towards the focus. They stand and breathe; the planner routes the cast around them."""
  ex=spec.get('extras')
  if not ex:return []
  import cast_registry as cr
  rnd=random.Random(ex.get('seed',1));x0,y0,x1,y1=ex['area'];focus=ex.get('focus',[0,0]);out=[];tries=0;species=ex.get('species') or list(EXTRA_SPECIES)
  while len(out)<ex['n'] and tries<ex['n']*60:
   tries+=1;x,y=rnd.uniform(x0,x1),rnd.uniform(y0,y1)
   if any(math.hypot(x-c[0],y-c[1])<c[2]+.6 for c in layout['obstacles']) or any(math.hypot(x-sx,y-sy)<1.8 for sx,sy in starts) or any(math.hypot(x-o['x'],y-o['y'])<1.25 for o in out):continue
   sp=rnd.choice(species);acc=rnd.sample(EXTRA_ACC,rnd.choice([0,1,1,2]))
   if sum(1 for a in acc if a in('hat_cap','hat_straw'))>1:acc=acc[:1]
   t=cr.SPECIES[sp]['tint'];tint=tuple(round(min(1.9,max(.1,v*rnd.uniform(.8,1.15))),3) for v in t)
   look=cr.resolve(dict(id='x%d'%len(out),name='Extra',species=sp,accessories=acc,tint=tint,posture=rnd.choice(EXTRA_POSTURES),height=cr.SPECIES[sp]['height']*rnd.uniform(.9,1.1)))
   h=math.atan2(focus[1]-y,focus[0]-x)+rnd.uniform(-.35,.35);out.append(dict(id='x%d'%len(out),x=x,y=y,h=h,look=look,focus=list(focus)))
  return out
class Prop:
 def __init__(s,spec,pos,table):
  s.id=spec['id'];s.kind=spec['kind'];k=PROP_KINDS_CHECK(s.kind);s.size=tuple(x*spec.get('size',1.) for x in k['size']);s.carry=k['carry'];s.yaw=math.radians(spec.get('yaw',0.));s.pos=tuple(pos);s.on=spec.get('on');s.track=[(0.,'world',tuple(pos))]
 def at(s,t,plan):
  cur=None
  for seg in s.track:
   if seg[0]<=t+1e-9:cur=seg
   else:break
  if cur[1]=='world':return cur[2]
  return plan.held_pos(cur[2],cur[3],t,s)
def PROP_KINDS_CHECK(kind):
 if kind not in pl.PROP_KINDS:raise SpecError('unknown prop kind %r (known: %s)'%(kind,', '.join(sorted(pl.PROP_KINDS))))
 return pl.PROP_KINDS[kind]
class Actor:
 def __init__(s,id_,look,x,y,h):
  s.id=id_;s.look=look;s.size=look['scale'][2];s.stride=look['scale'][1];s.radius=look['radius'];s.X=[x];s.Y=[y];s.H=[h];s.clips=[];s.hands={'R':[],'L':[]};s.state='stand';s.seat=None;s.holding=None;s.emotes=[];s.ignore=[];s.walks=[];s.gait=look['gait'];s.last_gesture=None
 @property
 def t(s):return (len(s.X)-1)/FPS
 def pos(s):return s.X[-1],s.Y[-1]
 def hold(s,dur):
  n=max(0,int(round(dur*FPS)))
  for _ in range(n):s.X.append(s.X[-1]);s.Y.append(s.Y[-1]);s.H.append(s.H[-1])
 def pad_to(s,t):s.hold(t-s.t)
 def walks_now(s,t):return any(w[0]<=t<=w[1] for w in s.walks)
 def turn_to(s,h1,dur=None):
  h0=s.H[-1];d=abs(wrap(h1-h0))
  if d<math.radians(4):return 0.
  dur=max(dur or 0.,d/math.radians(190.),.3);n=max(2,int(round(dur*FPS)));x,y=s.X[-1],s.Y[-1]
  if d>math.radians(25):s.hold(.16)      # the eyes and head go first, the body follows a moment later
  t0=s.t
  for i in range(1,n+1):s.X.append(x);s.Y.append(y);s.H.append(lerp_angle(h0,h1,ease(i/n)))
  if d>math.radians(55) and s.state=='stand':s.play('walk',t0,s.t,1.5)   # a big turn is taken with small steps, not by spinning on the spot
  return n/FPS
 def face_point(s,p,dur=None):return s.turn_to(math.atan2(p[1]-s.Y[-1],p[0]-s.X[-1]),dur)
 def play(s,name,t0,t1,scale=1.,**opt):
  if s.clips and s.clips[-1][1]>t0+1e-6:
   last=s.clips[-1]
   if last[0]>=t0-1e-6:s.clips.pop()
   else:s.clips[-1]=(last[0],t0,last[2],last[3],last[4])
  if t1>t0+1e-6:s.clips.append((t0,t1,name,scale,opt))
 def walk(s,points,speed,gait,scale,tau=.14):
  smp=polyline_samples(points,speed)
  if len(smp)<2:return 0.
  h_raw=smp[0][2];t0=s.t;h=s.H[-1];k=1-math.exp(-1./FPS/tau)
  for (x,y,hr) in smp[1:]:
   if hr is not None:h=h+wrap(hr-h)*k
   s.X.append(x);s.Y.append(y);s.H.append(h)
  t1=s.t;s.play(gaits.GAITS[gait]['clip'],t0,t1,scale);s.walks.append((t0,t1,gait,scale,speed));return t1-t0
class Plan:
 def __init__(s,spec,registry,layout=None):
  s.spec=spec;s.layout=layout or pl.layout(spec.get('location',dict(preset='meadow')));s.lint=[];s.lines=[];s.events=[];s.sfx=[];s.cams=[];s.steps_t=[];s.steps_text=[]
  looks={}
  for c in spec.get('cast',[]):
   looks[c['id']]=registry.resolve(c['id']) if hasattr(registry,'resolve') else registry[c['id']]
  s.looks=looks;s.actors={}
  for c in spec['cast']:
   x,y=c['at'][:2];s.actors[c['id']]=Actor(c['id'],looks[c['id']],x,y,0.)
  s.props={}
  for p in spec.get('props',[]):
   z=p.get('z');base=0.;pk=PROP_KINDS_CHECK(p['kind']);sz=pk['size'][2]*p.get('size',1.)
   if p.get('on'):
    if p['on'] not in s.layout['surfaces']:raise SpecError('prop %s sits on %r which is not a surface of the location'%(p['id'],p['on']))
    base=s.layout['surfaces'][p['on']][2]
   s.props[p['id']]=Prop(p,(p['at'][0],p['at'][1],(z if z is not None else base+sz/2)),None)
  for c in spec['cast']:
   a=s.actors[c['id']];f=c.get('face');a.H[0]=s._heading_to(a,f) if f is not None else math.pi/2
  walls=s.layout.get('walls',[])
  for c in spec['cast'] if walls else []:     # nobody starts squeezed against a wall or staring into one
   a=s.actors[c['id']];x,y=a.X[0],a.Y[0];cx,cy,r=min(walls,key=lambda w:math.hypot(x-w[0],y-w[1])-w[2]);d=math.hypot(x-cx,y-cy)-r;need=.95+.3*a.radius
   if d<need:
    ux,uy=(x-cx,y-cy) if math.hypot(x-cx,y-cy)>1e-6 else (0.,1.);L=math.hypot(ux,uy);ux,uy=ux/L,uy/L;a.X[0]=x+ux*(need-d);a.Y[0]=y+uy*(need-d)
   toward=abs(wrap(math.atan2(cy-a.Y[0],cx-a.X[0])-a.H[0]))
   if d<1.8 and toward<math.radians(60):a.H[0]=math.atan2(a.Y[0]-cy,a.X[0]-cx)    # turn to face the room
  s.extras=make_extras(spec,s.layout,[(c['at'][0],c['at'][1]) for c in spec['cast']])
  if s.extras:s.layout=dict(s.layout,obstacles=s.layout['obstacles']+[(e['x'],e['y'],e['look']['radius']*1.1) for e in s.extras])
  for c in spec['cast']:     # a start inside a solid (a new stand, a bench) is moved to the nearest free spot
   a=s.actors[c['id']];fp=s._free_goal(a,(a.X[0],a.Y[0]))
   if fp!=(a.X[0],a.Y[0]):a.X[0],a.Y[0]=fp
  s.t_end=0.;s.router=Router(s.layout['obstacles'],s.layout['half'],margin=.55)   # centre-to-solid clearance: a body, an apron or a skirt is wider than the walking point
 # ------------------------------------------------------------------------------------------------------ references
 def _heading_to(s,a,ref):
  p=s.point(ref);return math.atan2(p[1]-a.Y[-1],p[0]-a.X[-1])
 def point(s,ref,t=None):
  """(x,y,z) of a point, character, prop, marker, object or seat"""
  if isinstance(ref,(list,tuple)):return (ref[0],ref[1],ref[2] if len(ref)>2 else 0.)
  if ref in s.actors:a=s.actors[ref];return (a.X[-1],a.Y[-1],0.)
  if ref in s.props:
   p=s.props[ref];return p.at(s.cur_t() if t is None else t,s)
  if ref in s.layout['markers']:m=s.layout['markers'][ref];return (m[0],m[1],0.)
  if ref in s.layout['seats']:q=s.layout['seats'][ref];return (q[0],q[1],q[2])
  for o in s.layout['objects']:
   if o['id']==ref:return (o['at'][0],o['at'][1],0.)
  raise SpecError('unknown reference %r (not a point, character, prop, marker, seat or object)'%(ref,))
 def cur_t(s):return max(a.t for a in s.actors.values())
 def local_to_world(s,a,t,l):
  f=min(len(a.X)-1,max(0,int(round(t*FPS))));h=a.H[f]+math.pi/2;c,sn=math.cos(h),math.sin(h);k=a.size
  return (a.X[f]+(c*l[0]-sn*l[1])*k,a.Y[f]+(sn*l[0]+c*l[1])*k,l[2]*k)
 def hand_target(s,a,hand,t):
  """(influence, world position) of an actor's IK hand target at time t, from its keys"""
  ks=a.hands[hand]
  if not ks:return 0.,None
  def ev(k):
   mode=k[2][0]
   if mode=='local':return s.local_to_world(a,t,k[2][1])
   if mode=='world':return k[2][1]
   return s.props[k[2][1]].pos
  if t<=ks[0][0]:return ks[0][1],ev(ks[0])
  for k0,k1 in zip(ks,ks[1:]):
   if k0[0]<=t<=k1[0]:
    u=ease((t-k0[0])/max(1e-6,k1[0]-k0[0]));p0,p1=ev(k0),ev(k1);return k0[1]+(k1[1]-k0[1])*u,tuple(p0[i]+(p1[i]-p0[i])*u for i in range(3))
  return ks[-1][1],ev(ks[-1])
 def held_pos(s,who,hand,t,prop):
  a=s.actors[who];hs=('R','L') if hand=='both' else (hand,);ps=[s.hand_target(a,h,t)[1] for h in hs]
  if any(p is None for p in ps):return prop.pos
  return tuple(sum(p[i] for p in ps)/len(ps) for i in range(3))
 # ------------------------------------------------------------------------------------------------------ running
 def _snapshot(s):
  import copy
  return copy.deepcopy(dict(actors=s.actors,props=s.props,lines=s.lines,events=s.events,sfx=s.sfx,cams=s.cams,steps_t=s.steps_t,lint=s.lint))
 def _restore(s,snap):
  import copy
  for k,v in copy.deepcopy(snap).items():setattr(s,k,v)
 def _step_collisions(s,t0,end):
  """pairs of characters that come too close during [t0,end] (the retry threshold is a little looser than the audit's)"""
  f0,f1=int(t0*FPS),int(end*FPS)+1;ids=list(s.actors);out=[]
  for i in range(len(ids)):
   for j in range(i+1,len(ids)):
    A,B=s.actors[ids[i]],s.actors[ids[j]]
    if len(A.X)<=f0:continue
    xa,ya=np.array(A.X[f0:f1]),np.array(A.Y[f0:f1]);xb,yb=np.array(B.X[f0:f1]),np.array(B.Y[f0:f1]);n=min(len(xa),len(xb))
    if n and np.hypot(xa[:n]-xb[:n],ya[:n]-yb[:n]).min()<.78*(A.radius+B.radius)-.0:out.append((ids[i],ids[j]))
  return out
 def run(s):
  steps=s.spec['steps']
  for i,st in enumerate(steps):
   beats=st if isinstance(st,list) else [st];s._spread(beats);t0=s.cur_t();snap=s._snapshot();delays={};tries=0
   while True:
    spoke=s._run_step(i,beats,t0,delays)
    col=s._step_collisions(t0,max(a.t for a in s.actors.values())) if len([b for b in beats if b.get('do')=='go'])>1 else []
    if not col or tries>=5:break
    s._restore(snap);tries+=1;a,b=col[0];later=b if b in delays or a not in [x.get('who') for x in beats] else b;delays[later]=delays.get(later,0.)+.9
   for L in spoke:s._listen(L,set(b.get('who') for b in beats),t0,max(a.t for a in s.actors.values()))
  end=s.cur_t()+2.5
  for a in s.actors.values():a.pad_to(end)
  s.frames=len(next(iter(s.actors.values())).X);s.seconds=(s.frames-1)/FPS
  for a in s.actors.values():s._finish_clips(a)
  return s
 def _run_step(s,i,beats,t0,delays):
  s.steps_t.append(t0)
  for a in s.actors.values():a.pad_to(t0)
  used=set();spoke=[];s._hold_until=0.
  for b in beats:
   who=b.get('who')
   if b['do'] in ('wait','sfx','cam'):getattr(s,'b_'+b['do'])(b,t0);continue
   if b['do'] in ('look','emote'):
    if b.get('who') not in s.actors:raise SpecError('step %d: %s has no character %r (cast: %s)'%(i,b['do'],b.get('who'),', '.join(s.actors)))
    getattr(s,'b_'+b['do'])(b,t0);continue
   if who not in s.actors:raise SpecError('step %d: %s has no character %r (cast: %s)'%(i,b['do'],who,', '.join(s.actors)))
   if who in used:raise SpecError('step %d: %s has two beats at the same time'%(i,who))
   used.add(who)
   if not hasattr(s,'b_'+b['do']):raise SpecError('step %d: unknown beat %r'%(i,b['do']))
   if delays.get(who):s.actors[who].hold(delays[who])
   r=getattr(s,'b_'+b['do'])(b,t0+delays.get(who,0.))
   if b['do']=='say':spoke.append(r)
  if len([1 for b in beats if b['do']=='say'])>1:raise SpecError('step %d: two lines at the same time (put each line in its own step)'%i)
  end=max(max(a.t for a in s.actors.values()),s._hold_until)
  for a in s.actors.values():a.pad_to(end)
  return spoke
 def _finish_clips(s,a):
  src=sorted(a.clips,key=lambda c:c[0]);out=[];cur=0.
  for k,(t0,t1,name,sc,opt) in enumerate(src):
   if opt.get('hold'):   # a held pose (seated, fallen) lasts until the next clip starts
    nxt=src[k+1][0] if k+1<len(src) else s.seconds;opt=dict(opt,len=t1-t0);t1=max(t1,nxt)
   t0=max(t0,cur)
   if t1-t0<.05:continue
   if t0>cur+.04:out.append((cur,t0,'idle',1.,{}))
   out.append((t0,t1,name,sc,opt));cur=t1
  if cur<s.seconds-.04:out.append((cur,s.seconds,'idle',1.,{}))
  a.clips=out
 def _listen(s,L,used,t0,end):
  """listeners with no beat in the step: face the speaker if far off, then react at the end of the line"""
  for name,a in s.actors.items():
   if name in used or name==L['speaker'] or a.state!='stand':continue
   c=('think' if (L['text'].rstrip().endswith('?') and L['mood']=='concern') else ('nod' if re.search(r"\b(yes|agreed|deal|exactly|of course|right)\b",L['text'].lower()) else None))
   if L['to']==name and c:
    ta=max(t0,L['t1']-.9);tb=min(end,L['t1']+.5)
    if tb-ta>=.4:a.play(c,ta,tb,QUICK.get(c,1.))
 # ------------------------------------------------------------------------------------------------------ beats
 def _stand_only(s,a,what):
  if a.state!='stand':raise SpecError('%s: %s cannot %s while %s'%(s.cur_t(),a.id,what,a.state))
 def _spread(s,beats):
  """parallel walkers to the same target get side-by-side slots so they do not cross"""
  g={}
  for b in beats:
   if b.get('do')=='go' and isinstance(b.get('to'),str) and b['to'] not in ('',):g.setdefault(b['to'],[]).append(b)
  for k,v in g.items():
   if len(v)>1:
    for i,b in enumerate(v):b['_slot']=(i,len(v))
 def b_wait(s,b,t0):
  for a in s.actors.values():a.pad_to(t0+b['dur'])
  s.events.append(dict(kind='wait',t0=t0,t1=t0+b['dur']))
 def b_sfx(s,b,t0):s.sfx.append((t0+b.get('at',0.),b['name'],b.get('who'),b.get('gain',1.)))
 def b_cam(s,b,t0):s.cams.append(dict(t0=t0,**{k:v for k,v in b.items() if k!='do'}))
 def b_turn(s,b,t0):
  a=s.actors[b['who']];s._stand_only(a,'turn');p=s.point(b['to']);d=a.face_point(p);s.events.append(dict(kind='turn',who=a.id,t0=t0,t1=t0+d,to=b['to']))
 def b_point(s,b,t0):
  """point: the arm reaches out toward a point, character or prop while the head looks there; dur seconds, hand R or L"""
  a=s.actors[b['who']];tp=s.point(b['at']);dur=b.get('dur',1.6);hd=b.get('hand','R')
  if a.state!='stand':raise SpecError('point: %s must be standing'%a.id)
  dx,dy=tp[0]-a.X[-1],tp[1]-a.Y[-1];L=math.hypot(dx,dy) or 1.;ux,uy=dx/L,dy/L;side=-1. if hd=='R' else 1.
  M=(a.X[-1]+ux*.62*a.size-uy*side*.12*a.size,a.Y[-1]+uy*.62*a.size+ux*side*.12*a.size,a.size*(1.18+.5*max(-.4,min(.5,(tp[2]-a.size*1.2)/max(1.,L)))))
  if abs(wrap(math.atan2(dy,dx)-a.H[-1]))>math.radians(35):a.face_point(tp,.7)
  ts=a.t;ks=a.hands[hd];prev=(ks[-1][1],ks[-1][2]) if ks else (0.,('local',(-.36 if hd=='R' else .36,-.1,.66)))
  ks.append((ts,prev[0],prev[1]));ks.append((ts+.35,1.,('world',M)));ks.append((ts+.35+dur,1.,('world',M)));ks.append((ts+.35+dur+.45,0.,('local',(-.36 if hd=='R' else .36,-.1,.66))))
  a.hold(.35+dur+.45);s.events.append(dict(kind='point',who=a.id,t0=ts,t1=a.t,to=b['at']));s.b_look(dict(do='look',who=a.id,at=b['at'],dur=dur+.6),ts)
 def b_look(s,b,t0):
  a=s.actors[b['who']];s._hold_until=max(s._hold_until,t0+b.get('dur',1.));s.events.append(dict(kind='look',who=a.id,t0=t0,t1=t0+b.get('dur',1.),to=b['at']))
 def b_emote(s,b,t0):
  a=s.actors[b['who']];d=b.get('dur',2.);a.emotes.append((t0,t0+d,b['kind']));s._hold_until=max(s._hold_until,t0+d);s.events.append(dict(kind='emote',who=a.id,t0=t0,t1=t0+d,what=b['kind']))
 def b_act(s,b,t0):
  a=s.actors[b['who']];clip=b['clip']
  if clip=='joy':    # joy has ten different celebrations, picked per character and per time, so a crowd never repeats one animation
   V=[[('cele',1.)],[('jump',1.)],[('laugh',1.),('cele',.85)],[('wave',1.),('cele',1.15)],[('hips',1.)],[('bow',1.),('jump',1.)],[('nod',1.2),('cele',1.)],[('cele',.8),('laugh',1.)],[('hips',1.),('wave',1.)],[('jump',1.),('laugh',1.)]]
   s._joys=getattr(s,'_joys',0);i=(sum(map(ord,a.id))+3*s._joys)%len(V);s._joys+=1
   for c2,sc2 in V[i]:s.b_act(dict(b,clip=c2,scale=sc2),t0)
   return
  if clip not in ACT_CLIPS:raise SpecError('act: unknown clip %r (known: %s)'%(clip,', '.join(ACT_CLIPS)))
  if a.state=='sit' and clip not in SEATED_OK:raise SpecError('%s acts %r while seated'%(a.id,clip))
  if a.state=='down' and clip!='getup':raise SpecError('%s is on the ground and can only get up'%a.id)
  if clip=='getup' and a.state!='down':raise SpecError('%s gets up without having fallen'%a.id)
  if b.get('to') is not None:a.face_point(s.point(b['to']))
  ts=a.t;nat=CLIP_FRAMES[clip]/FPS;sc=b.get('scale',QUICK.get(clip,1.))
  dur=b.get('dur',nat*sc) if clip not in ('fall','getup','kneel','bow','jump','kick','hit','punch','cut','push','dodge','block','startle','wave','nod','shrug','think') else b.get('dur',nat*sc)
  sc=dur/nat if clip in ('fall','getup','kneel','bow','jump','kick','hit','punch','cut','dodge','block','startle','nod','shrug') else sc
  loopable=clip in ('talk','argue','laugh','cele','idle','look','think','wave','hips')
  if not loopable:dur=nat*sc
  a.hold(dur);a.play(clip,ts,ts+dur,sc,hold=(clip=='fall'))
  if clip=='fall':a.state='down'
  elif clip=='getup':a.state='stand'
  s.events.append(dict(kind='act',who=a.id,clip=clip,t0=ts,t1=ts+dur,to=b.get('to')))
 def b_react(s,b,t0):
  """a reaction (startle, nod, laugh, think, shrug, wave, ...) with the head and body turned towards what it reacts to"""
  kind=b.get('kind') or b.get('clip')
  if kind not in ('startle','nod','laugh','think','shrug','wave','cele','block','dodge','hit','bow'):raise SpecError('react: unknown reaction %r'%kind)
  nb=dict(do='act',who=b['who'],clip=kind)
  if b.get('to') is not None:nb['to']=b['to']
  return s.b_act(nb,t0)
 def b_say(s,b,t0):
  a=s.actors[b['who']];mood=b.get('mood') or dg.infer_mood(b['text']);to=b.get('to')
  if mood not in MOODS:raise SpecError('say: unknown mood %r'%mood)
  if to is None:
   prev=s.lines[-1]['speaker'] if s.lines and s.lines[-1]['speaker']!=a.id else None
   to=prev or min((o for o in s.actors if o!=a.id),key=lambda o:math.hypot(s.actors[o].X[-1]-a.X[-1],s.actors[o].Y[-1]-a.Y[-1]),default=a.id)
  ov=b.get('overlap_by',0.);n=int(ov*FPS)
  if n>0 and len(a.X)>n+2 and abs(a.X[-1]-a.X[-1-n])<1e-6 and abs(a.Y[-1]-a.Y[-1-n])<1e-6:del a.X[-n:];del a.Y[-n:];del a.H[-n:]    # an interruption: the line starts while the previous one is still ending
  if b.get('delay'):a.hold(b['delay'])    # a line that starts while another is still being spoken (inside a par): an interruption or an answer on the heels of the last word
  tp=s.point(to)
  if a.state=='sit' and abs(wrap(math.atan2(tp[1]-a.Y[-1],tp[0]-a.X[-1])-a.H[-1]))>math.radians(80):s.lint.append('AUDIT seated: %s speaks to %s who is %.0f deg off the way %s sits'%(a.id,to,abs(math.degrees(wrap(math.atan2(tp[1]-a.Y[-1],tp[0]-a.X[-1])-a.H[-1]))),a.id))
  lim=math.radians(72 if getattr(a,'settled',-1)==len(a.walks) else 35)   # once a character has turned into the conversation the body stays put; changing speaker is done with the eyes and head, not by rotating the body
  if a.state=='stand' and abs(wrap(math.atan2(tp[1]-a.Y[-1],tp[0]-a.X[-1])-a.H[-1]))>lim:a.face_point(tp,.9)
  a.settled=len(a.walks)
  syl=dg.syllables(b['text']);dur=max(1.5,len(syl)*.18+.45);real=DURATION_PROVIDER(a.look['voice'],b['text'],mood) if (DURATION_PROVIDER and a.look.get('voice')) else None
  if real:dur=real+.1
  ts=a.t+.12
  a.hold(.12+dur+.08);k=len(s.lines);L=dict(k=k,speaker=a.id,mood=mood,text=b['text'],t0=ts,t1=ts+dur,syl=syl,dur=dur,to=to,overlap=bool(b.get('delay') or b.get('overlap') or n>0));s.lines.append(L)
  if a.state=='stand':
   clip=b.get('gesture') or semantic_clip(b['text'],mood)
   if clip and clip not in ACT_CLIPS:raise SpecError('say: unknown gesture %r'%clip)
   if clip and clip!=a.last_gesture and (not a.clips or a.clips[-1][1]<=ts):a.play(clip,ts-.2,ts+dur+.2,QUICK.get(clip,1.))
   a.last_gesture=clip
   if not a.holding and not clip and not a.walks_now(ts):
    for h,keys in speech_gestures(b['text'],mood,ts,ts+dur,a.look['posture'],k*977+sum(map(ord,a.id))):
     for kt,infl,pos in keys:a.hands[h].append((kt,infl,('local',pos)))
  s.events.append(dict(kind='say',who=a.id,t0=ts,t1=ts+dur,to=to,mood=mood,k=k))
  turned=0
  for name,o in s.actors.items():   # the addressee turns to the speaker when far off, bystanders only when the speaker is behind them, and never all at the same moment
   if name==a.id or o.state!='stand' or o.t>ts-.1:continue
   off=abs(wrap(math.atan2(a.Y[-1]-o.Y[-1],a.X[-1]-o.X[-1])-o.H[-1]))
   lim2=math.radians((55 if getattr(o,'settled',-1)==len(o.walks) else 45) if name==to else 120)
   if off>lim2:
    o.hold(.25+.35*turned+.1*((sum(map(ord,name))+k)%4));turned+=1;o.face_point((a.X[-1],a.Y[-1]),1.0)
   if name==to:o.settled=len(o.walks)
  return L
 def _approach(s,a,target,stand,gait,face=None,mult=1.):
  """walk a to within `stand` metres of the point `target` (xy), then face `face` (default the target)"""
  px,py=a.pos();tx,ty=target[0],target[1];d=math.hypot(tx-px,ty-py)
  if d>stand+.05:
   ux,uy=(tx-px)/d,(ty-py)/d;end=(tx-ux*stand,ty-uy*stand);s._walk_to(a,end,gait,mult)
  a.face_point(face if face is not None else target)
 def _clear_spot(s,a,p):
  """move a goal point away from characters standing near it, so two characters never end up inside each other"""
  p=(p[0],p[1])
  for _ in range(3):
   for o in s.actors.values():
    if o is a:continue
    ox,oy=o.pos();d=math.hypot(p[0]-ox,p[1]-oy);need=a.radius+o.radius+.2
    if d<need:
     if d<1e-6:ux,uy=a.X[-1]-ox,a.Y[-1]-oy;L=math.hypot(ux,uy) or 1.;ux,uy=ux/L,uy/L
     else:ux,uy=(p[0]-ox)/d,(p[1]-oy)/d
     p=(ox+ux*need,oy+uy*need)
  return p
 def _stand_spot(s,a,target,z,what):
  """where a stands to reach a target point at height z: free of solids and of other characters, within arm's reach of the point, nearest to where it is now"""
  k=a.size;drop=1.12*k-z;arm=.5*k;lat=.22*k
  if abs(drop)>arm*.97 or arm*arm-drop*drop-lat*lat<.01:raise SpecError('%s: %s cannot reach %s at height %.2f (shoulder %.2f, arm %.2f)'%(what,a.id,target,z,1.12*k,arm))
  dmax=min(.42*k,math.sqrt(arm*arm-drop*drop-lat*lat)+.07*k);dmin=min(.3*k,dmax*.7);obst=s.layout['obstacles']
  def ok(q):
   if any(math.hypot(q[0]-c[0],q[1]-c[1])<c[2]+.02+a.radius*.2 for c in obst):return False
   return all(math.hypot(q[0]-o.X[-1],q[1]-o.Y[-1])>=(a.radius+o.radius)*.9+.1 for o in s.actors.values() if o is not a)
  best=None
  for r in [dmin+(dmax-dmin)*i/6. for i in range(7)]:
   for j in range(24):
    q=(target[0]+math.cos(j*math.pi/12)*r,target[1]+math.sin(j*math.pi/12)*r)
    if ok(q):
     d=math.hypot(q[0]-a.X[-1],q[1]-a.Y[-1])+r*2.
     if best is None or d<best[0]:best=(d,q)
  if best is None:raise SpecError('%s: %s cannot stand within reach (%.2f m) of %s; move the prop to the edge of its table or clear the way'%(what,a.id,dmax,tuple(round(v,2) for v in target)))
  return best[1]
 def _free_goal(s,a,p):
  """a goal inside a solid (a rock, a tree) is moved to the nearest free spot"""
  obst=s.layout['obstacles'];walls=s.layout.get('walls',[]);ok=lambda q:not any(math.hypot(q[0]-c[0],q[1]-c[1])<c[2]+.15+a.radius*.6 for c in obst) and not any(math.hypot(q[0]-w[0],q[1]-w[1])<w[2]+.9+a.radius*.3 for w in walls)    # goals keep clear of walls
  p=(p[0],p[1])
  if ok(p):return p
  for r in [.25*k for k in range(1,16)]:
   for j in range(16):
    q=(p[0]+math.cos(j*math.pi/8)*r,p[1]+math.sin(j*math.pi/8)*r)
    if ok(q):return q
  return p
 def _walk_to(s,a,end,gait,mult=1.,via=(),exact=False):
  if not exact:end=s._clear_spot(a,s._free_goal(a,end))
  if a.state=='sit':s._stand(a)
  if a.state!='stand':raise SpecError('%s cannot walk while %s'%(a.id,a.state))
  gait=gait or a.gait
  if gait not in gaits.GAITS:raise SpecError('unknown gait %r (known: %s)'%(gait,', '.join(gaits.GAITS)))
  pts=[a.pos()]+[tuple(v[:2]) for v in via]+[tuple(end[:2])];path=[pts[0]]
  extra=[(o.X[-1],o.Y[-1],o.radius+a.radius*.8) for o in s.actors.values() if o is not a]
  for p in pts[1:]:path+=s.router.route(path[-1],p,free_r=.6 if exact else .7,extra=extra)[1:]
  path=round_corners(path,1.0*a.size)
  if len(path)>1:
   first=math.atan2(path[1][1]-path[0][1],path[1][0]-path[0][0]);a.turn_to(first,None)
  size=a.stride;nat=gaits.natural_speed(gait);L=sum(math.hypot(q[0]-p0[0],q[1]-p0[1]) for p0,q in zip(path,path[1:]))
  tn=L/(nat*size*a.look['pace'])
  if tn>7. and gait in('shuffle','walk','strut','stomp'):    # a long walk is cut short by a quicker gait, then by a brisker cadence: the film never waits for someone to arrive
   g2='walk' if gait=='shuffle' else 'brisk'
   if gaits.natural_speed(g2)>nat:gait=g2;nat=gaits.natural_speed(g2);tn=L/(nat*size*a.look['pace'])
  if mult==1. and tn>6.:mult=min(1.4,tn/6.)
  speed=nat*size*a.look['pace']*mult;sc=gaits.play_scale(gait,speed,size);t0=a.t;a.walk(path,speed,gait,sc)
  s.events.append(dict(kind='go',who=a.id,t0=t0,t1=a.t,gait=gait,to=tuple(end[:2]),speed=speed));return a.t-t0
 def b_go(s,b,t0):
  a=s.actors[b['who']];ref=b['to'];tp=s.point(ref);gait=b.get('gait') or (None);t_start=a.t
  stop=b.get('stop')
  if stop is None:stop=(1.25*(a.size+s.actors[ref].size)/2 if isinstance(ref,str) and ref in s.actors else (.8*a.size if isinstance(ref,str) and ref in s.props else 0.))
  tp2=tp
  if b.get('_slot'):
   i,n=b['_slot'];px,py=a.pos();L=math.hypot(tp[0]-px,tp[1]-py) or 1.;nx,ny=-(tp[1]-py)/L,(tp[0]-px)/L;off=(i-(n-1)/2)*(1.0*a.size+.35);tp=(tp[0]+nx*off,tp[1]+ny*off,tp[2])
  tp2=tp
  if stop>0:
   px,py=a.pos();d=math.hypot(tp[0]-px,tp[1]-py)
   if d>stop+.05:ux,uy=(tp[0]-px)/d,(tp[1]-py)/d;tp2=(tp[0]-ux*stop,tp[1]-uy*stop)
   else:tp2=(px,py)
  if math.hypot(tp2[0]-a.X[-1],tp2[1]-a.Y[-1])>.05:s._walk_to(a,tp2,gait,b.get('pace',1.),b.get('via',()))
  face=b.get('face',ref if isinstance(ref,str) and (ref in s.actors or ref in s.props) else None)
  if face is not None:a.face_point(s.point(face))
  if b.get('talk'):    # walk and talk: the line is spoken while the character moves (a short walk is held until the line ends)
   text,mood,to=(list(b['talk'])+[None,None])[:3];mood=mood or dg.infer_mood(text)
   if mood not in MOODS:raise SpecError('go talk: unknown mood %r'%mood)
   to=to or min((o for o in s.actors if o!=a.id),key=lambda o:math.hypot(s.actors[o].X[-1]-a.X[-1],s.actors[o].Y[-1]-a.Y[-1]),default=a.id)
   syl=dg.syllables(text);dur=max(1.5,len(syl)*.18+.45);real=DURATION_PROVIDER(a.look['voice'],text,mood) if (DURATION_PROVIDER and a.look.get('voice')) else None
   if real:dur=real+.1
   ts=t_start+.4;te=ts+dur
   if te>a.t-.05:a.hold(te-a.t+.15)
   L=dict(k=len(s.lines),speaker=a.id,mood=mood,text=text,t0=ts,t1=te,syl=syl,dur=dur,to=to,overlap=True);s.lines.append(L);s.events.append(dict(kind='say',who=a.id,t0=ts,t1=te,to=to,mood=mood,k=L['k']))
 def b_sit(s,b,t0):
  a=s.actors[b['who']];sid=b['on']
  if sid not in s.layout['seats']:raise SpecError('sit: no seat %r (seats: %s)'%(sid,', '.join(sorted(s.layout['seats'])) or 'none'))
  if any(o.seat==sid for o in s.actors.values()):raise SpecError('sit: seat %s is taken'%sid)
  sx,sy,sz=s.layout['seats'][sid];f=b.get('face');fp=s.point(f) if f is not None else None;hd=math.atan2(fp[1]-sy,fp[0]-sx) if fp is not None else a.H[-1]
  root=(sx-math.cos(hd)*SIT_HIPS_FWD*a.size,sy-math.sin(hd)*SIT_HIPS_FWD*a.size)
  if math.hypot(root[0]-a.X[-1],root[1]-a.Y[-1])>.05:s._walk_to(a,root,b.get('gait'),b.get('pace',1.))
  a.turn_to(hd);ts=a.t;dur=3.2;a.hold(dur);a.play('sit',ts,ts+dur,(SIT_DOWN[1]/FPS)/dur,hold=True,f0=SIT_DOWN[0],f1=SIT_DOWN[1],sit=True);a.state='sit';a.seat=sid;a.ignore.append((ts-10,1e9,sid.split('.')[0]))
  s.events.append(dict(kind='sit',who=a.id,t0=ts,t1=ts+dur,seat=sid))
 def _stand(s,a):
  ts=a.t;dur=2.6;a.hold(dur);a.play('sit',ts,ts+dur,(SIT_DOWN[1]/FPS)/dur,reverse=True,f0=SIT_DOWN[0],f1=SIT_DOWN[1]);a.state='stand';a.ignore[-1:]=[(a.ignore[-1][0],ts+dur,a.ignore[-1][2])] if a.ignore else [];a.seat=None
  s.events.append(dict(kind='stand',who=a.id,t0=ts,t1=ts+dur))
 def b_stand(s,b,t0):
  a=s.actors[b['who']]
  if a.state!='sit':raise SpecError('%s stands up without sitting'%a.id)
  s._stand(a)
 # ---- props
 def _grip_points(s,prop,hand):
  hs=('R','L') if hand=='both' else (hand,);x,y,z=prop.at(s.cur_t(),s);w=prop.size[0]/2+.02
  return {h:(x,y,z) for h in hs} if len(hs)==1 else {'R':(x,y,z),'L':(x,y,z)}
 def _reach(s,a,hs,points,t,dur=.6):
  """key hands to world points: from their last key (or rest) at t to the points at t+dur"""
  for h in hs:
   ks=a.hands[h]
   if not ks or ks[-1][1]<.5:ks.append((t,0.,('local',(-.36 if h=='R' else .36,-.1,.66))))
   else:ks.append((t,ks[-1][1],ks[-1][2]))
   ks.append((t+dur,1.,('world',points[h])))
 def _carry(s,a,hs,t,dur=.7):
  for i,h in enumerate(hs):a.hands[h].append((t+dur,1.,('local',CARRY['both'][0 if h=='R' else 1] if len(hs)==2 else CARRY[h][0])))
 def _release(s,a,hs,t,dur=.7):
  for h in hs:a.hands[h].append((t+dur,0.,('local',(-.36 if h=='R' else .36,-.1,.66))))
 def b_take(s,b,t0):
  a=s.actors[b['who']];pid=b['prop'];p=s.props.get(pid)
  if p is None:raise SpecError('take: no prop %r'%pid)
  if p.carry is None:raise SpecError('take: a %s cannot be carried'%p.kind)
  if a.holding:raise SpecError('take: %s already holds %s'%(a.id,a.holding))
  hand=b.get('hand') or p.carry;hs=('R','L') if hand=='both' else (hand,);x,y,z=p.at(a.t,s)
  if z<.45*a.size or z>1.35*a.size:raise SpecError('take: %s is at z=%.2f, out of reach for %s (put it on a table or crate: %.2f..%.2f)'%(pid,z,a.id,.45*a.size,1.35*a.size))
  if p.on:a.ignore.append((a.t,a.t+30,p.on))
  spot=s._stand_spot(a,(x,y),z,'take')
  if math.hypot(spot[0]-a.X[-1],spot[1]-a.Y[-1])>.05:s._walk_to(a,spot,b.get('gait'),exact=True)
  a.face_point((x,y))
  ts=a.t;pts={h:(x,y,z) for h in hs};s._reach(a,hs,pts,ts,.6);tg=ts+.6;a.hold(.9)
  p.track.append((tg,'held',a.id,hand));a.holding=pid;s._carry(a,hs,tg+.1,.7);a.hold(.9)
  s.events.append(dict(kind='take',who=a.id,prop=pid,t0=ts,t1=a.t,hand=hand,t_grasp=tg))
 def b_put(s,b,t0):
  a=s.actors[b['who']];pid=b.get('prop') or a.holding;p=s.props.get(pid)
  if a.holding!=pid or p is None:raise SpecError('put: %s does not hold %r'%(a.id,pid))
  hand=[x for x in (p.track[-1][3],)][0];hs=('R','L') if hand=='both' else (hand,)
  if b.get('on'):
   if b['on'] not in s.layout['surfaces']:raise SpecError('put: %r is not a surface'%b['on'])
   sx,sy,top,r=s.layout['surfaces'][b['on']];at=b.get('at') or [sx,sy];z=top+p.size[2]/2
  else:at=b['at'];z=b.get('z',p.size[2]/2)
  if b.get('on'):a.ignore.append((a.t,a.t+30,b['on']))
  spot=s._stand_spot(a,(at[0],at[1]),z,'put')
  if math.hypot(spot[0]-a.X[-1],spot[1]-a.Y[-1])>.05:s._walk_to(a,spot,b.get('gait'),exact=True)
  a.face_point((at[0],at[1]))
  ts=a.t;pts={h:(at[0],at[1],z) for h in hs};s._reach(a,hs,pts,ts,.7);tg=ts+.7;a.hold(.9)
  p.track.append((tg,'world',(at[0],at[1],z)));a.holding=None;s._release(a,hs,tg+.1,.7);a.hold(.9)
  s.events.append(dict(kind='put',who=a.id,prop=pid,t0=ts,t1=a.t,t_grasp=tg));s.sfx.append((tg,'thud',a.id,.6))
 def b_give(s,b,t0):
  a=s.actors[b['who']];r=s.actors[b['to']];pid=a.holding;p=s.props.get(pid)
  if p is None or a.holding!=pid:raise SpecError('give: %s holds nothing'%a.id)
  if r.holding:raise SpecError('give: %s already holds %s'%(r.id,r.holding))
  hand=p.track[-1][3];hs=('R','L') if hand=='both' else (hand,)
  dist=.4*(a.size+r.size)+.1
  if math.hypot(r.X[-1]-a.X[-1],r.Y[-1]-a.Y[-1])>dist+.3:s._approach(a,(r.X[-1],r.Y[-1]),dist,b.get('gait'))
  a.face_point((r.X[-1],r.Y[-1]));r.face_point((a.X[-1],a.Y[-1]),.5)
  ts=max(a.t,r.t);a.pad_to(ts);r.pad_to(ts);fx,fy=math.cos(a.H[-1]),math.sin(a.H[-1])
  M=(a.X[-1]+fx*(.4*a.size+.05),a.Y[-1]+fy*(.4*a.size+.05),.85*(a.size+r.size)/2);rh=p.carry if p.carry in ('R','L') else 'R'
  for h in hs:a.hands[h].append((ts,a.hands[h][-1][1],a.hands[h][-1][2]));a.hands[h].append((ts+.7,1.,('world',M)))
  r._reach_hand=rh;s._reach(r,(rh,),{rh:M},ts,.7)
  tg=ts+.9;a.hold(1.1);r.pad_to(a.t);p.track.append((tg,'held',r.id,rh));r.holding=pid;a.holding=None
  s._release(a,hs,tg,.7);s._carry(r,(rh,),tg,.7);a.hold(.8);r.pad_to(a.t)
  s.events.append(dict(kind='give',who=a.id,to=r.id,prop=pid,t0=ts,t1=a.t,t_grasp=tg))
 def b_push(s,b,t0):
  a=s.actors[b['who']];pid=b['prop'];p=s.props.get(pid);dist=b.get('dist',1.2)
  if p is None:raise SpecError('push: no prop %r'%pid)
  x,y,z=p.at(a.t,s);d=b.get('dir')
  dirv=(math.cos(math.radians(d)),math.sin(math.radians(d))) if isinstance(d,(int,float)) else None
  if dirv is None:
   px,py=a.pos();L=math.hypot(x-px,y-py) or 1.;dirv=((x-px)/L,(y-py)/L)
  stand=.72*a.size+p.size[1]/2;sx_,sy_=x-dirv[0]*stand,y-dirv[1]*stand
  if math.hypot(sx_-a.X[-1],sy_-a.Y[-1])>.05:s._walk_to(a,(sx_,sy_),b.get('gait'))
  a.turn_to(math.atan2(dirv[1],dirv[0]));ts=a.t;nat=CLIP_FRAMES['push']/FPS;dur=nat*1.3;a.hold(dur);a.play('push',ts,ts+dur,1.3)
  tm0,tm1=ts+dur*13/72,ts+dur*40/72;p.track.append((tm0,'world',(x,y,z)));
  n=12
  for i in range(1,n+1):
   u=i/n;p.track.append((tm0+(tm1-tm0)*u,'world',(x+dirv[0]*dist*ease(u),y+dirv[1]*dist*ease(u),z)))
  s.events.append(dict(kind='push',who=a.id,prop=pid,t0=ts,t1=a.t,t_push0=tm0,t_push1=tm1));s.sfx.append((tm0,'scrape',a.id,.7))
 # ------------------------------------------------------------------------------------------------------ queries
 def pos(s,who,t):
  a=s.actors[who];f=min(len(a.X)-1,max(0,int(round(t*FPS))));return a.X[f],a.Y[f],a.H[f]
 def head_pos(s,who,t):
  a=s.actors[who];x,y,h=s.pos(who,t);z=1.42*a.size
  for (t0,t1,name,sc,opt) in a.clips:
   if t0<=t<t1 and opt.get('sit') and not opt.get('reverse'):z=1.12*a.size if t>t0+1.6 else z
  return (x,y,z)
 def line_at(s,t,pad=.1):
  for L in s.lines:
   if L['t0']-pad<=t<=L['t1']+pad:return L
 def gaze(s,who,t):
  """what who looks at at time t: ('char',id) | ('prop',id) | ('point',xyz) | None (look ahead)"""
  a=s.actors[who]
  for e in s.events:
   if e['kind']=='look' and e['who']==who and e['t0']<=t<=e['t1']+.3:return ('point',s.point(e['to'],t))
   if e['kind'] in ('take','put') and e['who']==who and e['t0']<=t<=e['t1']:return ('prop',e['prop'])
   if e['kind']=='give' and e['t0']-.2<=t<=e['t1'] and who in (e['who'],e['to']):return ('char',e['to'] if who==e['who'] else e['who'])
  L=s.line_at(t,.1)
  if L and L['to']==L['speaker']:
   return None if who==L['speaker'] else ('char',L['speaker'])
  if L:
   if L['speaker']==who:return ('char',L['to']) if L['to'] in s.actors else ('point',s.point(L['to'],t))
   return ('char',L['speaker'])
  prev=[x for x in s.lines if x['t1']<t and t-x['t1']<2.2]
  if prev and not s._walking(who,t):
   L=prev[-1];return ('char',L['to'] if L['speaker']==who else L['speaker'])
  for e in s.events:
   if e['kind']=='go' and e['who']==who and e['t0']<=t<=e['t1']:
    return None
   if e['kind'] in ('go','turn') and e['who']==who and e['t1']<=t<=e['t1']+.8 and isinstance(e['to'],str) and e['to'] in s.actors:return ('char',e['to'])
  return None
 def _walking(s,who,t):return any(w[0]<=t<=w[1] for w in s.actors[who].walks)
 def emote_at(s,who,t):return [(k,(t-t0)) for (t0,t1,k) in s.actors[who].emotes if t0<=t<=t1]
 def footsteps(s):
  """(time, who, foot, size) of every footfall, from the gait clip's own cycle: the strip starts 0.2 s before the walk (it blends in), the foot plants every cycle/steps_per_cycle seconds"""
  out=[]
  for who,a in s.actors.items():
   for (t0,t1,g,sc,speed) in a.walks:
    n=gaits.steps_per_cycle(g);dt=gaits.cycle_seconds(g,sc)/n;start=max(0.,t0-.2)+gaits.STEP_OFFSET.get(g,0.)*gaits.cycle_seconds(g,sc);k=0
    while start+dt*k<t1+.05:
     t=start+dt*k
     if t>=t0-.1:out.append((t,who,'L' if k%2==0 else 'R',a.size))
     k+=1
  return sorted(out)
 # ------------------------------------------------------------------------------------------------------ audit
 def audit(s):
  """numeric audits of the compiled plan: AUDIT strings (empty list = clean)"""
  out=list(s.lint);N=s.frames;ids=list(s.actors)
  for a,b in zip(s.lines,s.lines[1:]):
   if b['t0']<a['t1'] and not (a.get('overlap') or b.get('overlap')):out.append('AUDIT speech: lines %d and %d overlap'%(a['k'],b['k']))
  X=np.array([s.actors[i].X for i in ids]);Y=np.array([s.actors[i].Y for i in ids]);H=np.array([s.actors[i].H for i in ids]);R=np.array([s.actors[i].radius for i in ids])
  for i in range(len(ids)):
   for j in range(i+1,len(ids)):
    d=np.hypot(X[i]-X[j],Y[i]-Y[j])-.8*(R[i]+R[j]);k=int(np.argmin(d))
    if d[k]<-.05:out.append('AUDIT collision: %s and %s overlap by %.2f m at %.1f s'%(ids[i],ids[j],-d[k],k/FPS))
  obst=s.layout['obstacles'];per=s.layout['per_object']
  oid={};[oid.setdefault(c,k) for k,cs in per.items() for c in cs]
  for n,i in enumerate(ids):
   a=s.actors[i];worst=(0.,0,None)
   for (cx,cy,r) in obst:
    pen=(r+.42*a.radius)-np.hypot(X[n]-cx,Y[n]-cy)
    k=int(np.argmax(pen))
    if pen[k]>worst[0]+1e-9:
     ok=any(t0<=k/FPS<=t1 and o==oid.get((cx,cy,r)) for (t0,t1,o) in a.ignore)
     if not ok:worst=(pen[k],k,(cx,cy,r))
   if worst[0]>.14:out.append('AUDIT obstacle: %s walks %.2f m into a solid at %.1f s'%(i,worst[0],worst[1]/FPS))
   hx,hy=s.layout['half']
   if np.any(np.abs(X[n])>hx+2) or np.any(np.abs(Y[n])>hy+2):out.append('AUDIT bounds: %s leaves the location'%i)
   dh=np.abs(np.diff(np.unwrap(H[n])))*FPS
   if dh.size and dh.max()>math.radians(420):out.append('AUDIT turn: %s turns %.0f deg/s'%(i,math.degrees(dh.max())))
   for (t0,t1,g,sc,speed) in a.walks:
    nat=gaits.natural_speed(g)*a.stride*a.look['pace']
    if speed>nat*1.4 or speed<nat*.45:out.append('AUDIT gait: %s walks at %.2f m/s, natural for %s is %.2f'%(i,speed,g,nat))
    f0,f1=int(t0*FPS),int(t1*FPS);
    if f1-f0>6:
     v=np.hypot(np.diff(X[n][f0:f1+1]),np.diff(Y[n][f0:f1+1])).mean()*FPS
     if abs(v-speed)>.1*speed:out.append('AUDIT gait: %s moves %.2f m/s, planned %.2f'%(i,v,speed))
  seats={};
  for i,a in s.actors.items():
   if a.state=='sit':pass
  for e in s.events:
   if e['kind'] in ('take','put','give'):
    p=s.props[e['prop']]
    if e['t1']-e['t0']<1.2:out.append('AUDIT prop: %s %s too fast'%(e['kind'],e['prop']))
  for pid,p in s.props.items():
   z=p.at(s.seconds,s)[2]
   if z<p.size[2]/2-.06:out.append('AUDIT prop: %s ends below the floor'%pid)
  if s.seconds>130:out.append('AUDIT length: scene is %.0f s'%s.seconds)
  return out
import re
GESTURES={'serious':('talk','think','hips'),'warm':('talk','nod','wave'),'concern':('think','talk','shrug'),'sad':('shrug','think'),'angry':('argue','hips','argue'),'joy':('laugh','talk','wave')}
GESTURE_WORDS=((r"\b(hello|hi|goodbye|farewell|welcome|friends)\b",'wave'),(r"\b(no|never|not|enough|stop|wrong|cannot)\b",'argue'),(r"\b(yes|right|agreed|deal|of course|exactly)\b",'nod'),(r"\b(perhaps|maybe|mostly|who knows|i do not know)\b",'shrug'),(r"\b(think|remember|wonder|idea|plan)\b",'think'))
REST={'R':(-.36,-.1,.66),'L':(.36,-.1,.66)}
# hand gestures in the character's local frame (x left, y back, z up, metres at scale 1): (hands, first pose, second pose); the left hand mirrors x
GESTURES_HAND={'beat':('R',(-.36,-.4,.93),(-.36,-.32,.84)),'open':('RL',(-.5,-.42,.9),(-.55,-.46,.88)),'point':('R',(-.2,-.55,1.02),(-.2,-.6,1.02)),'chest':('R',(-.1,-.2,1.0),(-.1,-.22,1.02)),
 'chop':('R',(-.3,-.45,1.08),(-.3,-.48,.82)),'palm':('RL',(-.4,-.45,.88),(-.42,-.5,.93))}
EXPRESSIVE={'tired':.45,'hunched':.45,'proud':.65,'neutral':.6,'tense':.55,'jaunty':.85,'hurried':.85,'angry':.85}
PHRASE=re.compile(r"[^,.;:!?]+[,.;:!?]*")
def gesture_kind(phrase,mood):
  """the hand gesture a phrase calls for: I -> hand to chest, you -> point, we -> both hands open, no/not -> chop, a question -> palms up, otherwise a beat"""
  low=phrase.lower()
  if re.search(r"\b(no|not|never|cannot|stop|enough|nothing|wrong)\b",low):return 'chop'
  if re.search(r"\b(i|me|my|mine|myself|i'm)\b",low):return 'chest'
  if re.search(r"\b(you|your|yours)\b",low):return 'point'
  if re.search(r"\b(we|us|our|everyone|together)\b",low):return 'open'
  if phrase.strip().endswith('?'):return 'palm'
  return 'beat' if mood in('angry','joy') or phrase.strip().endswith('!') else 'open'
def speech_gestures(text,mood,t0,t1,posture,seed):
  """[(hand, [(t, influence, local pos)...])] hand gestures for a spoken line: one per phrase of five syllables or more, chosen from the words, thinned by how expressive the character's posture is"""
  import dialogue as dg
  ph=[m.group(0) for m in PHRASE.finditer(text) if m.group(0).strip()];sy=[max(1,len(dg.syllables(x))) for x in ph];tot=float(sum(sy));out=[];t=t0+.15;span=max(.5,t1-t0-.35);rnd=random.Random(seed);last=None
  for x,n in zip(ph,sy):
   d=span*n/tot;pa,pb=t,t+d;t+=d
   if n<4 or rnd.random()>EXPRESSIVE.get(posture,.6):continue
   kind=gesture_kind(x,mood)
   if kind==last and rnd.random()<.6:kind='beat' if kind!='beat' else 'open'
   last=kind;hands,p1,p2=GESTURES_HAND[kind];pm=(pa+pb)/2
   for h in hands:
    sg=1. if h=='R' else -1.;q1=(p1[0]*sg,p1[1],p1[2]);q2=(p2[0]*sg,p2[1],p2[2]);rest=REST[h]
    out.append((h,[(pa-.2,0.,rest),(pa+.18,.85,q1),(pm,.85,q2),(max(pm+.05,pb-.05),.85,q1),(pb+.3,0.,rest)]))
  return out
SEMANTIC=((r"\b(hello|hi|goodbye|farewell|welcome)\b",'wave'),(r"\b(yes|agreed|deal|of course|exactly)\b",'nod'),(r"\b(perhaps|maybe|mostly|who knows|do not know)\b",'shrug'),(r"\b(think|remember|wonder|idea)\b",'think'))
def semantic_clip(text,mood):
  """a whole-body clip for a line only when its meaning asks for one (greeting, agreement, doubt, thought, rage); the hands of every other line are acted by speech_gestures"""
  low=text.lower()
  for pat,c in SEMANTIC:
   if re.search(pat,low):return c
  if mood=='angry' and text.strip().endswith('!') and len(text)>24:return 'argue'
  return None
def gesture_for(text,mood,last=None,k=0):
  """a clip for the speaker of a line from its words and mood, never the same as the speaker's previous gesture"""
  low=text.lower()
  for pat,clip in GESTURE_WORDS:
   if re.search(pat,low) and clip!=last and (mood!='sad' or clip in('shrug','think','nod')):return clip
  opts=[c for c in GESTURES.get(mood,('talk',)) if c!=last] or ['talk'];return opts[k%len(opts)]
def normalise_spec(spec):
 """steps get a 'do' key from their first key if written as {'go':..}"""
 return spec
def compile(spec,registry):
 """Plan for a spec (runs it)"""
 for st in spec['steps']:
  for b in (st if isinstance(st,list) else [st]):
   if 'do' not in b:raise SpecError('beat without "do": %r'%(b,))
 return Plan(spec,registry).run()
