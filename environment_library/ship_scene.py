"""Blender script: 'The Storm Ship' - Leo the lookout cuts a torn sail loose in a storm, falls, and fights a sea serpent until lightning ends it (60 s).

blender -b --disable-autoexec --python ship_scene.py -- <ship_assets_dir> <out.blend> [seconds=60]

Everything is procedural low poly (ship, ocean with Wave modifiers, serpent that follows its own head path, rain particles, lightning) except Leo, whose clips
come from the normal pipeline (build_ship_assets.py). Leo and all cameras are parented to the ship, so the deck tilts under his feet. Climbing the mast
uses the walk clip with the body pitched along the mast (no real climb clip in the pipeline yet)."""
import bpy,math,random,sys,os,wave
import numpy as np
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 60.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(5)
def F(t):return 1+int(round(t*fps))
def smooth(u):u=max(0.,min(1.,u));return u*u*(3-2*u)
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
ship=bpy.data.objects.new('Ship',None);link(ship)
def put(o,color,name,emit=0.,parent=True):
 o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color,emit))
 if parent:o.parent=ship
 return o
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=True,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;return put(o,color,name,emit,parent)
def line(a,b,r,color,name='Rope',emit=0.,parent=True):
 a,b=Vector(a),Vector(b);d=b-a;o=prim('cyl',name,(a+b)/2,color,scale=(r,r,d.length/2),vertices=5,radius=1,depth=2,emit=emit,parent=parent);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def hide_keys(o,windows):
 """windows: [(t0,t1)] during which o is visible."""
 vis=lambda t:any(a<=t<b for a,b in windows)
 last=None
 for f in range(1,frames+1):
  v=vis((f-1)/fps)
  if v!=last:
   for prop in ('hide_viewport','hide_render'):setattr(o,prop,not v);o.keyframe_insert(prop,frame=f)
   last=v
# ---------------------------------------------------------------------------------------------------------- ship
L=9.;HB=3.2;DZ=1.6;MAST_X=-.4;CLIMB_Z=8.6
def storm(t):   # 0..1 storm strength
 return .22+.78*smooth((t-2)/9.)*(1-smooth((t-50)/5.)*.8) if t<54 else .2
def hull():
 import bmesh
 bm=bmesh.new();stations=[-L+i*L*2/16 for i in range(17)];rows=[]
 for x in stations:
  u=x/L;b=HB*max(.02,(1-u**4))**.65*(1 if x<0 else 1-.25*u*u);zd=DZ+.9*max(0,u)**3+.5*max(0,-u)**2;keel=-1.5*(1-.5*max(0,u)**2)
  rows.append([bm.verts.new(v) for v in ((x,-b,zd),(x,-b*.8,zd*.35+keel*.2),(x,0,keel),(x,b*.8,zd*.35+keel*.2),(x,b,zd))])
 for r0,r1 in zip(rows,rows[1:]):
  for k in range(4):
   try:f=bm.faces.new((r0[k],r0[k+1],r1[k+1],r1[k]));f.material_index=0
   except ValueError:pass
 try:bm.faces.new(rows[0][::-1])
 except ValueError:pass
 me=bpy.data.meshes.new('HullMesh');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('Hull',me);link(o);o.parent=ship;me.materials.append(mat('Hull',(.28,.15,.07)));return o
hull()
deck=prim('cube','Deck',(0,0,DZ-.04),(.58,.4,.2),scale=(L*.93,HB*.8,.05))
for i in range(-8,9):prim('cube','Plank',(i*1.0,0,DZ+.012),(.45,.3,.14),scale=(.02,HB*.78,.01))
for s in (-1,1):   # rails
 line((-L*.9,s*HB*.9,DZ+.9),(L*.78,s*HB*.8,DZ+.9),.05,(.35,.2,.1),'Rail')
 for x in np.linspace(-L*.9,L*.75,9):line((x,s*HB*.9*(1-max(0,x/L)**2*.1),DZ),(x,s*HB*.9*(1-max(0,x/L)**2*.1),DZ+.9),.04,(.35,.2,.1),'Post')
