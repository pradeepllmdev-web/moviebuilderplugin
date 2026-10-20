"""Blender script: 'The Conversation' - two to four characters talk in a ring around a campfire or a council table, from a script of lines (about 10-60 s, set by the lines).

blender -b --disable-autoexec --python talk_scene.py -- <ship_assets_dir> <out.blend>      (the script and setting come from SCENE_PARAMS: dialogue [{speaker, mood, text}], setting campfire|hall)

Technique: DIALOGUE FROM A SCRIPT. Lines are parsed from the story (dialogue.py), timed from their syllables or from real recordings (VOICE_DIR/line_<k>.wav), and voiced; the mouth (JawOpen/Round/Wide on the face and on the teeth, tongue and mouth
interior) is keyed from the syllable times of the actual voice, the mood of each line keys its expression (and a listener's reaction), blinks run on every character, the speaker plays a talk/argue/shrug/laugh clip and the addressee
a nod/think/laugh reaction, every head follows a damped-track gaze that moves to the speaker (and the speaker to the addressee) with a 0.35 s blend, and the camera coverage (establishing wide, over-the-shoulder on the speaker,
single on the listener's reaction, a two-shot now and then, wide close) is generated from the script with depth of field and a light handheld sway. Audit: no overlapping lines, every speaker seated in the ring, eye lines (speaker on
addressee, listeners on speaker) within tolerance at the middle of every line, lip-sync keys for every syllable, voice length against the line, persistence, camera visibility. Clips: idle, talk, argue, shrug, laugh, nod, think."""
import bpy,math,sys,os,hashlib
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2,dialogue as dg
from mathutils import Vector
S=sb.Scene('talk');PI=math.pi;smooth=kit.smooth;prm=S.params
DEFAULT=[dict(speaker='Leo',mood='warm',text='We made it to the clearing at last.'),dict(speaker='Mara',mood='serious',text='The pass behind us is closed. There is no turning back.'),dict(speaker='Leo',mood='serious',text='Then we go forward together.'),dict(speaker='Tarn',mood='concern',text='Do you hear that? Something is moving in the trees.')]
LINES=prm['dialogue'] or DEFAULT;SETTING=prm['setting'] or 'campfire'
CAST=dg.cast(LINES)[:4];LINES=[l for l in LINES if l['speaker'] in CAST];DROPPED=len(prm['dialogue'] or DEFAULT)-len(LINES)
NC=len(CAST);REAL=dg.real_lengths(LINES);SCHED=dg.schedule(LINES,2.6,.5,REAL);T_END=SCHED[-1]['t1']+3.5;S.clock(T_END);seconds=S.seconds
if SETTING=='hall':S.load_env('council_hall');R=3.7;FIRE=Vector((0,0,.9))
else:S.load_env('campfire');R=2.7;FIRE=Vector((0,0,.5))
# ---------------------------------------------------------------------------------------------------------- the ring of characters
def tint_of(name):
 if name=='Leo':return S.params['hero_tint']
 h=int(hashlib.sha1(name.encode()).hexdigest()[:6],16);return (.55+.4*((h>>0)%100)/100.,.5+.4*((h>>8)%100)/100.,.5+.4*((h>>4)%100)/100.)
ANG=[math.radians(-90+(360.*i/NC)+(0 if NC>2 else 90)) for i in range(NC)];CH={};POS={}
for i,name in enumerate(CAST):
 ch=S.character(name,tint_of(name));a=ANG[i];p=Vector((math.cos(a)*R,math.sin(a)*R,0));POS[name]=p;ch['root'].location=p;ch['root'].rotation_euler=(0,0,math.atan2(-p.y,-p.x)+PI/2);sc=.93+.12*((int(hashlib.sha1(name.encode()).hexdigest()[:4],16)%100)/100.);ch['root'].scale=(sc,)*3;CH[name]=ch
 ch['root'].keyframe_insert('location',frame=1);ch['root'].keyframe_insert('rotation_euler',frame=1);ch['root'].keyframe_insert('scale',frame=1)
HEADZ=1.6
def head(name):return POS[name]*.0+Vector((POS[name].x,POS[name].y,HEADZ*CH[name]['root'].scale[0]))
# ---------------------------------------------------------------------------------------------------------- clips: speaker clip while talking, a reaction for the addressee
def addressee_of(L):
 k=L['k'];nxt=SCHED[k+1]['speaker'] if k+1<len(SCHED) else None
 if nxt and nxt!=L['speaker']:return nxt
 others=[c for c in CAST if c!=L['speaker']];return others[k%len(others)] if others else L['speaker']
