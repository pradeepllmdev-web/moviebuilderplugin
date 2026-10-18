"""Blender script: 'The Great Escape' - Leo escapes across the roofs of a speeding prison train (54 s).

blender -b --disable-autoexec --python train_scene.py -- <ship_assets_dir> <out.blend> [seconds=54]

Leo wakes tied on the last wagon, runs forward over the roofs with two guard lions behind him, jumps the gaps between wagons (ballistic arcs from flight time, foot tuck, landing dip),
ducks under a low gantry that is placed exactly where he is when the train reaches it, kicks the first guard off the train (contact solver with skin targets, the guard flies on a real
projectile path and tumbles), turns a brake wheel with both hands (IK hands follow the rim) to release the coupling so the rear cars, with the second guard, fall behind, runs to the
locomotive and leaps from the bridge into the river. The train moves, the scenery is static, so everything is in world space and checked against the train position.
Clips come from build_ship_assets.py (idle, run, jump, kick, getup, fall, look, cele)."""
import bpy,math,random,sys,os,wave,bmesh
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 54.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(3)
F=lambda t:1+int(round(t*fps));smooth=kit.smooth;PI=math.pi
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
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color,emit))
 if parent:o.parent=parent
 return o
def hide_keys(o,windows):
 last=None
 for f in range(1,frames+1):
  v=any(a<=(f-1)/fps<b for a,b in windows)
  if v!=last:
   for prop in ('hide_viewport','hide_render'):setattr(o,prop,not v);o.keyframe_insert(prop,frame=f)
   last=v
# ---------------------------------------------------------------------------------------------------------- train kinematics (world x of the front group, the rear group after the coupling is released)
ROOF=3.2;V0=20.
XF=[0.]
for i in range(frames):XF.append(XF[-1]+V0*smooth(i/fps/4.)/fps)
def Xfun(t):
 i=min(frames-1e-6,max(0.,t*fps));lo=int(i);f=i-lo;return XF[lo]*(1-f)+XF[lo+1]*f
def vfun(t):return V0*smooth(t/4.)
GAPS=[(-63.,-61.6),(-50.6,-49.2),(-38.2,-36.8),(-25.8,-24.4),(-13.4,-12.),(-1.,.4)]
LEG1=kit.run_path(6.6,-69.6,-33.4,GAPS[:3],4.2);T_ARR=LEG1[-1][2]
WHEEL=Vector((-32.6,0,ROOF+.75));T_THROW0=T_ARR+1.6;T_D=T_THROW0+7.0;T_LEG2=T_D+1.0
LEG2=kit.run_path(T_LEG2,-33.4,7.2,GAPS[3:],4.2);T_END2=LEG2[-1][2]
T_LEAP=40.0;LEAP_X=7.2
def delta(t):
 s=t-T_D;return 0. if s<=0 else V0*(s-(1-math.exp(-.25*s))/.25)
def Xrear(t):return Xfun(t)-delta(t)
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
 return dict(root=root,rig=rig,body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices)),scale=scale)
