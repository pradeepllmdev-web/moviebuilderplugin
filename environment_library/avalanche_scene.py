"""Blender script: 'The Avalanche' - a village of lions flees an avalanche; Leo warns them, saves a lost cub and closes the shelter door in time (48 s).

blender -b --disable-autoexec --python avalanche_scene.py -- <ship_assets_dir> <out.blend> [seconds=48]

New in this scene: BULK. (1) A crowd of 36 cloned lions (shared mesh, own armature, scene_kit.clone_character) steered by a small Reynolds simulation: delayed alarm, seek the shelter,
separation, avoidance of stalls, funnel through the gate; each runs the Run clip scaled to its own speed. (2) An avalanche of 270 baked rigid-body boulders on a heightfield slope; the
time the front reaches the shelter is MEASURED from the bake and the hero's whole schedule is derived backwards from it. (3) Everything that appears is there for the whole film
(persistence rule); the audit checks it. Clips come from build_ship_assets.py."""
import bpy,math,random,sys,os,wave,bmesh
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 48.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(7);PI=math.pi
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color,emit=0.):
 if name in _m:return _m[name]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
 _m[name]=m;return m
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color));return o
# ---------------------------------------------------------------------------------------------------------- terrain: slope above the village, gentle valley, flat floor of the shelter
import locations,scene_params
_prm=scene_params.get();_loc=locations.load('mountain_village',dict(link=link,mat=mat,prim=prim),_prm['location_state'] or 'intact')
terrain=locations.village_terrain;HALL_X0,HALL_X1,HALL_HW,GATE_HW,DOOR_Z=locations.VILLAGE['hall'];STALLS=locations.VILLAGE['stalls']
passive=[(o,o['rb']) for o in bpy.data.objects if 'rb' in o.keys()];door=bpy.data.objects['SlidingDoor'];terr=bpy.data.objects['Terrain']
# ---------------------------------------------------------------------------------------------------------- the avalanche: baked rigid bodies
bpy.ops.rigidbody.world_add();rw=scene.rigidbody_world;rw.point_cache.frame_start=1;rw.point_cache.frame_end=frames
for o,sh in passive:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add(type='PASSIVE');o.rigid_body.collision_shape=sh;o.rigid_body.friction=.8;o.select_set(False)
DOOR_C0=GATE_HW*2;T_SLAM=None
BOULDERS=[]
def boulder(i,pre):
 r=rnd.uniform(.5,1.4) if not pre else rnd.uniform(.4,.8);x=rnd.uniform(-64,-46);y=rnd.uniform(-26,26) if not pre else rnd.uniform(-8,8);o=prim('sphere','Boulder' if rnd.random()<.55 else 'SnowBoulder',(x,y,terrain(x,y)+r+.15),(.5,.47,.43) if rnd.random()<.6 else (.93,.95,1),scale=(r,r*rnd.uniform(.8,1),r),subdivisions=1)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add(type='ACTIVE');rb=o.rigid_body;rb.collision_shape='SPHERE';rb.mass=r**3*400;rb.friction=.5;rb.restitution=.25;rb.linear_damping=.02;rb.angular_damping=.05
 rb.kinematic=True;rb.keyframe_insert('kinematic',frame=1);t=(rnd.uniform(3.5,8.0) if pre else rnd.uniform(30.5,38.5)+(-x-46)*.1);rb.kinematic=False;rb.keyframe_insert('kinematic',frame=F(t));o.select_set(False);BOULDERS.append((o,t,pre))
for i in range(12):boulder(i,True)
for i in range(270):boulder(i,False)
scene.frame_set(1)
try:bpy.ops.ptcache.bake_all(bake=True);print('avalanche baked')
except Exception as ex:print('bake skipped',ex)
# measure when the front reaches the shelter and how the mass moves (for sound and the snow cloud)
FRONT=[];ACTIVE=[]
for f in range(1,frames+1,3):
 scene.frame_set(f);xs_=[o.matrix_world.translation.x for o,t,pre in BOULDERS if not pre];FRONT.append((f,sorted(xs_)[-8]))
 mv=0
 for o,t,pre in BOULDERS[-40:]:mv+=1
T_SLAM=next(((f-1)/fps for f,x in FRONT if x>=HALL_X0-2),seconds-6);print('SLAM',round(T_SLAM,1))
T_SLAM=max(30.,min(T_SLAM,seconds-8))
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
 return dict(root=root,rig=rig,body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices)))