for L in SCHED:L['to']=addressee_of(L)
for name,ch in CH.items():
 ev=[]
 for L in SCHED:
  if L['speaker']==name:ev.append((L['t0']-.25,L['t1']+.25,dg.SPEAK_CLIP[L['mood']],1))
 for L in SCHED:
  if L['to']==name and L['speaker']!=name and dg.LISTEN_CLIP[L['mood']]:
   a,b=L['t1']-.9,L['t1']+.5
   if not any(not (b<=e[0] or a>=e[1]) for e in ev):ev.append((a,b,dg.LISTEN_CLIP[L['mood']],0))
 ev.sort();segs=[];cur=0.
 for a,b,c,prio in ev:
  a=max(a,cur)
  if b-a<.4:continue
  if a>cur+.05:segs.append((cur,a,'idle',1.))
  segs.append((a,b,c,1.));cur=b
 if cur<S.seconds:segs.append((cur,S.seconds,'idle',1.))
 S.play(ch,segs)
# ---------------------------------------------------------------------------------------------------------- eye lines
GZ={name:S.gaze(CH[name],(-POS[name].x,-POS[name].y,0)) for name in CAST}
def line_at(t):
 for L in SCHED:
  if L['t0']-.1<=t<=L['t1']+.1:return L
 return None
def focus(name,t):
 L=line_at(t)
 if L is None:
  prev=[x for x in SCHED if x['t1']<t]
  if not prev:return FIRE+Vector((0,0,.6))
  L=prev[-1]
 if L['speaker']==name:return head(L['to'])
 return head(L['speaker'])
for f in S.keys():
 t=(f-1)/S.fps
 for name in CAST:
  cur=focus(name,t);chg=[x['t0'] for x in SCHED if x['t0']-.1<=t<x['t0']+.25];w=smooth((t-(chg[0]-.1))/.35) if chg else 1.;prevt=focus(name,max(0,t-.4)) if chg else cur
  GZ[name].location=prevt.lerp(cur,w);GZ[name].keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- lip sync and expression from the voice
def meshes_with(ch,key):return [kb for o in ch['objs'] if o.type=='MESH' and o.data.shape_keys and key in o.data.shape_keys.key_blocks for kb in [o.data.shape_keys]]
for ch in CH.values():
 for o in ch['objs']:
  if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data is None:o.data.shape_keys.animation_data_create()
def key(ch,name,pts):
 for kb in meshes_with(ch,name):
  b=kb.key_blocks[name]
  for fr,v in pts:b.value=v;b.keyframe_insert('value',frame=fr)
VOICES=[];LIPKEYS={}
for L in SCHED:
 x,syl,real=dg.voice_for(dict(L,speaker=L['speaker']));VOICES.append((L,x,syl,real));ch=CH[L['speaker']];n=0
 for (tc,d,v) in syl:
  tcg=L['t0']+.2+tc;op,ro,wi=dg.VOWEL_KEYS[v];a,b,c=S.F(tcg-d*.5),S.F(tcg),S.F(tcg+d*.45)
  key(ch,'JawOpen',[(a,0),(b,op*.75),(c,0)]);key(ch,'Round',[(a,0),(b,ro*.7),(c,0)]);key(ch,'Wide',[(a,0),(b,wi*.5),(c,0)]);n+=1
 LIPKEYS[L['k']]=n
 for nm,val in dg.MOOD_KEYS[L['mood']].items():key(ch,nm,[(S.F(L['t0']-.3),0),(S.F(L['t0']+.2),val),(S.F(L['t1']-.2),val),(S.F(L['t1']+.3),0)])
 tgt=CH[L['to']]
 for nm,val in (dg.MOOD_KEYS['warm'] if L['mood'] in ('warm','joy') else (dg.MOOD_KEYS['concern'] if L['mood'] in ('angry','sad') else {})).items():
  key(tgt,nm,[(S.F(L['t0']+.4),0),(S.F(L['t0']+1.0),val*.8),(S.F(L['t1']-.1),val*.8),(S.F(L['t1']+.4),0)])
# ---------------------------------------------------------------------------------------------------------- cameras: coverage generated from the script
cen=Vector((0,0,0));A0=sum(ANG[:2])/2
shots=[('the clearing' if SETTING=='campfire' else 'the hall',0,SCHED[0]['t0']-.2,'wide',None)]
for L in SCHED:
 k=L['k'];mid=L['t0']+(L['t1']-L['t0'])*.7
 shots.append(('%s speaks'%L['speaker'],L['t0']-.2 if k else SCHED[0]['t0']-.2,mid,'ots' if k%3!=2 else 'two',L))
 shots.append(('%s listens'%L['to'],mid,L['t1']+.25,'single',L))
