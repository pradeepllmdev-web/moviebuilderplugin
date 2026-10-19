"""Blender script: 'The Night Heist' - Leo steals a jewel from a museum guarded by two sweeping sentries and a laser gate (about 60 s).

blender -b --disable-autoexec --python heist_scene.py -- <ship_assets_dir> <out.blend>

New in this scene: a STEALTH PLANNER. Two sentries sweep flashlight cones (angle, range, pillars and cases occlude them), a laser gate blinks on a pattern. The planner searches, for every
hop between cover points, the earliest departure time at which Leo waits unseen, crosses unseen and never touches a laser, and writes the timed route; the whole film (camera cuts, sounds, the
alarm after the theft) follows from it. The audit re-checks the finished route against the cones frame by frame (zero sightings before the alarm), checks the laser crossing, the grips on the
dial and jewel, ground contact and camera visibility. Clips: build_ship_assets.py (kneel, crawl, climb, idle, run, jump)."""
import bpy,math,random,sys,os,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit,scene_params,locations
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;rnd=random.Random(31);PI=math.pi
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color,emit=0.):
 if name in _m:return _m[name]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
  if emit:
   for key in ('Emission Color','Emission'):
    if key in b.inputs:b.inputs[key].default_value=(*color,1);break
   if 'Emission Strength' in b.inputs:b.inputs['Emission Strength'].default_value=emit
 _m[name]=m;return m
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=None,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color)+str(emit),color,emit))
 if parent:o.parent=parent
 return o
CTX=dict(link=link,mat=mat,prim=prim);M=locations.MUSEUM
locations.load('museum_hall',CTX,'intact')
objs={}
for o in bpy.data.objects:
 if 'role' in o.keys():objs[o['role']]=o
jewel,lid,dial=objs['jewel'],objs['lid'],objs['dial'];LASERS=[o for o in bpy.data.objects if 'group' in o.keys()]
PX,PY=M['pedestal']
# ---------------------------------------------------------------------------------------------------------- the sentries and the lasers
RANGE=11.;HALF=math.radians(17);SWEEP=math.radians(52)
SENT=[dict(pos=Vector((-16.6,6.9,0)),base=math.atan2(-6.9,16.6),period=7.4,phase=0.),dict(pos=Vector((16.6,-6.9,0)),base=math.atan2(6.9,-16.6),period=9.1,phase=2.4)]
T_ALARM=None
def sentry_dir(i,t):
 g=SENT[i];a=g['base']+SWEEP*math.sin(2*PI*t/g['period']+g['phase']);return a
def cone_vec(i,t):
 a=sentry_dir(i,t);return Vector((math.cos(a),math.sin(a),-.07)).normalized()
LASER_ON,LASER_OFF,LASER_PH=2.0,4.2,.0
def gate_on(t):return ((t-LASER_PH)%(LASER_ON+LASER_OFF))<LASER_ON
def corner_on(t):return ((t-1.1)%(2.6+2.0))<2.6
dg=bpy.context.evaluated_depsgraph_get()
OCCL=('Pillar','Case','Crate','Pedestal','Wall')
def sees(i,t,p,h):
 g=SENT[i];o=g['pos']+Vector((0,0,1.15));tgt=Vector((p.x,p.y,h));v=tgt-o;d=v.length
 if d>RANGE or d<.5:return False
 if math.acos(max(-1,min(1,v.normalized().dot(cone_vec(i,t)))))>HALF:return False
 ok,loc,n,idx,ob,mw=scene.ray_cast(dg,o+v.normalized()*.4,v.normalized(),distance=max(.1,d-.5))
 return not (ok and ob.name.startswith(OCCL))
HEIGHT={'wait':(.25,.5),'walk':(.3,.7),'crawl':(.18,.35)}
def visible_to_any(t,p,mode):
 for i in range(2):
  for h in HEIGHT[mode]:
   if sees(i,t,p,h):return True
 return False
