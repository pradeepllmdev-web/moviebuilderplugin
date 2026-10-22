"""Automatic camera director for the performance engine (pure Python, no Blender).

    cuts=perf_camera.direct(plan)               # [dict(t0,t1,kind,subject,to,side,lens,name)] covering the whole scene
    pos,aim,lens=perf_camera.frame(plan,cut,t)  # camera position, aim point and lens at time t

What it does, in order: an establishing wide at the start; for every step of the plan the coverage that step calls for -
 dialogue: over-the-shoulder on the speaker (two-shot every third line, single on the listener's reaction), the camera staying on one side of the line between a pair (the 180 degree rule);
 walking: a tracking shot beside the walker (a high follow for long walks, alternating sides and lenses so cuts do not jump);
 taking, putting, giving, pushing: an insert on the hands and prop, then a medium on the actor;
 sitting, standing, falling, big acts: a medium from the front quarter;  'cam' beats of the spec override the choice for their step.
Rules applied after the shots are chosen: no shot shorter than MIN_SHOT (merged into its neighbour), none longer than MAX_SHOT (split with a change of angle), no cut between two near-identical framings (the second gets another lens and angle),
and the last shot is a wide hold. All geometry comes from the plan (head positions, headings), so the director never needs Blender; the Blender side only evaluates frame() and clears the view of anything in the way."""
import math
import numpy as np
MIN_SHOT=2.2;MAX_SHOT=11.0    # longer holds: a shot is not cut on every short line
def _unit(v):
 n=math.hypot(*v) or 1.;return (v[0]/n,v[1]/n)
def _rotv(v,a):c,s=math.cos(a),math.sin(a);return (v[0]*c-v[1]*s,v[0]*s+v[1]*c)
def spread(plan,t):
 pts=[plan.pos(i,t)[:2] for i in plan.actors];cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts);return (cx,cy),max(math.hypot(p[0]-cx,p[1]-cy) for p in pts)
def heading_at(plan,who,t,win=.8):
 f=lambda tt:plan.pos(who,max(0,tt))
 x0,y0,_=f(t-win);x1,y1,h=f(t+win)
 if math.hypot(x1-x0,y1-y0)>.3:return math.atan2(y1-y0,x1-x0)
 return plan.pos(who,t)[2]
def _step_edges(plan):
 ts=list(plan.steps_t)+[plan.seconds];return [(a,b) for a,b in zip(ts,ts[1:])]
def _events_in(plan,a,b):return [e for e in plan.events if e.get('t0',0)<b-1e-6 and e.get('t1',0)>a+1e-6]
def _target(plan,ref,t):
 """(x,y,z) of what a character points at, at time t: a character's head, a prop where it is, or a point"""
 if isinstance(ref,str) and ref in plan.actors:x,y,_=plan.pos(ref,t);return (x,y,1.0)
 if isinstance(ref,str) and ref in plan.props:return tuple(plan.props[ref].at(t,plan))
 return tuple(plan.point(ref))
