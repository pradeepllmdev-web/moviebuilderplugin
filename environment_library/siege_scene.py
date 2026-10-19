"""Blender script: 'The Siege' - an army of lions storms a citadel; Leo climbs a ladder, kicks a defender off the wall, opens the gate and raises the banner (72 s).

blender -b --disable-autoexec --python siege_scene.py -- <ship_assets_dir> <out.blend> [seconds=72]

Scale: 4 catapults firing ballistic stones (flight time 3.2 s) that bring down a 12 m section of the wall (54 baked rigid-body blocks, released by the impacts and by loss of support),
a marching army of 34 real cloned lions plus 240 cone soldiers, 18 defenders on the walls firing arrows (ballistic, they stay stuck in the ground), ladders, a gate with a portcullis that
rises when Leo turns the winch (IK hands on the wheel), a flag he hoists hand over hand. The hero climbs a ladder with the hold-stepping grips of the cliff scene, kicks a defender
(contact solver, skin target, projectile). Nothing appears or disappears (persistence audit), cameras are cleared of scenery automatically. Clips: build_ship_assets.py."""
import bpy,math,random,sys,os,wave,bmesh,zlib
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 72.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(11);PI=math.pi
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color):
 if name in _m:return _m[name]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
 _m[name]=m;return m
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),parent=None,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color))
 if parent:o.parent=parent
 return o
def kf(o,f,**kw):
 for k,v in kw.items():setattr(o,k,v);o.keyframe_insert(k,frame=f)
# ---------------------------------------------------------------------------------------------------------- the citadel (y = 30 is the wall line, the field is at y < 29)
WY0,WY1,WH=29.3,30.7,9.;BLK=(2.,1.,1.4)
bpy.ops.mesh.primitive_plane_add(size=1,location=(0,-30,-.05));g=bpy.context.object;g.scale=(400,260,1);g.name='Field';g.data.materials.append(mat('Field',(.36,.44,.22)))
passive=[]
def solid(name,center,half,color):
 o=prim('cube',name,center,color,scale=half);passive.append(o);return o
STONE=(.58,.54,.47)
solid('WallW',(-26,30,WH/2),(8,.7,WH/2),STONE);solid('WallE',(18.5,30,WH/2),(15.5,.7,WH/2),STONE);solid('WallMidW',(-4.5,30,WH/2),(1.5,.7,WH/2),STONE)
for sx in (-5.5,5.5):
 for sy in (28.8,32.2):solid('GatePillar',(sx,sy,7.5),(.35,.35,7.5),(.5,.46,.4))
solid('GateRoof',(0,30.5,14.2),(6.2,2.6,.8),(.45,.3,.22));solid('GateLintel',(0,30,6.6),(3,.7,.6),STONE)
for x in (-34,34):
 prim('cyl','Tower',(x,30,7),(.52,.48,.42),scale=(5,5,7),vertices=12,radius=1,depth=2);prim('cone','TowerRoof',(x,30,15.5),(.5,.16,.14),scale=(5.6,5.6,2.8),vertices=12,radius1=1,depth=2)
solid('KeepWall',(0,60,8),(14,.8,8),STONE);solid('KeepTower',(0,57,10),(4,4,10),(.5,.46,.4));prim('cone','KeepRoof',(0,57,22),(.5,.16,.14),scale=(4.6,4.6,3),vertices=8,radius1=1,depth=2)
for s_ in (-1,1):solid('CourtWall',(s_*34,45,5),(.7,15,5),STONE)
for i in range(14):x=rnd.uniform(-28,28);y=rnd.uniform(36,52);prim('cube','House',(x,y,1.5),(.55,.4,.25),scale=(2,2,1.5));prim('cone','HouseRoof',(x,y,3.6),(.5,.2,.15),scale=(3,3,1.2),vertices=4,radius1=1,depth=2,rot=(0,0,PI/4))
# the breach section: 6 columns x 9 rows of blocks, x from -18 to -6
BLOCKS=[]
for c in range(6):
 for r in range(9):
  x=-17+c*2.;z=.5+r*1.;o=prim('cube','Block',(x,30,z),tuple(v*(.5+.02*((c+r)%2)) for v in (.58,.54,.47)) if False else ((.6,.56,.5) if (c+r)%2 else (.55,.5,.44)),scale=(BLK[0]/2-.02,BLK[2]/2-.02,BLK[1]/2-.02));BLOCKS.append((o,c,r))
# gate: portcullis (bars) in the opening, on a rail
port=prim('cube','PortcullisTop',(0,30,6.1),(.2,.2,.2),scale=(3,.15,.12))
portbars=[port]
for i,x in enumerate(np.linspace(-2.7,2.7,10)):portbars.append(prim('cube','PortBar',(x,30,3.0),(.22,.22,.22),scale=(.08,.12,3.0)))
for z in (1.5,3.0,4.5):portbars.append(prim('cube','PortCross',(0,30,z),(.22,.22,.22),scale=(3,.1,.07)))
for o in portbars:
 if o is not port:o.parent=port
 # parent keeps local offsets; the bars are positioned relative to the world origin so convert
port.location=(0,30,0);port.name='Portcullis'
for o in portbars[1:]:o.location=(o.location.x,o.location.y-30,o.location.z)
port.scale=(1,1,1)
# ---------------------------------------------------------------------------------------------------------- ground rigid-body setup and bake
bpy.ops.rigidbody.world_add();rw=scene.rigidbody_world;rw.point_cache.frame_start=1;rw.point_cache.frame_end=frames
for o in passive+[g]:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add(type='PASSIVE');o.rigid_body.collision_shape='BOX';o.rigid_body.friction=.8;o.select_set(False)
# catapults and the schedule of volleys: (fire time, catapult index, impact x, impact z)
CATS=[(-26.,-16.),(-12.,-16.),(12.,-16.),(26.,-16.)];FLIGHT=3.2
VOLLEYS=[];
for v,t0 in enumerate((6.0,11.0,16.0)):
 for c in range(4):VOLLEYS.append((t0+.55*c,c,-12.+rnd.uniform(-4.5,4.5),rnd.uniform(3.5,7.5)))
