"""Blender script: one performance scene compiled from a declarative spec (see perf_plan.py for the spec language).

blender -b --disable-autoexec --python perf_scene.py -- <ship_assets_dir> <out.blend> <spec.json> [<cast.json>]

Technique: PLAN FIRST, BLENDER SECOND. perf_plan compiles the spec to per-frame positions, clips, speech, hand reaches and prop tracks (and audits them); this script only plays the plan: it builds the location (perf_locations), the cast from the registry
(cast_builder: species proportions, tint, parts, accessories), keys every root and plays each clip on the NLA with the play scale derived from the gait table (planted feet), keys head gaze from the plan (eye lines move to the speaker, to the
prop being handled, ahead when walking), keys lip sync and expression from the synthesised voices, drives the arms with IK towards the plan's hand targets (props follow the hands), lets the automatic camera director (perf_camera) cut the coverage,
and writes the sound (voices, ambience, score, footsteps, effects). Audits (all numeric, printed as AUDIT lines): the plan's own (speech overlap, collisions, solids, gait speeds), eye lines, lip sync, planted-foot slip, hand-to-prop distance,
speaker framing in every dialogue cut, camera inside or behind solids, persistence. Also writes <out>.plan.json (cuts, lines, audits) for the movie runner and the contact sheets."""
import bpy,math,sys,os,json,random
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,scene_params,dialogue as dg,gaits
import cast_registry as cr,cast_builder as cb,perf_plan as pp,perf_camera as pc,perf_locations as pl,perf_audio as pa,perf_score as ps
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
SPEC=json.load(open(args[2],encoding='utf-8'))
REG=cr.Registry.load(args[3] if len(args)>3 else SPEC['registry'])
import perf_voices as pv
pp.DURATION_PROVIDER=pv.duration
S=sb.Scene(SPEC['id']);PI=math.pi;smooth=kit.smooth
PLAN=pp.compile(SPEC,REG);LAY=PLAN.layout;issues=list(PLAN.audit());S.clock(PLAN.seconds);FPS=24
TIME=SPEC.get('time','day');LOC=pl.build(S,SPEC.get('location',dict(preset='meadow')),TIME)
# ---------------------------------------------------------------------------------------------------------- the cast
def _piper(L,k):
 v=PLAN.actors[L['speaker']].look.get('voice')
 return pv.load(v,L['text'],L['mood']) if v else None
dg.register_voice_provider('piper',_piper)
orig_pitch=dg.pitch_of;PITCH={i:PLAN.actors[i].look['pitch'] for i in PLAN.actors}
dg.pitch_of=lambda name:PITCH.get(name,orig_pitch(name))
CH={};CRE={}      # people (the lion rig: lips, eyes, hands) and creatures (own skeleton and actions)
for i,a in PLAN.actors.items():
 ch_=cb.build(S,a.look,i);(CRE if ch_.get('creature') else CH)[i]=ch_
ALL=dict(CH,**CRE)
EXTRAS={}
for e in PLAN.extras:
 ch=cb.build(S,e['look'],e['id']);EXTRAS[e['id']]=ch;r=ch['root'];r.location=(e['x'],e['y'],0.);r.rotation_euler=(0,0,e['h']+PI/2)
def hop(i,t):
 """(height, step back) of a character at time t from the emotion beats: hops of joy, a recoil and a little jump of surprise, shaking laughter: the story's feelings read in the body"""
 a=PLAN.actors[i];sz=a.size;z=0.;back=0.
 for e in PLAN.events:
  if e.get('who')!=i or e['kind']!='act':continue
  c=e.get('clip');t0=e['t0']
  if c=='cele':
   for dt in (.25,.8):
    u=(t-(t0+dt))/.38
    if 0<=u<=1:z=max(z,.18*sz*4*u*(1-u))
  elif c=='startle':
   u=(t-(t0+.05))/.3
   if 0<=u<=1:z=max(z,.08*sz*4*u*(1-u))
   w=t-t0;back=max(back,.28*sz*(math.sin(min(1.,max(0.,w/.35))*PI/2) if w<.9 else max(0.,1-(w-.9)/.7)))
  elif c=='laugh':
   for k in range(3):
    u=(t-(t0+.2+.35*k))/.28
    if 0<=u<=1:z=max(z,.05*sz*4*u*(1-u))
 return z,back
def flair(i,t):
 """(extra height, extra yaw, squash) of a creature at time t from its joy flair events"""
 a=PLAN.actors[i];H=a.look['height'];z=0.;yaw=0.;sq=1.
 for e in PLAN.events:
  if e.get('who')!=i or e['kind']!='act' or not e.get('flair'):continue
  t0,t1=e['t0'],e['t1']
  if not t0<=t<=t1:continue
  u=(t-t0)/max(.1,t1-t0);fl=e['flair']
  if fl=='hop':z=max(z,.16*H*4*u*(1-u))
  elif fl=='hop3':z=max(z,.1*H*abs(math.sin(u*3*PI)))
  elif fl=='spin':yaw=2*PI*(u*u*(3-2*u));z=max(z,.1*H*4*u*(1-u))
  elif fl=='wiggle':yaw=math.radians(24)*math.sin(u*PI*7)*(1-u)
  elif fl=='squash':sq=1+.14*math.sin(u*PI*6)*(1-u)
 return z,yaw,sq
def keyroot(i):
 a=PLAN.actors[i];r=ALL[i]['root'];prev=None;base_scale=tuple(r.scale)
 for f in S.keys():
  k=min(len(a.X)-1,f-1);hz_,hb_=hop(i,(f-1)/FPS);fz_,fy_,fs_=flair(i,(f-1)/FPS) if a.look.get('creature') else (0.,0.,1.);r.location=(a.X[k]-math.cos(a.H[k])*hb_,a.Y[k]-math.sin(a.H[k])*hb_,hz_+fz_);h=a.H[k]+PI/2+fy_
  if a.look.get('creature'):r.scale=tuple(v_*fs_ for v_ in base_scale);r.keyframe_insert('scale',frame=f)
  if prev is not None:h=prev+pp.wrap(h-prev)
  prev=h;r.rotation_euler=(0,0,h);r.keyframe_insert('location',frame=f);r.keyframe_insert('rotation_euler',frame=f)
for i in ALL:keyroot(i)
# ---------------------------------------------------------------------------------------------------------- clips on the NLA (planted feet: play scale from the gait table)
def place(ch,name,t0,t1,sc,opt,first):
 act=S.clip(name);f0=opt.get('f0');f1=opt.get('f1');tr=ch['tracks'][ch['n']%2];ch['n']+=1;a=t0 if first else max(0,t0-.2)
 st=tr.strips.new(name,S.F(a),act);st.action_slot=act.slots[0];n=(f1 or int(act.frame_range[1]))-(f0 or int(act.frame_range[0]))+1
 if f0:st.action_frame_start=f0
 if f1:st.action_frame_end=f1
 st.scale=sc
 if opt.get('reverse'):st.use_reverse=True
 if opt.get('hold'):
  L=opt.get('len',t1-t0);st.scale=(L*FPS)/n if f1 else sc;st.extrapolation='HOLD'
 else:
  need=(S.F(t1)-st.frame_start)/(n*sc)
  if need>=1:st.repeat=need
  else:st.action_frame_end=st.action_frame_start+max(2,need*n)-1
  st.extrapolation='NOTHING'
 walk=name in ('walk','strut','shuffle','bounce','sneak','stomp','brisk','run')
 st.blend_in=(8 if walk else 5) if ch['n']>1 else 0;st.blend_out=0 if opt.get('hold') else (8 if walk else 5);return st