def direct(plan,seed=1):
 rnd=np.random.default_rng(seed);cuts=[];pair_side={};walk_side=[1.]
 hints={round(c['t0'],2):c for c in plan.cams}
 first=plan.steps_t[0] if plan.steps_t else 0.;(c0,r0)=spread(plan,0)
 tw=min(max(2.5,first+1.5),6.);ang=float(rnd.uniform(0,2*math.pi))
 cuts.append(dict(name='establish',kind='wide',t0=0.,t1=min(tw,plan.seconds-1),subject=None,ang=ang,lens=30))
 prev_walk=None
 for (a,b) in _step_edges(plan):
  if b<=cuts[-1]['t1']+.2:continue
  a=max(a,cuts[-1]['t1']);evs=_events_in(plan,a-.01,b)
  h=next((v for k,v in hints.items() if abs(k-a)<.6 or (a<=k<b)),None)
  says=[e for e in evs if e['kind']=='say'];gos=[e for e in evs if e['kind']=='go' and e['t1']-e['t0']>1.5];inter=[e for e in evs if e['kind'] in ('take','put','give','push')]
  acts=[e for e in evs if e['kind'] in ('act','sit','stand') and e.get('clip') not in ('nod','think','shrug','idle','look','hips')]
  if h and h.get('size')=='wide':cuts.append(dict(name='wide (hint)',kind='wide',t0=a,t1=b,subject=h.get('subject'),ang=float(rnd.uniform(0,6.28)),lens=28));continue
  if says:
   for L in says:
    k=L['k'];sp,to=L['who'],L['to']
    if to not in plan.actors:to=next(o for o in plan.actors if o!=sp) if len(plan.actors)>1 else sp
    if to==sp:
     cuts.append(dict(name='%s alone'%sp,kind='medium',t0=max(a,L['t0']-.25),t1=min(b,L['t1']+.3),subject=sp,side=1.,lens=40));continue
    key=tuple(sorted((sp,to)));side=pair_side.setdefault(key,1. if rnd.random()<.5 else -1.)
    t0=max(a,L['t0']-.25);t1=min(b,L['t1']+.3);mid=t0+(t1-t0)*.68
    kd='two' if k%3==2 and math.hypot(*[plan.pos(sp,mid)[i]-plan.pos(to,mid)[i] for i in (0,1)])<=5.5 and not plan.layout.get('inside') else 'medium'    # a face from the front quarter, never a foreground back of a head (a two-shot of people far apart is a tiny picture)   # a small room has no room for a two-shot
    if t0>cuts[-1]['t1']+.2 and mid-cuts[-1]['t1']>0:t0=cuts[-1]['t1']
    close=kd=='medium' and L.get('mood') in('sad','warm','joy','concern') and mid-t0>2.2     # an emotional line is played on the face
    cuts.append(dict(name='%s speaks'%sp,kind=kd,t0=t0,t1=mid,subject=sp,to=to,side=side,lens=52 if close else (40 if kd=='medium' else 36),close=close))
    if t1-mid>1.6:cuts.append(dict(name='%s listens'%to,kind='medium',t0=mid,t1=t1,subject=to,to=sp,side=-side,lens=40))
   if cuts[-1]['t1']<b-.1:cuts[-1]['t1']=b
  elif [e for e in evs if e['kind']=='point']:     # a character points: cut to what is pointed at, from behind the pointer's shoulder, then back
   e=[e for e in evs if e['kind']=='point'][0];tp=_target(plan,e['to'],e['t0']);dur=max(1.6,min(b-a,e['t1']-e['t0']))
   cuts.append(dict(name='%s points'%e['who'],kind='reveal',t0=a,t1=min(b,a+dur),subject=e['who'],target=tuple(tp),side=1.,lens=34))
   if cuts[-1]['t1']<b-.2:cuts.append(dict(name='%s reacts'%e['who'],kind='medium',t0=cuts[-1]['t1'],t1=b,subject=e['who'],side=-1.,lens=40))
   else:cuts[-1]['t1']=b
  elif gos:
   e=max(gos,key=lambda e:e['t1']-e['t0']);who=e['who'];mv=[g for g in gos if g['t0']<e['t1'] and g['t1']>e['t0']]
   walk_side[0]*=-1.;dur=b-a;tm=(a+b)/2;gp=[plan.pos(g['who'],tm)[:2] for g in mv]
   if max((math.hypot(p[0]-q[0],p[1]-q[1]) for p in gp for q in gp),default=0)>5.5:
    cuts.append(dict(name='%s and company'%who,kind='group',t0=a,t1=b,subject=None,ang=float(rnd.uniform(0,6.28)),lens=30));continue
   fast=e.get('gait') in ('run','brisk','sprint')
   cuts.append(dict(name='%s %s'%(who,'runs' if fast else 'walks'),kind='track' if (dur<9 or fast) else 'follow_high',t0=a,t1=b,subject=who,group=[g['who'] for g in mv],side=walk_side[0],lens=24 if fast else (34 if dur<9 else 30),dist=float(rnd.uniform(2.6,3.2)) if fast else float(rnd.uniform(3.4,4.6)),fast=fast))   # a run is filmed low, close and wide: the ground rushes past
  elif inter:
   e=inter[0];who=e['who'];cuts.append(dict(name='%s %s'%(who,e['kind']),kind='insert',t0=a,t1=max(a+1.5,(e.get('t_grasp') or e.get('t_push1') or (a+b)/2)+.9),subject=who,prop=e['prop'],lens=50,side=1.))
   if cuts[-1]['t1']<b-.2:cuts.append(dict(name='%s works'%who,kind='medium',t0=cuts[-1]['t1'],t1=b,subject=who,side=-1.,lens=34))
   else:cuts[-1]['t1']=b
  elif acts:
   e=acts[0];cuts.append(dict(name='%s %s'%(e['who'],e.get('clip') or e['kind']),kind='medium',t0=a,t1=b,subject=e['who'],side=float(rnd.choice([-1,1])),lens=34))
  else:
   if cuts[-1]['kind'] in('wide','group') and cuts[-1]['name']!='establish':cuts[-1]['t1']=b
   else:cuts.append(dict(name='hold',kind='group',t0=a,t1=b,subject=None,ang=float(rnd.uniform(0,6.28)),lens=32))
 cuts[-1]['t1']=max(cuts[-1]['t1'],plan.seconds)
 end_t0=max(plan.seconds-3.2,cuts[-1]['t0']+MIN_SHOT)
 if cuts[-1]['kind']!='wide':
  if cuts[-1]['t1']-cuts[-1]['t0']>MIN_SHOT+1.2:cuts[-1]['t1']=end_t0;cuts.append(dict(name='end',kind='wide',t0=end_t0,t1=plan.seconds,subject=None,ang=float(rnd.uniform(0,6.28)),lens=26))
 return _pick_sides(plan,_tidy(plan,cuts,rnd))
