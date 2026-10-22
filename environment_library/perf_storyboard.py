"""Storyboard and pacing review of a film, from the compiled plans (pure Python, no Blender).

    rows=perf_storyboard.scene_rows(plan)            one row per camera cut: time, shot, who, the PURPOSE of the shot, and what happens in it
    md=perf_storyboard.storyboard_md(film, plans)    the whole film as a readable storyboard (written as storyboard.md by perf_movie)
    md=perf_storyboard.review_md(film, plans)        a table read: lines and words per scene, speech share, action density, dead time, repeated beats, screen time and a list of notes

The purpose of a shot is read from what the plan puts in it: an establishing wide, a face for an emotional line, a reveal of what a character points at, a chase, a detail of the hands, a reaction. The review flags what makes a film drag: long stretches with no speech and no story event, scenes that are all talk, the same beat repeated, characters who never speak or act."""
import collections,math
STORY_EVENTS=('take','put','give','push','point','icon','act','sit','stand')
def _events(plan,a,b):return [e for e in plan.events if e.get('t0',0)<b-1e-6 and e.get('t1',0)>a+1e-6]
def purpose(plan,c):
 """(label, detail) for one camera cut"""
 a,b=c['t0'],c['t1'];ev=_events(plan,a,b);k=c['kind'];who=c.get('subject') or ''
 say=[e for e in ev if e['kind']=='say']
 if c['name']=='establish':return 'Establish','where we are and who is here'
 if k=='reveal':return 'Reveal','%s points: look at what they see'%who
 if k=='insert':return 'Detail','the hands and the %s'%c.get('prop','prop')
 if k in('track','follow_high'):
  fast=c.get('fast');return ('Chase' if fast else 'Travel'),('low, close and wide: speed' if fast else 'follow %s across the space'%who)
 if k in('wide','group'):return ('Wide hold' if c['name'].startswith(('end','hold')) else 'Wide'),'the whole space and everyone in it'
 if say:
  L=say[0];m=L.get('mood','');face='close on the face' if c.get('close') else 'front quarter'
  return 'Dialogue','%s (%s) - %s'%(who,m,face)
 icons=[e for e in ev if e['kind']=='icon']
 if icons:return 'Reaction','%s: %s'%(icons[0]['who'],icons[0]['what'])
 acts=[e for e in ev if e['kind']=='act']
 if acts:return 'Action','%s %s'%(acts[0]['who'],acts[0].get('clip'))
 return 'Hold',who
def scene_rows(plan):
 import perf_camera as pc
 out=[]
 for c in pc.direct(plan):
  p=purpose(plan,c);out.append(dict(t0=round(c['t0'],1),t1=round(c['t1'],1),kind=c['kind'],who=c.get('subject') or '',purpose=p[0],detail=p[1]))
 return out
def storyboard_md(film,plans):
 out=['# Storyboard: %s'%film.get('title',film.get('id','film')),'']
 for sp,P in zip(film['scenes'],plans):
  if P is None:continue
  out+=['## %s - %s'%(sp.get('title',sp['id']),sp.get('objective','')),'','_%s_'%sp.get('intent',''),'','| time | shot | purpose | detail |','|---|---|---|---|']
  for r in scene_rows(P):out.append('| %.1f-%.1f s | %s | %s | %s |'%(r['t0'],r['t1'],r['kind'],r['purpose'],r['detail']))
  out.append('')
 return '\n'.join(out)