# people on the Universal Animation Library rig: the planned clips become the library actions (walk gaits -> Walk / Jog / Sprint / Crouch at the planned ground speed, sitting, gestures, falls ...)
HUM_MAP={'idle':'Idle_Loop','look':'Idle_Loop','talk':'Idle_Talking_Loop','argue':'Idle_Talking_Loop','think':'Idle_FoldArms_Loop','nod':'Yes','laugh':'Idle_Talking_Loop','shrug':'Idle_No_Loop','wave':'Idle_Rail_Call','bow':'Yes','cele':'Idle_Talking_Loop','hips':'Idle_Talking_Loop','startle':'Hit_Chest','hit':'Punch_Jab','punch':'Punch_Jab','kick':'Melee_Hook','block':'Sword_Block','dodge':'Roll','cut':'Sword_Attack','push':'Push_Loop','pick':'PickUp_Table','kneel':'Fixing_Kneeling','climb':'Interact','fall':'Death01','getup':'LayToIdle','jump':'Jump_Start'}
HUM_LOOPS=('Idle_Loop','Idle_Talking_Loop','Idle_FoldArms_Loop','Dance_Loop','Walk_Loop','Walk_Carry_Loop','Walk_Formal_Loop','Crouch_Fwd_Loop','Jog_Fwd_Loop','Sprint_Loop','Push_Loop','Sitting_Idle_Loop','Sitting_Talking_Loop','Idle_No_Loop','Idle_Rail_Call')
def held_at(i,t):
 """True if actor i carries a prop at time t (from the props' tracks)"""
 for p in PLAN.props.values():
  cur=None
  for seg in p.track:
   if seg[0]<=t+1e-3:cur=seg
  if cur is not None and cur[1]=='held' and cur[2]==i:return True
 return False
def place_h(i,ch,name,t0,t1,sc,opt,first):
 a=PLAN.actors[i];ca=ch['cact'];k=ch['k'];sp=None
 for (w0,w1,g,scl,speed) in a.walks:
  if w0-1e-3<=t0<=w1+1e-3:sp=speed
 scale=1.
 if name=='run':act_n,nat='Jog_Fwd_Loop',cr.HUMAN_NAT['jog']     # a run is a jog: the sprint looks comic
 elif name=='brisk':act_n,nat='Walk_Loop',cr.HUMAN_NAT['walk']     # a hurry is a quicker walk
 elif name in('sneak','crawl'):act_n,nat='Crouch_Fwd_Loop',cr.HUMAN_NAT['slow']
 elif name in('walk','strut','stomp','bounce','shuffle'):act_n,nat=('Walk_Formal_Loop' if name=='strut' else 'Walk_Loop'),cr.HUMAN_NAT['walk']
 elif name=='sit':act_n,nat=('Sitting_Exit' if opt.get('reverse') else 'Sitting_Enter'),None
 else:act_n,nat=HUM_MAP.get(name,'Idle_Loop'),None
 if name in('walk','bounce','shuffle') and held_at(i,t0+.1) and 'Walk_Carry_Loop' in ca:act_n,nat='Walk_Carry_Loop',cr.HUMAN_NAT['carry']     # walking with something in the hands
 if act_n not in ca:act_n='Idle_Loop'
 if nat and sp:scale=max(.45,min(2.6,nat*k/max(.05,sp)))
 act=ca[act_n];n=int(act.frame_range[1]-act.frame_range[0])+1;f_start=S.F(t0 if first else max(0,t0-.4));dur_f=S.F(t1)-f_start+(0 if first else int(.2*FPS))
 def strip(act_,sc_,start,rep=1.,hold=False,end_extrap=None):
  tr=ch['rig'].animation_data.nla_tracks.new();ch['n']+=1;st=tr.strips.new(act_.name,start,act_);st.action_slot=act_.slots[0];st.scale=sc_;st.repeat=rep;st.extrapolation=end_extrap or ('HOLD' if hold else 'NOTHING');st.blend_in=10 if ch['n']>1 else 0;st.blend_out=0 if hold else 10;return st     # long blends: the hands and the body settle into the next pose instead of snapping
 if name=='sit' and not opt.get('reverse'):      # sit down, then sit
  d_=min(dur_f,int(3.2*FPS));strip(act,d_/n,f_start);idle=ca.get('Sitting_Idle_Loop');talk=ca.get('Sitting_Talking_Loop')
  if idle is not None and dur_f>d_+2:
   ts_=sorted((L['t0'],L['t1']) for L in PLAN.lines if L['speaker']==i and L['t1']>t0+3.2 and L['t0']<t1) if talk is not None else []
   cur=f_start+d_;end=f_start+dur_f;segs=[]
   for (a0,b0) in ts_:
    fa,fb=max(cur,S.F(a0)-4),min(end,S.F(b0)+4)
    if fb-fa<12:continue
    if fa-cur>=6:segs.append((idle,cur,fa))
    segs.append((talk,fa,fb));cur=fb
   if end-cur>=2:segs.append((idle,cur,end))
   for k_,(ac,fa,fb) in enumerate(segs):
    na=int(ac.frame_range[1]-ac.frame_range[0])+1;st_=strip(ac,1.,fa-(0 if k_==0 else 5),max(1.,(fb-fa+(0 if k_==0 else 5))/na),False,'HOLD' if k_==len(segs)-1 else None)
  return
 if name in('idle','look') and t1-t0>3.4 and not held_at(i,t0+.1):
  rr=random.Random(sum(map(ord,i+SPEC['id']))+int(t0*10));end=f_start+dur_f;plan_=[]
  for L in PLAN.lines:       # speaking: the talking loop (hands that gesture); being addressed: a nod now and then
   if L['speaker']==i and L['t1']>t0 and L['t0']<t1:plan_.append((max(f_start,S.F(L['t0'])-3),min(end,S.F(L['t1'])+3),'Idle_Talking_Loop'))
   elif L.get('to')==i and L['speaker']!=i and L['mood'] not in('angry','sad') and t0<L['t0']+1.<t1 and rr.random()<.6:plan_.append((S.F(L['t0']+.8),S.F(L['t0']+.8)+int(1.7*FPS),'Yes'))
  plan_.sort();clean=[];cur=f_start
  for a0,b0,kd in plan_:
   if a0>=cur and b0<=end:clean.append((a0,b0,kd));cur=b0
  segs=[];cur=f_start
  def fill(a0,b0):
   x=a0
   while b0-x>=int(1.2*FPS):
    dl=int(rr.uniform(2.6,4.4)*FPS)
    if b0-(x+dl)<int(1.6*FPS):dl=b0-x
    pick=rr.random();ac='Idle_FoldArms_Loop' if (pick<.22 and dl>=int(3*FPS) and 'Idle_FoldArms_Loop' in ca) else 'Idle_Loop'
    segs.append((x,x+dl,ac));x+=dl
  for a0,b0,kd in clean:
   fill(cur,a0);segs.append((a0,b0,kd));cur=b0
  fill(cur,end)
  if not segs:segs=[(f_start,end,'Idle_Loop')]
  segs[-1]=(segs[-1][0],end,segs[-1][2])
  for k_,(a0,b0,kd) in enumerate(segs):
   ac=ca.get(kd) or ca['Idle_Loop'];na=int(ac.frame_range[1]-ac.frame_range[0])+1;over=0 if k_==0 else 6
   if kd=='Yes':strip(ac,max(.5,(b0-a0)/na),a0-over)
   else:strip(ac,1.,a0-over,max(1.,(b0-a0+over)/na),False,'HOLD' if k_==len(segs)-1 else None)
  return
 if act_n in HUM_LOOPS:strip(act,scale,f_start,max(1.,dur_f/(n*scale)))
 elif name=='fall':strip(act,max(.5,dur_f/n),f_start,1.,True)
 else:strip(act,max(.4,dur_f/n),f_start)