shots.append(('end',SCHED[-1]['t1']+.25,S.seconds,'wide',None))
for i in range(len(shots)-1):shots[i]=(shots[i][0],shots[i][1],shots[i+1][1],shots[i][3],shots[i][4])
cuts=[(n,a,b,(kd,L)) for n,a,b,kd,L in shots if b-a>.35]
def pos_(kind,t,u):
 kd,L=kind
 if kd=='wide':
  phi=A0+PI/2;return Vector((math.cos(phi)*9,math.sin(phi)*9,3.4)),FIRE+Vector((0,0,.9)),26
 sp,to=L['speaker'],L['to'];hs,ht=head(sp),head(to);dire=(hs-ht).normalized();side=Vector((-dire.y,dire.x,0))
 if kd=='ots':return ht+dire*-.9+side*.45+Vector((0,0,.1)),hs,52
 if kd=='single':
  d2=(ht-hs).normalized();s2=Vector((-d2.y,d2.x,0));return ht+d2*-2.3*-1+s2*.5+Vector((0,0,.0)),ht,55
 mid=(hs+ht)/2;return mid+side*5.2+Vector((0,0,.4)),mid,34
S.cameras(cuts,pos_,(),cand=[(0,0,.6),(0,.8,0),(0,-.8,0),(.8,0,0),(-.8,0,0),(0,0,1.4)],shake=.012,fstop=2.8)
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
if DROPPED:issues.append('AUDIT cast: %d line(s) belong to a fifth speaker and were left out'%DROPPED)
for a,b in zip(SCHED,SCHED[1:]):
 if b['t0']<a['t1']:issues.append('AUDIT speech: lines %d and %d overlap'%(a['k'],b['k']))
for name in CAST:
 if (POS[name]-Vector((0,0,0))).length<1.0:issues.append('AUDIT ring: %s stands inside the fire'%name)
worst_sp=0.;worst_li=0.
for L in SCHED:
 f=S.F(L['t0']+(L['t1']-L['t0'])*.6);S.settle(f);sp=CH[L['speaker']];hs=S.head_pos(sp)
 for name in CAST:
  tgt=head(L['to']) if name==L['speaker'] else head(L['speaker']);v=(tgt-S.head_pos(CH[name])).normalized();ang=math.degrees(math.acos(max(-1,min(1,S.face_dir(CH[name]).dot(v)))))
  if name==L['speaker']:worst_sp=max(worst_sp,ang)
  else:worst_li=max(worst_li,ang)
if worst_sp>32:issues.append('AUDIT eye line: a speaker looks %.0f degrees off the addressee (limit 32)'%worst_sp)
if worst_li>38:issues.append('AUDIT eye line: a listener looks %.0f degrees off the speaker (limit 38)'%worst_li)
for L,x,syl,real in VOICES:
 if LIPKEYS[L['k']]<len(L['syl'])*.9:issues.append('AUDIT lip sync: line %d has %d mouth shapes for %d syllables'%(L['k'],LIPKEYS[L['k']],len(L['syl'])))
 if real is None and abs(len(x)/dg.SR-L['dur'])>.2:issues.append('AUDIT voice: line %d voice is %.2f s for a %.2f s slot'%(L['k'],len(x)/dg.SR,L['dur']))
print('TALK %d lines, %d speakers (%s), setting %s, %.1f s, eye line worst: speaker %.0f deg, listener %.0f deg, real recordings %d'%(len(SCHED),NC,', '.join(CAST),SETTING,S.seconds,worst_sp,worst_li,len(REAL)))
def snd(A):
 for name in CAST:
  v=A.buf(1)
  for L,x,syl,real in VOICES:
   if L['speaker']==name:A.at(v,L['t0']+.2,x,1.)
  A.track('voice %s'%name,v,.9)
 if SETTING=='campfire':
  fire=A.noise(A.N,50)*(.6+.4*np.sin(A.t*7.3));crack=np.zeros(A.N)
  for _ in range(int(A.S.seconds*3)):
   j=int(A.rng.uniform(0,A.N-400));crack[j:j+300]+=A.rng.standard_normal(300)*np.exp(-np.arange(300)/60.)*.4
  A.track('fire',fire*.5+crack,.3);A.track('night',A.noise(A.N,200)*.4,.15)
 else:A.track('hall',A.noise(A.N,150)*.5+np.sin(2*PI*60*A.t)*.1,.15)
 A.track('music',A.chords(((110,138.6,164.8),(98,123.5,146.8),(103.8,130.8,155.6),(116.5,146.8,174.6)),.16),.28)
S.audio(snd)
S.finish(issues,[CH[CAST[0]]['root']],world=(.03,.035,.06))