CLIPS={}
for c in ('idle','run','jump','kick','getup','fall','look','cele'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
FIG={'leo':load_char('Leo'),'ga':load_char('GuardA',1.1,(.32,.27,.25)),'gb':load_char('GuardB',1.1,(.45,.3,.22))}
def set_nla(key,sched):
 rig=FIG[key]['rig'];ad=rig.animation_data
 for tr in list(ad.nla_tracks):ad.nla_tracks.remove(tr)
 tracks=[ad.nla_tracks.new(),ad.nla_tracks.new()]
 for k,item in enumerate(sched):
  c,a,b,mode=item[:4];st=kit.add_strip(tracks[k%2],CLIPS[c],F(a)-(5 if k else 0),F(b),mode);st.extrapolation='HOLD' if (k==0 or 'hold' in item[4:]) else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
def legs_sched(segs,jump_pre=.3,jump_post=.2):
 out_=[];t_prev=None
 for i,(kind,a,b,x0,x1) in enumerate(segs):
  if kind=='run':
   a2=a+(jump_post if i and segs[i-1][0]=='jump' else 0);b2=b-(jump_pre if i+1<len(segs) and segs[i+1][0]=='jump' else 0)
   if b2-a2>.3:out_.append(('run',a2,b2,'loop'))
  else:out_.append(('jump',a-jump_pre,b+jump_post,'fit'))
 return out_
# ---------------------------------------------------------------------------------------------------------- the story in train coordinates (local x forward, y left)
T_THROW=99.        # time guard A is thrown: set from the measured impact (99 keeps him standing while the kick is measured)
LANE=0.
def leo_local(t):
 if t<6.6:return -69.6
 if t<=T_ARR:return kit.path_x(LEG1,t)
 if t<T_LEG2:return -33.4
 if t<=T_END2:return kit.path_x(LEG2,t)
 return LEAP_X
GA_SEGS=kit.run_path(7.4,-73.0,-34.3,GAPS[:3],4.5);GB_SEGS=kit.run_path(8.4,-75.0,-39.0,GAPS[:2],4.2)
T_GB_JUMP=T_D+1.3
def leo_heading(t):
 if t<T_ARR+.2:return 0.
 if t<T_ARR+.8:return PI*smooth((t-T_ARR-.2)/.6)
 if t<T_THROW0+1.2:return PI
 if t<T_THROW0+1.8:return PI*(1-smooth((t-T_THROW0-1.2)/.6))
 return 0.
def flights(segs):return [(a,b) for k,a,b,x0,x1 in segs if k=='jump']
FL={'leo':flights(LEG1)+flights(LEG2),'ga':flights(GA_SEGS),'gb':flights(GB_SEGS)}
def fl_state(key,t):
 """(z above the roof, pitch, tuck) of the pose layers of a jump for this fighter at time t."""
 for a,b in FL[key]:
  if a-.35<=t<=b+.35:
   p=kit.jump_profile(t,a,b);z=0.
   if a<=t<=b:z=kit.ballistic((t-a)/(b-a),kit.flight_apex(b-a))
   return z+p['dz'],p['pitch'],p['tuck']
 return 0.,0.,0.
def X_BR_time():
 best=None
 for i in range(int(6*fps),int(14*fps)):
  t=i/fps;x=Xfun(t)+leo_local(t)
  if abs(x-(Xfun(12.2)+leo_local(12.2)))<.02:best=t
 return 12.2
T_BR=12.2;X_BR=Xfun(T_BR)+leo_local(T_BR)
def duck(key,t):
 """crouch while passing under the gantry (world x of the fighter near X_BR); pitch and drop of the root."""
 x=Xfun(t)+(leo_local(t) if key=='leo' else kit.path_x(GA_SEGS if key=='ga' else GB_SEGS,t))
 if key=='gb' and t>T_D:x=Xrear(t)+kit.path_x(GB_SEGS,t)
 d=abs(x-X_BR);u=1-smooth((d-.5)/1.1)
 return -.3*u,.6*u
# thrown guard (a real projectile) and falling guard (b)
GA_STOP=-34.3
def ga_world(t):
 """world position and spin of guard A: runs and waits on the roof, is kicked at T_THROW, flies, lands and slides."""
 if t<T_THROW:return Vector((Xfun(t)+(GA_STOP if t>GA_SEGS[-1][2] else kit.path_x(GA_SEGS,t)),0,ROOF)),0.,'roof'
 p0=Vector((Xfun(T_THROW)+GA_STOP,0,ROOF));vz=3.;T=kit.flight_time_to_ground(ROOF+.0,vz);p1=Vector((p0.x+vfun(T_THROW)*1.0*T,p0.y+6.5,.12))
 if t<T_THROW+T:
  q=kit.ballistic_to(p0,p1,T,t-T_THROW);return Vector(q),2*PI*smooth((t-T_THROW)/T),'air'
 s=t-T_THROW-T;return Vector((p1.x+vfun(t)*.35*(1-math.exp(-2.*s))/2.,p1.y,.12)),0.,'ground'
def gb_world(t):
 if t<T_D:return Vector((Xfun(t)+kit.path_x(GB_SEGS,t),0,ROOF)),'roof'
 if t<T_GB_JUMP-.6:return Vector((Xrear(t)-39.0,0,ROOF)),'roof'
 if t<T_GB_JUMP:u=smooth((t-(T_GB_JUMP-.6))/.6);return Vector((Xrear(t)-39.0+.55*u,0,ROOF)),'roof'
 p0=Vector((Xrear(T_GB_JUMP)-38.45,0,ROOF));vz=2.;T=kit.flight_time_to_ground(ROOF,vz);p1=Vector((p0.x+(vfun(T_GB_JUMP)*.93+2.)*T,.3,.12))
 if t<T_GB_JUMP+T:return Vector(kit.ballistic_to(p0,p1,T,t-T_GB_JUMP)),'air'
 s=t-T_GB_JUMP-T;return Vector((p1.x+vfun(t)*.25*(1-math.exp(-2.*s))/2.,p1.y,.12)),'ground'
def leo_world(t):
 x=leo_local(t);z=ROOF;y=LANE
 if t<6.6:return Vector((Xfun(t)-69.6,0,ROOF))
 dz,pitch,tuck=fl_state('leo',t);z+=dz;dd,dp=duck('leo',t);z+=dd
 if T_LEAP<=t<T_LEAP+1.9:
  p0=Vector((Xfun(T_LEAP)+LEAP_X,0,ROOF));T=kit.flight_time_to_ground(ROOF+8.,3.);p1=Vector((p0.x+V0*T,7.5,-7.8));return Vector(kit.ballistic_to(p0,p1,T,t-T_LEAP))
 if t>=T_LEAP+1.9:
  p0=Vector((Xfun(T_LEAP)+LEAP_X,0,ROOF));T=kit.flight_time_to_ground(ROOF+8.,3.);return Vector((p0.x+V0*T,7.5,-7.8))
 return Vector((Xfun(t)+x,y,z))
def heading_of(key,t):
 if key=='leo':
  if t>=T_LEAP:return PI/2
  return leo_heading(t)
 return 0.
def rot_of(key,t):
 h=heading_of(key,t);pitch=0.
 if key in FL:
  _,pj,_=fl_state(key,t);pitch+=pj
 if key=='leo':
  if t<6.0:pitch=0.
  dd,dp=duck('leo',t);pitch+=dp
 if key=='ga':
  dd,dp=duck('ga',t);pitch+=dp
  if t>=T_THROW:
   w,spin,ph=ga_world(t);return Euler((spin,0,PI/2))
 if key=='gb':
  dd,dp=duck('gb',t);pitch+=dp
  if t>=T_GB_JUMP:return Euler((.5*math.sin(2*(t-T_GB_JUMP)),0,PI/2))
 return Euler((pitch,0,h+PI/2))
def world_of(key,t):
 if key=='leo':return leo_world(t)
 if key=='ga':
  w,s,ph=ga_world(t)
  if ph=='roof':
   dz,_,_=fl_state('ga',t);dd,dp=duck('ga',t);w.z+=dz+dd
  return w
 w,ph=gb_world(t)
 if ph=='roof' and t<T_GB_JUMP:
  dz,_,_=fl_state('gb',t);dd,dp=duck('gb',t);w.z+=dz+dd
 return w
OFF=[];ZL={'leo':{},'ga':{},'gb':{}}
def apply_all():
 for key in FIG:
  root=FIG[key]['root'];prev=None
  for f in range(1,frames+1,2):
   t=(f-1)/fps;p=world_of(key,t)+Vector((0,0,ZL[key].get(f,0.)))
   if key=='leo':
    for t0,tp,t1,v in OFF:
     if t0<=t<tp:p+=v*smooth((t-t0)/(tp-t0))
     elif tp<=t<t1:p+=v*(1-smooth((t-tp)/(t1-tp)))
   r=rot_of(key,t)
   if prev is not None:r.make_compatible(prev)
   prev=r.copy();root.location=p;root.rotation_euler=r;root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
# animation schedules
def sched_leo():
 s=[('getup',3.0,6.0,'fit'),('idle',6.0,6.6,'loop')]+legs_sched(LEG1)
 s+=[('idle',T_ARR+.0,T_THROW0-.4,'loop'),('kick',T_THROW0-.4,T_THROW0+1.1,'fit'),('idle',T_THROW0+1.1,T_LEG2,'loop')]
 s+=legs_sched(LEG2);s+=[('look',T_END2,T_LEAP-1.0,'loop'),('jump',T_LEAP-.3,T_LEAP+1.9,'fit'),('idle',T_LEAP+1.9,T_LEAP+2.6,'loop'),('cele',T_LEAP+2.6,seconds,'fit')]
 return s
def sched_ga():
 T=kit.flight_time_to_ground(ROOF,3.)
 return [('look',0,7.4,'loop')]+legs_sched(GA_SEGS)+[('idle',GA_SEGS[-1][2],T_THROW,'loop'),('jump',T_THROW,T_THROW+T,'fit'),('fall',T_THROW+T,T_THROW+T+3.0,'fit','hold')]
def sched_gb():
 T=kit.flight_time_to_ground(ROOF,2.)
 return [('look',0,8.4,'loop')]+legs_sched(GB_SEGS)+[('idle',GB_SEGS[-1][2],T_D+.6,'loop'),('run',T_D+.6,T_GB_JUMP-.3,'loop'),('jump',T_GB_JUMP-.3,T_GB_JUMP+T,'fit'),('fall',T_GB_JUMP+T,T_GB_JUMP+T+3.0,'fit','hold')]
set_nla('leo',sched_leo());set_nla('ga',sched_ga());set_nla('gb',sched_gb());apply_all()
# ---------------------------------------------------------------------------------------------------------- IK: tucked feet in flights, both hands on the brake wheel
def make_ik(key,hands):
 rig=FIG[key]['rig'];root=FIG[key]['root'];IK={};TG={}
 for limb,bone in ((('LH','LeftForeArm'),('RH','RightForeArm'),('LF','LeftLeg'),('RF','RightLeg')) if hands else (('LF','LeftLeg'),('RF','RightLeg'))):
  tg=bpy.data.objects.new('Grip_%s_%s'%(key,limb),None);tg.empty_display_size=.06;link(tg);TG[limb]=tg
  pole=bpy.data.objects.new('Pole_%s_%s'%(key,limb),None);link(pole);pole.parent=root;sgn=1 if limb[0]=='L' else -1;pole.location=((.55*sgn,.55,1.0) if limb[1]=='H' else (.45*sgn,-.9,.55))
  c=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');c.target=tg;c.pole_target=pole;c.pole_angle=math.radians(-90 if limb[0]=='L' else 90);c.chain_count=2;c.use_stretch=False;IK[limb]=c
 return IK,TG
IKS={};TGS={}
for k_ in FIG:IKS[k_],TGS[k_]=make_ik(k_,k_=='leo')
WHEEL_WIN=(T_THROW0+2.0,T_D)
def wheel_theta(t):return 1.0*(t-WHEEL_WIN[0])
def wheel_hands(t):
 """each hand pulls the rim through one radian, then regrabs; the other hand is half a cycle behind"""
 th=wheel_theta(t);R=.33;res={}
 for limb,off,sg in (('LH',0.,-1),('RH',.5,1)):
  ph=((th/1.0+off)%1.0);a=sg*(.9-1.0*ph)*(-1)+0;ang=sg*(-.9+1.0*ph)   # angle measured from +x (towards Leo) around the wheel
  res[limb]=Vector((WHEEL.x-R*math.cos(ang),WHEEL.y+R*math.sin(ang),WHEEL.z))
 return res
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for key in FIG:
  w=world_of(key,t);sc=FIG[key]['scale'];h=heading_of(key,t);fw=Vector((math.cos(h),math.sin(h),0));lf=Vector((-math.sin(h),math.cos(h),0))
  dz,pj,tuck=fl_state(key,t) if key in FL else (0,0,0)
  if key=='ga' and t>=T_THROW:tuck=1.0 if ga_world(t)[2]=='air' else 0.
  if key=='gb' and t>=T_GB_JUMP:tuck=1.0 if gb_world(t)[1]=='air' else 0.
  for side,sg in (('L',1),('R',-1)):
   TGS[key][side+'F'].location=w+lf*sg*.14*sc+fw*.05*sc+Vector((0,0,.12*sc+.30*sc*tuck));TGS[key][side+'F'].keyframe_insert('location',frame=f)
   IKS[key][side+'F'].influence=smooth(tuck/.2) if tuck<.2 else 1.;IKS[key][side+'F'].keyframe_insert('influence',frame=f)
 hv=smooth_ = smooth((t-WHEEL_WIN[0])/.4)*(1-smooth((t-(WHEEL_WIN[1]-.3))/.4)) if WHEEL_WIN[0]<=t<=WHEEL_WIN[1]+.2 else 0.
 hd=wheel_hands(t)
 for limb in ('LH','RH'):
  wp=hd[limb];IKS['leo'][limb].influence=hv;IKS['leo'][limb].keyframe_insert('influence',frame=f);TGS['leo'][limb].location=Vector((Xfun(t),0,0))+wp;TGS['leo'][limb].keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- the contact solver (kick)
def bone_w(rig,name):
 return rig.matrix_world@rig.pose.bones['mixamorig:'+name].head
def settle(f):
 scene.frame_set(f);bpy.context.view_layer.update()
def measure_kick():
 att=FIG['leo'];best=None
 for f in range(F(T_THROW0-.4),F(T_THROW0+1.1)):
  settle(f);fwd=Vector((0,-1,0));fwd.rotate(att['root'].rotation_euler);hp=bone_w(att['rig'],'RightFoot');ext=hp.z   # a kick lands at the top of the leg swing, so the instant is the highest foot
  if best is None or ext>best[0]:best=(ext,f,hp.copy())
 ext,f,hp=best;t=(f-1)/fps;settle(f-2);center=bone_w(FIG['ga']['rig'],'Hips');tp,depth=kit.surface_target(FIG['ga']['body'],hp,center,bpy.context.evaluated_depsgraph_get());return t,hp,tp,depth
t_imp,hp,tp,depth=measure_kick();print('KICK1',round(t_imp,2),tuple(round(x,2) for x in hp),tuple(round(x,2) for x in tp));OFF.append((t_imp-.3,t_imp,t_imp+.6,Vector((tp.x-hp.x,tp.y-hp.y,0))));apply_all()
t_imp,hp,tp,depth=measure_kick();KICK_ERR=(tp-hp).length;print('KICK2',tuple(round(x,2) for x in hp),tuple(round(x,2) for x in tp));KICK_DEPTH=depth;print('KICK t=%.2f miss %.0f cm penetration %.0f cm'%(t_imp,KICK_ERR*100,depth*100))
T_THROW=t_imp+.05;set_nla('ga',sched_ga());apply_all()
# lying guards rest on the ground
def lowest(key,f):
 settle(f);dg=bpy.context.evaluated_depsgraph_get();e=FIG[key]['body'].evaluated_get(dg);mw=e.matrix_world;return min((mw@v.co).z for v in list(e.data.vertices)[::4])
low={f:lowest('leo',f) for f in range(1,F(T_LEAP-1.0),2) if not any(a-.35<=(f-1)/fps<=b+.35 for a,b in FL['leo'])};ZL['leo'].update(kit.ground_lift(low,ROOF,.01,.8,1))
low={f:lowest('ga',f) for f in range(F(7.0),F(T_THROW-.2),2) if not any(a-.35<=(f-1)/fps<=b+.35 for a,b in FL['ga'])};ZL['ga'].update(kit.ground_lift(low,ROOF,.01,.8,1))
for key,t0 in (('ga',T_THROW),('gb',T_GB_JUMP)):
 low={f:lowest(key,f) for f in range(F(t0+1.0),frames+1,4)};ZL[key].update(kit.ground_lift(low,0.,.01,1.5,1))
apply_all()
# ---------------------------------------------------------------------------------------------------------- the world
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.data.energy=3.6;sun.data.color=(1,.78,.55);sun.rotation_euler=(math.radians(50),0,math.radians(70))
scene.world=bpy.data.worlds.new('Dawn');scene.world.color=(.8,.62,.5)
XMAX=Xfun(seconds)+120.
bpy.ops.mesh.primitive_plane_add(size=1,location=(XMAX/2-60,0,-.1));g=bpy.context.object;g.name='Ground';g.scale=(XMAX+300,260,1);g.data.materials.append(mat('Ground',(.34,.42,.2)))
XV0=Xfun(37.5)+9.;XV1=XV0+95.
# valley under the bridge: the ground has a hole, floor and water below
g.scale=(XV0+200,260,1);g.location=((XV0-200)/2,0,-.1)
g2=prim('cube','GroundAfter',(XV1+(XMAX+300-XV1)/2,0,-.6),(.34,.42,.2),scale=((XMAX+300-XV1)/2,130,.5))
prim('cube','ValleyFloor',((XV0+XV1)/2,0,-8.6),(.5,.42,.3),scale=((XV1-XV0)/2+2,130,.4));prim('cube','Water',((XV0+XV1)/2,0,-8.0),(.12,.3,.42),scale=((XV1-XV0)/2+2,20,.05))
for s_ in (-1,1):prim('cube','ValleyWall',((XV0+XV1)/2,s_*130,-4),(.45,.38,.3),scale=((XV1-XV0)/2+2,.5,5))
for xe in (XV0,XV1):prim('cube','Abutment',(xe,0,-4.2),(.45,.38,.3),scale=(.5,130,4.5))
prim('cube','BridgeDeck',((XV0+XV1)/2,0,-.35),(.3,.3,.32),scale=((XV1-XV0)/2,2.8,.25))
for x in np.arange(XV0+10,XV1,15.):prim('cube','Pier',(x,0,-4.4),(.4,.38,.34),scale=(.8,2.2,4.1))
for s_ in (-1,1):
 prim('cube','BridgeRail',((XV0+XV1)/2,s_*2.7,.7),(.5,.5,.5),scale=((XV1-XV0)/2,.05,.05))
 for x in np.arange(XV0,XV1,6.):prim('cube','RailPost',(x,s_*2.7,.4),(.5,.5,.5),scale=(.05,.05,.4))
for s_ in (-.72,.72):prim('cube','Rail',(XMAX/2-60,s_,.12),(.5,.5,.55),scale=((XMAX+300)/2,.04,.1))
prim('cube','Ballast',(XMAX/2-60,0,.02),(.28,.25,.22),scale=((XMAX+300)/2,1.6,.06))
for x in np.arange(-150.,XMAX,45.):
 for s_ in (-1,1):
  if XV0-3<x<XV1+3:continue
  prim('cyl','Pole',(x,s_*4.5,3.2),(.33,.24,.14),scale=(.08,.08,3.2),vertices=5,radius=1,depth=2);prim('cube','PoleArm',(x,s_*4.5,6.2),(.33,.24,.14),scale=(.04,.9,.05))
for i in range(520):
 x=rnd.uniform(-150,XMAX);y=rnd.choice((-1,1))*rnd.uniform(9,90)
 if XV0-10<x<XV1+10:continue
 prim('cone','Tree',(x,y,2.5),(.1,.3,.12),scale=(1.4,1.4,2.6),vertices=7,radius1=1,depth=2);prim('cyl','Trunk',(x,y,.5),(.3,.2,.1),scale=(.15,.15,.5),vertices=5,radius=1,depth=2)
for i in range(30):prim('cone','Hill',(rnd.uniform(-100,XMAX),rnd.choice((-1,1))*rnd.uniform(110,240),rnd.uniform(8,26)),(.38,.4,.3),scale=(rnd.uniform(30,70),rnd.uniform(30,60),rnd.uniform(16,50)),vertices=7,radius1=1,depth=2)
# the gantry Leo and the guards must duck under
for s_ in (-1,1):prim('cube','GantryPost',(X_BR,s_*2.6,(ROOF+1.4)/2),(.4,.36,.32),scale=(.35,.35,(ROOF+1.4)/2))
prim('cube','GantryBeam',(X_BR,0,ROOF+1.25),(.38,.34,.3),scale=(.6,3.0,.25))
# train: front group (locomotive + wagons 0..2) and rear group (wagons 3..5)
front=bpy.data.objects.new('FrontCars',None);link(front);rear=bpy.data.objects.new('RearCars',None);link(rear)
COL=[(.55,.18,.14),(.2,.32,.5),(.5,.42,.16),(.25,.45,.28),(.55,.3,.14),(.4,.2,.45)]
wheels=[]
def wagon(k,par):
 cx=-(6.5+12.4*k);c=COL[k];prim('cube','Wagon%d'%k,(cx,0,1.9),c,scale=(5.5,1.3,1.3),parent=par);prim('cube','Roof%d'%k,(cx,0,ROOF-.04),(.3,.28,.26),scale=(5.5,1.4,.05),parent=par)
 for dx in (-3.5,3.5):
  for s_ in (-.72,.72):wheels.append(prim('cyl','Wheel',(cx+dx,s_,.45),(.12,.12,.12),scale=(.45,.45,.1),rot=(PI/2,0,0),vertices=10,radius=1,depth=2,parent=par))
 prim('cube','Coupler',(cx+6.2,0,.9),(.1,.1,.1),scale=(.7,.12,.12),parent=par)
 for dx in np.linspace(-4.5,4.5,6):prim('cube','Board',(cx+dx,1.31,1.9),tuple(v*.6 for v in c),scale=(.04,.01,1.25),parent=par)
for k in range(3):wagon(k,front)
for k in range(3,6):wagon(k,rear)
prim('cube','LocoBody',(4.7,0,1.9),(.12,.12,.14),scale=(4.3,1.3,1.1),parent=front);prim('cube','LocoRoof',(4.7,0,ROOF-.04),(.2,.2,.2),scale=(4.3,1.4,.05),parent=front);prim('cube','Cab',(1.8,0,3.6),(.2,.18,.16),scale=(1.4,1.35,.55),parent=front)
prim('cyl','Chimney',(8.6,0,3.9),(.1,.1,.1),scale=(.3,.3,.7),vertices=8,radius=1,depth=2,parent=front)
for x in (1.5,4.0,6.5,8.0):
 for s_ in (-.72,.72):wheels.append(prim('cyl','Wheel',(x,s_,.55),(.14,.14,.14),scale=(.55,.55,.1),rot=(PI/2,0,0),vertices=10,radius=1,depth=2,parent=front))
prim('cyl','BrakeWheel',WHEEL,(.15,.15,.15),scale=(.33,.33,.03),vertices=14,radius=1,depth=2);bw=bpy.context.object;prim('cyl','BrakePost',(WHEEL.x,0,ROOF+.35),(.15,.15,.15),scale=(.05,.05,.4),vertices=6,radius=1,depth=2)
for k_,o in enumerate((bw,bpy.context.object)):pass
bw.parent=front
for f in range(1,frames+1,2):
 t=(f-1)/fps;front.location=(Xfun(t),0,0);front.keyframe_insert('location',frame=f);rear.location=(Xrear(t),0,0);rear.keyframe_insert('location',frame=f)
 bw.rotation_euler=(0,0,wheel_theta(t) if WHEEL_WIN[0]<=t<=WHEEL_WIN[1] else (wheel_theta(WHEEL_WIN[1]) if t>WHEEL_WIN[1] else 0));bw.keyframe_insert('rotation_euler',frame=f)
for w in wheels:
 for f in range(1,frames+1,12):w.rotation_euler=(PI/2,Xfun((f-1)/fps)/.5,0);w.keyframe_insert('rotation_euler',frame=f)
# steam from the chimney
puff=bpy.data.meshes.new('SteamMesh');bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.);bm.to_mesh(puff);bm.free()
te=0.
while te<seconds-2:
 o=bpy.data.objects.new('Steam',puff);link(o);o.data.materials.append(mat('Steam',(.92,.92,.92)));p0=Vector((Xfun(te)+8.6,0,4.7))
 for dt_,sc,up in ((0,.01,0),(.4,.28,.4),(1.6,.5,1.3),(2.6,.01,2.0)):
  o.location=(p0.x+vfun(te)*.0,p0.y,p0.z+up);o.scale=(sc,sc,sc);o.keyframe_insert('location',frame=F(te+dt_));o.keyframe_insert('scale',frame=F(te+dt_))
 te+=.22
