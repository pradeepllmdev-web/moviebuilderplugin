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
CH={}
for i,a in PLAN.actors.items():
 CH[i]=cb.build(S,a.look,i)
EXTRAS={}
for e in PLAN.extras:
 ch=cb.build(S,e['look'],e['id']);EXTRAS[e['id']]=ch;r=ch['root'];r.location=(e['x'],e['y'],0.);r.rotation_euler=(0,0,e['h']+PI/2)
def keyroot(i):
 a=PLAN.actors[i];r=CH[i]['root'];prev=None
 for f in S.keys():
  k=min(len(a.X)-1,f-1);r.location=(a.X[k],a.Y[k],0.);h=a.H[k]+PI/2
  if prev is not None:h=prev+pp.wrap(h-prev)
  prev=h;r.rotation_euler=(0,0,h);r.keyframe_insert('location',frame=f);r.keyframe_insert('rotation_euler',frame=f)
for i in CH:keyroot(i)
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
for i,ch in CH.items():
 segs=[];cl=PLAN.actors[i].clips
 for c in cl:
  if segs and c[1]-c[0]<.35 and not c[4]:segs[-1]=segs[-1][:1]+(c[1],)+segs[-1][2:];continue
  segs.append(c)
 for k,(t0,t1,name,sc,opt) in enumerate(segs):place(ch,name,t0,t1,sc,opt,k==0)
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
GZ={};FACE0={};SAC={i:Vector((0,0,0)) for i in CH};rnd_s={i:random.Random(sum(map(ord,SPEC['id']+i))) for i in CH}
for i,ch in CH.items():
 a=PLAN.actors[i];h0=a.H[0];FACE0[i]=(math.cos(h0),math.sin(h0),0);GZ[i]=S.gaze(ch,FACE0[i])
 cur=None
 for f in S.keys():
  t=(f-1)/FPS;tg=face_xyz(i,t)
  if (f-1)//2%5==0:SAC[i]=Vector((rnd_s[i].uniform(-.22,.22),rnd_s[i].uniform(-.22,.22),rnd_s[i].uniform(-.12,.12)))   # a small glance every ~0.4 s
  tg=tg+SAC[i];cur=tg if cur is None else cur+(tg-cur)*.28
  GZ[i].location=cur;GZ[i].keyframe_insert('location',frame=f)
for e in PLAN.extras:
 ch=EXTRAS[e['id']];fx=(math.cos(e['h']),math.sin(e['h']),0);g=S.gaze(ch,fx);g.location=(e['focus'][0],e['focus'][1],1.3*e['look']['scale'][2])
# ---------------------------------------------------------------------------------------------------------- lip sync and expression
def meshes_with(ch,key):return [o.data.shape_keys for o in ch['objs'] if o.type=='MESH' and o.data.shape_keys and key in o.data.shape_keys.key_blocks]
for ch in CH.values():
 for o in ch['objs']:
  if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data is None:o.data.shape_keys.animation_data_create()
def key(ch,name,pts):
 for kb in meshes_with(ch,name):
  b=kb.key_blocks[name]
  for fr,v in pts:b.value=v;b.keyframe_insert('value',frame=fr)
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
 for (t0,t1,kind) in a.emotes:
  for nm,val in EMOTE[kind].items():key(CH[i],nm,[(S.F(t0),0),(S.F(t0+.4),val),(S.F(t1-.3),val),(S.F(t1),0)])