def add_base(ch):
 """a looping idle under everything a person does: when a clip ends or blends out the body settles into an idle, never into the skeleton's rest pose (a T)"""
 ac=ch['cact']['Idle_Loop'];tr=ch['rig'].animation_data.nla_tracks.new();n=int(ac.frame_range[1]-ac.frame_range[0])+1;total=S.F(PLAN.seconds)+120
 st=tr.strips.new('base',1,ac);st.action_slot=ac.slots[0];st.repeat=total/n;st.extrapolation='HOLD';ch['n']=1
for i,ch in CH.items():
 if ch.get('human2'):add_base(ch)
 segs=[];cl=PLAN.actors[i].clips
 for c in cl:
  if segs and c[1]-c[0]<.35 and not c[4]:segs[-1]=segs[-1][:1]+(c[1],)+segs[-1][2:];continue
  segs.append(c)
 for k,(t0,t1,name,sc,opt) in enumerate(segs):(place_h(i,ch,name,t0,t1,sc,opt,k==0) if ch.get('human2') else place(ch,name,t0,t1,sc,opt,k==0))
# creatures: the plan's clips become the animal's own actions (walk gaits -> Walk / WalkSlow / Run with the play speed from the planned ground speed, acts -> Jump / Death / Idle)
CR_STEPS=[]
CR_SPEED={'walk':1.6,'walkslow':.9,'run':4.2}     # ground speed in body lengths per second of each action at play scale 1
def place_creature(i,ch,name,t0,t1,sc,opt,first):
 a=PLAN.actors[i];ca=ch['cact'];sp=None
 for (w0,w1,g,scl,speed) in a.walks:
  if w0-1e-3<=t0<=w1+1e-3:sp=speed
 if name in ('run','brisk'):key_='run'
 elif name in ('shuffle','sneak','crawl'):key_='walkslow'
 elif name in ('walk','strut','stomp','bounce'):key_='walk'
 elif name in ('jump','cele','startle','dodge','kick','hit','punch','getup','hips','bow'):key_='jump'
 elif name=='fall':key_='death'
 else:key_='idle'
 if key_ not in ca:key_='idle'
 act=ca[key_];n=int(act.frame_range[1]-act.frame_range[0])+1;loop=key_ in('idle','walk','walkslow','run')
 scale=1.
 if key_ in('walk','walkslow','run') and sp:
  nat_=cr.CREATURE_NAT[a.look['creature']][('walk','walkslow','run').index(key_)]
  if name=='brisk':nat_*=.55
  scale=max(.4,min(2.6,nat_/max(.05,sp)))    # the clip's own ground speed over the planned one: feet stay planted
 if key_ in('walk','walkslow','run') and sp:
  CR_STEPS.append((i,t0,t1,n*scale/FPS/4.,a.look['height']))     # a footfall every quarter of the cycle
 tr=ch['rig'].animation_data.nla_tracks.new();ch['n']+=1;f_start=S.F(t0 if first else max(0,t0-.2));st=tr.strips.new(key_,f_start,act);st.action_slot=act.slots[0];st.scale=scale     # one track per strip: strips may overlap for the blend
 if loop:st.repeat=max(1.,(S.F(t1)-f_start)/(n*scale));st.extrapolation='NOTHING'
 else:
  st.scale=max(.5,(S.F(t1)-f_start)/n) if key_=='jump' else 1.;st.extrapolation='HOLD' if key_=='death' else 'NOTHING'
 st.blend_in=6 if ch['n']>1 else 0;st.blend_out=0 if key_=='death' else 6
for i,ch in CRE.items():
 segs=[];cl=PLAN.actors[i].clips
 for c in cl:
  if segs and c[1]-c[0]<.35 and not c[4]:segs[-1]=segs[-1][:1]+(c[1],)+segs[-1][2:];continue
  segs.append(c)
 for k,(t0,t1,name,sc,opt) in enumerate(segs):place_creature(i,ch,name,t0,t1,sc,opt,k==0)
for e in PLAN.extras:     # extras stand and breathe out of step with each other, looking at the focus
 ch=EXTRAS[e['id']];rx=random.Random(sum(map(ord,e['id']+SPEC['id'])));place(ch,'idle',0,S.seconds,1.,dict(f0=rx.randint(1,60),f1=96),True)
# ---------------------------------------------------------------------------------------------------------- gaze
def face_xyz(who,t):
 a=PLAN.actors[who];hx,hy,hz=PLAN.head_pos(who,t);x,y,h=PLAN.pos(who,t);g=PLAN.gaze(who,t)
 if g is None:tgt=(hx+math.cos(h)*6,hy+math.sin(h)*6,hz)
 elif g[0]=='char':tgt=PLAN.head_pos(g[1],t)
 elif g[0]=='prop':tgt=PLAN.props[g[1]].at(t,PLAN)
 else:p=g[1];tgt=(p[0],p[1],p[2] if p[2]>.2 else hz)
 d=(tgt[0]-hx,tgt[1]-hy);ang=pp.wrap(math.atan2(d[1],d[0])-h);lim=math.radians(72)
 if abs(ang)>lim:
  na=h+math.copysign(lim,ang);r=max(1.,math.hypot(*d));tgt=(hx+math.cos(na)*r,hy+math.sin(na)*r,tgt[2])
 return Vector(tgt)
import random
GZ={};FACE0={};SAC={i:(0.,0.) for i in CH};rnd_s={i:random.Random(sum(map(ord,SPEC['id']+i))) for i in CH};EYES={}
def damped(x,v,target,w,dt,vmax):
 """critically damped follow with a speed limit (angles in radians): no overshoot, no snapping, never faster than a real head turns"""
 for _ in range(4):
  h=dt/4;acc=w*w*(target-x)-2*w*v;v+=acc*h;v=max(-vmax,min(vmax,v));x+=v*h
 return x,v
for i,ch in CH.items():
 a=PLAN.actors[i];h0=a.H[0];FACE0[i]=(math.cos(h0),math.sin(h0),0);GZ[i]=S.gaze(ch,FACE0[i])
 yaw=pit=vy=vp=0.;eye=veye=0.;EYES[i]=[]
 for f in S.keys():
  t=(f-1)/FPS;tg=face_xyz(i,t);hx,hy,hz=PLAN.head_pos(i,t);x_,y_,h=PLAN.pos(i,t)
  if (f-1)//2%5==0:SAC[i]=(rnd_s[i].uniform(-.05,.05),rnd_s[i].uniform(-.03,.03))     # a small glance every ~0.4 s
  d=tg-Vector((hx,hy,hz));ty=pp.wrap(math.atan2(d.y,d.x)-h)+SAC[i][0];tp=math.atan2(d.z,max(.3,math.hypot(d.x,d.y)))+SAC[i][1]
  yaw,vy=damped(yaw,vy,ty,8.,2./FPS,math.radians(330));pit,vp=damped(pit,vp,max(-.5,min(.5,tp)),8.,2./FPS,math.radians(200))
  eye,veye=damped(eye,veye,max(-.7,min(.7,ty-yaw)),22.,2./FPS,math.radians(900));EYES[i].append((f,max(0.,min(1.,eye/.45)),max(0.,min(1.,-eye/.45))))   # the eyes arrive first, the head follows
  hd=h+yaw;GZ[i].location=Vector((hx+math.cos(hd)*6,hy+math.sin(hd)*6,hz+math.tan(max(-.5,min(.5,pit)))*6));GZ[i].keyframe_insert('location',frame=f)
for e in PLAN.extras:
 ch=EXTRAS[e['id']];fx=(math.cos(e['h']),math.sin(e['h']),0);g=S.gaze(ch,fx);g.location=(e['focus'][0],e['focus'][1],1.3*e['look']['scale'][2])
# ---------------------------------------------------------------------------------------------------------- lip sync and expression
def meshes_with(ch,key):return [o.data.shape_keys for o in ch['objs'] if o.type=='MESH' and o.data.shape_keys and key in o.data.shape_keys.key_blocks]
for ch in CH.values():
 for o in ch['objs']:
  if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data is None:o.data.shape_keys.animation_data_create()