def _tidy(plan,cuts,rnd):
 out=[]
 for c in cuts:    # contiguous, ordered
  if out:c['t0']=out[-1]['t1']
  if c['t1']-c['t0']<MIN_SHOT and out:out[-1]['t1']=c['t1'];continue
  out.append(c)
 res=[]
 for c in out:    # long shots: split with another angle
  while c['t1']-c['t0']>MAX_SHOT:
   mid=c['t0']+MAX_SHOT*.75 if c['t1']-c['t0']>MAX_SHOT+MIN_SHOT else (c['t0']+c['t1'])/2;d=dict(c,t0=c['t0'],t1=mid);res.append(d)
   c=dict(c,t0=mid,side=-c.get('side',1.),ang=c.get('ang',0.)+2.2,lens=c['lens']*(1.25 if c['lens']<45 else .8),name=c['name']+' (b)')
  res.append(c)
 for a,b in zip(res,res[1:]):    # no cut between near-identical framings
  if a['kind']==b['kind'] and a.get('subject')==b.get('subject') and abs(a['lens']-b['lens'])<6 and a.get('side')==b.get('side'):b['lens']=b['lens']*1.3 if b['lens']<45 else b['lens']*.75;b['side']=-(b.get('side') or 1.);b['ang']=b.get('ang',0.)+1.5
 return res
