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
MIN_SHOT=1.3;MAX_SHOT=9.0
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
    kd='two' if k%3==2 or math.hypot(*[plan.pos(sp,mid)[i]-plan.pos(to,mid)[i] for i in (0,1)])>5. else 'ots'
    if t0>cuts[-1]['t1']+.2 and mid-cuts[-1]['t1']>0:t0=cuts[-1]['t1']
    cuts.append(dict(name='%s speaks'%sp,kind=kd,t0=t0,t1=mid,subject=sp,to=to,side=side,lens=42 if kd=='ots' else 36))
    if t1-mid>.4:cuts.append(dict(name='%s listens'%to,kind='single',t0=mid,t1=t1,subject=to,to=sp,side=side,lens=36))
   if cuts[-1]['t1']<b-.1:cuts[-1]['t1']=b
  elif gos:
   e=max(gos,key=lambda e:e['t1']-e['t0']);who=e['who'];mv=[g for g in gos if g['t0']<e['t1'] and g['t1']>e['t0']]
   walk_side[0]*=-1.;dur=b-a;tm=(a+b)/2;gp=[plan.pos(g['who'],tm)[:2] for g in mv]
   if max((math.hypot(p[0]-q[0],p[1]-q[1]) for p in gp for q in gp),default=0)>5.5:
    cuts.append(dict(name='%s and company'%who,kind='group',t0=a,t1=b,subject=None,ang=float(rnd.uniform(0,6.28)),lens=30));continue
   cuts.append(dict(name='%s walks'%who,kind='track' if dur<9 else 'follow_high',t0=a,t1=b,subject=who,group=[g['who'] for g in mv],side=walk_side[0],lens=34 if dur<9 else 30,dist=float(rnd.uniform(3.4,4.6))))
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
  if cuts[-1]['t1']-cuts[-1]['t0']>MIN_SHOT+3:cuts[-1]['t1']=end_t0;cuts.append(dict(name='end',kind='wide',t0=end_t0,t1=plan.seconds,subject=None,ang=float(rnd.uniform(0,6.28)),lens=26))
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
 pos,aim,lens=_frame(plan,c,t);ins=plan.layout.get('inside')
 if ins:
  pos=(min(max(pos[0],ins[0]),ins[2]),min(max(pos[1],ins[1]),ins[3]),min(max(pos[2],.6),2.5));lens=min(lens,{'wide':24,'group':24,'two':24,'track':26,'follow_high':26,'medium':30,'insert':40}.get(c['kind'],lens))   # a small room has no room to step back: widen instead
 return pos,aim,lens