prim('cube','Cabin',(-7.0,0,DZ+.6),(.5,.3,.14),scale=(1.4,HB*.75,.6));prim('cube','CabinRoof',(-7.0,0,DZ+1.25),(.38,.22,.1),scale=(1.55,HB*.82,.07))
wheel_pos=Vector((-5.2,0,DZ));prim('cyl','WheelRing',(-5.4,0,DZ+1.15),(.4,.25,.1),scale=(.5,.5,.04),rot=(0,math.pi/2,0),vertices=14,radius=1,depth=2)
for k in range(4):a=k*math.pi/4;line((-5.4,math.cos(a)*.55,DZ+1.15+math.sin(a)*.55),(-5.4,-math.cos(a)*.55,DZ+1.15-math.sin(a)*.55),.03,(.4,.25,.1),'Spoke')
prim('cyl','WheelPost',(-5.4,0,DZ+.55),(.3,.18,.08),scale=(.1,.1,.55),vertices=6,radius=1,depth=2)
MASTS=[(MAST_X,12.,'Main'),(4.4,9.5,'Fore'),(-5.3,8.,'Mizzen')]
for x,h,n in MASTS:
 prim('cyl',n+'Mast',(x,0,DZ+h/2),(.35,.22,.1),scale=(.22,.22,h/2),vertices=8,radius=1,depth=2)
 yv=DZ+h*.62;prim('cyl',n+'Yard',(x,0,yv),(.35,.22,.1),scale=(.1,.1,HB*1.1),rot=(math.pi/2,0,0),vertices=6,radius=1,depth=2)
 for s in (-1,1):line((x,0,DZ+h),(x-.5,s*HB*.85,DZ+.9),.025,(.15,.1,.07),'Shroud');line((x,0,DZ+h),(x+(2.5 if n!='Mizzen' else -1.5),0,DZ+.9),.025,(.15,.1,.07),'Stay')
def sail(name,x,yv,w,h,flap):
 bpy.ops.mesh.primitive_grid_add(x_subdivisions=14,y_subdivisions=10,size=1,location=(x+(-.45 if x==MAST_X else .45),0,yv-h/2),rotation=(0,math.pi/2,0));o=bpy.context.object;o.scale=(h,w,1)
 put(o,(.85,.8,.68),name);m=o.modifiers.new('Flap','WAVE');m.height=flap;m.width=1.5;m.speed=.25;m.narrowness=3.;m.use_normal=True;return o
mainsail=sail('MainSail',MAST_X,DZ+12*.62,HB*1.9,6.5,.28);sail('ForeSail',4.4,DZ+9.5*.62,HB*1.7,5.2,.2);sail('MizzenSail',-5.3,DZ+8*.62,HB*1.4,4.2,.15)
TORN=prim('cube','TornSail',(MAST_X-.45,.8,DZ+12*.62-1.6),(.85,.8,.68),scale=(.02,HB*.65,1.8))   # the strip that stays on the yard after the cut
for k in range(14):prim('cube','Rung',(.1,0,DZ+.5+k*.55),(.4,.25,.1),scale=(.04,.7,.03));
# ---------------------------------------------------------------------------------------------------------- the sea
bpy.ops.mesh.primitive_grid_add(x_subdivisions=170,y_subdivisions=170,size=320,location=(0,0,0));sea=bpy.context.object;sea.name='Sea';sea.data.materials.append(mat('Sea',(.06,.2,.3)))
for k,(h,w,sp,x0) in enumerate(((1.3,16,.55,0),(.5,6,.9,3))):
 m=sea.modifiers.new('Wave%d'%k,'WAVE');m.height=h;m.width=w;m.speed=sp;m.narrowness=1.6;m.start_position_x=-80;m.start_position_y=30+k*20;m.use_normal=True
 for t,sc in ((0,.25),(11,1.),(50,1.),(56,.2)):m.height=h*sc;m.keyframe_insert('height',frame=F(t))
