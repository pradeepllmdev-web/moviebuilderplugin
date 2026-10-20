"""Short constructors for performance-scene specs (pure Python): a scene reads like a script.

    from perf_dsl import *
    S=scene('s01','Dawn at the square',loc('village_square',seed=2),cast=[at('mara',-8,-6,face='well'),at('bram',6,-5)],time='dawn',music='calm',steps=[
        go('mara','well',stop=2), par(go('bram','mara'),look('mara','bram',3)), say('mara','We should not be here.','concern','bram'), act('bram','shrug'), sit('bram','bench_a.0',face='well')])
The beats are plain dicts (see perf_plan for what each does); convo() turns a list of (who, text[, mood[, to]]) into say beats; par() groups beats that run at the same time."""
def go(who,to,**k):return dict(do='go',who=who,to=to,**k)
def run(who,to,**k):return dict(do='go',who=who,to=to,gait='run',**k)
def turn(who,to):return dict(do='turn',who=who,to=to)
def say(who,text,mood=None,to=None,**k):
 d=dict(do='say',who=who,text=text,**k)
 if mood:d['mood']=mood
 if to:d['to']=to
 return d
def act(who,clip,**k):return dict(do='act',who=who,clip=clip,**k)
def react(who,kind,to=None):
 d=dict(do='react',who=who,kind=kind)
 if to is not None:d['to']=to
 return d
def look(who,at,dur=1.5):return dict(do='look',who=who,at=at,dur=dur)
def emote(who,kind,dur=2.):return dict(do='emote',who=who,kind=kind,dur=dur)
def wait(dur):return dict(do='wait',dur=dur)
def take(who,prop,hand=None):
 d=dict(do='take',who=who,prop=prop)
 if hand:d['hand']=hand
 return d
def put(who,at=None,on=None,prop=None):
 d=dict(do='put',who=who)
 if at is not None:d['at']=list(at)
 if on:d['on']=on
 if prop:d['prop']=prop
 return d
def give(who,to):return dict(do='give',who=who,to=to)
def push(who,prop,dist=1.2,dir=None):
 d=dict(do='push',who=who,prop=prop,dist=dist)
 if dir is not None:d['dir']=dir
 return d
def sit(who,on,face=None):
 d=dict(do='sit',who=who,on=on)
 if face is not None:d['face']=face
 return d
def stand(who):return dict(do='stand',who=who)
def sfx(name,at=0.,who=None,gain=1.):return dict(do='sfx',name=name,at=at,who=who,gain=gain)
def cam(size=None,subject=None,mode=None):return dict(do='cam',size=size,subject=subject,mode=mode)
def par(*beats):return list(beats)
class Convo(list):
 """a run of say beats that happen one after another (scene() spreads it into the step list)"""
def convo(lines):
 """[(who, text[, mood[, to]]), ...] -> say beats"""
 out=Convo()
 for l in lines:
  who,text=l[0],l[1];mood=l[2] if len(l)>2 else None;to=l[3] if len(l)>3 else None;out.append(say(who,text,mood,to))
 return out
def at(id_,x,y,face=None):
 d=dict(id=id_,at=[x,y])
 if face is not None:d['face']=list(face) if isinstance(face,(tuple,list)) else face
 return d
def loc(preset,seed=1,**k):return dict(preset=preset,seed=seed,**k)
def prop(id_,kind,x,y,z=None,on=None,**k):
 d=dict(id=id_,kind=kind,at=[x,y],**k)
 if z is not None:d['z']=z
 if on:d['on']=on
 return d
def scene(id_,title,location,cast,steps,props=None,time='day',ambience='wind',music='calm',intent=''):
 flat=[]
 for s in steps:
  if isinstance(s,Convo):flat+=list(s)
  else:flat.append(s)
 return dict(id=id_,title=title,intent=intent,location=location,time=time,ambience=ambience,music=music,cast=cast,props=props or [],steps=flat)