# blocks fall when hit or when what they stand on is gone
REL={}
for o,c,r in BLOCKS:
 x=o.location.x;z=o.location.z;best=None
 for tf,ci,ix,iz in VOLLEYS:
  d=math.hypot(x-ix,z-iz)
  if d<3.2:
   t=tf+FLIGHT+.06*d
   if best is None or t<best:best=t
 REL[(c,r)]=best
for r in range(1,9):
 for c in range(6):
  below=REL.get((c,r-1))
  if below is not None:REL[(c,r)]=min(REL[(c,r)],below+.35) if REL[(c,r)] is not None else below+.35
for c in range(6):
 for r in range(9):
  if REL[(c,r)] is None and r>=5 and sum(1 for cc in range(6) if REL.get((cc,r-1)) is not None)>=3:pass
for o,c,r in BLOCKS:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add(type='ACTIVE');rb=o.rigid_body;rb.collision_shape='BOX';rb.mass=BLK[0]*BLK[1]*BLK[2]*500;rb.friction=.8;rb.restitution=.12;rb.linear_damping=.08;rb.angular_damping=.2
 rb.kinematic=True;rb.keyframe_insert('kinematic',frame=1)
 if REL[(c,r)] is not None:
  tr_=REL[(c,r)];base=o.location.copy();rr=random.Random(c*31+r)
  o.location=base;o.rotation_euler=(0,0,0);o.keyframe_insert('location',frame=1);o.keyframe_insert('rotation_euler',frame=1);o.keyframe_insert('location',frame=F(tr_)-2);o.keyframe_insert('rotation_euler',frame=F(tr_)-2)
  o.location=base+Vector((rr.uniform(-.15,.15),rr.uniform(.35,.8),rr.uniform(.0,.12)));o.rotation_euler=(rr.uniform(-.35,.1),rr.uniform(-.1,.1),rr.uniform(-.15,.15));o.keyframe_insert('location',frame=F(tr_));o.keyframe_insert('rotation_euler',frame=F(tr_))
  rb.keyframe_insert('kinematic',frame=F(tr_));rb.kinematic=False;rb.keyframe_insert('kinematic',frame=F(tr_)+1)
 o.select_set(False)
scene.frame_set(1)
try:bpy.ops.ptcache.bake_all(bake=True);print('wall baked',sum(1 for v in REL.values() if v is not None),'of',len(REL),'blocks fall')
except Exception as ex:print('bake skipped',ex)
T_BREACH=max([v for v in REL.values() if v is not None]+[0.])
# ---------------------------------------------------------------------------------------------------------- characters
def load_char(tag,scale=1.):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new(tag+'Root',None);link(root);root.scale=(scale,)*3
 for o in new:
  if o.parent is None:o.parent=root
  if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
 rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
 return dict(root=root,rig=rig,body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices)),scale=scale)
