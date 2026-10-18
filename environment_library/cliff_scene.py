"""Blender script: 'The Cliff Rescue' - Leo free-climbs a cliff on real hand and foot holds, swings across a gap on a rope, climbs on while rocks fall, lifts a lost cub onto his back and
rappels down as the rope frays (62 s).

blender -b --disable-autoexec --python cliff_scene.py -- <ship_assets_dir> <out.blend> [seconds=62]

New in this scene: hand and foot GRIP. Holds are placed procedurally (alternating right hand, left foot, left hand, right foot, one step 0.33 m), every limb is IK to the hold it is
planted on, so hands and feet touch rock instead of cycling a walk clip. The rope swing is an exact pendulum (half period pi*sqrt(L/g)), the falling rocks are Blender rigid bodies (baked),
and an audit measures every grip (wrist/ankle bone against its target). Leo's clips come from build_ship_assets.py (look, idle, climb=walk, pick, cele)."""
import bpy,math,random,sys,os,wave,zlib,bmesh
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 62.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(8)
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
def put(o,color,name,emit=0.):
 o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color,emit));return o
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;return put(o,color,name,emit)
def hide_keys(o,windows):
 last=None
 for f in range(1,frames+1):
  v=any(a<=(f-1)/fps<b for a,b in windows)
  if v!=last:
   for prop in ('hide_viewport','hide_render'):setattr(o,prop,not v);o.keyframe_insert(prop,frame=f)
   last=v
def rope_obj(name,color=(.55,.42,.22),r=.03):
 return prim('cyl',name,(0,0,0),color,vertices=5,radius=r,depth=2)
def set_rope(o,a,b,frame):
 a,b=Vector(a),Vector(b);d=b-a;o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.scale=(1,1,max(.01,d.length/2));o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_euler',frame=frame);o.keyframe_insert('scale',frame=frame)
# ---------------------------------------------------------------------------------------------------------- geometry constants (metres; the wall is the plane y=0, the climber is at y<0)
COL_A,COL_B,COL_C=-2.6,3.0,9.6;ROOT_Y=-.30;LEDGE2_Z,SLAB_Z=7.0,13.0;LEDGE2=(2.6,6.5);SLAB=(3.45,9.0);GAP=(-2.0,2.4,6.4,15.2)
ROPE_L=6.;XS,XE=-2.35,3.0;AX=(XS+XE)/2;TH0=math.asin((XE-XS)/2/ROPE_L);ANCHOR=Vector((AX,-.05,8.3+ROPE_L*math.cos(TH0)));OMEGA=math.sqrt(9.81/ROPE_L);T_SW0=22.5;T_LAND=T_SW0+math.pi/OMEGA
STEP=.33
LIMBS={'RH':dict(off=0.,top=1.45,lat=.2),'LF':dict(off=.25,top=.49,lat=-.14),'LH':dict(off=.5,top=1.45,lat=-.2),'RF':dict(off=.75,top=.49,lat=.14)}   # right = +x when facing the wall
def rope_end(t):
 th=-TH0*math.cos(OMEGA*(t-T_SW0))*math.exp(-.2*max(0,t-T_LAND)) if t>=T_SW0 else -TH0
 return ANCHOR+Vector((ROPE_L*math.sin(th),0,-ROPE_L*math.cos(th)))
def ywall(x,z):
 n=.07*(3+math.sin(x*1.3+z*.7)+math.sin(x*.5-z*1.1+1)+math.sin(x*2.1+z*1.9))
 x0,x1,z0,z1=GAP;e=.5;inx=smooth((x-x0)/e)*smooth((x1-x)/e);inz=smooth((z-z0)/e)*smooth((z1-z)/e);return n+1.6*inx*inz
def hold_abs(limb,k,col):
 L=LIMBS[limb];r=random.Random(zlib.crc32(('%s%d%.1f'%(limb,k,col)).encode()));z=L['off']*STEP+k*STEP+L['top']+r.uniform(-.03,.03)
 return Vector((col+L['lat']+r.uniform(-.04,.04),-.04,z))