# ---------------------------------------------------------------------------------------------------------- props
SHAPE={'cyl':('cup','jar','basket','barrel_small','scroll','tool','bell'),'sphere':('sack','apple','egg','gem','boulder')}
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
  ld=bpy.data.lights.new('PropLight_'+pid,'POINT');ld.energy=60 if TIME in ('night','dusk','dawn') else 15;ld.color=(1,.8,.5);lo=bpy.data.objects.new('PropLight_'+pid,ld);lo.parent=root;S.link(lo)
 for f in S.keys():
  t=(f-1)/FPS;pos=p.at(t,PLAN);root.location=pos
  seg=None
  root.keyframe_insert('location',frame=f)
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
 for i,ch in CH.items():
  rig=ch['rig'];sig=pbody.signals(PLAN,i);ad=rig.animation_data;pa_=PLAN.actors[i]
  tt=(np.array(fr)-1)/FPS;reach_=np.array([max(PLAN.hand_target(pa_,'R',t)[0],PLAN.hand_target(pa_,'L',t)[0]) for t in tt]) if any(pa_.hands[h] for h in ('R','L')) else np.zeros(len(fr))
  for b_ in ('Hips','Spine','Spine1','Spine2'):sig[b_]=sig[b_]*(1-.8*np.clip(reach_,0,1))[:,None]     # the trunk keeps still while an arm reaches for something
  if ad.action is None:       # one real keyframe makes the action, its slot and its channelbag
   pb0=rig.pose.bones['mixamorig:Hips'];pb0.keyframe_insert('rotation_quaternion',frame=1)
  act=ad.action;cbag=anim_utils.action_ensure_channelbag_for_slot(act,ad.action_slot)
  for b,arr in sig.items():
   path='pose.bones["mixamorig:%s"].rotation_quaternion'%b;qs=np.array([tuple(Euler((x,y,z),'XYZ').to_quaternion()) for x,y,z in arr])
   for c in range(4):
    fc=next((f for f in cbag.fcurves if f.data_path==path and f.array_index==c),None) or cbag.fcurves.new(path,index=c)
    fc.keyframe_points.clear() if hasattr(fc.keyframe_points,'clear') else None
    n=len(fr);fc.keyframe_points.add(n);co=np.empty(n*2);co[0::2]=fr;co[1::2]=qs[:,c];fc.keyframe_points.foreach_set('co',co);fc.update()
  ad.action_blend_type='COMBINE';ad.action_influence=1.
body_layer()
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
 rig=ch['rig'];w=lambda n:rig.matrix_world@rig.pose.bones['mixamorig:'+n].head;return w('LeftFoot'),w('RightFoot')
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
  if t1-t0<1.6 or g=='run':continue
  fs=list(range(S.F(t0+.5),S.F(t1-.5),3))[:24];prev=None;vs=[]
  for f in fs:
   S.settle(f);L_,R_=lowest_feet(ch);low=L_ if L_.z<R_.z else R_
   if prev is not None and prev[1] is (L_ if low is L_ else R_) and False:pass
   cur=(Vector((low.x,low.y,0)),'L' if low is L_ else 'R')
   if prev and prev[1]==cur[1] and low.z<.12*a.size+.06:vs.append((cur[0]-prev[0]).length*FPS/3.)
   prev=cur
  if vs:slip+=sum(vs)/len(vs);nslip+=1
mean_slip=slip/max(1,nslip)
if mean_slip>.35:issues.append('AUDIT foot slip: planted feet slide at %.2f m/s on average while walking (limit 0.35)'%mean_slip)
reach_worst=0.;reach_n=0;reach_info=None
for i,(IK,TG) in IKS.items():
 a=PLAN.actors[i];ch=CH[i]
 for hand,lb,bone in (('R','RH','RightHand'),('L','LH','LeftHand')):
  for f in range(1,S.frames+1,6):
   t=(f-1)/FPS;infl,pos=PLAN.hand_target(a,hand,t)
   if pos is None or infl<.98:continue
   S.settle(f);hp=ch['rig'].matrix_world@ch['rig'].pose.bones['mixamorig:'+bone].head;e=(hp-Vector(pos)).length;reach_n+=1
   if e>reach_worst:reach_worst=e;reach_info=(i,hand,t,tuple(round(v,2) for v in pos),tuple(round(v,2) for v in hp))