# splash where Leo lands in the river
TL=T_LEAP+kit.flight_time_to_ground(ROOF+8.,3.);pl=Vector((Xfun(T_LEAP)+LEAP_X+V0*(TL-T_LEAP),7.5,-7.8));prim('cube','Sandbar',(pl.x,pl.y,-8.0),(.7,.62,.42),scale=(5,4,.25))
for i in range(16):
 o=bpy.data.objects.new('Splash',puff);link(o);o.data.materials.append(mat('Splash',(.75,.88,.95)));a=i*2*PI/16;r=rnd.uniform(.4,1.4)
 for dt_,sc,k in ((-.02,.001,0),(.08,.35,.3),(.4,.3,1.0),(.9,.001,1.3)):
  o.location=(pl.x+math.cos(a)*r*k,pl.y+math.sin(a)*r*k,pl.z+.2+(1.4*math.sin(math.pi*min(1,(dt_+.1)/.9))));o.scale=(sc,sc,sc);o.keyframe_insert('location',frame=F(TL+dt_));o.keyframe_insert('scale',frame=F(TL+dt_))
# ---------------------------------------------------------------------------------------------------------- cameras (world space, following the train)
def Wl(x,y,z,t,rearg=False):return Vector(((Xrear(t) if rearg else Xfun(t))+x,y,z))
CUTS=[('1 The prison train',0,3.0),('2 Leo wakes on the roof',3.0,6.4),('3 Run',6.4,8.0),('4 The first gap',8.0,9.3),('5 Chase from behind',9.3,11.4),('6 The low gantry',11.4,13.6),('7 Another gap',13.6,T_ARR+.4),('8 The kick',T_ARR+.4,T_THROW+1.6),
 ('9 The brake wheel',T_THROW+1.6,T_D-.5),('10 The coupling lets go',T_D-.5,T_D+3.5),('11 Along the roofs',T_D+3.5,T_END2),('12 The locomotive',T_END2,T_LEAP-.7),('13 The leap',T_LEAP-.7,T_LEAP+2.0),('14 The river',T_LEAP+2.0,seconds)]