def key(ch,name,pts):
 if ch.get('human2'):ch.setdefault('fk',{}).setdefault(name,[]).extend(pts);return     # a person face is a few solids on the head: collected here, keyed together in finalize_faces()
 for kb in meshes_with(ch,name):
  b=kb.key_blocks[name]
  for fr,v in pts:b.value=v;b.keyframe_insert('value',frame=fr)
for i_,rows in EYES.items():
 key(CH[i_],'GazeLeft',[(f,l) for f,l,r in rows]);key(CH[i_],'GazeRight',[(f,r) for f,l,r in rows])
VOICES=[];LIPKEYS={}
for L in PLAN.lines:
 x,syl,real=dg.voice_for(dict(L));VOICES.append((L,x,syl,real));ch=CH[L['speaker']];n=0
 for (tc,d,v) in syl:
  tcg=L['t0']+.2+tc;op,ro,wi=dg.VOWEL_KEYS[v];a,b,c=S.F(tcg-d*.5),S.F(tcg),S.F(tcg+d*.45)
  key(ch,'JawOpen',[(a,0),(b,op*.75),(c,0)]);key(ch,'Round',[(a,0),(b,ro*.7),(c,0)]);key(ch,'Wide',[(a,0),(b,wi*.5),(c,0)]);n+=1
 LIPKEYS[L['k']]=n
 for nm,val in dg.MOOD_KEYS[L['mood']].items():key(ch,nm,[(S.F(L['t0']-.3),0),(S.F(L['t0']+.2),val),(S.F(L['t1']-.2),val),(S.F(L['t1']+.3),0)])
 if L['to'] in CH and L['to']!=L['speaker']:
  for nm,val in (dg.MOOD_KEYS['warm'] if L['mood'] in ('warm','joy') else (dg.MOOD_KEYS['concern'] if L['mood'] in ('angry','sad') else {})).items():key(CH[L['to']],nm,[(S.F(L['t0']+.4),0),(S.F(L['t0']+1.0),val*.8),(S.F(L['t1']-.1),val*.8),(S.F(L['t1']+.4),0)])
for L in PLAN.lines:
 rb=random.Random(L['k']*131+sum(map(ord,SPEC['id'])));ch=CH[L['speaker']];t=L['t0']+rb.uniform(.4,.9)
 while t<L['t1']-.3:
  v=rb.uniform(.25,.45)
  for nm in ('ActingBrowL','ActingBrowR'):key(ch,nm,[(S.F(t),0),(S.F(t+.12),v),(S.F(t+.35),0)])
  t+=rb.uniform(.9,1.6)
EMOTE={'smile':dict(WarmSmile=.8),'frown':dict(Frown=.6),'concern':dict(Concern=.6,ActingBrowL=.4,ActingBrowR=.4),'sad':dict(ConcernStrong=.6,Frown=.2),'brows':dict(ActingBrowL=.7,ActingBrowR=.7)}
for i,a in PLAN.actors.items():
 if i not in CH:continue
 for (t0,t1,kind) in a.emotes:
  for nm,val in EMOTE[kind].items():key(CH[i],nm,[(S.F(t0),0),(S.F(t0+.4),val),(S.F(t1-.3),val),(S.F(t1),0)])
def finalize_faces():
 """the faces of the people: mouth, brows, eyes and pupils keyed from the collected speech, expression and gaze values (and a blink every few seconds)"""
 import numpy as np
 rb=random.Random(sum(map(ord,SPEC['id'])))
 for i,ch in CH.items():
  if not ch.get('human2'):continue
  F=ch['face'];fk=ch.get('fk',{});frames=list(S.keys())
  def val(nm,f):
   p=sorted(fk.get(nm,[]))
   if not p:return 0.
   return float(np.interp(f,[q[0] for q in p],[q[1] for q in p],left=0.,right=0.))
  blink=[];tb=rb.uniform(1.,3.)
  while tb<S.seconds:blink.append(tb);tb+=rb.uniform(2.4,5.5)
  base={n:o.matrix_basis.decompose() for n,o in F.items() if n!='hair'}
  for f in frames:
   t=(f-1)/FPS;j,wd,rd=val('JawOpen',f),val('Wide',f),val('Round',f);sm,fr_=val('WarmSmile',f),val('Frown',f)+.5*val('ConcernStrong',f);cn=val('Concern',f)+val('ConcernStrong',f)
   bl=max([max(0.,1-abs(t-b)/.09) for b in blink if abs(t-b)<.1],default=0.)
   loc,rot,scl=base['mouth'];o=F['mouth'];o.scale=(scl.x*(1+.4*wd+.5*sm-.35*rd),scl.y,scl.z*(1+5.*j+.7*rd-.25*fr_));o.location=(loc.x,loc.y,loc.z-.004*j+.002*sm);o.keyframe_insert('scale',frame=f);o.keyframe_insert('location',frame=f)
   for sg,nm in ((1,'L'),(-1,'R')):
    loc,rot,scl=base['brow'+nm];o=F['brow'+nm];up=val('ActingBrow'+nm,f);o.location=(loc.x,loc.y,loc.z+.007*up+.003*cn-.004*fr_);ang=sg*(.3*cn-.15*fr_);o.rotation_euler=(0,ang,0);o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
    loc,rot,scl=base['eye'+nm];e=F['eye'+nm];e.scale=(scl.x,scl.y,scl.z*(1-.92*bl));e.keyframe_insert('scale',frame=f)
    loc,rot,scl=base['pupil'+nm];pu=F['pupil'+nm];pu.scale=(scl.x,scl.y,scl.z*(1-.92*bl));pu.location=(loc.x+.007*(val('GazeRight',f)-val('GazeLeft',f)),loc.y,loc.z);pu.keyframe_insert('scale',frame=f);pu.keyframe_insert('location',frame=f)
finalize_faces()
# ---------------------------------------------------------------------------------------------------------- props
SHAPE={'cyl':('cup','jar','basket','barrel_small','scroll','tool','bell','pie'),'sphere':('sack','apple','egg','gem','boulder')}
PROPOBJ={}
def prop_shape(k):
 for s,ks in SHAPE.items():
  if k in ks:return s
 return 'cube'
for pid,p in PLAN.props.items():
 info=pl.PROP_KINDS[p.kind];root=bpy.data.objects.new('Prop_'+pid,None);S.link(root);sx,sy,sz=p.size;shp=prop_shape(p.kind);rot=(PI/2,0,0) if p.kind in ('scroll','tool') else (0,0,0)
 if p.kind in ('scroll','tool'):sc=(sy/2 if p.kind=='scroll' else sz/2,sz/2 if p.kind=='scroll' else sz/2,sx/2 if p.kind=='tool' else sz/2)
 sc=(sx/2,sy/2,sz/2) if shp!='cyl' else (sx/2,sy/2,sz/2)
 m=S.prim(shp,'PropM_'+pid,(0,0,0),info['color'],scale=sc,rot=rot,emit=info.get('emit',0.),parent=root);PROPOBJ[pid]=root
 if p.kind=='lantern':
  ld=bpy.data.lights.new('PropLight_'+pid,'POINT');ld.energy=260 if TIME in ('night','dusk','dawn','overcast') else 40;ld.color=(1,.78,.45);ld.shadow_soft_size=.2;lo=bpy.data.objects.new('PropLight_'+pid,ld);lo.parent=root;S.link(lo)
 for f in S.keys():
  t=(f-1)/FPS;pos=p.at(t,PLAN);root.location=pos
  seg=None
  root.keyframe_insert('location',frame=f)
for pid,p in PLAN.props.items():       # a quick pop when a prop is taken, put down or handed over: the eye finds the important object
 root=PROPOBJ[pid]
 for e in PLAN.events:
  if e['kind'] in ('take','put','give') and e.get('prop')==pid:
   tg=e.get('t_grasp',e['t0'])
   for dt,sc_ in ((-.05,1.),(.09,1.35),(.32,1.)):root.scale=(sc_,sc_,sc_);root.keyframe_insert('scale',frame=S.F(max(0,tg+dt)))