if reach_worst>.22:print('REACH worst',reach_info)
if reach_worst>.22:issues.append('AUDIT reach: a hand ends %.2f m from its target (limit 0.22; the arm cannot reach, move the prop or the actor)'%reach_worst)
# every dialogue cut shows its speaker: head inside the frame at the middle of the cut
from bpy_extras.object_utils import world_to_camera_view
sc=S.scene;marks=sorted(sc.timeline_markers,key=lambda m:m.frame);miss=0;chk=0
for k,m in enumerate(marks):
 c=CUTS[k] if k<len(CUTS) else None
 if not c or c['kind'] not in ('ots','two','medium','track','insert') or not c.get('subject'):continue
 f=int((m.frame+(marks[k+1].frame if k+1<len(marks) else sc.frame_end))/2);S.settle(f);sc.camera=m.camera
 subs=[c['subject']] if c['kind'] not in ('track',) else (c.get('group') or [c['subject']]);ok=False;chk+=1
 for subj in subs:
  pt=S.head_pos(CH[subj])+Vector((0,0,.28*PLAN.actors[subj].size))
  if c['kind']=='insert':pt=Vector(PLAN.props[c['prop']].at((f-1)/FPS,PLAN))
  co=world_to_camera_view(sc,m.camera,pt)
  if 0.03<co.x<.97 and 0.03<co.y<.97 and co.z>0:ok=True;break
 if not ok:miss+=1;issues.append('AUDIT framing: %s cut "%s" at %.1f s has %s outside the frame (%.2f,%.2f)'%(c['kind'],m.name,(f-1)/FPS,'/'.join(subs) if c['kind']!='insert' else c['prop'],co.x,co.y))
sc.camera=marks[0].camera
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
  if np.abs(v).max()>0:A.track('voice %s'%name,v,.9);vsum+=np.abs(v[:N])
 duck=pa.duck_mask(vsum,SR,.7);duck_l=pa.duck_mask(vsum,SR,.45)    # music and ambience make room for every line
 amb=pa.ambience(SPEC.get('ambience','wind'),N,SR,rng);A.track('ambience',amb*duck_l,{'fire':.1,'sea':.09,'rain':.1,'crowd':.07,'market':.07}.get(SPEC.get('ambience'),.045))   # a bed under everything, never the loudest thing
 mus=None
 if SPEC.get('theme'):mus=ps.render(PLAN,SPEC['theme'],SPEC.get('music','calm'),SPEC.get('location',{}).get('preset'),TIME,SPEC['id'],SPEC.get('music_cues'),sr=SR,arc=SPEC.get('arc'))
 if mus is None:mus=pa.music(SPEC.get('music','calm'),N,SR,sum(map(ord,SPEC['id'])))
 elif len(mus)<N:mus=np.pad(mus,(0,N-len(mus)))
 if np.abs(mus).max()>0:A.track('music',mus*duck,.3)
 ev=pa.footstep_events(PLAN.footsteps(),SR,rng,'stone' if LOC.get('floor')=='stone' else 'dirt')
 if ev:A.track('steps',pa.mix_events(N,SR,ev)*duck_l,.1)   # footsteps sit far below the voices
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
S.finish(issues,[CH[i]['root'] for i in CH],color_type='TEXTURE',world=pl.normalise(SPEC.get('location',dict(preset='meadow'))).get('world') or scene_params.preset(TIME if TIME in scene_params.TIME_OF_DAY else 'day')['world'])
if os.environ.get('PERF_DEBUG'):
 for nm in CH:
  S.settle(S.F(float(os.environ['PERF_DEBUG'])));print('DBG',nm,'head',tuple(round(v,2) for v in S.head_pos(CH[nm])),'face',tuple(round(v,2) for v in S.face_dir(CH[nm])),'root',tuple(round(v,2) for v in CH[nm]['root'].matrix_world.translation),'gz',tuple(round(v,2) for v in GZ[nm].matrix_world.translation),'H',round(math.degrees(PLAN.pos(nm,float(os.environ['PERF_DEBUG']))[2]),0))