for p in sea.data.polygons:p.use_smooth=False
# ---------------------------------------------------------------------------------------------------------- ship motion
for f in range(1,frames+1,2):
 t=(f-1)/fps;e=storm(t)
 ship.location=(0,0,.55*e*math.sin(2*math.pi*t/4.7)-.1);ship.rotation_euler=(math.radians(9*e*math.sin(2*math.pi*t/5.5)+2.5*e*math.sin(2*math.pi*t/3.1)),math.radians(4.5*e*math.sin(2*math.pi*t/4.3+1)),math.radians(2*e*math.sin(2*math.pi*t/9.)))
 ship.keyframe_insert('location',frame=f);ship.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo (one rig, clips on the NLA, ship-local root path)
CLIPS=['look','run','climb','cut','fall','hit','getup','dodge','punch','cele','idle']
with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
new=[]
for o in dst.objects:
 if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
 link(o);new.append(o)
leo=bpy.data.objects.new('LeoRoot',None);link(leo);leo.parent=ship
for o in new:
 if o.parent is None:o.parent=leo
 if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
acts={}
for c in CLIPS:
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 acts[c]=dst.actions[0]
SCHEDULE=[('look',0,9,'loop'),('run',9,11.6,'loop'),('climb',11.6,19,'loop'),('cut',19,22.2,'fit'),('fall',22.2,25.2,'fit'),('getup',25.2,28.2,'fit'),('climb',28.2,31.4,'loop'),('dodge',31.4,34.4,'fit'),('idle',34.4,37.6,'loop'),
 ('punch',37.6,40.6,'fit'),('idle',40.6,44.3,'loop'),('hit',44.3,47.3,'fit'),('idle',47.3,49,'loop'),('climb',49,55,'loop'),('cele',55,seconds,'fit')]
tracks=[rig.animation_data.nla_tracks.new() for _ in range(2)]
for k,(c,a,b,mode) in enumerate(SCHEDULE):
 if a>=seconds:break
 act=acts[c];b=min(b,seconds);start=F(a)-(5 if k else 0);end=F(b);length=act.frame_range[1]-act.frame_range[0]+1
 st=tracks[k%2].strips.new('%s%d'%(c,k),start,act);st.action_slot=act.slots[0]
 if mode=='fit':st.scale=(end-start)/length;st.repeat=1
 else:st.repeat=max(1.,(end-start)/length)
 st.extrapolation='HOLD' if k==0 else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
def keyp(pts,t):   # smooth path through (time, vector) keys, Catmull-Rom with clamped ends
 ts=[p[0] for p in pts]
 if t<=ts[0]:return Vector(pts[0][1])
 if t>=ts[-1]:return Vector(pts[-1][1])
 i=max(k for k in range(len(ts)) if ts[k]<=t);u=(t-ts[i])/(ts[i+1]-ts[i]);p=lambda j:Vector(pts[max(0,min(len(pts)-1,j))][1])
 p0,p1,p2,p3=p(i-1),p(i),p(i+1),p(i+2);return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3)
