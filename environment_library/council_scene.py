"""Blender script: 'The Council' - six lions argue and decide around a round table (about 65 s). The acting scene: dialogue, lip sync, eye lines, gestures, a scroll passed across the table, a gavel.

blender -b --disable-autoexec --python council_scene.py -- <ship_assets_dir> <out.blend> [seconds=0 (derived from the script)]

New in this scene: turn-taking (a script of lines with speaker, addressee and mood), LIP SYNC (the JawOpen/Round/Wide/Brow shape keys are keyed from the syllables of every line, and the voice audio is
synthesised from the same syllable times), EYE LINES (a damped-track constraint on every head follows a gaze target that moves to the speaker, the speaker looks at the addressee, with 0.35 s
transitions), GESTURES (both arms of each character are IK to wrist targets: resting on the table edge, open palm, pointing at the addressee; every target is clamped to the reach of the arm),
an object handoff (the scroll slides across the table from the elder to Leo, who then keeps a hand on it) and a gavel strike. Coverage is generated from the script (speaker, reaction, wide,
inserts) and cleared of scenery automatically. Audit: gaze angles, arm reach, no overlapping speech, camera visibility, persistence."""
import bpy,math,random,sys,os,wave,re
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit,scene_params,locations
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;rnd=random.Random(21);PI=math.pi
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color,emit=0.):
 if name in _m:return _m[name]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
 _m[name]=m;return m
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=None,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color))
 if parent:o.parent=parent
 return o
CTX=dict(link=link,mat=mat,prim=prim);C=locations.COUNCIL
locations.load('council_hall',CTX,'intact')
# ---------------------------------------------------------------------------------------------------------- the script: (speaker, addressee, mood, text)
NAMES=['Leo','Elder','Scout','Captain','Healer','Rival'];TINT=[None,(.62,.6,.62),(.9,.75,.5),(.55,.4,.35),(.75,.9,.75),(.38,.32,.3)];SCALE=[1.0,1.06,.92,1.12,.95,1.1];VOICE=[125.,92.,185.,105.,205.,82.]
LINES=[(1,0,'serious','The citadel gates are closing and the winter is coming'),(0,1,'serious','Then we cannot wait. We must move tonight'),(3,0,'angry','Tonight? Our soldiers are tired and the catapults are not ready'),
 (2,3,'warm','The walls are weakest near the western tower. I saw it myself'),(4,0,'concern','And the wounded? We cannot leave them behind'),(0,4,'warm','No one is left behind. We carry them with us'),
 (5,0,'angry','That is a fine speech, but speeches do not break walls'),(0,1,'serious','Then give me the map and I will show you how'),(1,0,'warm','Here. The old tunnels may still be open'),
 (2,0,'warm','The tunnel starts under the mill. I can guide you'),(3,5,'serious','Fine. Then we strike at dawn'),(5,0,'angry','I will hold the ridge, but if this fails the blame is yours'),
 (0,5,'serious','If this fails, I will be the first through the gate'),(1,3,'warm','Then it is decided. Let the gavel fall')]
def syllables(text):
 out_=[]
 for w in re.findall(r"[A-Za-z']+",text):
  groups=re.findall(r'[aeiouy]+',w.lower()) or ['a']
  for g in groups:out_.append(g[0] if g[0] in 'aeiou' else 'e')
 return out_
T=2.6;SCHED=[]
for k,(sp,to,mood,text) in enumerate(LINES):
 syl=syllables(text);dur=max(2.0,len(syl)*.2+.5);SCHED.append(dict(k=k,speaker=sp,to=to,mood=mood,text=text,t0=T,t1=T+dur,syl=syl));T+=dur+.45
seconds=T+3.5;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
PASS_K=8;GAVEL_K=13
# ---------------------------------------------------------------------------------------------------------- characters
def load_char(tag,scale=1.,tint=None):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new(tag+'Root',None);link(root);root.scale=(scale,)*3
 for o in new:
  if o.parent is None:o.parent=root
  if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
  if tint and o.type=='MESH':
   for i,slot in enumerate(o.material_slots):
    if slot.material:
     m=slot.material.copy();c=slot.material.diffuse_color;m.diffuse_color=(c[0]*tint[0],c[1]*tint[1],c[2]*tint[2],1);o.material_slots[i].material=m
 rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
 body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices))
 kb=body.data.shape_keys
 if kb:kb.animation_data_clear();kb.animation_data_create()
 return dict(root=root,rig=rig,body=body,keys=kb,scale=scale)