def frame(plan,c,t):
 """(camera position, aim point, lens) at time t for a cut; inside a room the camera stays inside its walls"""
 pos,aim,lens=_frame(plan,c,t);ins=plan.layout.get('inside');u=max(0.,min(1.,(t-c['t0'])/max(.1,c['t1']-c['t0'])))
 e=u*u*(3-2*u)    # eased progress: every shot moves, starting and ending softly
 if c['kind'] in ('ots','single','medium','insert','reveal'):    # a push-in over the shot with a slow slide sideways (parallax against the background)
  k=1-.12*e;px,py=pos[0]-aim[0],pos[1]-aim[1];L=math.hypot(px,py) or 1.;sl=(e-.5)*(.5 if c['kind']=='insert' else .7)*c.get('side',1.)
  pos=(aim[0]+(pos[0]-aim[0])*k-py/L*sl,aim[1]+(pos[1]-aim[1])*k+px/L*sl,aim[2]+(pos[2]-aim[2])*k)
 elif c['kind'] in ('wide','group'):     # a slow orbit round the scene while the camera sinks a little
  C,r=spread(plan,t);ang=.32*e;dx,dy=pos[0]-C[0],pos[1]-C[1];pos=(C[0]+dx*math.cos(ang)-dy*math.sin(ang),C[1]+dx*math.sin(ang)+dy*math.cos(ang),pos[2]-.7*e)
 elif c['kind']=='two':     # a slow dolly toward the pair
  k=1-.08*e;pos=(aim[0]+(pos[0]-aim[0])*k,aim[1]+(pos[1]-aim[1])*k,pos[2])
 if ins:
  pos=(min(max(pos[0],ins[0]),ins[2]),min(max(pos[1],ins[1]),ins[3]),min(max(pos[2],.6),2.5));lens=min(lens,{'wide':24,'group':24,'two':24,'track':26,'follow_high':26,'medium':30,'ots':30,'single':30,'insert':40}.get(c['kind'],lens))   # a small room has no room to step back: widen instead
 if not ins:pos=_out_of_solids(plan,pos,aim)
 return pos,aim,lens
def _out_of_solids(plan,pos,aim):
 """the lens never sits inside a tree crown, rock, house or tower: if it would, it is moved straight out of the solid (continuously, so a moving shot does not jump)"""
 O=_obs(plan)
 if not len(O):return pos
 x,y,z=pos
 for _ in range(3):
  moved=False
  for cx,cy,r in O:
   if r<=.5:continue
   d=math.hypot(x-cx,y-cy)
   if d<r+.45:
    if d<1e-6:ux,uy=_unit((x-aim[0],y-aim[1]))
    else:ux,uy=(x-cx)/d,(y-cy)/d
    x,y=cx+ux*(r+.45),cy+uy*(r+.45);moved=True
  if not moved:break
 return (x,y,z)