LX=3.0
def leo_state(t):
 """ship-local position, body pitch (rad) and heading (rad from +x) of Leo."""
 s=lambda a,b,u:Vector(a).lerp(Vector(b),smooth(u))
 if t<9:return Vector((6.4,.6,DZ)),0,0.
 if t<11.6:return s((6.4,.6,DZ),(.3,0,DZ),(t-9)/2.6),0,math.pi*smooth((t-9)/.5)
 if t<19:u=(t-11.6)/7.4;return Vector((.3,0,DZ+(CLIMB_Z-DZ)*u)),-1.35*smooth((t-11.6)/.6),math.pi
 if t<22.2:return Vector((.3,0,CLIMB_Z)),-1.35,math.pi
 if t<23.1:u=(t-22.2)/.9;return Vector((.3-.15*u,0,CLIMB_Z-(CLIMB_Z-DZ)*u*u)),-1.35*(1-smooth(u)),math.pi
 if t<28.2:return Vector((.15,0,DZ)),0,math.pi*(1-smooth((t-27.8)/.8))
 if t<31.4:return s((.15,0,DZ),(LX,0,DZ),(t-28.2)/3.2),0,0.
 if t<44.3:return Vector((LX+(.55 if t>37.6 else 0),0,DZ)),0,0.
 if t<47.3:return Vector((LX+.55-1.2*smooth((t-44.3)/.6),0,DZ)),0,0.
 if t<49:return Vector((LX-.65,0,DZ)),0,math.pi*smooth((t-47.8)/1.2)
 if t<55:return s((LX-.65,0,DZ),(-4.6,0,DZ),(t-49)/6.),0,math.pi
 return Vector((-4.6,0,DZ)),0,math.pi
for f in range(1,frames+1,2):
 p,pitch,h=leo_state((f-1)/fps);leo.location=p;leo.rotation_euler=(pitch,0,h+math.pi/2);leo.keyframe_insert('location',frame=f);leo.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- the serpent: its body follows its head's path
HEAD=[(-8,(-6,14,-14)),(22,(-5,14,-12)),(26,(-4,12,-6)),(29,(-4,9,1)),(31,(-3,8,8)),(32.2,(-.5,5,10)),(32.9,(3.4,.6,2.1)),(34.6,(3.8,.9,2.4)),(36,(4,5,8.5)),(37.4,(5.4,.8,3.4)),
 (39.4,(5.8,.1,3.1)),(40.6,(6,5,6)),(41.5,(9,5.5,3)),(42.4,(11,0,2.6)),(43.2,(9,-5,3)),(43.9,(1,-6,3.4)),(44.3,(2,0,15)),(45.5,(3,3,11)),(47,(3,7,5)),(49,(2,9,-3)),(51,(2,12,-11)),(56,(2,14,-22)),(70,(2,14,-30))]
N=44;LAG=.075;serp=[]
def hp(t):return keyp(HEAD,t)
for i in range(N+1):
 r=.75*(1-.62*i/N) if i else .72;o=prim('sphere','Serp%d'%i,(0,0,-30),(.12,.32,.2) if i%3 else (.18,.4,.25),scale=(r,r*1.2,r),subdivisions=2) ;serp.append(o)
head=serp[0];head.scale=(.8,1.4,.7);jaw=prim('cube','Jaw',(0,0,0),(.1,.25,.15),scale=(.45,.9,.12));jaw.parent=head;jaw.location=(0,.8,-.45)
for s in (-1,1):
 e=prim('sphere','SerpEye',(0,0,0),(1,.85,.1),scale=(.1,.1,.1),emit=5.,subdivisions=1);e.parent=head;e.location=(s*.55,.55,.42)
 hn=prim('cone','SerpHorn',(0,0,0),(.7,.65,.5),scale=(.12,.12,.45),vertices=5,radius1=1,depth=2);hn.parent=head;hn.location=(s*.4,-.2,.75)
hn=None
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for i,o in enumerate(serp):
  o.location=hp(t-i*LAG*(1 if i else 0.9));o.keyframe_insert('location',frame=f)
 d=hp(t+.15)-hp(t-.05);head.rotation_euler=d.to_track_quat('Y','Z').to_euler();head.keyframe_insert('rotation_euler',frame=f)
 jaw.rotation_euler=(math.radians(18+22*math.sin(t*5.) if 29<t<40.8 or 44<t<47 else 4),0,0);jaw.keyframe_insert('rotation_euler',frame=f)