CLIPS={}
for c in ('idle','look','run','climb','kick','fall','cele'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
def set_nla(rig,sched):
 ad=rig.animation_data
 for tr in list(ad.nla_tracks):ad.nla_tracks.remove(tr)
 tr=[ad.nla_tracks.new(),ad.nla_tracks.new()]
 for k,item in enumerate(sched):
  c,a,b,mode=item[:4]
  if b-a<.3:continue
  st=kit.add_strip(tr[k%2],CLIPS[c],F(a)-(5 if k else 0),F(b),mode)
  if len(item)>4 and isinstance(item[4],float):
   sc=item[4];ln=CLIPS[c].frame_range[1]-CLIPS[c].frame_range[0]+1;need=(F(b)-st.frame_start)/(ln*sc);st.action_frame_end=st.action_frame_start+ln-1;st.repeat=1.;st.scale=sc
   if need>=1:st.repeat=need
   else:st.action_frame_end=st.action_frame_start+max(2,need*ln)-1
  st.extrapolation='HOLD' if (k==0 or 'hold' in item) else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
# ---------------------------------------------------------------------------------------------------------- the hero timeline, in the order of the story
T_LAD=26.4;T_TOP=T_LAD+9.0;T_KICK=T_TOP+2.4;T_RUN=T_KICK+2.0;T_WHEEL=T_RUN+3.4;T_UP=T_WHEEL+7.0;T_FLAG=T_UP+4.0
LADX=18.;LADY=28.95;ROOTY=28.6;GATE_OPEN_T=T_UP-2.5
LEO=load_char('Leo');D1=load_char('Defender',1.0)
LEO_LIFT=0
def S_lad(t):return 9.*smooth((t-(T_LAD+.6))/7.8) if T_LAD+.6<=t<=T_LAD+8.4 else (0. if t<T_LAD+.6 else 9.)
# grips on the ladder (hold stepping as in the cliff scene, snapped to the rung grid)
STEP=.33;RUNG=.165
LIMBS={'RH':dict(off=0.,top=1.45,lat=.2),'LF':dict(off=.25,top=.49,lat=-.14),'LH':dict(off=.5,top=1.45,lat=-.2),'RF':dict(off=.75,top=.49,lat=.14)}
def hold_abs(limb,k):
 L=LIMBS[limb];z=L['off']*STEP+k*STEP+L['top'];z=round(z/RUNG)*RUNG;return Vector((LADX+L['lat']*.7,LADY,z))
def climb_target(limb,s):
 L=LIMBS[limb];u=(s-L['off']*STEP)/STEP;k=math.floor(u);f=u-k;h0=hold_abs(limb,k)
 if f<.7:return h0
 w=smooth((f-.7)/.3);p=h0.lerp(hold_abs(limb,k+1),w);p.y-=.10*math.sin(PI*w);return p
# path of Leo in world coordinates
RUN_FROM=Vector((12.,-.5,0.));LAD_BASE=Vector((LADX,ROOTY,0.))
def leo_pos(t):
 if t<22.:   # marches with the front rank
  y=-58.+3.2*(t-2.)-3 if t>2 else -61.;return Vector((12.+(t/22.)*0,max(-61.,y),0.)),PI/2
 if t<T_LAD:
  u=(t-22.)/(T_LAD-22.);p=Vector((12.,-61.+3.2*20-3,0)).lerp(LAD_BASE,smooth(u)*.2+u*.8);return p,math.atan2(LAD_BASE.y-(p.y),LAD_BASE.x-p.x)*0+PI/2
 if t<T_LAD+8.6:return Vector((LADX,ROOTY,S_lad(t))),PI/2
 if t<T_TOP:u=(t-(T_LAD+8.6))/(T_TOP-(T_LAD+8.6));return Vector((LADX,ROOTY+(30.0-ROOTY)*smooth(u),9.0)),PI/2
 if t<T_KICK+1.2:return Vector((LADX,30.0,9.0)),0.
 if t<T_RUN:return Vector((LADX,30.0,9.0)),0.
 if t<T_RUN+3.4:u=(t-T_RUN)/3.4;return Vector((LADX+(5.0-LADX)*u,30.0,9.0)),PI
 if t<T_UP+2.0:return Vector((5.0,30.0,9.0)),PI
 if t<T_UP+2.0+2.6:u=(t-T_UP-2.0)/2.6;return Vector((5.0+(25.3-5.)*smooth(u),30.0,9.0)),0.
 return Vector((25.3,30.,9.)),PI/2
def leo_heading(t):
 if T_TOP<=t<T_KICK-.6:return PI/2*(1-smooth((t-T_TOP)/.8))
 if T_RUN-.5<=t<T_RUN:return PI*smooth((t-(T_RUN-.5))/.5)
 if T_WHEEL<t<T_UP+2.0 and False:return PI
 return leo_pos(t)[1]
set_nla(LEO['rig'],[('run',0,T_LAD-1.0,'loop',3.0/3.4),('run',T_LAD-1.0,T_LAD,'loop'),('idle',T_LAD,T_LAD+8.6,'loop'),('climb',T_LAD+8.6,T_TOP+.5,'loop'),('idle',T_TOP+.5,T_KICK-.4,'loop'),('kick',T_KICK-.4,T_KICK+1.2,'fit'),('idle',T_KICK+1.2,T_RUN,'loop'),('run',T_RUN,T_RUN+3.4,'loop'),('idle',T_RUN+3.4,T_UP+2.0,'loop'),('run',T_UP+2.0,T_UP+4.6,'loop'),('idle',T_UP+4.6,T_FLAG,'loop'),('cele',T_FLAG+3.0,seconds,'fit')])
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
# the defender that gets kicked: stands at x 21 on the wall top, is thrown off when the kick lands
DEF_POS=Vector((21.3,30.,9.));T_THROW=99.
def def_world(t):
 if t<T_THROW:return DEF_POS,PI,'wall'
 p0=DEF_POS+Vector((0,0,0));T=kit.flight_time_to_ground(9.,2.5);p1=Vector((DEF_POS.x+1.5,DEF_POS.y-8.,.15))
 if t<T_THROW+T:return Vector(kit.ballistic_to(p0,p1,T,t-T_THROW)),PI,'air'
 return p1,PI,'ground'
# ---------------------------------------------------------------------------------------------------------- IK for Leo: ladder grips, kick-free arms on the winch wheel and the flag rope
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm'),('LF','LeftLeg'),('RF','RightLeg')):
 tg=bpy.data.objects.new('Grip_'+limb,None);tg.empty_display_size=.06;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb[0]=='L' else -1;pole.location=((.55*sgn,.55,1.0) if limb[1]=='H' else (.45*sgn,-.9,.55))
 c=LEO['rig'].pose.bones['mixamorig:'+bone].constraints.new('IK');c.target=tg;c.pole_target=pole;c.pole_angle=math.radians(-90 if limb[0]=='L' else 90);c.chain_count=2;c.use_stretch=False;IK[limb]=c
WHEEL=Vector((5.0-.65,31.0,9.9));FLAGPOLE=Vector((27.,30.,13.))
def wheel_theta(t):return 1.0*(t-T_WHEEL)
def wheel_hands(t):
 th=wheel_theta(t);R=.33;res={}
 for limb,off,sg in (('LH',0.,-1),('RH',.5,1)):
  ph=((th/1.0+off)%1.0);ang=sg*(-.9+1.0*ph);res[limb]=Vector((WHEEL.x+R*math.cos(ang),WHEEL.y+R*math.sin(ang),WHEEL.z))
 return res
def flag_z(t):return 10.6+5.*smooth((t-T_FLAG)/2.8) if t>T_FLAG else 10.6
SEG={}
def lad_win(t):return T_LAD<=t<=T_LAD+9.0
for f in range(1,frames+1,2):
 t=(f-1)/fps;infl={k:0. for k in IK};pos={}
 if T_LAD-.3<=t<=T_LAD+9.0:
  a=smooth((t-(T_LAD-.3))/.5)*(1-smooth((t-(T_LAD+8.5))/.5));s=S_lad(t)
  for limb in IK:pos[limb]=climb_target(limb,s);infl[limb]=a
 if T_WHEEL-.4<=t<=T_UP+.6 and (infl['LH']==0):
  v=smooth((t-(T_WHEEL-.4))/.5)*(1-smooth((t-T_UP)/.5));wh=wheel_hands(t)
  for limb in ('LH','RH'):pos[limb]=wh[limb];infl[limb]=v
 if T_FLAG-.5<=t<=T_FLAG+3.2 and infl['LH']==0:
  v=smooth((t-(T_FLAG-.5))/.5)*(1-smooth((t-(T_FLAG+3.0))/.4));z=flag_z(t)-.2
  for limb,sg in (('LH',-1),('RH',1)):pos[limb]=Vector((FLAGPOLE.x-.45,29.65+.0*sg+.35*sg,9.+1.1+(.3 if sg>0 else .0)*math.sin((t-T_FLAG)*3)));infl[limb]=v
 for limb in IK:
  if limb in pos:TG[limb].location=pos[limb];TG[limb].keyframe_insert('location',frame=f)
  IK[limb].influence=infl[limb];IK[limb].keyframe_insert('influence',frame=f)
# keys of the hero and the defender (kick time found by the contact solver below)
def key_hero():
 prev=None
 for f in range(1,frames+1,2):
  t=(f-1)/fps;p,_=leo_pos(t);h=leo_heading(t);r=Euler((0,0,h+PI/2))
  if prev is not None:r.make_compatible(prev)
  prev=r.copy();LEO['root'].location=p+Vector((0,0,0));LEO['root'].rotation_euler=r;LEO['root'].keyframe_insert('location',frame=f);LEO['root'].keyframe_insert('rotation_euler',frame=f)
def key_def():
 set_nla(D1['rig'],[('look',0,T_THROW,'loop'),('fall',T_THROW,T_THROW+3.0,'fit','hold')]) if T_THROW<seconds-3.2 else set_nla(D1['rig'],[('look',0,seconds,'loop')])
 prev=None
 for f in range(1,frames+1,2):
  t=(f-1)/fps;p,h,ph=def_world(t);r=Euler((0,0,h+PI/2))
  if ph=='air':r=Euler((2*PI*smooth((t-T_THROW)/kit.flight_time_to_ground(9.,2.5)),0,h+PI/2))
  if prev is not None:r.make_compatible(prev)
  prev=r.copy();D1['root'].location=p;D1['root'].rotation_euler=r;D1['root'].keyframe_insert('location',frame=f);D1['root'].keyframe_insert('rotation_euler',frame=f)
key_hero();key_def()
def lowest(f):
 settle(f);dg=bpy.context.evaluated_depsgraph_get();e=D1['body'].evaluated_get(dg);mw=e.matrix_world;return min((mw@v.co).z for v in list(e.data.vertices)[::4])
OFFV=Vector((0,0,0))
def measure():
 att=LEO;best=None
 for f in range(F(T_KICK-.4),F(T_KICK+1.2)):
  settle(f);hp=att['rig'].matrix_world@att['rig'].pose.bones['mixamorig:RightFoot'].head
  if best is None or hp.z>best[0]:best=(hp.z,f,hp.copy())
 z,f,hp=best;settle(f-2);center=D1['rig'].matrix_world@D1['rig'].pose.bones['mixamorig:Hips'].head;tp,depth=kit.surface_target(D1['body'],hp,center,bpy.context.evaluated_depsgraph_get());return (f-1)/fps,hp,tp,depth
t_imp,hp,tp,depth=measure();res=Vector((tp.x-hp.x,tp.y-hp.y,0));print('KICK1',round(t_imp,2),tuple(round(x,2) for x in hp),tuple(round(x,2) for x in tp))
# shift Leo toward the defender around the impact (smooth ramp) and re-key
_old=leo_pos
def leo_pos(t,_o=_old):
 p,h=_o(t);d=0.
 if t_imp-.3<=t<t_imp:d=smooth((t-(t_imp-.3))/.3)
 elif t_imp<=t<t_imp+.6:d=1-smooth((t-t_imp)/.6)
 return p+res*d,h
key_hero();t2,hp,tp,depth=measure();KICK_ERR=(tp-hp).length;print('KICK2 miss %.0f cm penetration %.0f cm'%(KICK_ERR*100,depth*100))
T_THROW=t_imp+.05;key_def()
# ---------------------------------------------------------------------------------------------------------- the army: 34 real clones and 240 cone soldiers, defenders on the wall
army=[]
def make_clone(i,pos,h,scale,tint):
 root,crig,cbody=kit.clone_character(LEO['rig'],LEO['body'],'Soldier%d'%i,pos,h,scale,tint);crig.animation_data_create();return root,crig
rows,cols=5,7;NEAR=[]
for r in range(rows):
 for c in range(cols):
  if len(NEAR)>=34:break
  NEAR.append(dict(slot=Vector((-27+c*9.+rnd.uniform(-1,1)+(r%2)*3,r*4.5)),k=len(NEAR)))
T_MARCH0,T_MARCH1,T_ASSAULT0,T_ASSAULT1=2.,22.,22.,27.
T_RUSH=GATE_OPEN_T+.8
def front_y(t):
 if t<T_MARCH0:return -58.
 if t<T_MARCH1:return -58.+3.2*(t-T_MARCH0)
 if t<T_ASSAULT0+5:return 6.+(24.-6.)*smooth((t-T_ASSAULT0)/5.)
 return 24.
GOAL=Vector((0,35.));INSIDE=[Vector((rnd.uniform(-22,22),rnd.uniform(34,50))) for _ in range(60)]
class A:pass
agents=[]
for n in NEAR:
 a=A();a.slot=n['slot'];a.k=n['k'];a.p=Vector((a.slot.x,front_y(0)-a.slot.y));a.v=Vector((0,0));a.h=PI/2;a.vmax=rnd.uniform(3.6,4.4);a.t_rush=T_RUSH+rnd.uniform(0,2.5);a.inside=False;a.goal=INSIDE[a.k];a.arr=None;agents.append(a)
TR=[[] for _ in agents]
for fi in range(frames+1):
 t=fi/fps
 for a in agents:
  TR[a.k].append((a.p.x,a.p.y,a.h,a.v.length))
  if t>=a.t_rush:
   if a.p.y>31.5 and abs(a.p.x)<3.5:a.inside=True
   goal=a.goal if a.inside else GOAL
   d=goal-a.p
   if a.inside and (d.length<1.8 or (a.v.length<.15 and a.p.y>36)):
    a.v*=.8
    if a.arr is None:a.arr=t
    continue
   des=d.normalized()*a.vmax
   if not a.inside and a.p.y>16:des.x+=-a.p.x*1.2
  else:
   tgt=Vector((a.slot.x,front_y(t)-a.slot.y));d=tgt-a.p;des=d.normalized()*min(a.vmax,d.length*1.5) if d.length>.05 else Vector((0,0))
  for b in agents:
   if b is a:continue
   r=a.p-b.p;dist=r.length
   if 0<dist<1.6:des+=r/dist*(1.6-dist)*4.
  a.v+=(des-a.v)*min(1,(1/fps)*3.5);a.p+=a.v*(1/fps)
  if a.v.length>.3:a.h=math.atan2(a.v.y,a.v.x)
  for b in agents:
   if b is a:continue
   r=a.p-b.p;dist=r.length
   if 0<dist<.6:a.p+=r/dist*(.6-dist)*.5;b.p-=r/dist*(.6-dist)*.5
print('ARMY arrived',sum(1 for a in agents if a.arr),'of',len(agents))
SOLD=[]
for a in agents:
 root,crig=make_clone(a.k,(a.p.x,a.p.y,0),0,.8+.2*rnd.random(),(rnd.uniform(.75,1.15),rnd.uniform(.6,1.0),rnd.uniform(.45,.9)))
 t0=T_MARCH0;tr_=a.arr or seconds
 set_nla(crig,[('idle',0,t0,'loop'),('run',t0,seconds if not a.arr else tr_,'loop',3.0/3.6)]+([('idle',tr_,seconds,'loop')] if a.arr and tr_<seconds-.4 else []))
 for f in range(1,frames+1,2):
  x,y,h,sp=TR[a.k][f-1];root.location=(x,y,0);root.rotation_euler=(0,0,h+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 SOLD.append(root)
# 240 cone soldiers: marching rows behind the real ones, then a rush through the gate; always visible, keyed every 12 frames
conemesh=None
for i in range(240):
 rk=i//30;col=i%30;sx=-30+col*2.1+rnd.uniform(-.4,.4);sy=-9.-rk*5.5-rnd.uniform(0,1)
 o=prim('cone','Trooper',(sx,sy-60+0,.9),(rnd.uniform(.4,.9),rnd.uniform(.25,.6),rnd.uniform(.2,.5)),scale=(.4,.4,.9),vertices=6,radius1=1,depth=2);h_=prim('sphere','TrooperHead',(sx,sy-60,2.0),(.85,.7,.55),scale=(.28,.28,.28),subdivisions=1);h_.parent=o;h_.location=(0,0,1.15/ .9*0+1.15);h_.scale=(.7,.7,.31)
 for f in range(1,frames+1,12):
  t=(f-1)/fps
  if t<T_MARCH0:y=sy-60
  elif t<T_MARCH1:y=sy-60+3.2*(t-T_MARCH0)
  elif t<T_ASSAULT1:y=min(sy-60+3.2*(T_MARCH1-T_MARCH0)+(18.)*smooth((t-T_ASSAULT0)/5.),22.-rk*1.2)
  else:y=min(sy-60+3.2*(T_MARCH1-T_MARCH0)+18.,22.-rk*1.2)
  x=sx;z=.9+(abs(math.sin(t*5.+i))*.12 if (T_MARCH0<=t<T_MARCH1) else 0)
  if t>T_RUSH+rk*.5:   # through the gate into the courtyard
   u=smooth((t-(T_RUSH+rk*.5+col*.03))/6.);y=min(y,22.-rk*1.2)+(36.+random.Random(i).uniform(0,14)-(22.-rk*1.2))*u;x=sx+(random.Random(i+7).uniform(-18,18)-sx)*u*u
  o.location=(x,y,z);o.keyframe_insert('location',frame=f)
# defenders: 18 on the wall tops (clones) plus cone defenders, standing guard
for k,x in enumerate([x for x in np.arange(-33,34,4.) if not -19<x<-5 and abs(x-21.3)>1.5][:18]):
 root,crig=make_clone(100+k,(x,30,9.),PI,.8+.2*rnd.random(),(.45,.35,.3));set_nla(crig,[('look',0,seconds,'loop')])
# ---------------------------------------------------------------------------------------------------------- stones, arrows, dust
puff=bpy.data.meshes.new('PuffMesh');bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.);bm.to_mesh(puff);bm.free()
def burst(f,x,y,z,size):
 o=bpy.data.objects.new('Puff',puff);link(o);o.data.materials.append(mat('Dust',(.62,.55,.45)))
 for fr,sc,dr in ((f-1,.001,0),(f+4,size,.4),(f+20,size*2.2,2.0),(f+48,.001,3.2)):
  o.location=(x,y,z+dr*.6);o.scale=(sc,sc,sc*.8);o.keyframe_insert('location',frame=fr);o.keyframe_insert('scale',frame=fr)
CATBASE=[]
for ci,(cx,cy) in enumerate(CATS):
 base=prim('cube','CatBase',(cx,cy,.6),(.4,.28,.15),scale=(1.6,1.0,.6));arm=bpy.data.objects.new('CatArm%d'%ci,None);link(arm);arm.location=(cx,cy,1.8)
 beam=prim('cube','CatBeam',(0,0,0),(.45,.3,.15),scale=(.12,3.0,.12),parent=arm);beam.location=(0,-1.2,.0)
 for s_ in (-1,1):prim('cube','CatFrame',(cx+s_*1.3,cy,1.4),(.4,.28,.15),scale=(.12,.12,1.4));prim('cyl','CatWheel',(cx+s_*1.5,cy,.45),(.2,.15,.1),scale=(.45,.45,.1),rot=(0,PI/2,0),vertices=8,radius=1,depth=2)
 CATBASE.append((cx,cy,arm))
 arm.rotation_euler=(math.radians(55),0,0);arm.keyframe_insert('rotation_euler',frame=1)
stones=[]
for v,(tf,ci,ix,iz) in enumerate(VOLLEYS):
 cx,cy,arm=CATBASE[ci];s_=prim('sphere','Stone',(cx,cy+1.9,2.4),(.5,.46,.4),scale=(.5,.5,.5),subdivisions=1)
 p0=Vector((cx,cy+1.2,3.4));p1=Vector((ix,WY0-.4,iz));rest=Vector((ix+rnd.uniform(-1.5,1.5),WY0-1.2-rnd.uniform(0,2),.4))
 s_.location=(cx,cy+1.9,2.4);s_.keyframe_insert('location',frame=1);s_.keyframe_insert('location',frame=F(tf)-1)
 for f in range(F(tf),F(tf+FLIGHT)+1,2):
  q=kit.ballistic_to(p0,p1,FLIGHT,(f-F(tf))/fps);s_.location=q;s_.keyframe_insert('location',frame=f)
 s_.location=rest;s_.keyframe_insert('location',frame=F(tf+FLIGHT)+2)
 arm.rotation_euler=(math.radians(55),0,0);arm.keyframe_insert('rotation_euler',frame=F(tf)-12);arm.rotation_euler=(math.radians(-45),0,0);arm.keyframe_insert('rotation_euler',frame=F(tf)+3);arm.rotation_euler=(math.radians(55),0,0);arm.keyframe_insert('rotation_euler',frame=F(tf)+60)
 burst(F(tf+FLIGHT),ix,WY0-.8,iz,1.2)
for k,(tf,ci,ix,iz) in enumerate(VOLLEYS[:0]):pass
ARROW_T=[14.0,17.0,20.0,23.0,26.0,29.0]
defs=[x for x in np.arange(-33,34,4.) if not -19<x<-5][:18]
for vi,tv in enumerate(ARROW_T):
 for k,x in enumerate(defs[::2][:9]):
  tx=x*.6+rnd.uniform(-10,10);ty=rnd.uniform(5,20)
  a=prim('cyl','Arrow',(x,29.8,9.8),(.45,.35,.2),scale=(.02,.02,.5),vertices=4,radius=1,depth=2);p0=Vector((x,29.8,9.8));p1=Vector((tx,ty,.2));T=2.2+rnd.uniform(0,.4);t0=tv+rnd.uniform(0,1.0)
  a.location=p0;a.rotation_euler=(PI/2,0,0);a.keyframe_insert('location',frame=1);a.keyframe_insert('rotation_euler',frame=1);a.keyframe_insert('location',frame=F(t0)-1);a.keyframe_insert('rotation_euler',frame=F(t0)-1)
  prev=p0
  for f in range(F(t0)+1,F(t0+T)+1,2):
   q=Vector(kit.ballistic_to(p0,p1,T,(f-F(t0))/fps));d=q-prev;prev=q;a.location=q;a.rotation_euler=d.to_track_quat('Z','Y').to_euler() if d.length>1e-4 else a.rotation_euler;a.keyframe_insert('location',frame=f);a.keyframe_insert('rotation_euler',frame=f)
# gate winch, portcullis and flag
wheel=prim('cyl','WinchWheel',WHEEL,(.18,.16,.12),scale=(.33,.33,.03),vertices=14,radius=1,depth=2);prim('cyl','WinchPost',(WHEEL.x,WHEEL.y,9.5),(.18,.16,.12),scale=(.05,.05,.5),vertices=6,radius=1,depth=2)
prim('cube','WinchHouse',(5.0,31.2,11.5),(.4,.3,.22),scale=(2.2,1.6,.2))
pole=prim('cyl','FlagPole',FLAGPOLE,(.5,.5,.5),scale=(.07,.07,4),vertices=6,radius=1,depth=2)
flag=prim('cube','Flag',(FLAGPOLE.x-1.0,FLAGPOLE.y,10.6),(.8,.12,.12),scale=(1.0,.03,.55));wv=flag.modifiers.new('Flap','WAVE');wv.height=.15;wv.width=1.6;wv.speed=.3;wv.use_normal=True
for f in range(1,frames+1,2):
 t=(f-1)/fps;wheel.rotation_euler=(0,0,wheel_theta(t) if T_WHEEL<=t<=T_UP else (wheel_theta(T_UP) if t>T_UP else 0));wheel.keyframe_insert('rotation_euler',frame=f)
 port.location=(0,30,6.2*smooth((t-GATE_OPEN_T)/2.6) if t>GATE_OPEN_T else 0);port.keyframe_insert('location',frame=f)
 flag.location=(FLAGPOLE.x-1.0,FLAGPOLE.y,flag_z(t));flag.keyframe_insert('location',frame=f)
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.data.energy=3.4;sun.data.color=(1,.82,.62);sun.rotation_euler=(math.radians(48),0,math.radians(-30))
scene.world=bpy.data.worlds.new('Dawn');scene.world.color=(.85,.66,.52)
for i in range(120):prim('cone','Pine',(rnd.choice((-1,1))*rnd.uniform(40,120),rnd.uniform(-90,20),3.5),(.08,.26,.14),scale=(1.6,1.6,3.5),vertices=7,radius1=1,depth=2)
for i in range(18):prim('cone','Hill',(rnd.uniform(-180,180),rnd.uniform(110,200),rnd.uniform(10,30)),(.4,.42,.34),scale=(rnd.uniform(30,60),rnd.uniform(30,60),rnd.uniform(20,50)),vertices=7,radius1=1,depth=2)
# tents of the camp
for i in range(10):x=rnd.uniform(-45,45);y=rnd.uniform(-95,-70);prim('cone','Tent',(x,y,1.5),(.75,.62,.4),scale=(2.2,2.2,1.5),vertices=6,radius1=1,depth=2)
# ---------------------------------------------------------------------------------------------------------- cameras
def army_c(t):
 xs=[TR[a.k][min(frames,int(t*fps))] for a in agents];x=sum(v[0] for v in xs)/len(xs);y=sum(v[1] for v in xs)/len(xs);return Vector((x,y,1.2))
CUTS=[('1 Dawn over the field',0,5.0),('2 The catapults',5.0,10.0),('3 The army marches',10.0,16.0),('4 The wall takes hits',16.0,T_BREACH+2.5),('5 The breach',T_BREACH+2.5,26.4),('6 Leo at the ladder',26.4,T_LAD+4.0),('7 The climb',T_LAD+4.0,T_TOP),('8 The kick',T_TOP,T_KICK+2.2),
 ('9 Along the wall',T_KICK+2.2,T_WHEEL),('10 The winch',T_WHEEL,GATE_OPEN_T),('11 The gate rises',GATE_OPEN_T,GATE_OPEN_T+4.0),('12 The army floods in',GATE_OPEN_T+4.0,T_FLAG-.5),('13 The banner',T_FLAG-.5,T_FLAG+3.5),('14 Victory',T_FLAG+3.5,seconds)]
cams=[];CAMKEYS=[]
for k,(name,a,b) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=3000;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(min(b,seconds))+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);L,_=leo_pos(t);lh=L+Vector((0,0,1.0));ac=army_c(t);cam.data.lens=28
  if k==0:p=Vector((-60+30*u,-95,18));q=Vector((0,0,6));cam.data.lens=22
  elif k==1:p=Vector((-35,-26,5.5));q=Vector((-15+u*5,-12,2.5));cam.data.lens=28
  elif k==2:p=ac+Vector((-26,-18,6));q=ac+Vector((8,6,1));cam.data.lens=28
  elif k==3:p=Vector((-16,0,5));q=Vector((-12,WY0,5.5));cam.data.lens=24
  elif k==4:p=Vector((-8,10,6));q=Vector((-12,WY0,3));cam.data.lens=24
  elif k==5:p=lh+Vector((-5,-5,1.5));q=lh;cam.data.lens=34
  elif k==6:p=Vector((LADX-7,LADY-7,max(2.,L.z)+1));q=lh+Vector((0,0,.5));cam.data.lens=32
  elif k==7:p=Vector((LADX-5,26.0,9.8));q=(L+DEF_POS)/2+Vector((0,0,1.0));cam.data.lens=34
  elif k==8:p=Vector((L.x+9,24,9.5));q=lh;cam.data.lens=30
  elif k==9:p=Vector((WHEEL.x-3.0,34.6,13.0));q=Vector((WHEEL.x,31,10.4));cam.data.lens=34
  elif k==10:p=Vector((0,18,3));q=Vector((0,30,4));cam.data.lens=24
  elif k==11:p=Vector((0,8,8));q=Vector((0,32,1.5));cam.data.lens=24
  elif k==12:p=Vector((21,22,12.5));q=Vector((FLAGPOLE.x-1,30,flag_z(t)));cam.data.lens=34
  else:p=Vector((14+8*u,16,14+8*u));q=lh+Vector((0,0,4));cam.data.lens=30
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
FAMILY=set()
for d_ in (LEO,D1):FAMILY|=kit._family(d_['root'])
for r_ in SOLD:FAMILY|=kit._family(r_)
for o in bpy.data.objects:
 if o.name.startswith(('Trooper','Soldier','Stone','Arrow','Puff','Fan','Block')):FAMILY.add(o.name)