# ---------------------------------------------------------------------------------------------------------- the planner
def cover(x):return [(Vector((x+dx,sy*2.25,0)),'walk') for sy in (1,-1) for dx in (-.5,0,.5)]
NODES=[[(Vector((-16.9,-1.6,0)),'wait',0.)],cover(-12.),cover(-6.),cover(0.),[(Vector((5.0,0.2,0)),'walk',0.)],cover(6.),[(Vector((PX-1.25,PY,0)),'crawl',9.4)]]
SPEED={'walk':1.15,'crawl':.7}
def lerp(a,b,u):return a+(b-a)*u
def seg_safe(a,b,td,dur,mode,check_gate=True):
 n=max(2,int(dur/.1))
 for k in range(n+1):
  t=td+dur*k/n;p=lerp(a,b,k/n)
  if visible_to_any(t,p,mode):return False
  if check_gate and abs(p.x-M['gate_x'])<.45 and gate_on(t):return False
 return True
def hidden_wait(a,t0,t1):
 t=t0
 while t<=t1+1e-6:
  if visible_to_any(t,a,'wait'):return False
  t+=.1
 return True
def plan():
 t=1.5;segs=[];warns=[];cur=NODES[0][0][0];curname='start'
 segs.append(dict(kind='wait',t0=0.,t1=t,pos=cur,node='start'))
 for li in range(1,len(NODES)):
  best=None
  for ci,cand in enumerate(NODES[li]):
   b,mode=cand[0],cand[1];dwell=cand[2] if len(cand)>2 else .6;a_=cur;dur=(b-a_).length/SPEED[mode];td=t
   while td<t+70:
    if not hidden_wait(a_,t,td):break
    if seg_safe(a_,b,td,dur,mode) and hidden_wait(b,td+dur,td+dur+dwell):
     if best is None or td+dur<best[0]:best=(td+dur,td,dur,b,mode,'c%d_%d'%(li,ci))
     break
    td+=.1
  if best is None:
   warns.append('no safe hop to layer %d'%li);b,mode=NODES[li][0][0],NODES[li][0][1];dur=(b-cur).length/SPEED[mode];best=(t+dur,t,dur,b,mode,'c%d_x'%li)
  arr,td,dur,b,mode,name=best
  if td>t+.05:segs.append(dict(kind='wait',t0=t,t1=td,pos=cur,node=curname))
  segs.append(dict(kind='move',t0=td,t1=arr,a=cur,b=b,mode=mode,node=name));t=arr;cur=b;curname=name
 return segs,t,warns
SEGS,T_PED,PLAN_WARN=plan();print('PLAN reaches the pedestal at %.1f s'%T_PED,PLAN_WARN)
for s in SEGS:print('SEG',s['kind'],s.get('node'),round(s['t0'],1),round(s['t1'],1))
# ---------------------------------------------------------------------------------------------------------- the theft and the escape (after the route)
T_DIAL0=T_PED+1.0;T_DIAL1=T_DIAL0+4.2;T_LID0=T_DIAL1+.3;T_LID1=T_LID0+1.4;T_GRAB0=T_LID1+.2;T_GRAB1=T_GRAB0+1.2;T_ALARM=T_GRAB1+1.0
T_RUN0=T_ALARM+.2;WIN=Vector(M['window']);RUN_END=Vector((WIN.x-1.6,0,0));T_JUMP0=T_RUN0+(RUN_END-Vector((PX-.9,PY,0))).length/3.6;T_JUMP1=T_JUMP0+.6
T_OUT=T_JUMP1+2.2;seconds=T_OUT+5.0;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
ST_POS=Vector((PX-.95,PY,0))
def leo_state(t):
 """(position, heading, mode) of Leo at time t from the plan, the theft and the escape."""
 for s in SEGS:
  if s['t0']<=t<s['t1']:
   if s['kind']=='wait':return s['pos'],hd_to(s['pos'],t),'wait'
   u=(t-s['t0'])/(s['t1']-s['t0']);p=lerp(s['a'],s['b'],u);return p,math.atan2((s['b']-s['a']).y,(s['b']-s['a']).x),s['mode']
 if t<T_RUN0:return ST_POS,0.,'steal' if t>T_PED+.6 else 'stand'
 if t<T_JUMP0:u=(t-T_RUN0)/(T_JUMP0-T_RUN0);return lerp(ST_POS,RUN_END,u),0.,'run'
 if t<T_JUMP1:u=(t-T_JUMP0)/(T_JUMP1-T_JUMP0);return lerp(RUN_END,Vector((WIN.x+.5,0,0)),u),0.,'jump'
 u=min(1.,(t-T_JUMP1)/1.6);return lerp(Vector((WIN.x+.5,0,0)),Vector((WIN.x+4.8,.8,0)),smooth(u)),.15,'run' if u<1 else 'idle'