# the sail cut loose: the main sail flies off in the wind and the torn strip stays
mainsail.hide_viewport=False
hide_keys(mainsail,[(0,20.6)]);hide_keys(TORN,[(20.6,seconds)])
flap=prim('cube','CutSail',(0,0,0),(.85,.8,.68),scale=(.02,HB*.9,3.2));flap.data.materials.clear();flap.data.materials.append(mat('Sail',(.85,.8,.68)))
for tt,p,rot in ((20.6,(MAST_X-.5,0,DZ+12*.62-3.2),(0,0,0)),(21.6,(MAST_X+6,-3,DZ+11),(.6,.3,1)),(23.2,(MAST_X+14,-9,DZ+9),(1.4,.9,2.4)),(25,(MAST_X+24,-18,1),(2.3,1.4,4)),(26,(MAST_X+26,-19,-4),(2.6,1.5,4.5))):
 flap.location=p;flap.rotation_euler=rot;flap.keyframe_insert('location',frame=F(tt));flap.keyframe_insert('rotation_euler',frame=F(tt))
hide_keys(flap,[(20.6,26)])
# ---------------------------------------------------------------------------------------------------------- sky, rain, lightning
scene.world=bpy.data.worlds.new('Sky')
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.rotation_euler=(math.radians(55),0,math.radians(30))
for t,c,en,wc in ((0,(.7,.75,.85),1.6,(.45,.5,.58)),(8,(.45,.5,.65),.7,(.12,.14,.2)),(50,(.45,.5,.65),.7,(.1,.12,.18)),(54,(1,.85,.6),4.,(.55,.75,.95)),(seconds,(1,.85,.6),4.,(.55,.75,.95))):
 sun.data.color=c;sun.data.energy=en;scene.world.color=wc
 for tt in (F(t),):sun.data.keyframe_insert('color',frame=tt);sun.data.keyframe_insert('energy',frame=tt);scene.world.keyframe_insert('color',frame=tt)
STRIKES=[(14.,None),(27.,None),(41.,None),(44.,'serpent')]
bolt_mat=mat('Bolt',(.85,.9,1),8.)
for t0,target in STRIKES:
 x=rnd.uniform(-8,10);top=Vector((x+rnd.uniform(-4,4),rnd.uniform(-20,20),34));end=Vector((x,rnd.uniform(-6,6),0)) if not target else hp(t0+.25)
 if not target:end.x+=rnd.uniform(-20,20);end.y+=rnd.choice((-1,1))*rnd.uniform(15,35)
 pts=[top.lerp(end,k/9)+(Vector((rnd.uniform(-1.8,1.8),rnd.uniform(-1.8,1.8),0)) if 0<k<9 else Vector()) for k in range(10)];parts=[line(a,b,.1 if target else .06,(.85,.9,1),'Bolt',emit=8.) for a,b in zip(pts,pts[1:])]
 for o in parts:hide_keys(o,[(t0,t0+.2)])
 for tt,en,wc in ((t0-.04,sun.data.energy,None),(t0,9.,(.8,.85,1)),(t0+.08,1.,None),(t0+.14,6.,(.7,.75,.95)),(t0+.3,.7,(.1,.12,.18))):
  pass
 fr0=F(t0)
 for off,en in ((-1,.7),(0,10),(2,1.2),(4,7),(8,.7)):
  sun.data.energy=en;sun.data.keyframe_insert('energy',frame=fr0+off)
  if off in (0,4):scene.world.color=(.75,.8,1) if off==0 else (.5,.55,.75);scene.world.keyframe_insert('color',frame=fr0+off)
  if off==8:scene.world.color=(.1,.12,.18);scene.world.keyframe_insert('color',frame=fr0+off)