def scene_stats(plan):
 """numbers for one scene: seconds, lines, words, speech seconds, story events per ten seconds, the longest stretch with neither speech nor a story event, repeated acts"""
 secs=plan.seconds;words=sum(len(L['text'].split()) for L in plan.lines);speech=sum(L['t1']-L['t0'] for L in plan.lines)
 busy=sorted([(L['t0'],L['t1']) for L in plan.lines]+[(e['t0'],e['t1']) for e in plan.events if e['kind'] in STORY_EVENTS and not (e['kind']=='act' and e.get('clip') in('idle','look'))])
 last=0.;worst=(0.,0.)
 for a,b in busy:
  if a-last>worst[0]:worst=(a-last,last)
  last=max(last,b)
 if secs-last>worst[0]:worst=(secs-last,last)
 acts=collections.Counter((e['who'],e.get('clip')) for e in plan.events if e['kind']=='act' and e.get('clip') not in('idle','look'))
 rep=[(k,v) for k,v in acts.items() if v>=3]
 n_story=sum(1 for e in plan.events if e['kind'] in STORY_EVENTS)
 return dict(seconds=secs,lines=len(plan.lines),words=words,speech=speech,events=n_story,density=10.*n_story/max(1.,secs),dead=worst[0],dead_at=worst[1],repeats=rep,speakers={L['speaker'] for L in plan.lines},actors=set(plan.actors))
ACTIVE=('take','put','give','push','point','icon','sit','stand','act')
def _norm(t):return ' '.join(''.join(ch for ch in t.lower() if ch.isalnum() or ch==' ').split())
def story_check(film,plans):
 """the story-level checks of a film (pure Python, from the plans): returns a list of notes. A scene without a goal; a walk that arrives at nothing (no line, action or sign within three seconds of arriving, and nobody speaks while walking); a prop that is picked up and never given, put down or carried into the next scene; a line used twice; a scene that is silent for too long at the start, or talks for a long time before anything is shown"""
 notes=[];scenes=film['scenes'];taken={}
 for k,(sp,P) in enumerate(zip(scenes,plans)):
  if P is None:continue
  sid=sp['id']
  if not sp.get('objective') and not sp.get('intent'):notes.append('%s: no goal or intent written for the scene'%sid)
  ev=P.events
  def near(who,a,b):
   for e in ev:
    if e['kind']=='say' and (e['who']==who or e.get('to')==who) and e['t0']<b and e['t1']>a:return True
    if e['kind'] in ACTIVE and e['who']==who and e['t0']<b and e['t1']>a and not (e['kind']=='act' and e.get('clip') in('idle','look')):return True
   return False
  for e in ev:
   if e['kind']!='go' or e['t1']-e['t0']<4.:continue
   if e['t1']>P.seconds-1.5:continue            # leaving the scene is a purpose
   if e.get('gait') in('run','brisk'):continue     # a chase or a hurry has its own purpose
   px,py=P.pos(e['who'],e['t1'])[:2]
   if any(j!=e['who'] and math.hypot(px-P.pos(j,e['t1'])[0],py-P.pos(j,e['t1'])[1])<2.6 for j in P.actors):continue     # walks up to someone
   if any(math.hypot(px-q.at(e['t1'],P)[0],py-q.at(e['t1'],P)[1])<1.6 for q in P.props.values()):continue     # walks up to a prop
   if sum(1 for g in ev if g['kind']=='go' and g['t0']<e['t1'] and g['t1']>e['t0'])>=3:continue     # a crowd on the move (a march, a flight)
   if near(e['who'],e['t0'],e['t1']+3.):continue   # speaks while walking, or something happens on arrival
   notes.append('%s: %s walks for %.0f s from %.0f s and then nothing happens (give the walk a reason, a line or an action on arrival, or cut it)'%(sid,e['who'],e['t1']-e['t0'],e['t0']))
  if P.lines:
   first=min(L['t0'] for L in P.lines)
   if first>9. and P.seconds>20:notes.append('%s: the first line comes at %.0f s: say what the scene is about sooner'%(sid,first))
  held=set();
  for pid,pr in P.props.items():
   last=None
   for seg in pr.track:
    if seg[1]=='held':last=seg[2]
    elif seg[1]=='world' and seg[0]>0:last=None
   if last:held.add((pid,last))
  for pid,who in held:
   nxt=scenes[k+1] if k+1<len(scenes) else None
   carried=nxt is not None and any(c.get('holds')==pid for c in nxt['cast'])
   if nxt is not None and not carried and who in {c['id'] for c in nxt['cast']}:notes.append('%s: %s ends the scene holding %s but the next scene does not carry it on (at(..., holds=%r))'%(sid,who,pid,pid))
  for pid,pr in P.props.items():
   taken[pid]=taken.get(pid,0)+sum(1 for seg in pr.track if seg[1]=='held')
 used=set()                       # setup and payoff: a prop that is shown and never used, and a film that does not end on a button
 for sp,P in zip(scenes,plans):
  if P is None:continue
  for pid,pr in P.props.items():
   if any(seg[1]=='held' for seg in pr.track) or any(e.get('prop')==pid for e in P.events) or any(c.get('holds')==pid for c in sp['cast']):used.add(pid)
 for sp,P in zip(scenes,plans):
  if P is None:continue
  for pid,pr in P.props.items():
   if pid not in used and pr.kind not in('table','bench','crate','barrel','sack'):notes.append('%s: the prop %r is set up but never used (a setup needs a payoff, or it is just clutter)'%(sp['id'],pid))
 last=next((P for P in reversed(plans) if P is not None),None)
 if last is not None and len(scenes)>2:
  tail=[e for e in last.events if e['t0']>last.seconds-9.]
  button=any(e['kind']=='act' and e.get('clip') in('laugh','cele','joy','hips','bow','wave') for e in tail) or any(e['kind']=='icon' and e.get('what') in('joy','laugh','love') for e in tail) or any(L['mood'] in('joy','warm') for L in last.lines if L['t0']>last.seconds-12.)
  if not button:notes.append('the last scene has no closing beat (a laugh, a warm line, a small joke): end on a button')
 texts={}
 for sp,P in zip(scenes,plans):
  if P is None:continue
  for L in P.lines:texts.setdefault(_norm(L['text']),[]).append(sp['id'])
 for t,w in texts.items():
  if len(w)>1 and len(t.split())>2:notes.append('the line %r is spoken %d times (%s): vary it'%(t,len(w),', '.join(w)))
 return notes