def hd_to(p,t):
 for s in SEGS:
  if s['kind']=='move' and s['t0']>=t:return math.atan2((s['b']-p).y,(s['b']-p).x)
 return 0.
def leo_z(t):
 if T_JUMP0<=t<=T_JUMP1:
  u=(t-T_JUMP0)/(T_JUMP1-T_JUMP0);return (WIN.z-.0)*smooth(u)+kit.ballistic(u,kit.flight_apex(T_JUMP1-T_JUMP0))
 if t>T_JUMP1:return .9
 return 0.
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
 return dict(root=root,rig=rig,body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices)),objs=new,scale=scale)
prm=scene_params.get()
LEO=load_char('Leo',1.,prm['hero_tint'] or (.28,.3,.4));G=[load_char('Sentry%d'%i,1.1,(.3,.38,.6)) for i in range(2)]
CLIPS={}
for c in ('idle','run','climb','crawl','kneel','jump','look','startle'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
def add_strip(tr,clip,a,b,scale=None,hold=False,f0=None,f1=None):
 act=CLIPS[clip];st=tr.strips.new(clip,F(a),act);st.action_slot=act.slots[0];n=(f1 or act.frame_range[1])-(f0 or act.frame_range[0])+1
 if f0:st.action_frame_start=f0
 if f1:st.action_frame_end=f1
 sc=scale or 1.;st.scale=sc;need=(F(b)-st.frame_start)/(n*sc)
 if need>=1:st.repeat=need
 else:st.action_frame_end=st.action_frame_start+max(2,need*n)-1
 st.extrapolation='HOLD' if hold else 'NOTHING';st.blend_in=5;st.blend_out=5;return st
def clip_for(mode):
 return {'wait':('kneel',49,96,1.),'walk':('climb',None,None,.7),'crawl':('crawl',None,None,.75),'stand':('idle',None,None,1.),'steal':('idle',None,None,1.),'run':('run',None,None,.85),'jump':('jump',None,None,.55),'idle':('look',None,None,1.)}[mode]
# Leo's strips: merge consecutive samples of the same mode
timeline=[];tcur=0.
modes=[]
tt_=0.
while tt_<seconds:
 modes.append((tt_,leo_state(tt_)[2]));tt_+=.2
runs=[];start=0.;cur=modes[0][1]
for t,m in modes[1:]:
 if m!=cur:runs.append((start,t,cur));start=t;cur=m
runs.append((start,seconds,cur))
merged=[]
for a,b,m in runs:
 if merged and b-a<.45:merged[-1]=(merged[-1][0],b,merged[-1][2]);continue
 merged.append((a,b,m))
ad=LEO['rig'].animation_data;tracks=[ad.nla_tracks.new(),ad.nla_tracks.new()]
for k,(a,b,m) in enumerate(merged):
 clip,f0,f1,sc=clip_for(m);st=add_strip(tracks[k%2],clip,a if not k else a-.2,b,sc,hold=(k==0),f0=f0,f1=f1)
# the sentries stand at their posts, their bodies turn with their flashlights
for i,g in enumerate(G):
 ad=g['rig'].animation_data;tr=ad.nla_tracks.new();add_strip(tr,'look',0,seconds,1.,hold=True)
 g['root'].location=SENT[i]['pos']
prev=[None,None]
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for i,g in enumerate(G):
  a=sentry_dir(i,t) if t<T_ALARM else sentry_dir(i,T_ALARM)
  if t>=T_ALARM:
   u=smooth((t-T_ALARM)/2.8);tgt=Vector((PX-1.2,PY+(1.5 if i==0 else -1.5),0));g['root'].location=SENT[i]['pos'].lerp(tgt,u);a=math.atan2((tgt-SENT[i]['pos']).y,(tgt-SENT[i]['pos']).x)
  r=Euler((0,0,a+PI/2))
  if prev[i] is not None:r.make_compatible(prev[i])
  prev[i]=r.copy();g['root'].rotation_euler=r;g['root'].keyframe_insert('rotation_euler',frame=f);g['root'].keyframe_insert('location',frame=f)
# flashlights: a spot light on each sentry that follows the cone (it is the vision cone you can see)
for i,g in enumerate(G):
 sp=bpy.data.objects.new('Flashlight%d'%i,bpy.data.lights.new('Flashlight%d'%i,'SPOT'));link(sp);sp.data.energy=3500;sp.data.spot_size=2*HALF*1.15;sp.data.spot_blend=.35;sp.data.color=(1,.95,.7)
 for f in range(1,frames+1,2):
  t=(f-1)/fps;v=cone_vec(i,min(t,T_ALARM));sp.location=g['root'].location+Vector((0,0,1.15));sp.rotation_euler=v.to_track_quat('-Z','Y').to_euler();sp.keyframe_insert('location',frame=f);sp.keyframe_insert('rotation_euler',frame=f)
 bm_=prim('cone','DustBeam%d'%i,SENT[i]['pos']+Vector((0,0,1.15)),(1,.95,.5),scale=(1,1,1),vertices=16,radius1=math.tan(HALF)*RANGE*.9,depth=RANGE*.9);bm_.display_type='WIRE';bm_.hide_render=False
 for f in range(1,frames+1,2):
  t=(f-1)/fps;v=cone_vec(i,min(t,T_ALARM));base=g['root'].location+Vector((0,0,1.15));bm_.location=base+v*RANGE*.45;bm_.rotation_euler=(-v).to_track_quat('Z','Y').to_euler() if False else v.to_track_quat('-Z','Y').to_euler();bm_.rotation_euler=(-v).to_track_quat('Z','Y').to_euler();bm_.keyframe_insert('location',frame=f);bm_.keyframe_insert('rotation_euler',frame=f)
# Leo's root path and crouch lean
prevl=None
for f in range(1,frames+1,2):
 t=(f-1)/fps;p,h,m=leo_state(t);pitch=.32 if m in ('walk',) else 0.;r=Euler((pitch,0,h+PI/2))
 if prevl is not None:r.make_compatible(prevl)
 prevl=r.copy();LEO['root'].location=(p.x,p.y,leo_z(t));LEO['root'].rotation_euler=r;LEO['root'].keyframe_insert('location',frame=f);LEO['root'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- dial and jewel: hands by IK, the jewel follows the wrist, then rides at his chest
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Wrist_'+limb,None);tg.empty_display_size=.05;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,1.0)
 k_=LEO['rig'].pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;IK[limb]=k_
DIAL_C=Vector((PX-.72,PY,.8));JEWEL0=Vector((PX,PY,1.2))
def dial_theta(t):
 if t<T_DIAL0:return 0.
 u=min(1.,(t-T_DIAL0)/(T_DIAL1-T_DIAL0));return 3*PI*smooth(u)+.3*math.sin(u*18)*(1-u)
def lid_z(t):return 1.22+(.7*smooth((t-T_LID0)/(T_LID1-T_LID0)) if t>T_LID0 else 0.)
def hands(t):
 """wrist targets and influence: both hands on the dial (turning it), the left hand lifting the lid, the right hand taking the jewel."""
 res={'LH':(None,0.),'RH':(None,0.)}
 if T_DIAL0-.5<=t<=T_GRAB1+1.2:
  w=smooth((t-(T_DIAL0-.5))/.5)*(1-smooth((t-(T_GRAB1+.6))/.6));th=dial_theta(t)
  if t<T_LID0:
   for limb,sg in (('LH',1),('RH',-1)):
    ang=th*.9;res[limb]=(DIAL_C+Vector((-.05,math.sin(ang+sg*1.4)*.13,math.cos(ang+sg*1.4)*.13)),w)
  elif t<T_GRAB0:
   u=smooth((t-T_LID0)/(T_LID1-T_LID0));res['LH']=(Vector((PX-.4,PY+.4,1.12+.6*u)),1.);res['RH']=(DIAL_C+Vector((-.05,0,.15)),1.)
  else:
   u=smooth((t-T_GRAB0)/(T_GRAB1-T_GRAB0));res['LH']=(Vector((PX-.4,PY+.4,1.72)),1.);res['RH']=(JEWEL0.lerp(Vector((PX-.45,PY-.05,1.0)),u)+Vector((-.08,0,.0)),w if t<T_GRAB1 else w)
 return res
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
REACH=.44
for f in range(1,frames+1,2):
 t=(f-1)/fps;h=hands(t)
 if T_DIAL0-.6<=t<=T_GRAB1+1.3:settle(f)
 for limb in ('LH','RH'):
  p,w=h[limb]
  if p is not None and w>0:
   sh=LEO['rig'].matrix_world@LEO['rig'].pose.bones['mixamorig:'+('LeftArm' if limb=='LH' else 'RightArm')].head;d=p-sh
   if d.length>REACH:p=sh+d.normalized()*REACH
   h[limb]=(p,w)
  if p is not None:TG[limb].location=p;TG[limb].keyframe_insert('location',frame=f)
  IK[limb].influence=w;IK[limb].keyframe_insert('influence',frame=f)
  if p is None:TG[limb].location=(PX-.9,PY,.8);TG[limb].keyframe_insert('location',frame=f)
dial.rotation_euler=(0,0,0)
for f in range(1,frames+1,2):
 t=(f-1)/fps;dial.rotation_euler=(dial_theta(t),0,0);dial.keyframe_insert('rotation_euler',frame=f);lid.location=(lid.location.x,lid.location.y,lid_z(t)) if False else lid.location;lid.location.z=lid_z(t);lid.keyframe_insert('location',frame=f)
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
for f in range(1,frames+1,2):
 t=(f-1)/fps
 if t<T_GRAB0:p=JEWEL0
 else:
  settle(f);rig=LEO['rig'];wr=rig.matrix_world@rig.pose.bones['mixamorig:RightHand'].head;ch=rig.matrix_world@rig.pose.bones['mixamorig:Spine2'].head
  if t<T_GRAB1:p=JEWEL0.lerp(wr,smooth((t-T_GRAB0)/.5)) if t<T_GRAB0+.5 else wr
  else:p=wr.lerp(ch+Vector((.12*math.cos(leo_state(t)[1]),.12*math.sin(leo_state(t)[1]),.0)),smooth((t-T_GRAB1)/.8))
 jewel.location=p;jewel.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- lights: the alarm
al=bpy.data.objects.new('AlarmLight',bpy.data.lights.new('AlarmLight','POINT'));link(al);al.location=(0,0,6.5);al.data.color=(1,.1,.05)
for f in range(1,frames+1,2):
 t=(f-1)/fps;al.data.energy=(2500*(.5+.5*math.sin(2*PI*2.2*(t-T_ALARM))) if t>=T_ALARM else 0.);al.data.keyframe_insert('energy',frame=f)
for ob in LASERS:
 m=ob.data.materials[0].copy();ob.data.materials[0]=m;b=m.node_tree.nodes.get('Principled BSDF')
 if not b:continue
 grp=ob['group'];sock=b.inputs['Emission Strength']
 for f in range(1,frames+1,3):
  t=(f-1)/fps;on=gate_on(t) if grp.startswith('gate') else corner_on(t);on=on and t<T_ALARM+.1 or (t>=T_ALARM and False)
  sock.default_value=6. if on else 0.;sock.keyframe_insert('default_value',frame=f)
scene.world=bpy.data.worlds.new('Night');scene.world.color=(.015,.02,.04)
# ---------------------------------------------------------------------------------------------------------- cameras generated from the route
cuts=[('1 The museum',0,min(4.2,SEGS[0]['t1']+2.5),'wide')]
for k,s in enumerate(SEGS):
 if s['kind']=='move' and s['t1']-s['t0']>.9:cuts.append(('move to %s'%s['node'],s['t0']-.2,s['t1']+.2,'follow'))
 elif s['kind']=='wait' and s['t1']-s['t0']>1.6 and s['t0']>0:cuts.append(('hiding at %s'%s['node'],s['t0'],s['t1'],'peek'))
cuts+=[('the dial',T_DIAL0-.4,T_DIAL1,'dial'),('the lid',T_DIAL1,T_GRAB0+.2,'lid'),('the jewel',T_GRAB0+.2,T_ALARM+.3,'jewel'),('alarm',T_ALARM+.3,T_JUMP0-.3,'alarm'),('the leap',T_JUMP0-.3,T_JUMP1+.7,'leap'),('outside',T_JUMP1+.7,seconds,'outside')]
cl=[];pe=0.
for name,a,b,kind in cuts:
 a=max(a,pe)
 if b-a<.6:continue
 cl.append((name,a,b,kind));pe=b
cl[-1]=(cl[-1][0],cl[-1][1],seconds,cl[-1][3])
cams=[];CAMKEYS=[]
for k,(name,a,b,kind) in enumerate(cl):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=200;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);p0,h0,m0=leo_state(t);lh=Vector((p0.x,p0.y,leo_z(t)+.55));cam.data.lens=30
  if kind=='wide':p=Vector((-15+10*u,-7.4,6.6));q=Vector((-2,0,.6));cam.data.lens=22
  elif kind=='follow':p=Vector((p0.x-1.9*math.cos(h0)+.8*math.sin(h0),p0.y-1.9*math.sin(h0)-.8*math.cos(h0),.9));q=lh;cam.data.lens=32
  elif kind=='peek':
   g=min(range(2),key=lambda i:(SENT[i]['pos']-p0).length);gp=SENT[g]['pos']+Vector((0,0,1.0));p=lh+(gp-lh).normalized()*-.9+Vector((0,0,.05));q=gp+Vector((0,0,.2));cam.data.lens=40
  elif kind=='dial':p=DIAL_C+Vector((-1.5,-.9,.3));q=DIAL_C;cam.data.lens=44
  elif kind=='lid':p=Vector((PX-1.3,PY-1.1,1.5));q=Vector((PX,PY,1.3));cam.data.lens=46
  elif kind=='jewel':p=Vector((PX-.9,PY-1.2,1.35));q=Vector((PX-.3,PY,1.15));cam.data.lens=52
  elif kind=='alarm':p=Vector((p0.x-3.2,-1.2,4.8));q=lh;cam.data.lens=28
  elif kind=='leap':p=Vector((WIN.x-5.5,-3.4,1.4));q=Vector((WIN.x,0,1.1));cam.data.lens=32
  else:p=Vector((WIN.x+9,-4.5,2.6));q=lh;cam.data.lens=34
  p.x=max(p.x,-17.2);cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
FAMILY=set()
for c in [LEO]+G:FAMILY|=kit._family(c['root'])
for o in bpy.data.objects:
 if o.name.startswith(('Jewel','Laser','Exhibit','GlassLid')):FAMILY.add(o.name)
CAND=[(0,0,.6),(0,0,1.2),(0,0,2.4),(0,-1.2,.8),(0,1.2,.8),(0,0,4.)]
offs={}
for k,cam,aim,f in CAMKEYS:
 settle(f);d_=bpy.context.evaluated_depsgraph_get();p=Vector(cam.location);q=Vector(aim.location);np_,idx=kit.clear_view(scene,d_,p,q,FAMILY,CAND);offs[(k,f)]=np_-p
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
issues+=kit.camera_checks(scene,[LEO['root']])
issues+=['AUDIT planner: '+w for w in PLAN_WARN]
seen=[];near=[]
t=0.
while t<T_ALARM:
 p,h,m=leo_state(t);md={'wait':'wait','walk':'walk','crawl':'crawl'}.get(m,'wait')
 if visible_to_any(t,p,md):seen.append(round(t,1))
 for i in range(2):
  v=Vector((p.x,p.y,.5))-(SENT[i]['pos']+Vector((0,0,1.15)))
  if v.length<RANGE and math.acos(max(-1,min(1,v.normalized().dot(cone_vec(i,t)))))<HALF*2.2:near.append(round(t,1))
 t+=.05
if seen:issues.append('AUDIT stealth: Leo is seen at t=%s'%seen[:6])
crossing=[t for t in np.arange(0,T_ALARM,.05) if abs(leo_state(t)[0].x-M['gate_x'])<.4]
if any(gate_on(t) for t in crossing):issues.append('AUDIT laser: Leo is inside the laser gate while it is on')
print('STEALTH seen',len(seen),'near misses (cone within 2.2x half angle)',len(set(near)),'gate crossing %.1f..%.1f s'%(min(crossing),max(crossing)) if crossing else '')
worst={}
for f in range(F(T_DIAL0),F(T_GRAB1)+1,4):
 settle(f);t=(f-1)/fps;h=hands(t)
 for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
  if h[limb][1]<.99:continue
  d=(LEO['rig'].matrix_world@LEO['rig'].pose.bones['mixamorig:'+bone].tail-TG[limb].matrix_world.translation).length
  if d>worst.get(limb,(0,0))[0]:worst[limb]=(d,t)
for limb,(d,t) in worst.items():
 if d>.08:issues.append('AUDIT grip: %s misses the dial or jewel by %.0f cm at %.1f s'%(limb,d*100,t))
print('GRIP',{k:(round(v[0]*100,1),round(v[1],1)) for k,v in worst.items()})
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_heist');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(17)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
def at(arr,t,x,g=1.):
 i=int(t*SR)
 if 0<=i<len(arr):
  n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
hum=np.zeros(N_)
for t0 in np.arange(0,T_ALARM,LASER_ON+LASER_OFF):
 i=int(t0*SR);n=int(LASER_ON*SR);k=np.arange(n)/SR;hum[i:i+n]=(np.sin(2*PI*120*k)+.4*np.sin(2*PI*240*k))*.25*np.minimum(k/.1,1)*np.minimum((LASER_ON-k)/.1,1) if i+n<=N_ else 0
step=np.zeros(N_+SR);sk=np.arange(int(.1*SR))/SR;tick=lp(nr.standard_normal(len(sk)),8)*np.exp(-sk*40)
for s in SEGS:
 if s['kind']=='move':
  t=s['t0']
  while t<s['t1']:at(step,t,tick,.25 if s['mode']=='walk' else .15);t+=.55
click=np.zeros(N_+SR);ck=np.arange(int(.03*SR))/SR;cl_=np.sin(2*PI*2400*ck)*np.exp(-ck*150)
for t in np.arange(T_DIAL0+.2,T_DIAL1,.28):at(click,t,cl_,.6)
glass=np.zeros(N_+SR);gk=np.arange(int(1.2*SR))/SR;at(glass,T_LID0,np.sin(2*PI*1500*gk)*np.exp(-gk*3)*.2+lp(nr.standard_normal(len(gk)),5)*np.exp(-gk*3)*.1,1.)
siren=np.zeros(N_);sn=int((seconds-T_ALARM)*SR);sk2=np.arange(sn)/SR;siren[int(T_ALARM*SR):int(T_ALARM*SR)+sn]=np.sin(2*PI*np.cumsum(700+300*np.sin(2*PI*1.1*sk2))/SR)*.4*np.minimum(sk2/.3,1)
heart=np.zeros(N_+SR)
for t in sorted(set(near)):
 hb=np.sin(2*PI*55*np.arange(int(.18*SR))/SR)*np.exp(-np.arange(int(.18*SR))/SR*22);at(heart,t,hb,.4)
ambient=lp(nr.standard_normal(N_),80)*.05
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.3,1)*np.exp(-k*.9/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 chord=((82.4,98,123.5),(73.4,87.3,110),(65.4,77.8,98),(73.4,87.3,110))[ci%4]
 for f0 in chord:at(music,ci*4.,note(f0,4.2,.2))
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('ambient.wav',ambient+hum,.5),wav('steps.wav',step[:N_],.5),wav('dial.wav',click[:N_]+glass[:N_],.6),wav('alarm.wav',siren,.7),wav('heartbeat.wav',heart[:N_],.5),wav('music.wav',music,.35)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('ambient and lasers','steps','dial and glass','alarm','heartbeat','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('HEIST_DONE',frames,'frames')