def _frame(plan,c,t):
 kd=c['kind'];lens=c['lens']
 if kd in ('wide','group'):
  C,r=spread(plan,t);d=max(6.5 if len(plan.actors)>2 else 4.8,r*1.4+(5.5 if len(plan.actors)>2 else 3.5));a=c.get('ang',0.);hz=3.2+r*.2
  return (C[0]+math.cos(a)*d,C[1]+math.sin(a)*d,hz),(C[0],C[1],1.0),lens
 sp=c.get('subject')
 if kd in ('ots','two','single'):
  hs=plan.head_pos(sp,t);to=c.get('to') or sp;ht=plan.head_pos(to,t);side=c.get('side',1.)
  d=_unit((hs[0]-ht[0],hs[1]-ht[1]));n=(-d[1]*side,d[0]*side)
  if kd in ('ots','single'):    # a single is the reverse angle: behind the speaker, on the listener's face, a little tighter
   k=plan.actors[to].size;wk=plan.actors[to].look['scale'][0]*.8;sep=max(.6,math.hypot(hs[0]-ht[0],hs[1]-ht[1]));back=(3.0+.7*k)*(.75 if kd=='single' else 1.)      # costumes (capes, armour, robes) make the listener wider than the body alone
   lat=min(3.2,max(.7*k,(wk+.25)*(back+sep)/sep))*(.95 if kd=='single' else 1.2);return (ht[0]-d[0]*back+n[0]*lat,ht[1]-d[1]*back+n[1]*lat,hs[2]+.15),(hs[0],hs[1],hs[2]),lens
  mid=((hs[0]+ht[0])/2,(hs[1]+ht[1])/2,(hs[2]+ht[2])/2);dist=max(4.2,math.hypot(hs[0]-ht[0],hs[1]-ht[1])*1.6+1.5)
  return (mid[0]+n[0]*dist,mid[1]+n[1]*dist,mid[2]+.4),mid,lens
 if kd in ('track','follow_high'):
  g=c.get('group') or [sp];mid_t=(c['t0']+c['t1'])/2;h=heading_at(plan,sp,mid_t);side=c.get('side',1.);dist=c.get('dist',4.)
  ps=[plan.pos(w,t) for w in g];cx=sum(p[0] for p in ps)/len(ps);cy=sum(p[1] for p in ps)/len(ps)
  f=(math.cos(h),math.sin(h));n=(-f[1]*side,f[0]*side);lead=1.2
  size=plan.actors[sp].size;hz=((.55 if c.get('fast') else 1.4) if kd=='track' else 3.8)*size if kd=='track' else 3.6
  if kd=='follow_high':dist*=1.5
  dist*=c.get('dm',1.)*max(.72,size**.6)    # a small walker is followed from closer, so he stays big in the frame
  ahead=1.6*c.get('front',1.)    # the camera stands a little ahead of the walker, so the face is seen
  return (cx+n[0]*dist+f[0]*ahead,cy+n[1]*dist+f[1]*ahead,hz),(cx+f[0]*lead*.5,cy+f[1]*lead*.5,1.1*size*(1.12 if plan.actors[sp].look.get('humanoid') else 1.)),lens
 if kd=='insert':
  p=plan.props[c['prop']];pp=p.at(t,plan);x,y,h=plan.pos(sp,t);a=plan.actors[sp];dm=c.get('dm',1.)
  f=(math.cos(h),math.sin(h));n=(-f[1]*c.get('side',1.),f[0]*c.get('side',1.))
  return (pp[0]+f[0]*.6*dm+n[0]*1.5*a.size*dm,pp[1]+f[1]*.6*dm+n[1]*1.5*a.size*dm,pp[2]+.45),(pp[0]-f[0]*.2,pp[1]-f[1]*.2,pp[2]),lens
 if kd=='reveal':
  hs=plan.head_pos(sp,t);tp=c['target'];d=_unit((tp[0]-hs[0],tp[1]-hs[1]));n=(-d[1],d[0]);aim=(tp[0],tp[1],max(.9,tp[2]) if len(tp)>2 else .9)
  return (hs[0]-d[0]*1.3+n[0]*.7,hs[1]-d[1]*1.3+n[1]*.7,hs[2]+.25),aim,lens
 if kd=='medium':
  x,y,h=plan.pos(sp,t);a=plan.actors[sp];f=(math.cos(h),math.sin(h));n=(-f[1]*c.get('side',1.),f[0]*c.get('side',1.));d=4.6*max(.65,a.size)*c.get('dm',1.)*(.72 if c.get('close') else 1.)
  fx,fy=_rotv(f,math.radians(30*c.get('side',1.)));hk=1.12 if a.look.get('humanoid') else 1.     # a person's head is higher for the same size than the lion's
  return (x+fx*d,y+fy*d,1.35*a.size*hk),(x,y,1.05*a.size*hk),lens
 raise ValueError('unknown shot kind %r'%kd)

def _obs(plan):
 if not hasattr(plan,'_obs_arr'):plan._obs_arr=np.array(plan.layout['obstacles'],float).reshape(-1,3)
 return plan._obs_arr