CAND=[(0,0,1.5),(0,0,3.),(0,0,5.),(0,-4,3.),(0,4,3.),(0,0,8.),(0,-8,6.),(0,0,14.)]
offs={}
for k,cam,aim,f in CAMKEYS:
 settle(f);dg=bpy.context.evaluated_depsgraph_get();p=Vector(cam.location);q=Vector(aim.location);np_,idx=kit.clear_view(scene,dg,p,q,FAMILY,CAND);offs[(k,f)]=np_-p
for k in set(a for a,b in offs):
 fs=sorted(f for a,f in offs if a==k)
 for i,f in enumerate(fs):
  win=[offs[(k,g)] for g in fs[max(0,i-3):i+4]];offs[(k,f)]=Vector((sum(v.x for v in win)/len(win),sum(v.y for v in win)/len(win),max(v.z for v in win)))
for k,cam,aim,f in CAMKEYS:
 o=offs[(k,f)]
 if o.length>1e-6:settle(f);cam.location=Vector(cam.location)+o;cam.keyframe_insert('location',frame=f)
print('CAMERAS adjusted',sum(1 for v in offs.values() if v.length>1e-6),'of',len(offs))
# ---------------------------------------------------------------------------------------------------------- audit
issues=kit.persistence_audit(scene)
issues+=kit.camera_checks(scene,[LEO['root']]+SOLD[:8])
if KICK_ERR>.20:issues.append('AUDIT contact: the kick misses the defender by %.0f cm'%(KICK_ERR*100))
if depth>.06:issues.append('AUDIT penetration: the kick goes %.0f cm inside the defender'%(depth*100))
worst={}
for f in range(1,frames+1,4):
 t=(f-1)/fps
 if not (T_LAD<=t<=T_LAD+8.8):continue
 settle(f)
 for limb,bone in (('RH','RightForeArm'),('LH','LeftForeArm'),('LF','LeftLeg'),('RF','RightLeg')):
  c=IK[limb];
  if c.influence<.99:continue
  tail=LEO['rig'].matrix_world@LEO['rig'].pose.bones['mixamorig:'+bone].tail;d=(tail-TG[limb].matrix_world.translation).length
  if d>worst.get(limb,(0,0))[0]:worst[limb]=(d,t)