def climb_target(limb,s,col):
 L=LIMBS[limb];u=(s-L['off']*STEP)/STEP;k=math.floor(u);f=u-k;h0=hold_abs(limb,k,col)
 if f<.7:return h0
 w=smooth((f-.7)/.3);p=h0.lerp(hold_abs(limb,k+1,col),w);p.y-=.10*math.sin(math.pi*w);return p
# ---------------------------------------------------------------------------------------------------------- Leo's climbing height over time
B_KEYS=[(26.7,7.0),(28.5,9.0),(30.8,9.4),(33.0,13.0)];C_KEYS=[(46.3,13.),(49.7,7.6),(49.9,7.6),(50.25,6.7),(55.,0.)]
def S(t):
 if t<7:return 0.
 if t<17:return 7*smooth((t-7)/10.)
 if t<26.7:return 7.
 if t<=33:return kit.catmull([(a,(b,0,0)) for a,b in B_KEYS],t)[0]
 if t<46.3:return 13.
 return kit.catmull([(a,(b,0,0)) for a,b in C_KEYS],t)[0]
def hop(t,ph):return .08*math.sin(2*math.pi*t/.9+ph)
SEG={
 'RH':[(0,5,None),(5,20.0,lambda t:climb_target('RH',S(t),COL_A)),(20.0,T_LAND-.5,lambda t:rope_end(t)+Vector((.05,0,0))),(T_LAND-.5,26.2,None),(26.2,33.0,lambda t:climb_target('RH',S(t),COL_B)),(33.0,45.5,None),(45.5,55.,lambda t:Vector((COL_C+.08,-.2,S(t)+1.15))),(55,999,None)],
 'LH':[(0,5,None),(5,20.8,lambda t:climb_target('LH',S(t),COL_A)),(20.8,T_LAND-.5,lambda t:rope_end(t)+Vector((-.05,0,0))),(T_LAND-.5,26.2,None),(26.2,33.0,lambda t:climb_target('LH',S(t),COL_B)),(33.0,45.5,None),(45.5,55.,lambda t:Vector((COL_C-.08,-.2,S(t)+1.15))),(55,999,None)],
 'LF':[(0,5,None),(5,21.6,lambda t:climb_target('LF',S(t),COL_A)),(21.6,T_LAND-.5,None),(T_LAND-.5,T_LAND+.2,lambda t:leo_root(t)[0]+Vector((-.14,.05,.12+.30*kit.jump_profile(t,T_LAND-.5,T_LAND+.2)['tuck']))),(T_LAND+.2,26.2,lambda t:Vector((XE-.14,-.28,LEDGE2_Z+.12))),(26.2,33.0,lambda t:climb_target('LF',S(t),COL_B)),(33.0,33.8,lambda t:Vector((3.3-.12,-.28,SLAB_Z+.12))),(33.8,45.9,None),(45.9,55.,lambda t:Vector((COL_C-.14,-.04,S(t)+.30+hop(t,0)))),(55,999,None)],
 'RF':[(0,5,None),(5,21.6,lambda t:climb_target('RF',S(t),COL_A)),(21.6,T_LAND-.5,None),(T_LAND-.5,T_LAND+.2,lambda t:leo_root(t)[0]+Vector((.14,.05,.12+.30*kit.jump_profile(t,T_LAND-.5,T_LAND+.2)['tuck']))),(T_LAND+.2,26.2,lambda t:Vector((XE+.14,-.28,LEDGE2_Z+.12))),(26.2,33.0,lambda t:climb_target('RF',S(t),COL_B)),(33.0,33.8,lambda t:Vector((3.3+.12,-.28,SLAB_Z+.12))),(33.8,45.9,None),(45.9,55.,lambda t:Vector((COL_C+.14,-.04,S(t)+.30+hop(t,math.pi)))),(55,999,None)]}