# ---------------------------------------------------------------------------------------------------------- IK arms
IKS={}
for i,ch in CH.items():
 a=PLAN.actors[i]
 if not any(a.hands[h] for h in ('R','L')):continue
 IK,TG=S.ik(ch,0.,.5);IKS[i]=(IK,TG);sh=S.shoulders(ch)
 for hand,lb in (('R','RH'),('L','LH')):
  prev_pos=None
  for f in S.keys():
   t=(f-1)/FPS;infl,pos=PLAN.hand_target(a,hand,t)
   if pos is None:pos=tuple(sh[lb]);infl=0.
   TG[lb].location=pos;TG[lb].keyframe_insert('location',frame=f);IK[lb].influence=infl;IK[lb].keyframe_insert('influence',frame=f)
# holders turn the held prop with them
for pid,p in PLAN.props.items():
 root=PROPOBJ[pid]
 for f in S.keys():
  t=(f-1)/FPS;cur=None
  for seg in p.track:
   if seg[0]<=t+1e-9:cur=seg
  yaw=p.yaw
  if cur and cur[1]=='held':yaw=PLAN.actors[cur[2]].H[min(len(PLAN.actors[cur[2]].H)-1,f-1)]
  root.rotation_euler=(0,0,yaw);root.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- body language: breathing, sway, speech nods, listening nods and the upper body leading every turn, as a COMBINE layer over the clips
import perf_body as pbody
from mathutils import Euler
from bpy_extras import anim_utils
def body_layer():
 fr=pbody.key_frames(PLAN)
 UAL={'Hips':'pelvis','Spine':'spine_01','Spine1':'spine_02','Spine2':'spine_03','Neck':'neck_01','Head':'Head','ThighL':'thigh_l','ThighR':'thigh_r'}
 for i,ch in CH.items():
  rig=ch['rig'];hum=bool(ch.get('human2'));sig=pbody.signals(PLAN,i);ad=rig.animation_data;pa_=PLAN.actors[i]
  tt=(np.array(fr)-1)/FPS
  if hum:       # a narrower stance while standing (the library's idles stand with the feet wide apart): the thighs close in, and ease out again for walking, sitting and every action
   stand=np.array([1. if (not PLAN._walking(i,t) and any(c0<=t<c1 and nm in('idle','look','talk','think','nod','laugh','shrug','wave','argue','cele','bow','hips','startle') for (c0,c1,nm,_s,_o) in pa_.clips) and not held_at(i,t)) else 0. for t in tt])
   stand=np.convolve(np.pad(stand,6,mode='edge'),np.ones(13)/13.,mode='valid');sig['ThighL']=np.zeros((len(tt),3));sig['ThighR']=np.zeros((len(tt),3));sig['ThighL'][:,2]=-.10*stand;sig['ThighR'][:,2]=.10*stand
   for (w0,w1,wg,_sc,wsp) in pa_.walks:       # the principles of animation: anticipation before a walk begins, follow-through (the upper body carries on, then settles) when it ends
    if w1-w0<.8:continue
    amp=min(1.3,.6+.4*wsp)
    ga=np.exp(-((tt-(w0-.12))/.16)**2);sig['Spine1'][:,0]-=.035*ga;sig['Head'][:,0]+=.02*ga
    dt_=np.maximum(tt-w1,0.);gf=np.where(tt>=w1,np.exp(-dt_/.42)*np.cos(2*np.pi*1.9*dt_),0.)
    sig['Spine1'][:,0]+=.06*amp*gf;sig['Spine2'][:,0]+=.04*amp*gf;sig['Neck'][:,0]+=.035*amp*gf;sig['Head'][:,0]+=.03*amp*gf
   rf=random.Random(sum(map(ord,i+SPEC['id']))+7);tf=rf.uniform(1.5,4.)       # a person never stands frozen: every few seconds a weight shift, a head tilt, a glance away or a small settle
   while tf<tt[-1]:
    sg=rf.choice((-1,1));kd=rf.choice(('shift','tilt','glance','settle','shift','tilt'));gb=np.exp(-((tt-tf)/.6)**2)*stand
    if kd=='shift':sig['Spine'][:,2]+=.05*sg*gb;sig['Spine1'][:,2]-=.03*sg*gb
    elif kd=='tilt':sig['Head'][:,2]+=.09*sg*gb;sig['Neck'][:,2]+=.04*sg*gb
    elif kd=='glance':sig['Head'][:,1]+=.26*sg*gb;sig['Neck'][:,1]+=.1*sg*gb
    else:sig['Spine2'][:,0]+=.04*gb;sig['Head'][:,0]-=.03*gb
    tf+=rf.uniform(3.5,7.)
  reach_=np.array([max(PLAN.hand_target(pa_,'R',t)[0],PLAN.hand_target(pa_,'L',t)[0]) for t in tt]) if any(pa_.hands[h] for h in ('R','L')) else np.zeros(len(fr))
  for b_ in ('Hips','Spine','Spine1','Spine2'):sig[b_]=sig[b_]*(1-.8*np.clip(reach_,0,1))[:,None]     # the trunk keeps still while an arm reaches for something
  if ad.action is None:       # one real keyframe makes the action, its slot and its channelbag
   pb0=rig.pose.bones[UAL['Hips'] if hum else 'mixamorig:Hips'];pb0.rotation_mode='QUATERNION';pb0.keyframe_insert('rotation_quaternion',frame=1)
  act=ad.action;cbag=anim_utils.action_ensure_channelbag_for_slot(act,ad.action_slot)
  for b,arr in sig.items():
   if hum:arr=arr*(0. if b=='Hips' else (1. if b.startswith('Thigh') else 1.1))      # the library's own idles already breathe: the layer adds the listening, speaking and turning on top
   path='pose.bones["%s"].rotation_quaternion'%(UAL[b] if hum else 'mixamorig:'+b);qs=np.array([tuple(Euler((x,y,z),'XYZ').to_quaternion()) for x,y,z in arr])
   for c in range(4):
    fc=next((f for f in cbag.fcurves if f.data_path==path and f.array_index==c),None) or cbag.fcurves.new(path,index=c)
    fc.keyframe_points.clear() if hasattr(fc.keyframe_points,'clear') else None
    n=len(fr);fc.keyframe_points.add(n);co=np.empty(n*2);co[0::2]=fr;co[1::2]=qs[:,c];fc.keyframe_points.foreach_set('co',co);fc.update()
  ad.action_blend_type='COMBINE';ad.action_influence=1.