cams=[]
for k,(name,a,b) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=3000;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(min(b,seconds))+1,2):
  t=(f-1)/fps;u=(t-a)/(b-a);L=leo_world(t);lh=L+Vector((0,0,.9));cam.data.lens=32;GA=world_of('ga',t);GB=world_of('gb',t)
  if k==0:ang=math.radians(-60+40*u);c0=Vector((Xfun(t)-30,0,0));p=c0+Vector((math.cos(ang)*60,math.sin(ang)*60,28));q=Vector((Xfun(t)-30,0,3));cam.data.lens=26
  elif k==1:p=Wl(-66.5,-3.4,ROOF+1.4,t);q=Vector((Xfun(t)-69.6,0,ROOF+.4));cam.data.lens=36
  elif k==2:p=Wl(leo_local(t)-.5,-5.5,ROOF+1.6,t);q=lh;cam.data.lens=32
  elif k==3:p=Wl(-61.5,-5.5,ROOF+.9,t);q=lh;cam.data.lens=34
  elif k==4:p=Wl(leo_local(t)-6,.8,ROOF+2.4,t);q=Wl(leo_local(t)+3,0,ROOF+.8,t);cam.data.lens=30
  elif k==5:p=Vector((X_BR-14,-9,ROOF+3.0));q=Vector((X_BR+2,0,ROOF+1.2));cam.data.lens=28
  elif k==6:p=Wl(leo_local(t)+1.5,-6,ROOF+1.4,t);q=(L+GA)/2+Vector((0,0,.9));cam.data.lens=30
  elif k==7:p=Wl(-33.8,-4.2,ROOF+1.0,t);q=(L+GA)/2+Vector((0,0,.8));cam.data.lens=34
  elif k==8:p=Wl(-29.4,-3.6,ROOF+1.3,t);q=Wl(-33.0,0,ROOF+.9,t);cam.data.lens=34
  elif k==9:p=Vector((Xfun(T_D)-30,-14,9));q=Vector(((Xfun(t)+Xrear(t))/2-36,0,ROOF));cam.data.lens=26
  elif k==10:p=Wl(leo_local(t)+7,-3.5,ROOF+1.8,t);q=lh;cam.data.lens=30
  elif k==11:p=Wl(10.5,-3.6,ROOF+1.7,t);q=Wl(5.0,0,ROOF+1.4,t);cam.data.lens=30
  elif k==12:p=Vector((Xfun(T_LEAP)+4,-13,-2.0));q=Vector((L.x,L.y,max(L.z,-3)+1));cam.data.lens=28
  else:ang=math.radians(-120+40*u);p=Vector((pl.x+math.cos(ang)*11,pl.y+math.sin(ang)*11,-4.2));q=Vector((pl.x,pl.y,-6.6));cam.data.lens=30
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
if KICK_ERR>.20:issues.append('AUDIT contact: the kick misses the guard by %.0f cm'%(KICK_ERR*100))
if KICK_DEPTH>.06:issues.append('AUDIT penetration: the kick goes %.0f cm inside the guard'%(KICK_DEPTH*100))
runwins=[(a+.3,b-.3) for k,a,b,x0,x1 in LEG1+LEG2 if k=='run' and b-a>.8]+[(WHEEL_WIN[0],WHEEL_WIN[1])]
def complement(wins,t0,t1):
 out_=[];cur=t0
 for a,b in sorted(wins):
  if a>cur:out_.append((cur,a))
  cur=max(cur,b)
 if cur<t1:out_.append((cur,t1))
 return out_