def limb_eval(limb,t,tr=.5):
 segs=SEG[limb];i=max(k for k,sg in enumerate(segs) if sg[0]<=t);t0,t1,fn=segs[i];prev=segs[i-1] if i else None
 if fn is None:
  if prev and prev[2] and t-t0<tr:return prev[2](t0),1-smooth((t-t0)/tr)
  return None,0.
 pos=fn(t)
 if prev is None or prev[2] is None:return pos,smooth((t-t0)/tr)
 if t-t0<tr:pos=prev[2](t0).lerp(pos,smooth((t-t0)/tr))
 return pos,1.
# ---------------------------------------------------------------------------------------------------------- the cliff
bpy.ops.mesh.primitive_plane_add(size=1,location=(10,6,-.05));g=bpy.context.object;g.scale=(120,90,1);put(g,(.25,.33,.14),'Ground')
bm=bmesh.new();NX,NZ=57,53;grid=[[bm.verts.new((-14+i*.5,ywall(-14+i*.5,j*.5),j*.5)) for j in range(NZ)] for i in range(NX)]
for i in range(NX-1):
 for j in range(NZ-1):bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]))
me=bpy.data.meshes.new('CliffMesh');bm.to_mesh(me);bm.free();cliff=bpy.data.objects.new('Cliff',me);link(cliff);me.materials.append(mat('Cliff',(.42,.38,.33)))
for p in me.polygons:p.use_smooth=False
prim('cube','CliffBack',(0,5,13),(.34,.31,.27),scale=(15,4.8,13.5))
for i in range(30):prim('cone','CliffPeak',(rnd.uniform(-40,50),rnd.uniform(25,70),rnd.uniform(2,18)),(.36,.34,.32),scale=(rnd.uniform(8,16),rnd.uniform(8,16),rnd.uniform(14,34)),vertices=6,radius1=1,depth=2)
ledge2=prim('cube','Ledge2',((LEDGE2[0]+LEDGE2[1])/2,-.7,LEDGE2_Z-.2),(.4,.36,.31),scale=((LEDGE2[1]-LEDGE2[0])/2,.7,.2))
slab=prim('cube','CubLedge',((SLAB[0]+SLAB[1])/2,-.8,SLAB_Z-.2),(.4,.36,.31),scale=((SLAB[1]-SLAB[0])/2,.8,.2))
prim('cone','Spur',(AX,-.2,13.9),(.36,.32,.28),scale=(.35,.35,.5),vertices=6,radius1=1,depth=2)
prim('cube','Peg',(XS,-.05,8.3),(.3,.2,.1),scale=(.05,.05,.05));prim('cyl','EyeBolt',(COL_C,-.12,14.0),(.2,.2,.2),scale=(.05,.05,.05),vertices=6,radius=1,depth=1)
for i in range(22):prim('sphere','Boulder',(rnd.uniform(-12,22),rnd.uniform(-12,-6),.3),(.4,.38,.35),scale=(rnd.uniform(.4,1.2),rnd.uniform(.4,1),rnd.uniform(.3,.7)),subdivisions=1)
for i in range(70):
 x=rnd.uniform(-12,26);y=rnd.uniform(-34,-15);prim('cone','Pine',(x,y,2.4),(.07,.26,.12),scale=(1.1,1.1,2.4),vertices=7,radius1=1,depth=2);prim('cyl','Trunk',(x,y,.5),(.3,.2,.1),scale=(.15,.15,.5),vertices=5,radius=1,depth=2)
allholds=[]
for col,lo,hi in ((COL_A,0,8),(COL_B,7,13.8),(COL_C,12.5,14.6)):
 for limb in LIMBS:
  for k in range(int((lo-LIMBS[limb]['off']*STEP)/STEP)-1,int((hi-LIMBS[limb]['off']*STEP)/STEP)+3):
   p=hold_abs(limb,k,col);allholds.append(p);prim('sphere','Hold',p+Vector((0,.03,0)),(.85,.62,.3),scale=(.09,.06,.07),subdivisions=1)