def review_md(film,plans):
 out=['# Table read: %s'%film.get('title',film.get('id','film')),'','| scene | s | lines | words | speech | events/10 s | longest dead stretch |','|---|---|---|---|---|---|---|'];notes=[];speak=collections.Counter();cast=set(c['id'] for c in film['cast']);total=0.;talk=0.;used=set()
 for sp,P in zip(film['scenes'],plans):
  if P is None:continue
  s=scene_stats(P);total+=s['seconds'];talk+=s['speech'];speak.update(L['speaker'] for L in P.lines);used|=s['actors']
  out.append('| %s | %.0f | %d | %d | %.0f%% | %.1f | %.1f s at %.0f s |'%(sp['id'],s['seconds'],s['lines'],s['words'],100*s['speech']/max(1,s['seconds']),s['density'],s['dead'],s['dead_at']))
  if s['dead']>6.:notes.append('%s: %.0f s with no speech and no story event from %.0f s (cut it, speed the walk or add a beat)'%(sp['id'],s['dead'],s['dead_at']))
  if s['density']<2.5 and s['seconds']>15:notes.append('%s: few story events (%.1f per 10 s): the scene may drag'%(sp['id'],s['density']))
  if s['speech']/max(1,s['seconds'])>.7:notes.append('%s: %.0f%% talk: show something while they speak (walk and talk, props, reactions)'%(sp['id'],100*s['speech']/s['seconds']))
  for (who,clip),n in s['repeats']:notes.append('%s: %s does %r %d times: vary it'%(sp['id'],who,clip,n))
  if s['lines']==0 and s['seconds']>20:notes.append('%s: no dialogue for %.0f s: make sure the action carries the story (icons, reveals)'%(sp['id'],s['seconds']))
 notes+=story_check(film,plans)
 out+=['','Film: %.0f s, speech %.0f%%'%(total,100*talk/max(1,total))]
 mute=[c for c in cast if speak[c]==0 and c in used]
 if mute:notes.append('characters who never speak (fine for animals, a gap for people): %s'%', '.join(sorted(mute)))
 out+=['','## Notes','']+(['* '+n for n in notes] or ['* nothing flagged'])
 return '\n'.join(out)