issues+=kit.audit(scene,bodies=[(FIG['leo']['rig'],FIG['leo']['body'])],floor_z=ROOF,skip=complement(runwins,0,seconds),subjects=[FIG['leo']['root'],FIG['ga']['root'],FIG['gb']['root']],step=12)
# the three characters must not occupy the same place on the roof (outside the kick)
worst=(9,0)
for f in range(F(6.6),F(T_D+1.0),6):
 t=(f-1)/fps;a=world_of('leo',t);b=world_of('ga',t);c=world_of('gb',t)
 for x_,y_,nm in ((a,b,'leo-guardA'),(a,c,'leo-guardB')):
  d=(x_-y_).length
  if d<worst[0] and not (nm=='leo-guardA' and T_THROW-.6<t<T_THROW+.6):worst=(d,t)
if worst[0]<.9:issues.append('AUDIT overlap: Leo and a guard are only %.1f m apart at t=%.1f s'%worst)
print('MINDIST %.1f at %.1f'%worst)
for i in issues:print(i)
print('AUDIT',len(issues),'issues');print('TIMES arrive %.1f decouple %.1f gap-jump-B %.1f leap %.1f bridge %.1f..%.1f'%(T_ARR,T_D,T_GB_JUMP,T_LEAP,(XV0),(XV1)))
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_train');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(5)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
vel=np.interp(tt,np.arange(frames+1)/fps,[vfun(i/fps) for i in range(frames+1)])
rumble=lp(nr.standard_normal(N_),40)*(vel/V0)*1.0+lp(nr.standard_normal(N_),400)*(vel/V0)*.6
clack=np.zeros(N_+SR);ct=np.arange(int(.12*SR))/SR;cl=np.sin(2*PI*180*ct)*np.exp(-ct*40)+lp(nr.standard_normal(len(ct)),6)*np.exp(-ct*50)
last=-1
for i in range(frames):
 x0=XF[i];x1=XF[i+1]
 if int(x1/12.5)>int(x0/12.5):
  j=int(i/fps*SR);clack[j:j+len(cl)]+=cl*(.3+vfun(i/fps)/V0*.7)