# ---------------------------------------------------------------------------------------------------------- sky, rain, lightning
scene.world=bpy.data.worlds.new('Sky');sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.rotation_euler=(math.radians(60),0,math.radians(-30))
for t,c,en,wc in ((0,(.55,.6,.75),1.0,(.14,.16,.22)),(52,(.55,.6,.75),1.0,(.14,.16,.22)),(56,(1,.85,.6),4.,(.55,.75,.95)),(seconds,(1,.85,.6),4.,(.55,.75,.95))):
 sun.data.color=c;sun.data.energy=en;scene.world.color=wc;sun.data.keyframe_insert('color',frame=F(t));sun.data.keyframe_insert('energy',frame=F(t));scene.world.keyframe_insert('color',frame=F(t))
STRIKES=[4.2,16.5,26.0,40.5];bolt_parts=[]
for t0 in STRIKES:
 top=Vector((rnd.uniform(-22,-12),rnd.uniform(14,22),44));end=Vector((top.x+rnd.uniform(-3,3),top.y-rnd.uniform(2,5),0));pts=[top.lerp(end,k/9)+(Vector((rnd.uniform(-1.8,1.8),rnd.uniform(-1.8,1.8),0)) if 0<k<9 else Vector()) for k in range(10)]
 for a,b in zip(pts,pts[1:]):
  d=b-a;o=prim('cyl','Bolt',(a+b)/2,(.85,.9,1),scale=(.08,.08,d.length/2),vertices=5,radius=1,depth=2,emit=8.);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();hide_keys(o,[(t0,t0+.2)])
 for off,en in ((-1,1.0),(0,10),(2,1.2),(4,7),(8,1.0)):
  sun.data.energy=en;sun.data.keyframe_insert('energy',frame=F(t0)+off)
  scene.world.color=(.75,.8,1) if off==0 else (.14,.16,.22);scene.world.keyframe_insert('color',frame=F(t0)+off)
bpy.ops.mesh.primitive_plane_add(size=60,location=(4,-2,32),rotation=(math.radians(10),0,0));rain_e=bpy.context.object;rain_e.name='RainEmitter';rain_e.display_type='WIRE'
bpy.ops.mesh.primitive_cylinder_add(vertices=4,radius=.012,depth=1.1,location=(0,0,-90));streak=bpy.context.object;streak.name='Streak';streak.data.materials.append(mat('Rain',(.75,.85,1),1.))
bpy.ops.object.select_all(action='DESELECT');rain_e.select_set(True);bpy.context.view_layer.objects.active=rain_e;bpy.ops.object.particle_system_add();ps=rain_e.particle_systems[0].settings
ps.count=6000;ps.frame_start=-40;ps.frame_end=frames;ps.lifetime=30;ps.emit_from='FACE';ps.normal_factor=-26.;ps.render_type='OBJECT';ps.instance_object=streak;ps.effector_weights.gravity=.1
hide_keys(rain_e,[(0,52)])
# ---------------------------------------------------------------------------------------------------------- characters
def load_char(tag):
 before=set(bpy.data.objects.keys())
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new(tag+'Root',None);link(root)
 for o in new:
  if o.parent is None:o.parent=root
  if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
 rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
 return root,rig,new