prm=scene_params.get()
CH=[load_char(NAMES[i],SCALE[i],prm['hero_tint'] if (i==0 and prm['hero_tint']) else TINT[i]) for i in range(6)]
with bpy.data.libraries.load(os.path.join(ASSETS,'leo_sit.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_sit']
SIT=dst.actions[0]
ANG=[math.radians(-90+i*60) for i in range(6)]
for i,c in enumerate(CH):
 a=ANG[i];c['root'].location=(math.cos(a)*C['seat_r'],math.sin(a)*C['seat_r'],0);c['root'].rotation_euler=(0,0,a+PI+PI/2)
 ad=c['rig'].animation_data;tr=ad.nla_tracks.new();st=tr.strips.new('sit',1-rnd.randint(0,50),SIT);st.action_slot=SIT.slots[0];st.action_frame_start=91;st.action_frame_end=145;st.repeat=(frames+120)/55.;st.extrapolation='HOLD'
scene.frame_set(1);bpy.context.view_layer.update()
def bw(i,name,tail=False):
 pb=CH[i]['rig'].pose.bones['mixamorig:'+name];return CH[i]['rig'].matrix_world@(pb.tail if tail else pb.head)
HEAD=[bw(i,'Head')+Vector((0,0,.12)) for i in range(6)];SHOULD={(i,s):bw(i,s+'Arm') for i in range(6) for s in ('Left','Right')}
# the head axis that points where the face looks
fwd0=-(Vector((math.cos(ANG[0]),math.sin(ANG[0]),0)));hm=(CH[0]['rig'].matrix_world@CH[0]['rig'].pose.bones['mixamorig:Head'].matrix).to_3x3()
AXES={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
FACE_AXIS=max(AXES,key=lambda k:AXES[k].normalized().dot(fwd0.normalized()));print('FACE_AXIS',FACE_AXIS)
# ---------------------------------------------------------------------------------------------------------- props
GOB=[]
for i in range(6):
 a=ANG[i];p=Vector((math.cos(a)*1.85,math.sin(a)*1.85,C['table_z']));r,_=locations.load_prop('goblet',CTX,p,0.);GOB.append(r)
sx=Vector((math.cos(ANG[1]),math.sin(ANG[1]),0));SCROLL0=sx*2.12+Vector((0,0,C['table_z']+.02));sroot,sp=locations.load_prop('scroll',CTX,SCROLL0,ANG[1]+PI/2);scroll=sp['scroll']
gv_a=ANG[1]+math.radians(14);GAV0=Vector((math.cos(gv_a)*2.0,math.sin(gv_a)*2.0,C['table_z']));groot,gp=locations.load_prop('gavel',CTX,GAV0,gv_a+PI/2);pivot=gp['pivot']
# ---------------------------------------------------------------------------------------------------------- IK arms
IK={};TG={}
for i,c in enumerate(CH):
 for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
  tg=bpy.data.objects.new('Wrist_%d_%s'%(i,limb),None);tg.empty_display_size=.05;link(tg);TG[(i,limb)]=tg
  pole=bpy.data.objects.new('Pole_%d_%s'%(i,limb),None);link(pole);pole.parent=c['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,.8)
  k_=c['rig'].pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;IK[(i,limb)]=k_
def side(i,limb):
 a=ANG[i];l=Vector((math.sin(a),-math.cos(a),0));return l if limb=='LH' else -l
def rest_pos(i,limb):
 a=ANG[i];u=Vector((math.cos(a),math.sin(a),0));return u*(C['table_r']-.2)+side(i,limb)*.24+Vector((0,0,C['table_z']+.05))
def clamp(i,limb,p):
 sh=SHOULD[(i,'Left' if limb=='LH' else 'Right')];d=p-sh
 return sh+d.normalized()*min(d.length,.455)
def line_at(t):
 for L in SCHED:
  if L['t0']<=t<L['t1']:return L
 return None
def gesture(i,limb,t):
 """wrist target of a speaker: two gesture pulses per line (open palm, then pointing at the addressee)."""
 L=line_at(t)
 if L is None or L['speaker']!=i or limb!='RH':return rest_pos(i,limb),0.
 u=(t-L['t0'])/(L['t1']-L['t0']);rp=rest_pos(i,limb);pulses=((.15,.4,'open'),(.55,.85,'point'))
 for a,b,kind in pulses:
  if a<=u<=b:
   w=math.sin(PI*(u-a)/(b-a))
   if kind=='open':return rp+Vector((0,0,.24))*w+(-Vector((math.cos(ANG[i]),math.sin(ANG[i]),0)))*.05*w,1.
   d=(HEAD[L['to']]-HEAD[i]);d.z=0;d.normalize();return rp+d*.2*w+Vector((0,0,.14))*w,1.
 return rp,0.
SC_T=SCHED[PASS_K]['t0']+1.0;SC_T1=SC_T+1.5;A1,A0=ANG[1],ANG[0]
def scroll_pos(t):
 if t<SC_T:return SCROLL0
 u=smooth((t-SC_T)/(SC_T1-SC_T));a=A1+(A0-A1)*u;return Vector((math.cos(a)*2.12,math.sin(a)*2.12,C['table_z']+.02))
T_GAVEL=SCHED[GAVEL_K]['t1']-.5
def wrist(i,limb,t):
 """(target position, influence) of a wrist at time t: gestures, scroll handoff, gavel, otherwise resting on the table."""
 pos,infl=gesture(i,limb,t);pos=Vector(pos)
 if i==1 and limb=='RH' and SC_T-.5<=t<=SC_T1+.3:
  w=smooth((t-(SC_T-.5))/.4)*(1-smooth((t-(SC_T1-.2))/.5));pos=rest_pos(1,'RH').lerp(scroll_pos(t)+Vector((0,0,.06)),w);infl=1.
 if i==0 and limb=='LH' and t>=SC_T1-.2:
  w=smooth((t-(SC_T1-.2))/.5);pos=rest_pos(0,'LH').lerp(scroll_pos(SC_T1)+Vector((0,0,.06)),w);infl=max(infl,w)
 if i==1 and limb=='LH' and T_GAVEL-1.4<=t<=T_GAVEL+.9:   # the gavel
  w=smooth((t-(T_GAVEL-1.4))/.5)*(1-smooth((t-(T_GAVEL+.4))/.5));up=.3*math.sin(PI*min(1,max(0,(t-(T_GAVEL-.9))/.9)))*(1 if t<T_GAVEL else 0)
  pos=rest_pos(1,'LH').lerp(GAV0+Vector((0,0,.12+up)),w);infl=1.
 return clamp(i,limb,pos),infl
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for i in range(6):
  for limb in ('LH','RH'):
   p,_=wrist(i,limb,t);TG[(i,limb)].location=p;TG[(i,limb)].keyframe_insert('location',frame=f);IK[(i,limb)].influence=1.;IK[(i,limb)].keyframe_insert('influence',frame=f)
# the scroll follows the table slide, then Leo's hand; the gavel swings
for f in range(1,frames+1,2):
 t=(f-1)/fps;p=scroll_pos(t);sroot.location=p;sroot.keyframe_insert('location',frame=f)
 sw=0.
 if T_GAVEL-.9<=t<=T_GAVEL-.05:sw=math.radians(-55)*math.sin(PI*(t-(T_GAVEL-.9))/.85)
 elif T_GAVEL-.05<t<=T_GAVEL+.25:sw=math.radians(8)*math.sin(PI*(t-(T_GAVEL-.05))/.3)
 pivot.rotation_euler=(sw,0,0);pivot.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- eye lines: damped track on every head, gaze targets move to the speaker (and the speaker to the addressee)
GZ=[]
for i,c in enumerate(CH):
 g=bpy.data.objects.new('Gaze%d'%i,None);link(g);GZ.append(g)
 k_=c['rig'].pose.bones['mixamorig:Head'].constraints.new('DAMPED_TRACK');k_.target=g;k_.track_axis=FACE_AXIS;k_.influence=.85
def gaze_target(i,t):
 L=line_at(t)
 if L is None:
  prev=[x for x in SCHED if x['t1']<=t];L=prev[-1] if prev else None
  if L is None:return HEAD[(i+1)%6]
 if L['speaker']==i:return HEAD[L['to']]
 return HEAD[L['speaker']]
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for i in range(6):
  cur=gaze_target(i,t);prev=gaze_target(i,t-.35) if t>.35 else cur
  # blend from the previous target over 0.35 s after a change of target
  chg=[x['t0'] for x in SCHED if x['t0']<=t<x['t0']+.35 or x['t1']<=t<x['t1']+.35]
  w=1.
  if chg:w=smooth((t-chg[0])/.35) if t<chg[0]+.35 else 1.
  g=prev.lerp(cur,w)+Vector((0,0,.02));GZ[i].location=g;GZ[i].keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- lip sync and expression from the same syllable times
VOW={'a':(.85,0,.2),'e':(.5,0,.8),'i':(.4,0,.9),'o':(.65,.8,0),'u':(.5,.9,0)}
MOOD={'serious':dict(Concern=.25),'angry':dict(Frown=.5,ActingBrowL=.5,ActingBrowR=.5),'warm':dict(WarmSmile=.5),'concern':dict(Concern=.6,ActingBrowL=.4,ActingBrowR=.4)}
SYL_TIMES=[]
for L in SCHED:
 n=len(L['syl']);d=(L['t1']-L['t0']-.6)/n;kb=CH[L['speaker']]['keys'];st=[]
 for j,v in enumerate(L['syl']):
  tc=L['t0']+.3+(j+.5)*d;op,ro,wi=VOW[v];st.append((tc,d,v))
  if kb:
   for name,val in (('JawOpen',op*.75),('Round',ro*.7),('Wide',wi*.5)):
    kblk=kb.key_blocks.get(name)
    if kblk:
     kblk.value=0;kblk.keyframe_insert('value',frame=F(tc-d*.5));kblk.value=val;kblk.keyframe_insert('value',frame=F(tc));kblk.value=0;kblk.keyframe_insert('value',frame=F(tc+d*.45))
 SYL_TIMES.append(st)
 for i in (L['speaker'],):
  kb=CH[i]['keys']
  for name,val in MOOD[L['mood']].items():
   kblk=kb.key_blocks.get(name) if kb else None
   if kblk:kblk.value=0;kblk.keyframe_insert('value',frame=F(L['t0']-.3));kblk.value=val;kblk.keyframe_insert('value',frame=F(L['t0']+.2));kblk.keyframe_insert('value',frame=F(L['t1']-.2));kblk.value=0;kblk.keyframe_insert('value',frame=F(L['t1']+.3))
 for i in range(6):   # listeners react: concern on a hard line, a smile on a warm one
  if i==L['speaker'] or L['mood'] not in ('angry','warm'):continue
  kb=CH[i]['keys'];name='Concern' if L['mood']=='angry' else 'WarmSmile';kblk=kb.key_blocks.get(name) if kb else None
  if kblk and (i+L['k'])%2==0:kblk.value=0;kblk.keyframe_insert('value',frame=F(L['t0']+.3));kblk.value=.45;kblk.keyframe_insert('value',frame=F(L['t0']+.9));kblk.keyframe_insert('value',frame=F(L['t1']-.1));kblk.value=0;kblk.keyframe_insert('value',frame=F(L['t1']+.4))
# ---------------------------------------------------------------------------------------------------------- cameras: coverage generated from the script
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.data.energy=.15;sun.rotation_euler=(math.radians(50),0,0)
scene.world=bpy.data.worlds.new('Hall');scene.world.color=(.04,.035,.03)
def pos_seat(i,r=C['seat_r']):a=ANG[i];return Vector((math.cos(a)*r,math.sin(a)*r,0))
shots=[('1 The hall',0,SCHED[0]['t0']-.2,'wide',0)]
for L in SCHED:
 k=L['k'];mid=L['t0']+(L['t1']-L['t0'])*.7
 shots.append(('%d %s speaks'%(k+2,NAMES[L['speaker']]),L['t0']-.2 if k else SCHED[0]['t0']-.2,mid,'speaker',L['speaker']))
 nxt=SCHED[k+1]['speaker'] if k+1<len(SCHED) else L['to'];shots.append(('%d reaction %s'%(k+2,NAMES[nxt]),mid,L['t1']+.25,'reaction',nxt))
 if k==PASS_K:shots[-1]=('%d the scroll'%(k+2),SC_T-.4,SC_T1+.6,'insert_scroll',0)
 if k==GAVEL_K:shots[-1]=('%d the gavel'%(k+2),T_GAVEL-1.3,T_GAVEL+.8,'insert_gavel',1)
shots.append(('end',SCHED[-1]['t1']+.25,seconds,'wide',0))
# make the cuts contiguous
cuts=[];prev_end=0.
for name,a,b,kind,who in shots:
 a=max(a,prev_end)
 if b-a<.5:continue
 cuts.append((name,a,b,kind,who));prev_end=b
cuts[-1]=(cuts[-1][0],cuts[-1][1],seconds,cuts[-1][3],cuts[-1][4])
cams=[];CAMKEYS=[]
for k,(name,a,b,kind,who) in enumerate(cuts):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=200;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a)
  if kind=='wide':ang=math.radians(-60+60*u+k*20);p=Vector((math.cos(ang)*7.8,math.sin(ang)*7.8,3.6));q=Vector((0,0,1.0));cam.data.lens=24
  elif kind=='speaker':
   opp=ANG[who]+PI+math.radians(28*(1 if who%2 else -1));p=Vector((math.cos(opp)*3.5,math.sin(opp)*3.5,1.35));q=HEAD[who]+Vector((0,0,-.12));cam.data.lens=50
  elif kind=='reaction':
   opp=ANG[who]+PI-math.radians(30*(1 if who%2 else -1));p=Vector((math.cos(opp)*3.3,math.sin(opp)*3.3,1.3));q=HEAD[who]+Vector((0,0,-.12));cam.data.lens=60
  elif kind=='insert_scroll':
   sp_=scroll_pos(t);p=Vector((math.cos(ANG[1]-.5)*3.6,math.sin(ANG[1]-.5)*3.6,1.9));p=Vector((0,0,2.2))+Vector((math.cos(ANG[2]+PI)*1.2,math.sin(ANG[2]+PI)*1.2,0));q=sp_;cam.data.lens=40
  else:
   p=Vector((math.cos(ANG[1]+.8)*3.0,math.sin(ANG[1]+.8)*3.0,1.7));q=GAV0+Vector((0,0,.2));cam.data.lens=44
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
FAMILY=set()
for c in CH:FAMILY|=kit._family(c['root'])
for o in bpy.data.objects:
 if o.name.startswith(('Goblet','Scroll','Gavel','Candle')):FAMILY.add(o.name)
CAND=[(0,0,.6),(0,0,1.2),(0,0,2.),(0,-1.0,.6),(0,1.0,.6),(0,0,3.)]
offs={}
for k,cam,aim,f in CAMKEYS:
 settle(f);dg=bpy.context.evaluated_depsgraph_get();p=Vector(cam.location);q=Vector(aim.location);np_,idx=kit.clear_view(scene,dg,p,q,FAMILY,CAND);offs[(k,f)]=np_-p
for k in set(a for a,b in offs):
 fs=sorted(f for a,f in offs if a==k)
 for j,f in enumerate(fs):
  win=[offs[(k,g)] for g in fs[max(0,j-3):j+4]];offs[(k,f)]=Vector((sum(v.x for v in win)/len(win),sum(v.y for v in win)/len(win),max(v.z for v in win)))
for k,cam,aim,f in CAMKEYS:
 o=offs[(k,f)]
 if o.length>1e-6:settle(f);cam.location=Vector(cam.location)+o;cam.keyframe_insert('location',frame=f)
print('CAMERAS adjusted',sum(1 for v in offs.values() if v.length>1e-6),'of',len(offs))
# ---------------------------------------------------------------------------------------------------------- audit
issues=kit.persistence_audit(scene)
issues+=kit.camera_checks(scene,[c['root'] for c in CH])
worst_gaze=(0,0);worst_reach={}
for L in SCHED:
 for tt in np.linspace(L['t0']+.5,L['t1']-.3,3):
  settle(F(tt))
  for i in range(6):
   hmat=CH[i]['rig'].matrix_world@CH[i]['rig'].pose.bones['mixamorig:Head'].matrix;face=(hmat.to_3x3()@Vector((1,0,0)) if FACE_AXIS=='TRACK_X' else hmat.to_3x3().col[('X','Y','Z').index(FACE_AXIS[-1])]*(-1 if 'NEGATIVE' in FACE_AXIS else 1)).normalized()
   target=HEAD[L['to']] if i==L['speaker'] else HEAD[L['speaker']];want=(target-bw(i,'Head')).normalized();ang=math.degrees(math.acos(max(-1,min(1,face.dot(want)))))
   if ang>worst_gaze[0]:worst_gaze=(ang,tt)
  for i in range(6):
   for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
    d=(bw(i,bone,True)-TG[(i,limb)].matrix_world.translation).length
    if d>worst_reach.get(limb,(0,0))[0]:worst_reach[limb]=(d,tt)
print('GAZE worst %.0f deg at %.1f s'%worst_gaze,'REACH',{k:(round(v[0]*100,1),round(v[1],1)) for k,v in worst_reach.items()})
if worst_gaze[0]>60:issues.append('AUDIT gaze: a head is %.0f degrees off its target at %.1f s'%worst_gaze)
for k,(d,t) in worst_reach.items():
 if d>.08:issues.append('AUDIT reach: %s misses its target by %.0f cm at %.1f s'%(k,d*100,t))
for a,b in zip(SCHED,SCHED[1:]):
 if b['t0']<a['t1']:issues.append('AUDIT speech: lines %d and %d overlap'%(a['k'],b['k']))
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound: voices from the same syllable times, gavel, fire, music
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_council');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(14)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
FORM={'a':(800,1200),'e':(500,1900),'i':(350,2300),'o':(500,900),'u':(350,700)}
voice=np.zeros(N_+SR)
for L,sy in zip(SCHED,SYL_TIMES):
 f0=VOICE[L['speaker']]*(1.0+.05*(L['mood']=='angry'))
 for tc,d,v in sy:
  n=int(max(.08,d*.85)*SR);k=np.arange(n)/SR;pitch=f0*(1+.06*np.sin(2*PI*5.5*k)+.04*(L['mood']=='angry'));ph=2*PI*np.cumsum(pitch)/SR;f1,f2=FORM[v]
  x=(np.sin(ph)+.5*np.sin(2*ph)+.3*np.sin(3*ph));x=x*(.6+.4*np.sin(2*PI*f1*k/ SR*.0+ph*(f1/f0)/6.))+.15*nr.standard_normal(n)*(v in 'ei');env=np.sin(np.pi*np.arange(n)/n)**.7
  i=int((tc-d*.4)*SR)
  if 0<=i<N_:voice[i:i+n]+=x[:max(0,min(n,len(voice)-i))]*env[:max(0,min(n,len(voice)-i))]*.5
voice=voice[:N_]
gav=np.zeros(N_+SR);n=int(.5*SR);k=np.arange(n)/SR;i=int(T_GAVEL*SR);gav[i:i+n]=(np.sin(2*PI*(900-300*k)*k)*np.exp(-k*14)+lp(nr.standard_normal(n),8)*np.exp(-k*30))*1.2;gav=gav[:N_]
fire=lp(nr.standard_normal(N_),50)*.05*(1+.5*np.sin(tt*7.3));crack=np.zeros(N_)
for _ in range(int(seconds*3)):
 j=int(nr.uniform(0,N_-400));crack[j:j+300]+=nr.standard_normal(300)*np.exp(-np.arange(300)/60.)*.25
slide=np.zeros(N_+SR);n=int((SC_T1-SC_T)*SR);i=int(SC_T*SR);slide[i:i+n]=lp(nr.standard_normal(n),40)*np.sin(np.pi*np.arange(n)/n)*.3;slide=slide[:N_]
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.3,1)*np.exp(-k*.9/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 t0=ci*4.;chord=((110,130.8,164.8),(98,123.5,146.8),(103.8,123.5,155.6),(110,138.6,164.8))[ci%4]
 for f0 in chord:
  n_=note(f0,4.2,.18);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('voices.wav',voice,.9),wav('gavel.wav',gav+slide,.8),wav('fire.wav',fire+crack,.5),wav('music.wav',music,.35)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('voices','gavel and scroll','fire','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('COUNCIL_DONE',frames,'frames',len(SCHED),'lines')