body_layer()
# ---------------------------------------------------------------------------------------------------------- animals and dinosaurs: head and neck turn to what they attend to, breathing, tail sway (a wag when they celebrate), as a COMBINE layer over the few clips they have
def creature_layer():
 if not CRE:return
 from mathutils import Matrix
 fr=list(range(1,S.frames+1,2));dt=2./FPS
 def attend(i,t):
  """world xy the animal looks at (its planned gaze, else the speaker it is near, else straight ahead) and whether it is looking at all"""
  g=PLAN.gaze(i,t);x,y,h=PLAN.pos(i,t)
  if g is None:
   cand=[(math.hypot(*(np.array(PLAN.pos(j,t)[:2])-(x,y))),j) for j in PLAN.actors if j!=i and PLAN.line_at(t) is not None and PLAN.line_at(t)['speaker']==j]
   if cand:return PLAN.pos(min(cand)[1],t)[:2]
   return None
  if g[0]=='char':return PLAN.pos(g[1],t)[:2]
  if g[0]=='prop':return PLAN.props[g[1]].at(t,PLAN)[:2]
  return g[1][:2]
 for i,ch in CRE.items():
  rig=ch['rig'];pbs=rig.pose.bones;a_=PLAN.actors[i];rb=random.Random(sum(map(ord,i+SPEC['id'])));ph=rb.uniform(0,6.28)
  chain=[n for n in ('Neck','Head') if n in pbs];tails=[n for n in pbs.keys() if n.startswith('Tail')];body=[n for n in ('Torso','Back') if n in pbs]
  rest={n:pbs[n].bone.matrix_local.to_3x3() for n in chain+tails+body}
  joy=[(t0,t1) for (t0,t1,nm,sc,opt) in a_.clips if nm in('cele','jump','hips','bow','laugh','kick')]
  yaw=vy=pit=vp=0.;sig={n:[] for n in chain+tails+body}
  for f in fr:
   t=(f-1)/FPS;x,y,h=PLAN.pos(i,t);tg=attend(i,t);moving=PLAN._walking(i,t)
   if tg is not None:ty=max(-1.1,min(1.1,pp.wrap(math.atan2(tg[1]-y,tg[0]-x)-h)));tp=.05
   else:ty=.22*math.sin(2*math.pi*.09*t+ph)+.1*math.sin(2*math.pi*.23*t+ph*2);tp=.04*math.sin(2*math.pi*.13*t+ph)     # no one to look at: an idle glance around
   k=.35 if moving else 1.
   yaw,vy=damped(yaw,vy,ty*k,5.,dt,math.radians(160));pit,vp=damped(pit,vp,tp,5.,dt,math.radians(90))
   happy=any(a0-.2<=t<=b0+.2 for a0,b0 in joy);wag=(.5 if happy else .16)*(.5 if moving else 1.)
   ws=2*math.pi*(2.6 if happy else .55)
   for n in chain:
    w=.6 if n=='Neck' else .4;R=Euler((pit*w,0,yaw*w),'XYZ').to_matrix();sig[n].append(rest[n].inverted()@R@rest[n])
   for j,n in enumerate(tails):
    R=Euler((0,0,wag*math.sin(ws*t-j*.7+ph)/(1+.3*j)),'XYZ').to_matrix();sig[n].append(rest[n].inverted()@R@rest[n])
   for n in body:
    R=Euler((.012*math.sin(2*math.pi*.33*t+ph),0,.01*math.sin(2*math.pi*.09*t+ph)),'XYZ').to_matrix();sig[n].append(rest[n].inverted()@R@rest[n])
  ad=rig.animation_data
  if not sig:continue
  first=next(iter(sig));pb0=pbs[first];pb0.rotation_mode='QUATERNION'
  for n in sig:pbs[n].rotation_mode='QUATERNION'
  ad.action=None;pb0.keyframe_insert('rotation_quaternion',frame=1)
  act=ad.action;cbag=anim_utils.action_ensure_channelbag_for_slot(act,ad.action_slot)
  for n,mats in sig.items():
   qs=np.array([tuple(m.to_quaternion()) for m in mats]);path='pose.bones["%s"].rotation_quaternion'%n
   for c in range(4):
    fc=next((q for q in cbag.fcurves if q.data_path==path and q.array_index==c),None) or cbag.fcurves.new(path,index=c)
    fc.keyframe_points.clear() if hasattr(fc.keyframe_points,'clear') else None
    m_=len(fr);fc.keyframe_points.add(m_);co=np.empty(m_*2);co[0::2]=fr;co[1::2]=qs[:,c];fc.keyframe_points.foreach_set('co',co);fc.update()
  ad.action_blend_type='COMBINE';ad.action_influence=1.
creature_layer()
# ---------------------------------------------------------------------------------------------------------- grounding: the in-place clips of falling, getting up, kneeling, crawling and sitting sink into or float over the floor, so the root is lifted per frame until the lowest point of the body rests on it
GROUNDED=('sit','fall','getup','kneel','lie','crawl','jump')
def ground_pass():
 report={}
 for i,ch in CH.items():
  a=PLAN.actors[i];win=[(c[0]-.3,c[1]+.3) for c in a.clips if c[2] in GROUNDED]
  if not win:continue
  body=max((o for o in ch['objs'] if o.type=='MESH' and o.name.startswith(('char1','Body'))),key=lambda o:len(o.data.vertices),default=None)
  if body is None:continue
  frames=sorted({f for (a0,b0) in win for f in range(S.F(max(0,a0)),S.F(min(S.seconds,b0))+1) if (f-1)%2==0});low={}
  for f in frames:
   S.settle(f);dg=bpy.context.evaluated_depsgraph_get();e=body.evaluated_get(dg);me=e.to_mesh();n=len(me.vertices);co=np.empty(n*3);me.vertices.foreach_get('co',co);co=co.reshape(n,3);M=np.array(e.matrix_world)
   low[f]=float((co@M[2,:3]+M[2,3]).min());e.to_mesh_clear()
  lift=kit.ground_lift(low,0.,margin=.005,limit=.8,window=1);r=ch['root']
  for f,z in lift.items():
   k=min(len(a.X)-1,f-1);r.location=(a.X[k],a.Y[k],z);r.keyframe_insert('location',frame=f)
  report[i]=max(lift.values()) if lift else 0.
 return report
GROUND=ground_pass()
# ---------------------------------------------------------------------------------------------------------- cameras
CUTS=pc.direct(PLAN,seed=sum(map(ord,SPEC['id'])))
def pos_(kind,t,u):return pc.frame(PLAN,kind,t)
S.cameras([(c['name'],c['t0'],c['t1'],c) for c in CUTS],pos_,('Prop',),cand=[(0,0,.6),(0,.8,0),(0,-.8,0),(.8,0,0),(-.8,0,0),(0,0,1.4),(0,0,2.5),(1.6,0,0),(-1.6,0,0),(0,1.6,0),(0,-1.6,0)],shake=.01,fstop=2.8)
# a camera that view-clearing pushed far up goes back down: no cut is allowed to become a bird's-eye view
CAP={'wide':7.,'group':7.,'follow_high':5.}
for k,cam in enumerate(S.scene.timeline_markers):
 pass
def clamp_cameras():
 marks=sorted((m for m in S.scene.timeline_markers if m.camera),key=lambda m:m.frame)
 for k,m in enumerate(marks):
  cam=m.camera;cap=CAP.get(CUTS[k]['kind'],3.4) if k<len(CUTS) else 7.;ad=cam.animation_data
  if not ad or not ad.action:continue
  cb=anim_utils.action_ensure_channelbag_for_slot(ad.action,ad.action_slot)
  for fc in cb.fcurves:
   if fc.data_path=='location' and fc.array_index==2:
    for kp in fc.keyframe_points:
     if kp.co[1]>cap:kp.co[1]=cap;kp.handle_left[1]=cap;kp.handle_right[1]=cap
    fc.update()
clamp_cameras()
# ---------------------------------------------------------------------------------------------------------- audits (Blender side)
def lowest_feet(ch):
 rig=ch['rig'];w=lambda n:rig.matrix_world@rig.pose.bones[sb.B(ch,n)].head;return w('lfoot'),w('rfoot')
worst_sp=0.;worst_li=0.
for L in PLAN.lines:
 t=L['t0']+(L['t1']-L['t0'])*.6;f=S.F(t);S.settle(f)
 for name,ch in CH.items():
  a=PLAN.actors[name]
  if L['to']==L['speaker']:continue
  if name!=L['speaker'] and (PLAN._walking(name,t) or name!=L['to']):continue
  if name==L['speaker'] and PLAN._walking(name,t):continue
  tgt_id=L['to'] if name==L['speaker'] else L['speaker']
  if tgt_id not in CH:continue
  v=(S.head_pos(CH[tgt_id])-S.head_pos(ch)).normalized();ang=math.degrees(math.acos(max(-1,min(1,S.face_dir(ch).dot(v)))))
  if name==L['speaker']:worst_sp=max(worst_sp,ang)
  else:worst_li=max(worst_li,ang)
  if ang>30:print('EYE line %d %s -> %s at %.1fs: %.0f deg'%(L['k'],name,tgt_id,t,ang))