bpy.ops.mesh.primitive_plane_add(size=90,location=(0,0,28),rotation=(math.radians(12),0,0));rain_e=bpy.context.object;rain_e.name='RainEmitter';rain_e.display_type='WIRE'
bpy.ops.mesh.primitive_cylinder_add(vertices=4,radius=.012,depth=1.1,location=(0,0,-90));streak=bpy.context.object;streak.name='Streak';streak.data.materials.append(mat('Rain',(.75,.85,1),1.))
bpy.ops.object.select_all(action='DESELECT');rain_e.select_set(True);bpy.context.view_layer.objects.active=rain_e;bpy.ops.object.particle_system_add();ps=rain_e.particle_systems[0].settings
ps.count=7000;ps.frame_start=-40;ps.frame_end=frames;ps.lifetime=26;ps.emit_from='FACE';ps.normal_factor=-26.;ps.render_type='OBJECT';ps.instance_object=streak;ps.particle_size=1.;ps.use_rotation_instance=True if hasattr(ps,'use_rotation_instance') else None;ps.effector_weights.gravity=.1
for t,vis in ((0,True),(4,True),(51.5,False)):
 pass
hide_keys(rain_e,[(0,51.5)])
# ---------------------------------------------------------------------------------------------------------- cameras
LEO_HEAD=lambda t:leo_state(t)[0]+Vector((0,0,.7 if abs(leo_state(t)[1])<.5 else .2))
WHEEL=wheel_pos+Vector((0,0,1.3))
CUTS=[('1 Storm ship, orbit',0,5,'world'),('2 Leo on lookout',5,9,'ship'),('3 Leo runs to the mast',9,11.6,'ship'),('4 Climbing',11.6,19,'ship'),('5 Cutting the sail',19,22.2,'ship'),('6 The fall',22.2,28.2,'ship'),
 ('7 The serpent rises',28.2,31.4,'ship'),('8 The strike',31.4,35,'ship'),('9 Fist to snout',35,41,'ship'),('10 The coil',41,44.2,'world'),('11 Lightning',44.2,48,'ship'),('12 It sinks',48,53,'ship'),('13 Calm, at the wheel',53,seconds,'ship')]