CLIPS={}
for c in ('idle','look','run','climb','pick','cele'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
LEO=load_char('Leo');CUB=load_char('Cub',.45)
def set_nla(rig,sched):
 ad=rig.animation_data
 for tr in list(ad.nla_tracks):ad.nla_tracks.remove(tr)
 tr=[ad.nla_tracks.new(),ad.nla_tracks.new()]
 for k,item in enumerate(sched):
  c,a,b,mode=item[:4]
  try:st=kit.add_strip(tr[k%2],CLIPS[c],F(a)-(5 if k else 0),F(b),mode)
  except RuntimeError:print('NLA FAIL',rig.name,k,c,a,b,F(a),F(b),[ (x.frame_start,x.frame_end) for x in tr[k%2].strips]);raise
  if len(item)>4 and item[4]!=1.:
   sc=item[4];ln=CLIPS[c].frame_range[1]-CLIPS[c].frame_range[0]+1;need=(F(b)-st.frame_start)/(ln*sc);st.action_frame_end=st.action_frame_start+ln-1;st.repeat=1.;st.scale=sc
   if need>=1:st.repeat=need
   else:st.action_frame_end=st.action_frame_start+max(2,need*ln)-1
  st.extrapolation='HOLD' if k==0 else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
# ---------------------------------------------------------------------------------------------------------- the crowd: Reynolds steering (alarm delay, seek, separation, stalls, funnel through the gate)
N=36;DT=1/fps;GOAL1=Vector((99.,0.));
agents=[]
for i in range(N):
 while True:
  p=Vector((rnd.uniform(26,64),rnd.uniform(-8,8)))
  if all((p-Vector(s)).length>2.2 for s in STALLS) and all((p-a['p']).length>1.4 for a in agents):break
 agents.append(dict(p=p,v=Vector((0,0)),vmax=rnd.uniform(3.6,4.5),t_alarm=6.0+max(0.,(p.x-26)/16.)+rnd.uniform(0,1.5),h=rnd.uniform(0,2*PI),inside=False,arr=None,goalY=rnd.uniform(-6,6),goalX=rnd.uniform(102,112)))
TRAJ=[[] for _ in agents]
for fi in range(frames+1):
 t=fi/fps
 for k,a in enumerate(agents):
  TRAJ[k].append((a['p'].x,a['p'].y,a['h'],a['v'].length))
  if t<a['t_alarm']:continue
  goal=Vector((a['goalX'],a['goalY'])) if a['inside'] else GOAL1
  if a['p'].x>97.0 and abs(a['p'].y)<GATE_HW+.5:a['inside']=True
  d=goal-a['p']
  if a['inside'] and (d.length<1.8 or (a['v'].length<.15 and a['p'].x>100.5)):
   a['v']*=.8
   if a['arr'] is None:a['arr']=t
   continue
  des=d.normalized()*a['vmax']
  for j,b in enumerate(agents):
   if b is a:continue
   r=a['p']-b['p'];dist=r.length
   if 0<dist<1.6:des+=r/dist*(1.6-dist)*5.
  for sx,sy in STALLS:
   r=a['p']-Vector((sx,sy));dist=r.length
   if dist<2.6:des+=r/max(dist,.1)*(2.6-dist)*4.
  if not a['inside']:   # funnel: stay in the lane that leads to the opening
   if a['p'].x>84:des.y+=-a['p'].y*1.8
  if a['inside']:
   if a['p'].y>HALL_HW-1.5:des.y-=2.
   if a['p'].y<-HALL_HW+1.5:des.y+=2.
  a['v']+=(des-a['v'])*min(1,DT*3.5)
  if a['v'].length>a['vmax']:a['v']*=a['vmax']/a['v'].length
  a['p']+=a['v']*DT
  for b in agents:   # hard personal space (position based dynamics): nobody overlaps
   if b is a:continue
   r=a['p']-b['p'];dist=r.length
   if 0<dist<.6:a['p']+=r/dist*(.6-dist)*.5;b['p']-=r/dist*(.6-dist)*.5
  if a['v'].length>.3:a['h']=math.atan2(a['v'].y,a['v'].x)
for k_,a in enumerate(agents):
 if not a['arr']:print('STUCK',k_,tuple(round(x,1) for x in a['p']),a['inside'],round(a['v'].length,2))
ARR=[a['arr'] for a in agents if a['arr']];print('CROWD arrived',len(ARR),'of',N,'last at %.1f s'%(max(ARR) if ARR else -1))
crowd=[]
for k,a in enumerate(agents):
 start=TRAJ[k][0];root,crig,cbody=kit.clone_character(LEO['rig'],LEO['body'],'Fan%d'%k,(start[0],start[1],terrain(start[0],start[1])),0.,.75+.2*rnd.random(),(rnd.uniform(.75,1.15),rnd.uniform(.6,1.0),rnd.uniform(.45,.9)))
 crig.animation_data_create();ta=a['t_alarm'];tr_=a['arr'] or seconds
 sched=[('look',0,ta-.6,'loop'),('run',ta-.6,tr_,'loop',3.0/a['vmax'])]+([('look',tr_,seconds,'loop')] if tr_<seconds-.4 else [])
 set_nla(crig,sched);crowd.append((root,crig,cbody))
 for f in range(1,frames+1,2):
  x,y,h,sp=TRAJ[k][f-1];root.location=(x,y,terrain(x,y));root.rotation_euler=(0,0,h+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
print('CROWD clones',len(crowd))
# ---------------------------------------------------------------------------------------------------------- the hero, derived backwards from the measured slam time
T_DOOR_END=T_SLAM-1.0;T_PUSH0=T_DOOR_END-4.0;T_GATE=T_PUSH0-4.4;V_RUN2=3.8;T_RUN2=T_GATE-(94.-49.)/V_RUN2;T_PICK0=T_RUN2-5.0;V_RUN1=4.2;T_RUN1=T_PICK0-(48.-20.)/V_RUN1
print('HERO run1 %.1f pick %.1f run2 %.1f gate %.1f push %.1f slam %.1f'%(T_RUN1,T_PICK0,T_RUN2,T_GATE,T_PUSH0,T_SLAM))
def door_y(t):return DOOR_C0-DOOR_C0*smooth((t-T_PUSH0)/(T_DOOR_END-T_PUSH0)) if t>T_PUSH0 else DOOR_C0
CUBP=Vector((49.4,-.4,terrain(49.4,-.4)))
WPS=[(0,20.,0.,0.),(T_RUN1,20.,0.,0.),(T_PICK0-.2,48.,0.,0.),(T_RUN2,48.,0.,0.),(T_GATE,94.,0.,0.),(T_GATE+1.6,98.,0.,0.),(T_GATE+2.0,98.,0.,PI/2),(T_GATE+4.4,97.55,9.9,PI/2),(T_GATE+5.0,97.55,9.9,-PI/2)]
def leo_xyh(t):
 if t<T_PUSH0-.6:
  w=WPS
  if t<=w[0][0]:return w[0][1],w[0][2],w[0][3]
  for a,b in zip(w,w[1:]):
   if a[0]<=t<b[0]:
    u=(t-a[0])/(b[0]-a[0]);u=smooth(u) if (a[1],a[2])==(b[1],b[2]) or True else u;dh=(b[3]-a[3]+PI)%(2*PI)-PI
    mode_run=(a[0],b[0]) in ((T_RUN1,T_PICK0-.2),(T_RUN2,T_GATE))
    if mode_run:u=(t-a[0])/(b[0]-a[0])   # constant speed on the run legs
    return a[1]+(b[1]-a[1])*u,a[2]+(b[2]-a[2])*u,a[3]+dh*u
  return w[-1][1],w[-1][2],w[-1][3]
 yt=door_y(t)+GATE_HW;return HALL_X0+.7,yt+.7,-PI/2
def leo_world(t):
 x,y,h=leo_xyh(t);return Vector((x,y,terrain(x,y)))
def leo_h(t):return leo_xyh(t)[2]
PICK_T=(T_PICK0,T_PICK0+5.0)
set_nla(LEO['rig'],[('look',0,T_RUN1,'loop'),('run',T_RUN1,T_PICK0-.2,'loop',3.0/V_RUN1),('pick',T_PICK0,T_PICK0+5.0,'fit'),('run',T_RUN2,T_GATE,'loop',3.0/V_RUN2),('climb',T_GATE,T_GATE+1.4,'loop'),('idle',T_GATE+1.4,T_GATE+2.0,'loop'),('climb',T_GATE+2.0,T_GATE+4.4,'loop'),('climb',T_PUSH0,T_DOOR_END,'loop'),('idle',T_DOOR_END,T_DOOR_END+1.5,'loop'),('look',T_DOOR_END+1.5,T_DOOR_END+6.0,'loop'),('cele',T_DOOR_END+6.0,seconds,'fit')])
for f in range(1,frames+1,2):
 t=(f-1)/fps;p=leo_world(t);LEO['root'].location=p;LEO['root'].rotation_euler=(0,0,leo_h(t)+PI/2);LEO['root'].keyframe_insert('location',frame=f);LEO['root'].keyframe_insert('rotation_euler',frame=f)
# hands on the door for the push
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Grip_'+limb,None);tg.empty_display_size=.06;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.55*sgn,.55,1.0)
 c=LEO['rig'].pose.bones['mixamorig:'+bone].constraints.new('IK');c.target=tg;c.pole_target=pole;c.pole_angle=math.radians(-90 if limb=='LH' else 90);c.chain_count=2;c.use_stretch=False;IK[limb]=c
for f in range(1,frames+1,2):
 t=(f-1)/fps;v=smooth((t-(T_PUSH0-.6))/.5)*(1-smooth((t-T_DOOR_END)/.5)) if T_PUSH0-.6<=t<=T_DOOR_END+.6 else 0.
 yt=door_y(t)+GATE_HW+.05;zt=terrain(HALL_X0,0)+1.15
 for limb,sg in (('LH',1),('RH',-1)):
  TG[limb].location=(HALL_X0+.7-.14*sg*(-1)*0+(.14*sg),yt,zt);TG[limb].keyframe_insert('location',frame=f);IK[limb].influence=v;IK[limb].keyframe_insert('influence',frame=f)
# the door slides on its rail; it is a kinematic (animated) rigid body so the boulders hit it
door.rigid_body.kinematic=True
for f in range(1,frames+1,2):
 t=(f-1)/fps;door.location=(HALL_X0+.7,door_y(t),DOOR_Z+2.6);door.keyframe_insert('location',frame=f)
# the cub: waits scared, is lifted in Leo's right hand, held, then rides on his back
CUB['root'].scale=(.45,)*3;set_nla(CUB['rig'],[('look',0,T_PICK0+1.0,'loop'),('idle',T_PICK0+1.0,seconds,'loop')])
def settle(f):
 scene.frame_set(f);bpy.context.view_layer.update()
def cub_pose(f):
 t=(f-1)/fps;t0=T_PICK0+1.2
 if t<t0:return CUBP,PI
 settle(f);h=leo_h(t);ang=h+PI/2;rig=LEO['rig']
 hand=rig.matrix_world@rig.pose.bones['mixamorig:RightHand'].head+Vector((0,0,-.10));sp=rig.matrix_world@rig.pose.bones['mixamorig:Spine1'].head
 back=sp+Vector((-.30*math.cos(h),-.30*math.sin(h),.06))
 if t<t0+1.0:return CUBP.lerp(hand,smooth((t-t0)/1.0)),PI+(ang-PI)*smooth((t-t0)/1.0)
 if t<t0+1.6:return hand,ang
 if t<t0+2.5:return hand.lerp(back,smooth((t-t0-1.6)/.9)),ang
 return back,ang
for f in range(1,F(T_PICK0+1.0),30):
 CUB['root'].location=CUBP;CUB['root'].rotation_euler=(0,0,PI);CUB['root'].keyframe_insert('location',frame=f);CUB['root'].keyframe_insert('rotation_euler',frame=f)
for f in range(F(T_PICK0+1.0),frames+1,2):
 pos,ang=cub_pose(f);CUB['root'].location=pos;CUB['root'].rotation_euler=(0,0,ang);CUB['root'].keyframe_insert('location',frame=f);CUB['root'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- sky, light, snow cloud, dust
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.data.energy=2.6;sun.data.color=(1,.9,.8);sun.rotation_euler=(math.radians(52),0,math.radians(-60))
scene.world=bpy.data.worlds.new('Cold');scene.world.color=(.62,.7,.82)
kit.apply_params(scene,sun,[o for o in bpy.data.objects if o.type=='MESH' and o.parent==LEO['root']])   # SCENE_PARAMS: time of day and hero tint
puff=bpy.data.meshes.new('SnowPuffMesh');bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.);bm.to_mesh(puff);bm.free()
FRONT_X=lambda f:next((x for ff,x in FRONT if ff>=f),FRONT[-1][1])
for fi in range(0,frames,12):
 t=fi/fps
 if t<12:continue
 xm=FRONT_X(F(t))
 for k in range(3):
  o=bpy.data.objects.new('SnowPuff',puff);link(o);o.data.materials.append(mat('SnowCloud',(.96,.97,1)));y=rnd.uniform(-18,18);zb=terrain(xm,y)
  for dt_,sc in ((0,.1),(.7,5.0),(2.6,9.),(4.5,.1)):
   o.location=(xm-rnd.uniform(0,6)-dt_*2,y,zb+1.5+dt_*.8);o.scale=(sc,sc,sc*.7);o.keyframe_insert('location',frame=F(t+dt_));o.keyframe_insert('scale',frame=F(t+dt_))
# ---------------------------------------------------------------------------------------------------------- cameras (auto-cleared of scenery in the way)
CUTS=[('1 The valley',0,4.0),('2 Leo hears it',4.0,T_RUN1+2.5),('3 The first stones',T_RUN1+2.5,T_PICK0-.5),('4 The lost cub',T_PICK0-.5,T_PICK0+3.2),('5 Cub on his back',T_PICK0+3.2,T_RUN2+2.5),('6 The village runs',T_RUN2+2.5,T_GATE-3.5),
 ('7 The avalanche comes',T_GATE-3.5,T_GATE+.5),('8 Into the hall',T_GATE+.5,T_PUSH0-.3),('9 The door',T_PUSH0-.3,T_DOOR_END+.8),('10 The slam',T_DOOR_END+.8,T_DOOR_END+4.5),('11 Silence',T_DOOR_END+4.5,seconds-5),('12 Safe',seconds-5,seconds)]
cams=[];CAMKEYS=[]
def crowd_center(t):
 xs=[TRAJ[k][min(frames,int(t*fps))][0] for k in range(N)];ys=[TRAJ[k][min(frames,int(t*fps))][1] for k in range(N)];x=sum(xs)/N;y=sum(ys)/N;return Vector((x,y,terrain(x,y)))
for k,(name,a,b) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=3000;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(min(b,seconds))+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);L=leo_world(t);lh=L+Vector((0,0,1.0));cc=crowd_center(t);cam.data.lens=30
  if k==0:p=Vector((8+10*u,-60,25));q=Vector((-20,0,22));cam.data.lens=24
  elif k==1:p=L+Vector((4,-5.5,3.2));q=lh;cam.data.lens=36
  elif k==2:p=L+Vector((-6,-7,2.2));q=lh+Vector((5,0,0));cam.data.lens=30
  elif k==3:p=Vector((CUBP.x-3.2,CUBP.y-3.4,CUBP.z+1.4));q=(L+CUBP)/2+Vector((0,0,.8));cam.data.lens=34
  elif k==4:p=L+Vector((3.5,-4.5,1.4));q=lh;cam.data.lens=34
  elif k==5:p=cc+Vector((-6,-16,6));q=cc+Vector((6,0,1));cam.data.lens=28
  elif k==6:p=Vector((70,-14,6));q=Vector((20,0,8));cam.data.lens=50
  elif k==7:p=Vector((HALL_X0+11,-8.5,DOOR_Z+2.4));q=Vector((HALL_X0+3,max(-3,min(10,L.y)),DOOR_Z+1.2));cam.data.lens=26
  elif k==8:p=Vector((HALL_X0+9,-1,DOOR_Z+2.2));q=Vector((HALL_X0+.5,door_y(t)+1.5,DOOR_Z+1.3));cam.data.lens=28
  elif k==9:p=Vector((HALL_X0+12,0,DOOR_Z+2.0));q=Vector((HALL_X0+.5,0,DOOR_Z+2.0));cam.data.lens=24
  elif k==10:p=Vector((HALL_X0+14,-5,DOOR_Z+3.0));q=Vector((HALL_X0+8,0,DOOR_Z+.8));cam.data.lens=28
  else:p=Vector((HALL_X0+9,-4.5,DOOR_Z+1.3))*(1-u)+Vector((HALL_X0+14,-8,DOOR_Z+3.5))*u;q=lh+Vector((0,0,.2));cam.data.lens=30
  sh=sum(a_*math.exp(-abs(t-T_SLAM)*2.5) for a_ in (.35,)) if k in (9,) else 0.
  cam.location=p+Vector((rnd.uniform(-1,1),rnd.uniform(-1,1),rnd.uniform(-1,1)))*sh;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
FAMILY=set()
for d_ in (LEO,CUB):FAMILY|=kit._family(d_['root'])
for r_,c_,b_ in crowd:FAMILY|=kit._family(r_)
FAMILY|={o.name for o,t,pre in BOULDERS}
CAND=[(0,0,1.5),(0,0,3.),(0,0,5.),(0,-4,3.),(0,4,3.),(0,0,8.),(-4,0,3.),(0,-8,6.)]
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
issues+=kit.camera_checks(scene,[LEO['root']]+[c[0] for c in crowd][:6])
if len(ARR)<N-2:issues.append('AUDIT crowd: only %d of %d lions reached the shelter before the slam'%(len(ARR),N))
if ARR and max(ARR)>T_SLAM-1.0:issues.append('AUDIT crowd: the last lion arrives at %.1f s, too close to the slam at %.1f s'%(max(ARR),T_SLAM))
md=9.
for fi in range(int(8*fps),int(32*fps),6):
 for i in range(N):
  for j in range(i+1,N):
   d=math.hypot(TRAJ[i][fi][0]-TRAJ[j][fi][0],TRAJ[i][fi][1]-TRAJ[j][fi][1]);md=min(md,d)
print('CROWD min spacing %.2f m'%md)
if md<.45:issues.append('AUDIT crowd: two lions come within %.2f m of each other'%md)
if T_RUN1<1.5:issues.append('AUDIT schedule: Leo has to start running at %.1f s; the avalanche is too early'%T_RUN1)
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_avalanche');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(2)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
rel=np.array([t for o,t,pre in BOULDERS if not pre]);dens=np.array([(np.sum((rel<tq)&(rel>tq-6))/270.) for tq in tt[::400]]);dens=np.interp(tt,tt[::400],dens)
rumble=lp(nr.standard_normal(N_),90)*(.15+dens*1.6)+lp(nr.standard_normal(N_),500)*dens*.6
pre=np.zeros(N_+SR)
for o,t,p_ in BOULDERS:
 if p_:
  n=int(.4*SR);k=np.arange(n)/SR;x=(lp(nr.standard_normal(n),30)*np.exp(-k*10)+np.sin(2*PI*(100-60*k)*k)*np.exp(-k*9))*.5;i=int((t+1.2)*SR);pre[i:i+n]+=x
pre=pre[:N_]
slam=np.zeros(N_+SR*3);n=int(2.4*SR);k=np.arange(n)/SR;x=(lp(nr.standard_normal(n),60)*np.exp(-k*2.2)*2.5+np.sin(2*PI*(55-20*k)*k)*np.exp(-k*3)*2.);i=int(T_SLAM*SR);slam[i:i+n]+=x;slam=slam[:N_]
foot=np.zeros(N_+SR);ft=np.arange(int(.12*SR))/SR;st=np.sin(2*PI*140*ft)*np.exp(-ft*40)+.3*lp(nr.standard_normal(len(ft)),6)*np.exp(-ft*50)
for k_,a in enumerate(agents):
 if a['arr']:
  tt_=a['t_alarm'];
  while tt_<a['arr']:
   i=int(tt_*SR);foot[i:i+len(st)]+=st*.15;tt_+=.32/(a['vmax']/3.)
foot=foot[:N_]
def meow(t0,n_=1.0):
 n=int(n_*SR);k=np.arange(n)/SR;f=700+250*np.sin(np.pi*k/n_)+60*np.sin(2*PI*7*k);ph=2*PI*np.cumsum(f)/SR;x=(np.sin(ph)+.4*np.sin(2*ph))*np.sin(np.pi*k/n_)**.7;tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=x[:max(0,min(n,N_-i))];return tr
voice=meow(1.0)+meow(2.8,.8)*.7+meow(T_PICK0+.4,.9)+meow(T_PICK0+3.5,.7)*.5
wind=lp(nr.standard_normal(N_),28)*.35*(1+.4*np.sin(tt*.6))
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=T_SLAM+5 else minor[ci%4];vol=.4 if t0<10 else .8 if t0<T_SLAM+1 else .4
 for j,f0 in enumerate(chord):
  n_=note(f0,2.6,vol*.5);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
 if 10<=t0<=T_SLAM:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.2*SR))/SR;kk=np.sin(2*PI*(55*kt-90*kt**2))*np.exp(-kt*20)
   if i<N_:music[i:i+len(kk)]+=kk*1.4
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('avalanche.wav',rumble+pre,.9),wav('slam.wav',slam,.95),wav('crowd_steps.wav',foot,.6),wav('cubs.wav',voice,.6),wav('wind.wav',wind,.4),wav('music.wav',music,.5)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('avalanche','slam','crowd steps','cub','wind','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('AVALANCHE_DONE',frames,'frames')