if worst_sp>34:issues.append('AUDIT eye line: a speaker looks %.0f degrees off the addressee (limit 34)'%worst_sp)
if worst_li>40:issues.append('AUDIT eye line: the addressed listener looks %.0f degrees off the speaker (limit 40)'%worst_li)
for L,x,syl,real in VOICES:
 if LIPKEYS[L['k']]<len(L['syl'])*.9:issues.append('AUDIT lip sync: line %d has %d mouth shapes for %d syllables'%(L['k'],LIPKEYS[L['k']],len(L['syl'])))
slip=0.;nslip=0
for i,ch in CH.items():
 a=PLAN.actors[i]
 for (t0,t1,g,sc,speed) in a.walks:
  if t1-t0<1.6 or g=='run' or (ch.get('human2') and g=='brisk'):continue     # a jog has a flight phase: no planted foot to measure
  fs=list(range(S.F(t0+.5),S.F(t1-.5),3))[:24];prev=None;vs=[]
  for f in fs:
   S.settle(f);L_,R_=lowest_feet(ch);low=L_ if L_.z<R_.z else R_
   if prev is not None and prev[1] is (L_ if low is L_ else R_) and False:pass
   cur=(Vector((low.x,low.y,0)),'L' if low is L_ else 'R')
   if prev and prev[1]==cur[1] and low.z<(.14*ch['k'] if ch.get('human2') else .12*a.size+.06):vs.append((cur[0]-prev[0]).length*FPS/3.)
   prev=cur
  if vs:slip+=sum(vs)/len(vs);nslip+=1
mean_slip=slip/max(1,nslip)
if mean_slip>.35:issues.append('AUDIT foot slip: planted feet slide at %.2f m/s on average while walking (limit 0.35)'%mean_slip)
reach_worst=0.;reach_n=0;reach_info=None
for i,(IK,TG) in IKS.items():
 a=PLAN.actors[i];ch=CH[i]
 for hand,lb,bone in (('R','RH','rhand'),('L','LH','lhand')):
  for f in range(1,S.frames+1,6):
   t=(f-1)/FPS;infl,pos=PLAN.hand_target(a,hand,t)
   if pos is None or infl<.98:continue
   S.settle(f);hp=ch['rig'].matrix_world@ch['rig'].pose.bones[sb.B(ch,bone)].head;e=(hp-Vector(pos)).length;reach_n+=1
   if e>reach_worst:reach_worst=e;reach_info=(i,hand,t,tuple(round(v,2) for v in pos),tuple(round(v,2) for v in hp))