for limb,(d,t) in worst.items():
 if d>.07:issues.append('AUDIT grip: %s misses its rung by %.0f cm at t=%.1f s'%(limb,d*100,t))
print('GRIP',{k:(round(v[0]*100,1),round(v[1],1)) for k,v in worst.items()})
ARR_=[a.arr for a in agents if a.arr]
if len(ARR_)<len(agents)-2:issues.append('AUDIT army: only %d of %d clones reached the courtyard'%(len(ARR_),len(agents)))
for i in issues:print(i)
print('AUDIT',len(issues),'issues');print('TIMES breach %.1f ladder %.1f top %.1f kick %.1f winch %.1f gate %.1f flag %.1f'%(T_BREACH,T_LAD,T_TOP,t_imp,T_WHEEL,GATE_OPEN_T,T_FLAG))
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_siege');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(6)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
def at(arr,t,x,g=1.):
 i=int(t*SR)
 if 0<=i<len(arr):
  n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
thump=lambda n_=.35:(lambda k:np.sin(2*PI*(70-40*k)*k)*np.exp(-k*14)+lp(nr.standard_normal(len(k)),12)*np.exp(-k*18))(np.arange(int(n_*SR))/SR)
whoosh=lambda n_=2.4:(lambda k:lp(nr.standard_normal(len(k)),60)*np.sin(np.pi*k/n_)**2*.5)(np.arange(int(n_*SR))/SR)
crash=lambda n_=1.2:(lambda k:(lp(nr.standard_normal(len(k)),40)*np.exp(-k*3)+np.sin(2*PI*(50-20*k)*k)*np.exp(-k*4)))(np.arange(int(n_*SR))/SR)
cat=np.zeros(N_+SR*4);imp=np.zeros(N_+SR*4)
for tf,ci,ix,iz in VOLLEYS:
 at(cat,tf,thump(),1.);at(cat,tf+.3,whoosh(),.5);at(imp,tf+FLIGHT,crash(.9),.8)