def _frame(plan,c,t):
 kd=c['kind'];lens=c['lens']
 if kd in ('wide','group'):
  C,r=spread(plan,t);d=max(6.5,r*1.4+5.5);a=c.get('ang',0.);hz=3.2+r*.2
  return (C[0]+math.cos(a)*d,C[1]+math.sin(a)*d,hz),(C[0],C[1],1.0),lens
 sp=c.get('subject')
 if kd in ('ots','two','single'):
  hs=plan.head_pos(sp,t);to=c.get('to') or sp;ht=plan.head_pos(to,t);side=c.get('side',1.)
  d=_unit((hs[0]-ht[0],hs[1]-ht[1]));n=(-d[1]*side,d[0]*side)
  if kd=='ots':
   k=plan.actors[to].size;wk=plan.actors[to].look['scale'][0]*.62;sep=max(.6,math.hypot(hs[0]-ht[0],hs[1]-ht[1]));back=2.4+.6*k
   lat=min(2.4,max(.6*k,(wk+.2)*(back+sep)/sep));return (ht[0]-d[0]*back+n[0]*lat,ht[1]-d[1]*back+n[1]*lat,hs[2]+.15),(hs[0],hs[1],hs[2]),lens
  if kd=='single':
   k=plan.actors[to].size*c.get('dm',1.);return (ht[0]+(d[0]*.8+n[0]*1.0)*3.1*k,ht[1]+(d[1]*.8+n[1]*1.0)*3.1*k,ht[2]+.05),ht,lens
  mid=((hs[0]+ht[0])/2,(hs[1]+ht[1])/2,(hs[2]+ht[2])/2);dist=max(4.2,math.hypot(hs[0]-ht[0],hs[1]-ht[1])*1.6+1.5)
  return (mid[0]+n[0]*dist,mid[1]+n[1]*dist,mid[2]+.4),mid,lens
 if kd in ('track','follow_high'):
  g=c.get('group') or [sp];mid_t=(c['t0']+c['t1'])/2;h=heading_at(plan,sp,mid_t);side=c.get('side',1.);dist=c.get('dist',4.)
  ps=[plan.pos(w,t) for w in g];cx=sum(p[0] for p in ps)/len(ps);cy=sum(p[1] for p in ps)/len(ps)
  f=(math.cos(h),math.sin(h));n=(-f[1]*side,f[0]*side);lead=1.2
  size=plan.actors[sp].size;hz=(1.4 if kd=='track' else 3.8)*size if kd=='track' else 3.6
  if kd=='follow_high':dist*=1.5
  dist*=c.get('dm',1.)
  return (cx+n[0]*dist-f[0]*.6,cy+n[1]*dist-f[1]*.6,hz),(cx+f[0]*lead,cy+f[1]*lead,1.1*size),lens
 if kd=='insert':
  p=plan.props[c['prop']];pp=p.at(t,plan);x,y,h=plan.pos(sp,t);a=plan.actors[sp];dm=c.get('dm',1.)
  f=(math.cos(h),math.sin(h));n=(-f[1]*c.get('side',1.),f[0]*c.get('side',1.))
  return (pp[0]+f[0]*.6*dm+n[0]*1.5*a.size*dm,pp[1]+f[1]*.6*dm+n[1]*1.5*a.size*dm,pp[2]+.45),(pp[0]-f[0]*.2,pp[1]-f[1]*.2,pp[2]),lens
 if kd=='medium':
  x,y,h=plan.pos(sp,t);a=plan.actors[sp];f=(math.cos(h),math.sin(h));n=(-f[1]*c.get('side',1.),f[0]*c.get('side',1.));d=4.6*max(.8,a.size)*c.get('dm',1.)
  fx,fy=_rotv(f,math.radians(30*c.get('side',1.)));return (x+fx*d,y+fy*d,1.35*a.size),(x,y,1.05*a.size),lens
 raise ValueError('unknown shot kind %r'%kd)

def _score(plan,c,side):
 """how good this side is for a cut: distance of uninvolved characters from the line of sight, camera not inside a solid or off the map"""
 c2=dict(c,side=side);t=(c['t0']+c['t1'])/2;pos,aim,_=frame(plan,c2,t);sc=1.5
 inv={c.get('subject'),c.get('to')}|set(c.get('group') or [])
 for w in plan.actors:
  if w in inv:continue
  p=plan.pos(w,t);d,_=_segdist2(pos,aim,p);sc=min(sc,d)
 for w in plan.actors:
  p=plan.pos(w,t);k=plan.actors[w].size;d=math.hypot(pos[0]-p[0],pos[1]-p[1])
  if d<1.5*k:sc-=(1.5*k-d)*2.
 if any(math.hypot(pos[0]-cx,pos[1]-cy)<r+.3 for cx,cy,r in plan.layout['obstacles']):sc-=2.
 hx,hy=plan.layout['half']
 if abs(pos[0])>hx+4 or abs(pos[1])>hy+4:sc-=1.
 return sc
def _segdist2(a,b,p):
 dx,dy=b[0]-a[0],b[1]-a[1];L2=dx*dx+dy*dy or 1.;u=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2));return math.hypot(a[0]+dx*u-p[0],a[1]+dy*u-p[1]),u
def _pick_sides(plan,cuts):
 for c in cuts:
  if c['kind'] in ('wide','group') or c.get('side') is None:continue
  s0=c['side']
  if c['kind'] in ('ots','two'):
   if _score(plan,c,s0)<0 and _score(plan,c,-s0)>=0:c['side']=-s0
   continue
  best=None
  for dm in (1.,.8,1.3,1.6):
   for sd in (s0,-s0):
    c2=dict(c,dm=dm);sc=_score(plan,c2,sd)-.05*abs(dm-1.)-(.02 if sd!=s0 else 0)
    if best is None or sc>best[0]:best=(sc,sd,dm)
  c['side']=best[1];c['dm']=best[2]
 return cuts
