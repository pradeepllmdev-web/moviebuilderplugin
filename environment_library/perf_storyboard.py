"""Storyboard and pacing review of a film, from the compiled plans (pure Python, no Blender).

    rows=perf_storyboard.scene_rows(plan)            one row per camera cut: time, shot, who, the PURPOSE of the shot, and what happens in it
    md=perf_storyboard.storyboard_md(film, plans)    the whole film as a readable storyboard (written as storyboard.md by perf_movie)
    md=perf_storyboard.review_md(film, plans)        a table read: lines and words per scene, speech share, action density, dead time, repeated beats, screen time and a list of notes

The purpose of a shot is read from what the plan puts in it: an establishing wide, a face for an emotional line, a reveal of what a character points at, a chase, a detail of the hands, a reaction. The review flags what makes a film drag: long stretches with no speech and no story event, scenes that are all talk, the same beat repeated, characters who never speak or act."""
import collections
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
 out+=['','Film: %.0f s, speech %.0f%%'%(total,100*talk/max(1,total))]
 mute=[c for c in cast if speak[c]==0 and c in used]
 if mute:notes.append('characters who never speak (fine for animals, a gap for people): %s'%', '.join(sorted(mute)))
 out+=['','## Notes','']+(['* '+n for n in notes] or ['* nothing flagged'])
 return '\n'.join(out)