if reach_worst>.23:print('REACH worst',reach_info)
if reach_worst>.23:issues.append('AUDIT reach: a hand ends %.2f m from its target (limit 0.23; the arm cannot reach, move the prop or the actor)'%reach_worst)
# cartoon signs over heads (the planned 'icon' beats): text solids that pop in, follow the head and always face the active camera
def make_icons():
 import bpy
 ev=[e for e in PLAN.events if e['kind']=='icon']
 if not ev:return
 marks=sorted((m for m in S.scene.timeline_markers if m.camera),key=lambda m:m.frame)
 for n,e in enumerate(ev):
  txt,col=pp.ICONS[e['what']];cu=bpy.data.curves.new('Icon%d'%n,'FONT');cu.body=txt;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=.5;cu.extrude=.04
  o=bpy.data.objects.new('Icon%d'%n,cu);S.link(o);m=bpy.data.materials.new('Icon%d'%n);m.diffuse_color=(*col,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
  if bs:bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=2.5
  o.data.materials.append(m);sz=PLAN.actors[e['who']].size;f0,f1=S.F(e['t0']),S.F(e['t1'])
  for f in range(f0,f1+1,2):
   t=(f-1)/FPS;hx,hy,hz=PLAN.head_pos(e['who'],t);u=min(1.,(f-f0)/6.,(f1-f)/6.+.05);pop=max(.01,u*(1.15 if u<1. else 1.))
   o.location=(hx,hy,hz+.62*max(.5,sz)+.05*math.sin((f-f0)*.5));o.scale=(pop*max(.6,sz),)*3
   cam=next((m_.camera for m_ in reversed(marks) if m_.frame<=f),marks[0].camera if marks else None)
   if cam is not None:
    S.scene.frame_set(f);cp=cam.matrix_world.translation;o.rotation_euler=(PI/2,0,math.atan2(cp.y-hy,cp.x-hx)+PI/2)
   for pth in ('location','scale','rotation_euler'):o.keyframe_insert(pth,frame=f)
make_icons()
# every dialogue cut shows its speaker: head inside the frame at the middle of the cut
from bpy_extras.object_utils import world_to_camera_view
sc=S.scene;marks=sorted(sc.timeline_markers,key=lambda m:m.frame);miss=0;chk=0
for k,m in enumerate(marks):
 c=CUTS[k] if k<len(CUTS) else None
 if not c or c['kind'] not in ('ots','two','medium','track','insert') or not c.get('subject'):continue
 f=int((m.frame+(marks[k+1].frame if k+1<len(marks) else sc.frame_end))/2);S.settle(f);sc.camera=m.camera
 subs=[c['subject']] if c['kind'] not in ('track',) else (c.get('group') or [c['subject']]);ok=False;chk+=1
 for subj in subs:
  pt=(S.head_pos(CH[subj]) if subj in CH else Vector(PLAN.head_pos(subj,(f-1)/FPS)))+Vector((0,0,.28*PLAN.actors[subj].size))
  if c['kind']=='insert':pt=Vector(PLAN.props[c['prop']].at((f-1)/FPS,PLAN))
  co=world_to_camera_view(sc,m.camera,pt)
  if 0.03<co.x<.97 and 0.03<co.y<.97 and co.z>0:ok=True;break
 if not ok:miss+=1;issues.append('AUDIT framing: %s cut "%s" at %.1f s has %s outside the frame (%.2f,%.2f)'%(c['kind'],m.name,(f-1)/FPS,'/'.join(subs) if c['kind']!='insert' else c['prop'],co.x,co.y))
sc.camera=marks[0].camera;sc.sync_mode='AUDIO_SYNC'
nl=len(PLAN.lines)
print('PERF %s: %.0f s, %d characters, %d lines, %d cuts, %d footsteps, eye line worst: speaker %.0f listener %.0f, foot slip %.2f m/s, reach worst %.2f m (%d samples), framing misses %d/%d'%(SPEC['id'],PLAN.seconds,len(CH),nl,len(CUTS),len(PLAN.footsteps()),worst_sp,worst_li,mean_slip,reach_worst,reach_n,miss,chk))
# ---------------------------------------------------------------------------------------------------------- sound
def snd(A):
 rng=A.rng
 N=A.N;SR=A.SR;vsum=np.zeros(N)
 for name in CH:
  v=A.buf(1)
  for L,x,syl,real in VOICES:
   if L['speaker']==name:A.at(v,L['t0']+.2,x,1.)
  if np.abs(v).max()>0:A.track('voice %s'%name,v,1.0);vsum+=np.abs(v[:N])
 duck=pa.duck_mask(vsum,SR,.6);duck_l=pa.duck_mask(vsum,SR,.6)    # music and ambience make room for every line
 amb=pa.ambience(SPEC.get('ambience','wind'),N,SR,rng);A.track('ambience',amb*duck_l,{'fire':.1,'sea':.09,'rain':.1,'crowd':.07,'market':.07}.get(SPEC.get('ambience'),.032))   # a bed under everything, never the loudest thing
 mus=None
 if SPEC.get('theme'):mus=ps.render(PLAN,SPEC['theme'],SPEC.get('music','calm'),SPEC.get('location',{}).get('preset'),TIME,SPEC['id'],SPEC.get('music_cues'),sr=SR,arc=SPEC.get('arc'))
 if mus is None:mus=pa.music(SPEC.get('music','calm'),N,SR,sum(map(ord,SPEC['id'])))
 elif len(mus)<N:mus=np.pad(mus,(0,N-len(mus)))
 if np.abs(mus).max()>0:A.track('music',mus*duck,.34)
 ev=pa.footstep_events(PLAN.footsteps(),SR,rng,'stone' if LOC.get('floor')=='stone' else 'dirt')
 if ev:A.track('steps',pa.mix_events(N,SR,ev)*duck_l,.1)   # footsteps sit far below the voices

 # foley: cloth on every big gesture and turn, props taken, put and handed over, pointing, creature footfalls, birds by day and crickets by night
 fo=[];CLOTH=('cele','wave','bow','shrug','startle','jump','hit','punch','kick','dodge','block','getup','fall','cut','hips','laugh','nod')
 for e in PLAN.events:
  who=PLAN.actors[e['who']] if e.get('who') in PLAN.actors else None
  if who is not None and who.look.get('creature'):continue
  if e['kind']=='act' and e.get('clip') in CLOTH:fo.append((e['t0']+.12,pa.sfx('cloth',SR,rng),.5))
  elif e['kind']=='point':fo.append((e['t0']+.1,pa.sfx('swish',SR,rng),.45))
  elif e['kind'] in('take','put','give'):
   pk=PLAN.props[e['prop']].kind if e.get('prop') in PLAN.props else '';nm='rustle' if pk in('letter','scroll','map','book') else ('clink' if pk in('cup','key','bell','gem','jar','lantern') else ('pop' if pk in('apple','egg','pie') else 'thud'))
   fo.append((e.get('t_grasp',e['t0']),pa.sfx(nm,SR,rng),.55 if nm!='thud' else .3));fo.append((e['t0']+.1,pa.sfx('cloth',SR,rng),.35))
  elif e['kind'] in('sit','stand'):fo.append((e['t0']+.2,pa.sfx('cloth',SR,rng),.5))
 for (i_,t0_,t1_,iv,hh) in CR_STEPS:      # animals: a footfall every quarter cycle, a very large body with a very large thud
  tt_=t0_+.1;big=hh>2.
  while tt_<t1_:fo.append((tt_,pa.sfx('bigstep' if big else 'step',SR,rng),.9 if big else .5*min(1.,hh+.2)));tt_+=max(.12,iv)
 if fo:A.track('foley',pa.mix_events(N,SR,fo)*duck_l,.28)
 outdoor=SPEC.get('location',{}).get('preset') not in('room','hall','workshop','cave')
 if outdoor and SPEC.get('ambience') not in('rain','sea','fire'):
  nat=[];tt_=rng.uniform(.5,2.5)
  while tt_<S.seconds-.5:
   nat.append((tt_,pa.sfx('chirp' if TIME in('day','dawn','dusk') else 'cricket',SR,rng),rng.uniform(.4,1.)));tt_+=rng.uniform(1.8,5.5) if TIME in('day','dawn','dusk') else rng.uniform(.8,2.4)
  if nat:A.track('nature',pa.mix_events(N,SR,nat)*duck_l,.07)
 ev=[(t,pa.sfx(nm,SR,rng),g) for (t,nm,who,g) in PLAN.sfx]
 if ev:A.track('effects',pa.mix_events(N,SR,ev),.6)
S.audio(snd)
os.makedirs(os.path.dirname(S.out),exist_ok=True)
json.dump(dict(id=SPEC['id'],title=SPEC.get('title',''),seconds=PLAN.seconds,cuts=[dict(name=c['name'],t0=c['t0'],t1=c['t1'],kind=c['kind'],subject=c.get('subject')) for c in CUTS],lines=[dict(k=L['k'],speaker=L['speaker'],to=L['to'],mood=L['mood'],text=L['text'],t0=L['t0'],t1=L['t1']) for L in PLAN.lines],audit=issues,
 cast=list(CH),stats=dict(ground_lift=max(GROUND.values(),default=0.),foot_slip=mean_slip,reach=reach_worst,eye_speaker=worst_sp,eye_listener=worst_li,framing_misses=miss,framing_checked=chk)),open(S.out+'.plan.json','w',encoding='utf-8'),indent=1)
for scr in bpy.data.screens:      # the saved window opens in Solid with textures, through the active camera
 for ar in scr.areas:
  if ar.type=='VIEW_3D':
   for sp in ar.spaces:
    if sp.type=='VIEW_3D':
     try:sp.shading.type='SOLID';sp.shading.light='STUDIO';sp.shading.color_type='TEXTURE';sp.shading.show_cavity=False;sp.overlay.show_overlays=False;sp.region_3d.view_perspective='CAMERA'
     except Exception as _e:print('viewport:',_e)
# a focus light: a soft spot above the action, so the scene has a bright pool with darker edges
try:
 import mathutils
 _pts=[PLAN.pos(i,PLAN.seconds*.5)[:2] for i in PLAN.actors];_cx=sum(p[0] for p in _pts)/len(_pts);_cy=sum(p[1] for p in _pts)/len(_pts)
 _sp=bpy.data.lights.new('FocusSpot','SPOT');_sp.energy={'night':1200,'dusk':600,'dawn':450,'day':160,'overcast':350}.get(TIME,500);_sp.spot_size=math.radians(75);_sp.spot_blend=.9;_sp.color=(1.,.88,.7);_sp.shadow_soft_size=1.5
 _so=bpy.data.objects.new('FocusSpot',_sp);_so.location=(_cx+2.5,_cy-5.5,8.5);S.link(_so)
 _tg=bpy.data.objects.new('FocusTarget',None);_tg.location=(_cx,_cy,1.0);S.link(_tg);_tc=_so.constraints.new('TRACK_TO');_tc.target=_tg;_tc.track_axis='TRACK_NEGATIVE_Z';_tc.up_axis='UP_Y'
except Exception as _e:print('focus light skipped',_e)
# atmosphere: dust, leaves, fireflies, rain or snow, chosen from the time of day, the ambience and the place (or the scene's own 'fx' list)
try:
 import perf_fx as fx
 _pts=[PLAN.pos(i,PLAN.seconds*.5)[:2] for i in PLAN.actors];_kinds=fx.choose(TIME,SPEC.get('ambience'),SPEC.get('location',{}).get('preset'),float(SPEC.get('fog',0.)),SPEC.get('fx'))
 if _kinds:print('FX',_kinds,fx.build(S,_kinds,(sum(p[0] for p in _pts)/len(_pts),sum(p[1] for p in _pts)/len(_pts)),S.seconds,seed=sum(map(ord,SPEC['id']))))
except Exception as _e:print('fx skipped',_e)
S.sky_hook=lambda sc:pl.sky(sc,TIME,float(SPEC.get('fog',0.)))
S.finish(issues,[ALL[i]['root'] for i in ALL],color_type='TEXTURE',world=pl.normalise(SPEC.get('location',dict(preset='meadow'))).get('world') or scene_params.preset(TIME if TIME in scene_params.TIME_OF_DAY else 'day')['world'])
if os.environ.get('PERF_DEBUG'):
 for nm in CH:
  S.settle(S.F(float(os.environ['PERF_DEBUG'])));print('DBG',nm,'head',tuple(round(v,2) for v in S.head_pos(CH[nm])),'face',tuple(round(v,2) for v in S.face_dir(CH[nm])),'root',tuple(round(v,2) for v in CH[nm]['root'].matrix_world.translation),'gz',tuple(round(v,2) for v in GZ[nm].matrix_world.translation),'H',round(math.degrees(PLAN.pos(nm,float(os.environ['PERF_DEBUG']))[2]),0))