clack=clack[:N_];wind=lp(nr.standard_normal(N_),25)*(vel/V0)*.8
chuff=np.zeros(N_+SR);ht=np.arange(int(.15*SR))/SR;hf=lp(nr.standard_normal(len(ht)),30)*np.exp(-ht*28)
t_=0.
while t_<seconds-1:
 v=vfun(t_);t_+=max(.12,.5-v*.02)
 j=int(t_*SR);chuff[j:j+len(hf)]+=hf*(.4+v/V0*.6)
chuff=chuff[:N_]
def whistle(t0,d):
 n=int(d*SR);k=np.arange(n)/SR;x=(np.sin(2*PI*(660+20*np.sin(k*6))*k)+.5*np.sin(2*PI*990*k))*np.minimum(k/.05,1)*np.minimum((d-k)/.3,1);tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=x[:max(0,min(n,N_-i))];return tr
hit=np.zeros(N_+SR);n=int(.5*SR);k=np.arange(n)/SR;hs=(lp(nr.standard_normal(n),25)*np.exp(-k*9)+np.sin(2*PI*(80-50*k)*k)*np.exp(-k*7))*1.2;i=int(t_imp*SR);hit[i:i+n]+=hs;i=int((T_THROW+kit.flight_time_to_ground(ROOF,3.))*SR);hit[i:i+n]+=hs*.7;hit=hit[:N_]
spl=np.zeros(N_+SR);n=int(1.1*SR);k=np.arange(n)/SR;i=int(TL*SR);spl[i:i+n]=lp(nr.standard_normal(n),12)*np.exp(-k*4)*np.minimum(k/.02,1)*1.4;spl=spl[:N_]
def roar(t0,d,f0,amp=1.):
 n=int(d*SR);k=np.arange(n)/SR;f=f0+60*np.sin(2*PI*5*k)*np.exp(-k)-20*k;ph=2*PI*np.cumsum(f)/SR;x=(np.sin(ph)+.6*np.sin(2*ph)+.4*np.sin(3*ph)+.6*nr.standard_normal(n))*np.minimum(k/.08,1)*np.exp(-k*.9);tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=lp(x,4)[:max(0,min(n,N_-i))]*amp;return tr
voice=roar(6.3,1.2,150,.8)+roar(T_THROW,1.0,120,.7)+roar(T_GB_JUMP+.3,1.1,170,.7)+roar(T_LEAP+2.6,1.6,200,1.)
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=T_LEAP+2.5 else minor[ci%4];vol=.45 if t0<6 else .8
 for j,f0 in enumerate(chord):
  n_=note(f0,2.6,vol*.5);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
 if 6<=t0<=T_LEAP+2:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.2*SR))/SR;kk=np.sin(2*PI*(55*kt-90*kt**2))*np.exp(-kt*20)
   if i<N_:music[i:i+len(kk)]+=kk*1.4
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('train.wav',rumble+clack+chuff+wind*.7,.8),wav('whistle.wav',whistle(3.8,1.8)+whistle(T_D,1.2),.6),wav('hits.wav',hit+spl,.95),wav('roars.wav',voice,.85),wav('music.wav',music,.5)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('train and wind','whistle','impacts and splash','roars','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('TRAIN_DONE',frames,'frames')