for o_,c_,r_ in BLOCKS:
 t_=REL[(c_,r_)]
 if t_:at(imp,t_+.2,crash(.5),.15)
at(imp,t_imp,thump(.5),1.2)
arrow=np.zeros(N_+SR*3)
for tv in ARROW_T:
 for k in range(9):at(arrow,tv+rnd.uniform(0,1.),whoosh(.5),.25)
crowd=lp(nr.standard_normal(N_),9)*(.12+.8*np.clip((tt-T_RUSH)/3,0,1))+lp(nr.standard_normal(N_),30)*.1
foot=lp(nr.standard_normal(N_),300)*np.clip((tt-2)/3,0,1)*np.clip((T_ASSAULT1-tt)/3,0,1)*.3
chains=np.zeros(N_+SR*3);n=int(3*SR);k=np.arange(n)/SR;at(chains,GATE_OPEN_T,lp(nr.standard_normal(n),6)*(np.sin(k*40)>0)*.6*np.minimum(k/.3,1))
horn=np.zeros(N_);hn=lambda t0,d,f:at(horn,t0,(np.sin(2*PI*f*np.arange(int(d*SR))/SR)+.5*np.sin(4*PI*f*np.arange(int(d*SR))/SR))*np.minimum(np.arange(int(d*SR))/SR/.1,1)*np.minimum((d-np.arange(int(d*SR))/SR)/.2,1))
hn(1.0,2.0,196.);hn(T_RUSH,2.4,233.);hn(T_FLAG+2.6,2.5,262.)
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=T_FLAG+2 else minor[ci%4];vol=.45 if t0<6 else .8
 for j,f0 in enumerate(chord):at(music,t0,note(f0,2.6,vol*.5))
 if 6<=t0<=T_FLAG+2:
  for b in range(5):at(music,t0+b*.5,(lambda kt:np.sin(2*PI*(55*kt-90*kt**2))*np.exp(-kt*20))(np.arange(int(.2*SR))/SR),1.4)
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('catapults.wav',cat[:N_],.9),wav('impacts.wav',imp[:N_],.95),wav('arrows.wav',arrow[:N_],.5),wav('army.wav',crowd+foot,.7),wav('gate.wav',chains[:N_],.6),wav('horns.wav',horn,.5),wav('music.wav',music,.5)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('catapults','impacts','arrows','army','gate chains','horns','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('SIEGE_DONE',frames,'frames')