CLIPS={}
for c in ('look','idle','climb','pick','cele','jump'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
leo,rig,leo_objs=load_char('Leo');cub,crig,cub_objs=load_char('Cub')
def nla(rig,sched):
 tracks=[rig.animation_data.nla_tracks.new() for _ in range(2)]
 for k,(c,a,b,mode) in enumerate(sched):
  st=kit.add_strip(tracks[k%2],CLIPS[c],F(a)-(5 if k else 0),F(b),mode);st.extrapolation='HOLD' if k==0 else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
nla(rig,[('look',0,5,'loop'),('idle',5,T_LAND-.9,'loop'),('jump',T_LAND-.9,T_LAND+.9,'fit'),('idle',T_LAND+.9,34.8,'loop'),('climb',34.8,37.8,'loop'),('pick',37.8,42.8,'fit'),('climb',42.8,44.3,'loop'),('idle',44.3,55.2,'loop'),('cele',55.2,seconds,'fit')])
nla(crig,[('look',0,41,'loop'),('idle',41,seconds,'loop')])
# Leo root path
def heading_at(t):   # from +x: pi/2 faces the wall (+y), 0 faces +x
 if t<33.8:return math.pi/2
 if t<34.8:return math.pi/2*(1-smooth(t-33.8))
 if t<44.3:return 0.
 if t<45.3:return math.pi/2*smooth(t-44.3)
 return math.pi/2
def leo_root(t):
 if t<19.6:x,z=COL_A,S(t)
 elif t<T_SW0:x=COL_A+(XS-COL_A)*smooth((t-19.6)/.8);z=7.0;
 elif t<T_LAND-.5:P=rope_end(t);x,z=P.x,P.z-1.3
 elif t<T_LAND+.2:
  P=rope_end(T_LAND-.5);u=(t-(T_LAND-.5))/.7;x=(P.x)+(XE-P.x)*u;z=(P.z-1.3)+(7.0-(P.z-1.3))*u+kit.ballistic(u,kit.flight_apex(.7))
 elif t<26.2:x,z=XE,7.0
 elif t<33.0:x,z=COL_B,S(t)
 elif t<33.8:x,z=COL_B+.5*smooth((t-33)/.8),SLAB_Z
 elif t<34.8:x,z=3.5,SLAB_Z
 elif t<37.8:x,z=3.5+3.7*smooth((t-34.8)/3.),SLAB_Z
 elif t<42.8:x,z=7.2,SLAB_Z
 elif t<44.3:x,z=7.2+1.3*smooth((t-42.8)/1.5),SLAB_Z
 elif t<45.3:x,z=8.5,SLAB_Z
 elif t<46.3:x,z=8.5+1.1*smooth(t-45.3),SLAB_Z
 else:x,z=COL_C,S(t)
 if (7<t<20 or 26.7<t<33) and t not in(): x+=.035*math.sin(math.pi*S(t)/STEP)
 jp=kit.jump_profile(t,T_LAND-.5,T_LAND+.2)
 if t>T_LAND+.2 or t<T_LAND-.5:z+=jp['dz']*(t>T_LAND+.2)
 if t>55:z=0.
 return Vector((x,ROOT_Y,z)),heading_at(t)
for f in range(1,frames+1,2):
 p,h=leo_root((f-1)/fps);leo.location=p;leo.rotation_euler=(0,0,h+math.pi/2);leo.keyframe_insert('location',frame=f);leo.keyframe_insert('rotation_euler',frame=f)
# IK: arms and legs of the climber follow grip targets; poles keep elbows and knees out of the way
IK={};targets={}
for limb,bone,chain in (('RH','RightForeArm',2),('LH','LeftForeArm',2),('LF','LeftLeg',2),('RF','RightLeg',2)):
 tg=bpy.data.objects.new('Grip_'+limb,None);tg.empty_display_size=.06;link(tg);targets[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=leo;sgn=1 if limb[0]=='L' else -1   # local x of Leo's left is positive
 pole.location=((.55*sgn,.55,1.0) if limb[1]=='H' else (.45*sgn,-.9,.55))
 c=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');c.target=tg;c.pole_target=pole;c.pole_angle=math.radians(-90 if limb[0]=='L' else 90);c.chain_count=chain;c.use_stretch=False;IK[limb]=c
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for limb in LIMBS:
  pos,infl=limb_eval(limb,t)
  if pos is not None:targets[limb].location=pos;targets[limb].keyframe_insert('location',frame=f)
  IK[limb].influence=infl;IK[limb].keyframe_insert('influence',frame=f)
# the cub waits on the slab, then rides on Leo's back
CUB_SLAB=Vector((8.1,-.55,SLAB_Z));cub.scale=(.45,.45,.45)
def cub_pose(f):
 """The cub waits on the slab, is lifted in Leo's right hand (40.2 to 41.2), held, then settled on his back (41.8 to 42.7) and rides there, always following the bones."""
 t=(f-1)/fps
 if t<40.2:return CUB_SLAB,math.pi
 scene.frame_set(f);bpy.context.view_layer.update();h=leo_root(t)[1];ang=h+math.pi/2
 hand=rig.matrix_world@rig.pose.bones['mixamorig:RightHand'].head+Vector((0,0,-.10));sp=rig.matrix_world@rig.pose.bones['mixamorig:Spine1'].head
 back=sp+Vector((-.30*math.cos(h),-.30*math.sin(h),.06))
 if t<41.2:return CUB_SLAB.lerp(hand,smooth((t-40.2)/1.0)),math.pi+(ang-math.pi)*smooth((t-40.2)/1.0)
 if t<41.8:return hand,ang
 if t<42.7:return hand.lerp(back,smooth((t-41.8)/.9)),ang
 return back,ang
for f in range(1,F(40.0),30):
 cub.location=CUB_SLAB;cub.rotation_euler=(0,0,math.pi);cub.keyframe_insert('location',frame=f);cub.keyframe_insert('rotation_euler',frame=f)
for f in range(F(40.0),frames+1,2):
 pos,ang=cub_pose(f);cub.location=pos;cub.rotation_euler=(0,0,ang);cub.keyframe_insert('location',frame=f);cub.keyframe_insert('rotation_euler',frame=f)
# ropes
ropeA=rope_obj('RopeSwing');ropeC=rope_obj('RopeRappel');fray=[prim('cube','Fray',(0,0,0),(.62,.5,.3),scale=(.012,.012,.2)) for _ in range(5)]
for f in range(1,frames+1,2):
 t=(f-1)/fps;set_rope(ropeA,ANCHOR,rope_end(t),f)
set_rope(ropeC,Vector((COL_C,-.2,14.0)),Vector((COL_C,-.2,.2)),1);hide_keys(ropeC,[(44.0,seconds)])
FRAY_Z=S(49.6)+1.15
for i,o in enumerate(fray):
 a=Vector((COL_C+(i-2)*.03,-.2,FRAY_Z+.25));b=Vector((COL_C+(i-2)*.12,-.2+rnd.uniform(-.06,.06),FRAY_Z-.35));d=b-a;o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.scale=(.012,.012,d.length/2);hide_keys(o,[(49.6,seconds)])
# ---------------------------------------------------------------------------------------------------------- falling rocks: real rigid bodies, baked
bpy.ops.rigidbody.world_add();rw=scene.rigidbody_world;rw.point_cache.frame_start=1;rw.point_cache.frame_end=frames
for o,sh in ((cliff,'MESH'),(ledge2,'BOX'),(slab,'BOX'),(bpy.data.objects['Ground'],'BOX')):
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add(type='PASSIVE');o.rigid_body.collision_shape=sh;o.rigid_body.friction=.7;o.select_set(False)
ROCKS=[];REL=[27.5,28.4,29.2,30.0]
for i,(rx,rt) in enumerate(zip((2.0,1.4,2.3,.9),REL)):
 r=prim('sphere','Rock',(rx,-.30,22.5),(.46,.42,.38),scale=(.35,.3,.32),subdivisions=1);bpy.context.view_layer.objects.active=r;r.select_set(True);bpy.ops.rigidbody.object_add(type='ACTIVE')
 r.rigid_body.collision_shape='CONVEX_HULL';r.rigid_body.mass=60;r.rigid_body.friction=.6;r.rigid_body.restitution=.3;r.rigid_body.kinematic=True;r.rigid_body.keyframe_insert('kinematic',frame=1)
 r.rigid_body.kinematic=False;r.rigid_body.keyframe_insert('kinematic',frame=F(rt));ROCKS.append((r,rt));r.select_set(False)
# ---------------------------------------------------------------------------------------------------------- cameras
CUTS=[('1 Storm and cliff',0,5),('2 The first hold',5,7.2),('3 Climbing',7.2,17),('4 The rope',17,22.4),('5 Swing',22.4,25.3),('6 Landing',25.3,27.5),('7 Rocks fall',27.5,33),('8 The slab',33,37.8),('9 The cub',37.8,43),('10 Off the ledge',43,46.3),('11 Rappel',46.3,55),('12 Sun',55,seconds)]
cams=[]
def leo_head(t):
 p,h=leo_root(t);return p+Vector((0,0,1.0))
for k,(name,a,b) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=2500;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(min(b,seconds))+1,3):
  t=(f-1)/fps;u=(t-a)/(b-a);lh=leo_head(t);cam.data.lens=32
  if k==0:p=Vector((-8+6*u,-34,12));q=Vector((3,0,11));cam.data.lens=24
  elif k==1:p=Vector((COL_A+1.9,-3.8,1.7));q=Vector((COL_A,0,1.0));cam.data.lens=34
  elif k==2:p=Vector((COL_A-5.5,-6.5,lh.z+1.5));q=lh+Vector((0,0,.2));cam.data.lens=30
  elif k==3:p=Vector((-5.2,-5.5,8.8));q=Vector((XS+.2,0,8.4));cam.data.lens=34
  elif k==4:p=Vector((AX,-15,9));q=Vector((AX,0,9.2));cam.data.lens=28
  elif k==5:p=Vector((6.6,-4.2,8.4));q=Vector((3.0,0,7.8));cam.data.lens=32
  elif k==6:p=Vector((9.5,-9.5,lh.z+.5));q=lh+Vector((-.8,0,1.8));cam.data.lens=24
  elif k==7:p=Vector((6,-6.5,SLAB_Z+2.2));q=lh+Vector((0,0,.2));cam.data.lens=32
  elif k==8:p=Vector((5.4,-4.4,SLAB_Z+1.6));q=Vector((7.7,-.3,SLAB_Z+.8));cam.data.lens=40
  elif k==9:p=Vector((8,-6.5,SLAB_Z+2.0));q=lh;cam.data.lens=32
  elif k==10:p=Vector((COL_C+5.5,-6.5,max(2.5,lh.z-2.5)));q=lh+Vector((0,0,.4));cam.data.lens=32
  else:p=Vector((COL_C-4+3*u,-9,1.6));q=Vector((COL_C,-.3,1.4));cam.data.lens=30
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ---------------------------------------------------------------------------------------------------------- bake the rocks, audit the grips
scene.frame_set(1)
try:bpy.ops.ptcache.bake_all(bake=True);print('rocks baked')
except Exception as ex:print('bake skipped',ex)
impacts=[]
for r,rt in ROCKS:
 last=None
 for f in range(F(rt),min(frames,F(rt)+150)):
  scene.frame_set(f);z=r.matrix_world.translation.z
  if last is not None and last[0]-z<-.02 and last[1] and last[1]>.12:impacts.append(((f-1)/fps,abs(last[1])))
  vz=(z-(last[0] if last else z))*fps;last=(z,vz if last else 0.)
rocks_hit=sorted(impacts)[:12];print('ROCKS',[(round(a,1),round(b,1)) for a,b in rocks_hit])
issues=[]
def grip_audit():
 worst={}
 for f in range(1,frames+1,4):
  t=(f-1)/fps
  scene.frame_set(f);bpy.context.view_layer.update()
  for limb,bone in (('RH','RightForeArm'),('LH','LeftForeArm'),('LF','LeftLeg'),('RF','RightLeg')):
   pos,infl=limb_eval(limb,t)
   if pos is None or infl<.99:continue
   pb=rig.pose.bones['mixamorig:'+bone];tail=rig.matrix_world@pb.tail;d=(tail-pos).length
   if d>worst.get(limb,(0,0))[0]:worst[limb]=(d,t)
 for limb,(d,t) in worst.items():
  if d>.07:issues.append('AUDIT grip: %s misses its hold by %.0f cm at t=%.1f s (unreachable or pole wrong)'%(limb,d*100,t))
 return worst
worst=grip_audit();print('GRIP',{k:(round(v[0]*100,1),round(v[1],1)) for k,v in worst.items()})
issues+=kit.audit(scene,bodies=[(rig,max((o for o in leo_objs if o.type=='MESH'),key=lambda o:len(o.data.vertices)))],floor_z=0.,skip=[(5,54.5)],subjects=[leo,cub],step=12)
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_cliff');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(4)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
calm=np.clip((tt-52)/4,0,1);wind=lp(nr.standard_normal(N_),30)*(1.1-.8*calm)*(1+.4*np.sin(tt*.6));rain=(nr.standard_normal(N_)-lp(nr.standard_normal(N_),12))*.22*np.clip((tt-1)/3,0,1)*(tt<52)
th=np.zeros(N_+SR*6)
for t0 in STRIKES:
 n=int(3.2*SR);k=np.arange(n)/SR;x=lp(nr.standard_normal(n),160)*np.exp(-k*.9)*np.minimum(k/.05,1)*3+np.sin(2*np.pi*46*k)*np.exp(-k*1.4)*2;i=int((t0+.8)*SR);th[i:i+n]+=x
th=th[:N_]
rk=np.zeros(N_+SR);
for ti,v in rocks_hit:
 n=int(.5*SR);k=np.arange(n)/SR;x=(lp(nr.standard_normal(n),30)*np.exp(-k*10)+np.sin(2*np.pi*(90-60*k)*k)*np.exp(-k*8))*min(1.,v/6+.3);i=int(ti*SR);rk[i:i+n]+=x
rk=rk[:N_]
ticks=np.zeros(N_+SR);tk=np.arange(int(.05*SR))/SR;tick=np.sin(2*np.pi*400*tk)*np.exp(-tk*80)+.3*nr.standard_normal(len(tk))*np.exp(-tk*90)
for limb in LIMBS:
 prev=None
 for f in range(1,frames,2):
  t=(f-1)/fps;seg=[sg for sg in SEG[limb] if sg[0]<=t<sg[1]][0]
  if seg[2] is None or seg[0] in(20.0,20.8,45.5,45.9):prev=None;continue
  if seg[0] in (5,26.2):
   L=LIMBS[limb];k=math.floor((S(t)-L['off']*STEP)/STEP)
   if prev is not None and k!=prev and (f-1)/fps<54:
    i=int(t*SR);ticks[i:i+len(tick)]+=tick*.5
   prev=k
ticks=ticks[:N_]
def meow(t0,n_=1.1):
 n=int(n_*SR);k=np.arange(n)/SR;f=700+250*np.sin(np.pi*k/n_)+60*np.sin(2*np.pi*7*k);ph=2*np.pi*np.cumsum(f)/SR;x=(np.sin(ph)+.4*np.sin(2*ph))*np.sin(np.pi*k/n_)**.7;tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=x[:max(0,min(n,N_-i))];return tr
voice=meow(1.5)+meow(3.2,.8)*.8+meow(34.5,1.2)+meow(38.6,.9)*.7+meow(53.5,.9)*.5
creak=np.sin(2*np.pi*(150+50*np.sin(tt*3.1))*tt)*np.clip(np.sin((tt-20)*2.4),0,1)**3*.12*((tt>20)&(tt<26)|(tt>46)&(tt<55))
fraysnd=np.zeros(N_);i=int(49.7*SR);n=int(.4*SR);fraysnd[i:i+n]=nr.standard_normal(n)*np.exp(-np.arange(n)/SR*9)*.8
note=lambda f,d,v=1.:(lambda k:(np.sin(2*np.pi*f*k)+.4*np.sin(4*np.pi*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=54.9 else minor[ci%4];vol=.4 if t0<20 else .7 if t0<54 else .5
 for j,f0 in enumerate(chord):
  n_=note(f0,2.6,vol*.5);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
 if 46<=t0<=54:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.2*SR))/SR;kk=np.sin(2*np.pi*(55*kt-90*kt**2))*np.exp(-kt*20)
   if i<N_:music[i:i+len(kk)]+=kk*1.3
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('wind_rain.wav',wind+rain,.8),wav('thunder.wav',th,.95),wav('rocks.wav',rk,.9),wav('grips.wav',ticks+creak+fraysnd,.7),wav('cub.wav',voice,.7),wav('music.wav',music,.5)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('wind and rain','thunder','falling rocks','grips and rope','cub','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('CLIFF_DONE',frames,'frames')