cams=[]
for k,(name,a,b,kind) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=2000;link(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.parent=ship;aim.hide_viewport=True
 if kind=='ship':cam.parent=ship
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y';cams.append(cam)
 for f in range(F(a),F(min(b,seconds))+1,3):
  t=(f-1)/fps;u=(t-a)/(b-a);lp=LEO_HEAD(t);hd=hp(t);cam.data.lens=32
  if k==0:ang=math.radians(-70+40*u);p=Vector((math.cos(ang)*38,math.sin(ang)*38,11));q=Vector((0,0,5))
  elif k==1:p=Vector((8.7,-2.6,2.9));q=lp;cam.data.lens=40
  elif k==2:p=Vector((3.5,-5.5,3.0));q=lp;cam.data.lens=34
  elif k==3:p=Vector((3.2,-4.2,2.4+(lp.z-DZ)*.35));q=lp+Vector((-.3,0,0));cam.data.lens=30
  elif k==4:p=Vector((4.5,-5.5,CLIMB_Z+.8));q=Vector((MAST_X,0,CLIMB_Z+1.5));cam.data.lens=32
  elif k==5:p=Vector((-3.8,4.2,3.4));q=lp
  elif k==6:p=Vector((6.5,-9,3.2));q=Vector((-3.4,9,6.5));cam.data.lens=26
  elif k==7:p=Vector((-1.4,-4.6,3.6));q=(lp+hd)/2+Vector((0,0,.3))
  elif k==8:p=Vector((8.6,-4.4,3.8));q=Vector((5.2,0,3.0));cam.data.lens=36
  elif k==9:p=Vector((-6,-17,10));q=Vector((0,0,3));cam.data.lens=24
  elif k==10:p=Vector((-6,-9,5.5));q=hd;cam.data.lens=28
  elif k==11:p=Vector((12,-12,4.5));q=hd+Vector((0,0,1)) if hd.z>-1 else Vector((0,0,4+2*smooth((t-49)/3)));cam.data.lens=26
  else:
   p=Vector((-1.8,-3.4,2.9))*(1-smooth((u-.6)/.4))+Vector((-5,-34,12))*smooth((u-.6)/.4);q=WHEEL if u<.6 else WHEEL.lerp(Vector((0,0,3)),smooth((u-.6)/.4));cam.data.lens=36 if u<.6 else 28
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_ship');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(3)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
def lp(x,k):return np.convolve(x,np.ones(k)/k,mode='same')
env=np.array([storm(t) for t in tt[::200]]);env=np.interp(tt,tt[::200],env)
wind=lp(nr.standard_normal(N_),30)*(.3+.9*env)*(1+.5*np.sin(tt*.7)) ;rain=(nr.standard_normal(N_)-lp(nr.standard_normal(N_),12))*.25*np.clip((tt-1)/3,0,1)*(tt<51.5)*np.clip(env*1.3,0,1)
creak=np.sin(2*np.pi*(120+40*np.sin(tt*2.3))*tt)*np.clip(np.sin(tt*1.7),0,1)**3*.05*env
swell=np.zeros(N_)
for c in np.arange(2.,seconds-1,4.5):
 i=int(c*SR);n=int(2.2*SR);k=np.arange(n)/SR
 if i+n<N_:swell[i:i+n]+=lp(nr.standard_normal(n),60)*np.sin(np.pi*k/2.2)**2*(.5+env[min(i,N_-1)])
thunder=np.zeros(N_+SR*6)
for t0,_ in STRIKES:
 n=int(3.5*SR);k=np.arange(n)/SR;th=lp(nr.standard_normal(n),180)*np.exp(-k*.9)*np.minimum(k/.05,1)*3+np.sin(2*np.pi*48*k)*np.exp(-k*1.4)*2;i=int((t0+(.15 if _ else .5))*SR);thunder[i:i+n]+=th
thunder=thunder[:N_]
def roar(t0,length,f0):
 n=int(length*SR);k=np.arange(n)/SR;f=f0+70*np.sin(2*np.pi*5*k)*np.exp(-k)-25*k;ph=2*np.pi*np.cumsum(f)/SR;x=(np.sin(ph)+.6*np.sin(2*ph)+.4*np.sin(3*ph)+.7*nr.standard_normal(n))*np.minimum(k/.1,1)*np.exp(-k*.9);x=lp(x,4);tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=x[:max(0,min(n,N_-i))];return tr
voice=roar(29.8,2.6,150)+roar(32.4,1.3,200)*.8+roar(36.,2.2,170)+roar(44.35,2.2,300)*1.1+roar(46.,2.6,130)*.8
slam=np.zeros(N_);i=int(32.9*SR);k=np.arange(int(.8*SR))/SR;slam[i:i+len(k)]=np.sin(2*np.pi*(70-60*k)*k)*np.exp(-k*7)+lp(nr.standard_normal(len(k)),40)*np.exp(-k*9)
note=lambda f,d,v=1.:(lambda k:(np.sin(2*np.pi*f*k)+.4*np.sin(4*np.pi*f*k)+.2*np.sin(6*np.pi*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=52.5 else minor[ci%4];vol=.5 if t0<26 else .85 if t0<46 else .4
 for j,f0 in enumerate(chord):
  n_=note(f0,2.6,vol*.5);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
 if 31<=t0<=44:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.2*SR))/SR;kk=np.sin(2*np.pi*(55*kt-90*kt**2))*np.exp(-kt*20)
   if i<N_:music[i:i+len(kk)]+=kk*1.4
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('wind_rain.wav',wind+rain+swell*.8,.8),wav('thunder.wav',thunder+slam,.95),wav('serpent.wav',voice,.9),wav('creak.wav',creak,.4),wav('music.wav',music,.55)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('wind and rain and waves','thunder','serpent','timber','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('SHIP_DONE',frames,'frames')