def _score(plan,c,side):
 """how good this side is for a cut: distance of uninvolved characters from the line of sight, camera not inside a solid or off the map"""
 c2=dict(c,side=side);t=(c['t0']+c['t1'])/2;pos,aim,_=frame(plan,c2,t);sc=1.5
 inv={c.get('subject')}|set(c.get('group') or [])|({c.get('to')} if c['kind'] in ('ots','two') else set())    # in a single the other speaker is a possible blocker
 for w in plan.actors:
  if w in inv:continue
  p=plan.pos(w,t);d,_=_segdist2(pos,aim,p);sc=min(sc,d)
 for w in plan.actors:
  p=plan.pos(w,t);k=plan.actors[w].size;d=math.hypot(pos[0]-p[0],pos[1]-p[1])
  if d<1.5*k:sc-=(1.5*k-d)*2.
 O=_obs(plan)
 if len(O):
  if np.any(np.hypot(pos[0]-O[:,0],pos[1]-O[:,1])<O[:,2]+.3):sc-=2.
  dx,dy=aim[0]-pos[0],aim[1]-pos[1];L2=dx*dx+dy*dy or 1.;u=np.clip(((O[:,0]-pos[0])*dx+(O[:,1]-pos[1])*dy)/L2,0,1);d=np.hypot(pos[0]+dx*u-O[:,0],pos[1]+dy*u-O[:,1])
  if np.any((O[:,2]>.5)&(d<O[:,2]*.8)&(u>.05)&(u<.92)):sc-=1.5
  if np.any((O[:,2]<=.5)&(d<O[:,2]+.25)&(u>.05)&(u<.6)):sc-=.8       # a post or lamp close in front of the lens       # a solid between the lens and the subject
 hx,hy=plan.layout['half']
 if abs(pos[0])>hx+4 or abs(pos[1])>hy+4:sc-=1.
 if c['kind'] not in ('wide','group'):
  for u in (.15,.5,.85):
   off,face=shot_quality(plan,c2,c['t0']+(c['t1']-c['t0'])*u)
   if off>.8:sc-=2.5*(off-.8)+.5     # the people drift out of the frame
   if face<.25 and c['kind']!='ots':sc-=1.5*(.25-face)+.3    # we would be looking at the back of the head
 return sc
def shot_quality(plan,c,t):
 """(worst angle off the lens axis as a fraction of the half field of view over the people the shot is about, face-to-camera cosine of the main subject): a shot should keep them in frame and show the face"""
 pos,aim,lens=frame(plan,c,t);half=math.atan(18./lens);ax=np.array(aim)-np.array(pos);ax/=np.linalg.norm(ax) or 1.
 who=[c['subject']] if c.get('subject') and c['kind'] not in ('insert','reveal') else []    # an insert is about the hands and the prop, not the face
 if c['kind']=='two' and c.get('to'):who.append(c['to'])
 off=0.
 for w in who:
  v=np.array(plan.head_pos(w,t))-np.array(pos);v/=np.linalg.norm(v) or 1.;off=max(off,math.acos(max(-1.,min(1.,float(ax@v))))/half)
 face=1.
 if who and c['kind'] not in ('wide','group','insert','reveal','ots','two'):
  w=who[0];x,y,h=plan.pos(w,t);d=_unit((pos[0]-x,pos[1]-y));face=math.cos(h)*d[0]+math.sin(h)*d[1]
 return off,face
def _segdist2(a,b,p):
 dx,dy=b[0]-a[0],b[1]-a[1];L2=dx*dx+dy*dy or 1.;u=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2));return math.hypot(a[0]+dx*u-p[0],a[1]+dy*u-p[1]),u
def _pick_sides(plan,cuts):
 for c in cuts:
  if c['kind'] in ('wide','group'):    # turn the wide round until no wall or house stands between the lens and the people
   best=None
   for k in range(8):
    c2=dict(c,ang=c.get('ang',0.)+k*math.pi/4);sc=_score(plan,c2,1.)-.02*k
    if best is None or sc>best[0]:best=(sc,c2['ang'])
   c['ang']=best[1];continue
  if c.get('side') is None:continue
  s0=c['side']
  if c['kind'] in ('ots','two'):
   a_,b_=_score(plan,c,s0),_score(plan,c,-s0)
   if b_>a_+.05:c['side']=-s0;a_=b_
   if a_<-.4 and c['kind']=='ots':c.update(kind='medium',side=s0,lens=36)    # no clean over-the-shoulder: a front medium of the speaker instead
   continue
  best=None
  for fr in ((1.,2.,3.) if c['kind'] in ('track','follow_high') else (1.,)):
   for dm in (1.,.8,1.3,1.6):
    for sd in (s0,-s0):
     c2=dict(c,dm=dm,front=fr);sc=_score(plan,c2,sd)-.05*abs(dm-1.)-(.02 if sd!=s0 else 0)-.03*(fr-1.)
     if best is None or sc>best[0]:best=(sc,sd,dm,fr)
  c['side']=best[1];c['dm']=best[2];c['front']=best[3]
 return cuts
