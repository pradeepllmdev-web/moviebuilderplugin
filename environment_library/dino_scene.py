"""Blender script: 'The Last Egg' - Leo the lion rescues a stolen dinosaur egg in a prehistoric valley (about 50 s).

blender -b --disable-autoexec --python dino_scene.py -- <dino_blends_dir> <leo_assets_dir> <out.blend> [seconds=50]

Story: Leo walks through giant ferns to a nest and takes the last apatosaurus egg; a pack of velociraptors chases him; he leaps onto a grazing
triceratops and sits down; the triceratops gallops through the swamp; a T-Rex roars from a ridge and the raptors scatter; Leo rides to the
apatosaurus mother at the foot of the volcano and gives the egg back; it glows.

Assets: the CC0 Quaternius dinosaurs (rigged, Idle/Walk/Run/Attack/Jump clips) and Leo's animations built by the normal pipeline
(build_leo_assets.py: walk, run, pick up, sit). Everything else is procedural low poly: ferns, tree ferns, pines, boulders, a swamp, a volcano with
lava and a smoke plume, embers; hoof and foot dust, mud splashes, nine camera cuts on markers, and a synthesised soundtrack (footsteps at the real
contact times, a roar, lava rumble, music)."""
import bpy,math,random,sys,os,wave,bmesh
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];DINO_DIR,LEO_DIR,out=args[0],args[1],args[2];seconds=float(args[3]) if len(args)>3 else 50.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
rnd=random.Random(21)
def F(t):return 1+int(round(t*fps))
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
# ---------------------------------------------------------------------------------------------------------- materials and primitives
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
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat(name+str(color),color,emit));return o
# ---------------------------------------------------------------------------------------------------------- dinosaurs
SIZES={'Trex':(12.,'TRex_'),'Triceratops':(8.,'Triceratops_'),'Velociraptor':(2.1,'Velociraptor_'),'Apatosaurus':(24.,'Apatosaurus_')}
templates={}
for name,(length,prefix) in SIZES.items():
 with bpy.data.libraries.load(os.path.join(DINO_DIR,name+'.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects];dst.actions=list(src.actions)
 rig=next(o for o in dst.objects if o.type=='ARMATURE');body=next(o for o in dst.objects if o.type=='MESH');rig.name='T_'+name;body.name='T_'+name+'_mesh';acts={a.name[len(prefix):] if a.name.startswith(prefix) else a.name:a for a in dst.actions}
 if name=='Apatosaurus':acts={k.replace('Apatosaurus_',''):v for k,v in acts.items()}
 for o in (rig,body):link(o)
 pinv=body.matrix_parent_inverse.copy();body.parent=rig;body.matrix_parent_inverse=pinv;rig.animation_data_clear();bpy.context.view_layer.update()
 co=np.array([(body.matrix_world@v.co) for v in body.data.vertices]);span=float(co[:,1].max()-co[:,1].min());factor=length/span
 templates[name]=dict(rig=rig,body=body,acts=acts,factor=factor,orig_scale=rig.scale.copy());rig.hide_viewport=True;body.hide_viewport=True;rig.hide_render=True;body.hide_render=True
def make_dino(kind,label):
 t=templates[kind];rig=t['rig'].copy();rig.data=t['rig'].data.copy();rig.name=label;rig.animation_data_clear();link(rig);body=t['body'].copy();body.data=t['body'].data.copy();body.name=label+'_mesh';link(body);body.parent=rig;body.matrix_parent_inverse=t['body'].matrix_parent_inverse.copy()
 for mod in body.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 rig.hide_viewport=False;body.hide_viewport=False;rig.hide_render=False;body.hide_render=False;rig.scale=t['orig_scale']*t['factor'];return rig
def nla(rig,kind,segments):
 """segments: [(action name, start s, end s, play speed, loops?)] on alternating tracks with 6-frame overlaps."""
 acts=templates[kind]['acts'];rig.animation_data_create();tracks=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()]
 for k,(name,a,b,play) in enumerate(segments):
  act=acts[name];start=F(a)-(6 if k else 0);strip=tracks[k%2].strips.new(name+str(k),start,act);strip.action_slot=act.slots[0] if len(act.slots) else None;strip.scale=1/play;strip.extrapolation='HOLD' if k==0 else 'NOTHING'
  length=act.frame_range[1]-act.frame_range[0]+1;strip.repeat=max(1.,(F(b)-start)/(length/play));strip.blend_in=6 if k else 0;strip.blend_out=6
for o in templates.values():pass
# ---------------------------------------------------------------------------------------------------------- Leo groups (rig + meshes under a root empty)
def load_leo(kind):
 with bpy.data.libraries.load(os.path.join(LEO_DIR,'leo_%s.blend'%kind),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or o.hide_render or (o.type=='MESH' and (o.hide_viewport or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new('Leo_'+kind,None);link(root)
 for o in new:
  if o.parent is None:o.parent=root
 rig=next(o for o in new if o.type=='ARMATURE')
 for o in new:
  if o.animation_data and o.type!='ARMATURE':o.animation_data_clear()
 return dict(root=root,objs=new,rig=rig,kind=kind)
def clip_to_nla(g,start_t,loops=1.,hold=False):
 rig=g['rig'];ad=rig.animation_data;act=ad.action;ad.action=None
 for tr in list(ad.nla_tracks):ad.nla_tracks.remove(tr)
 tr=ad.nla_tracks.new();s=tr.strips.new('leo',F(start_t),act);s.repeat=loops;s.extrapolation='HOLD' if hold else 'NOTHING'
 return (act.frame_range[1]-act.frame_range[0]+1)/fps
def visible(objs,a,b):
 for o in objs:
  for prop in ('hide_viewport','hide_render'):
   setattr(o,prop,True);o.keyframe_insert(prop,frame=max(0,F(a)-1));setattr(o,prop,False);o.keyframe_insert(prop,frame=F(a));setattr(o,prop,True);o.keyframe_insert(prop,frame=F(b)+1)
def constant(obj):
 if obj.animation_data and obj.animation_data.action:
  act=obj.animation_data.action;curves=list(act.fcurves) if hasattr(act,'fcurves') else [fc for l in act.layers for st in l.strips for bag in st.channelbags for fc in bag.fcurves]
  for fc in curves:
   if fc.data_path in ('hide_viewport','hide_render'):
    for kp in fc.keyframe_points:kp.interpolation='CONSTANT'
# ---------------------------------------------------------------------------------------------------------- timeline and paths
T=dict(walk=(0.,8.),pick=(8.,17.),run=(17.,25.5),leap=(25.5,26.7),sit=(26.7,45.),charge=26.5,roar=33.5,hatch=45.)
NEST=Vector((7.5,-1.5,0));TRI0=Vector((34.,-3.,0));APATO=Vector((128.,8.,0));TREX=Vector((78.,30.,0))
def smooth(u):u=max(0.,min(1.,u));return u*u*(3-2*u)
def tri_speed(t):
 if t<T['charge']:return 0.
 if t<T['charge']+2.:return 8.5*smooth((t-T['charge'])/2.)
 if t<39.:return 8.5
 if t<42.:return 8.5*(1-smooth((t-39.)/3.))*.85+0.0
 return 0.
TRI_S=[0.];dt=1/fps
for i in range(frames):TRI_S.append(TRI_S[-1]+tri_speed(i*dt)*dt)
def tri_pos(f):
 s=TRI_S[min(f-1,frames)];x=TRI0.x+s;y=TRI0.y+2.5*math.sin(s/18.)+ (s/55.)*5.5;h=math.atan2(2.5/18.*math.cos(s/18.)+5.5/55.,1.);return Vector((x,y,0)),h
# ---------------------------------------------------------------------------------------------------------- build the world
def sky_and_light():
 scene.world=bpy.data.worlds.new('Dusk');scene.world.color=(.86,.52,.34)
 global SUN
 sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));SUN=sun;sun.data.energy=3.5;sun.data.color=(1,.72,.5);sun.rotation_euler=(math.radians(62),0,math.radians(120));link(sun)
sky_and_light()
ground=prim('cube','Ground',(70,0,-.05),(.26,.30,.12),scale=(260,160,.05))
swamp=prim('cube','Swamp',(70,0,.02),(.12,.30,.28),scale=(28,24,.02))      # x 42..98
for i in range(60):prim('cone','Reed',(rnd.uniform(44,96),rnd.choice((-1,1))*rnd.uniform(9,22),.6),(.3,.45,.2),scale=(.06,.06,.6),vertices=4,radius1=1,depth=2)
def fern(x,y,s=1.,color=(.12,.42,.14)):
 for k in range(8):
  a=k*math.pi/4+rnd.uniform(-.2,.2);prim('cone','Frond',(x+math.cos(a)*.9*s,y+math.sin(a)*.9*s,.7*s),color,scale=(.18*s,1.6*s,.05*s),rot=(math.radians(55),0,a-math.pi/2),vertices=4,radius1=1,depth=2)
def tree_fern(x,y,s=1.):
 prim('cyl','Trunk',(x,y,1.6*s),(.35,.25,.12),scale=(.18*s,.18*s,1.6*s),vertices=6,radius=1,depth=2)
 for k in range(9):
  a=k*2*math.pi/9;prim('cone','Frond',(x+math.cos(a)*1.3*s,y+math.sin(a)*1.3*s,3.4*s),(.1,.38,.12),scale=(.22*s,2.2*s,.05*s),rot=(math.radians(40),0,a-math.pi/2),vertices=4,radius1=1,depth=2)
def pine(x,y,h):
 prim('cyl','Trunk',(x,y,h*.3),(.3,.2,.1),scale=(.3,.3,h*.3),vertices=6,radius=1,depth=2);prim('cone','Pine',(x,y,h*.7),(.07,.26,.12),scale=(h*.16,h*.16,h*.3),vertices=7,radius1=1,depth=2)
for i in range(160):
 x=rnd.uniform(-25,215);y=rnd.choice((-1,1))*rnd.uniform(7,70)
 if abs(y)<8 and 0<x<150:continue
 if 42<x<98 and abs(y)<24:continue
 r=rnd.random()
 if r<.55:fern(x,y,rnd.uniform(.8,1.9))
 elif r<.8:tree_fern(x,y,rnd.uniform(.9,1.8))
 else:pine(x,y,rnd.uniform(14,26))
for i in range(40):prim('sphere','Boulder',(rnd.uniform(-20,210),rnd.choice((-1,1))*rnd.uniform(6,60),.4),(.45,.43,.4),scale=(rnd.uniform(.5,1.8),rnd.uniform(.5,1.5),rnd.uniform(.4,1.))) if True else None
# the ridge the T-Rex stands on
prim('cone','Ridge',(TREX.x,TREX.y,1.6),(.4,.36,.3),scale=(11,9,3.2),vertices=8,radius1=1,depth=1)
RIDGE_TOP=3.2
# the volcano, lava and smoke
VOL=Vector((205.,120.,0));prim('cone','Volcano',(VOL.x,VOL.y,38),(.3,.26,.24),scale=(120,120,38),vertices=9,radius1=1,depth=2);prim('cone','Crater',(VOL.x,VOL.y,76),(1,.35,.08),scale=(20,20,2),vertices=9,radius1=1,depth=1,emit=6.)
for k in range(4):
 a=rnd.uniform(3.6,5.2);pts=[(VOL.x+math.cos(a+.15*math.sin(i))*(i*14+16),VOL.y+math.sin(a+.15*math.sin(i))*(i*14+16),74-i*8.5) for i in range(8)]
 for p,q in zip(pts,pts[1:]):prim('cube','Lava',((p[0]+q[0])/2,(p[1]+q[1])/2,(p[2]+q[2])/2+.4),(1,.4,.08),scale=(math.dist(p[:2],q[:2])/2+1,2.2,.35),rot=(0,0,math.atan2(q[1]-p[1],q[0]-p[0])),emit=5.)
lava_light=bpy.data.objects.new('LavaGlow',bpy.data.lights.new('LavaGlow','POINT'));lava_light.data.energy=400000;lava_light.data.color=(1,.45,.15);lava_light.location=(VOL.x-30,VOL.y-30,60);link(lava_light)
for k in range(9):   # smoke plume
 o=prim('sphere','Smoke',(VOL.x,VOL.y,80+k*9),(.28,.26,.26),scale=(10+k*2,10+k*2,8+k));
for k in range(40):
 o=prim('sphere','Ember',(VOL.x+rnd.uniform(-8,8),VOL.y+rnd.uniform(-8,8),78),(1,.55,.1),scale=(.5,.5,.5),emit=8.,subdivisions=1);t0=rnd.uniform(0,seconds*.6)
 for tt,z,sc in ((t0,78,.01),(t0+1.5,88+rnd.uniform(0,10),.6),(t0+5,115+rnd.uniform(0,25),.01)):
  o.location=(VOL.x+rnd.uniform(-8,8)+tt,VOL.y+rnd.uniform(-8,8),z);o.scale=(sc,sc,sc);o.keyframe_insert('location',frame=F(tt));o.keyframe_insert('scale',frame=F(tt))
# ---------------------------------------------------------------------------------------------------------- the animals
trex=make_dino('Trex','TRex');trex.location=(TREX.x,TREX.y,RIDGE_TOP);trex.rotation_euler=(0,0,math.pi/2+math.radians(-150))
nla(trex,'Trex',[('Idle',0,T['roar'],1.),('Attack',T['roar'],T['roar']+1.2,1.),('Idle',T['roar']+1.2,seconds,1.)])
apato=make_dino('Apatosaurus','Apatosaurus');apato.location=APATO;apato.rotation_euler=(0,0,math.pi/2+math.radians(175))
nla(apato,'Apatosaurus',[('Idle',0,44.,1.),('Attack',44.,45.9,1.),('Idle',45.9,seconds,1.)])
tri=make_dino('Triceratops','Triceratops')
nla(tri,'Triceratops',[('Idle',0,T['charge'],1.),('Run',T['charge'],39.,.9),('Walk',39.,42.5,1.0),('Idle',42.5,seconds,1.)])
for f in range(1,frames+1,2):
 p,h=tri_pos(f);tri.location=(p.x,p.y,0);tri.rotation_euler=(0,0,h+math.pi/2);tri.keyframe_insert('location',frame=f);tri.keyframe_insert('rotation_euler',frame=f)
trimesh=bpy.data.objects['Triceratops_mesh']
def tri_low(f):
 scene.frame_set(f);bpy.context.view_layer.update();e=trimesh.evaluated_get(bpy.context.evaluated_depsgraph_get());mw=e.matrix_world
 return min((mw@v.co).z for v in list(e.data.vertices)[::4])
lift=kit.ground_lift({f:tri_low(f) for f in range(1,frames+1,2)},0.,0.,.5,1)   # keep its feet on the ground
for f,z in lift.items():
 p,h=tri_pos(f);tri.location=(p.x,p.y,z);tri.keyframe_insert('location',frame=f)
RAPTORS=[]
for k,(sx,sy) in enumerate(((-22,5),(-26,-1),(-18,-6))):
 r=make_dino('Velociraptor','Raptor%d'%k);RAPTORS.append((r,sx,sy))
def raptor_pos(k,t):
 """Raptors hide until 12 s, run toward Leo, then turn and flee when the T-Rex roars."""
 sx,sy=RAPTORS[k][1],RAPTORS[k][2]
 if t<13:return Vector((sx,sy,0)),0.,0.
 t1=min(t,T['roar']+.6);x=sx+9.*(t1-13)*(1 if t1<T['roar']+.6 else 1)
 if t<=T['roar']+.6:return Vector((min(x,TRI_S[min(F(t)-1,frames)]+TRI0.x-4-k*3.5 if t>25 else x),sy+k*.8,0)),0.,9.
 x_flee=sx+9.*(T['roar']+.6-13)
 cur=min(x,TRI_S[min(F(T['roar']+.6)-1,frames)]+TRI0.x-4-k*3.5);return Vector((cur-9.*(t-T['roar']-.6)*1.0,sy+k*.8+1.5*(t-T['roar']),0)),math.pi,9.
for k,(r,sx,sy) in enumerate(RAPTORS):
 nla(r,'Velociraptor',[('Idle',0,13,1.),('Run',13,seconds,1.0)])
 for f in range(1,frames+1,2):
  t=(f-1)/fps;p,h,sp=raptor_pos(k,t);r.location=(p.x,p.y,0);r.rotation_euler=(0,0,h+math.pi/2*1.0+math.pi/2*0+0.0 if False else h+math.pi/2);r.keyframe_insert('location',frame=f);r.keyframe_insert('rotation_euler',frame=f)
# Leo: ONE rig with all clips on the NLA (persistence rule: no group swapping, nothing pops in or out)
def load_one(tag):
 with bpy.data.libraries.load(os.path.join(LEO_DIR,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new(tag+'Root',None);link(root)
 for o in new:
  if o.parent is None:o.parent=root
  if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
 rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
 return dict(root=root,rig=rig,objs=new,body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices)))
LEOG=load_one('Leo');LCL={}
for c in ('climb','idle','pick','run','jump','sit'):
 with bpy.data.libraries.load(os.path.join(LEO_DIR,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 LCL[c]=dst.actions[0]
def set_leo_nla(sched):
 ad=LEOG['rig'].animation_data;tr=[ad.nla_tracks.new(),ad.nla_tracks.new()]
 for k,item in enumerate(sched):
  c,a,b,mode=item[:4];st=kit.add_strip(tr[k%2],LCL[c],F(a)-(5 if k else 0),F(b),mode);st.extrapolation='HOLD' if (k==0 or 'hold' in item[4:]) else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
set_leo_nla([('climb',0,8,'loop'),('idle',8,9.5,'loop'),('pick',9.5,14.5,'fit'),('idle',14.5,17,'loop'),('run',17,25.2,'loop'),('jump',25.2,26.8,'fit'),('sit',26.8,35.8,'fit','hold')])
leo_root=LEOG['root']
def leo_walk_pos(t):return Vector((7.5-6.+0.75*t,-3.0,0)),0.
PICK_ROOT=Vector((7.5-6.+0.75*8.,-3.0,0));NEST_EGG=PICK_ROOT+Vector((.62,0,.58))
LEAP_FROM=PICK_ROOT+Vector((.8,.2,0))
def leo_run_pos(t):
 u=(t-T['run'][0])/(T['run'][1]-T['run'][0]);p=LEAP_FROM.lerp(Vector((TRI0.x-4.,TRI0.y-1.5,0)),smooth(u)*0.15+u*0.85);return p,math.atan2(TRI0.y-LEAP_FROM.y,TRI0.x-LEAP_FROM.x)
tri_rig=tri;torso=tri_rig.pose.bones['Torso']
def back_surface(f):
 scene.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();body=bpy.data.objects['Triceratops_mesh'];e=body.evaluated_get(deps);tw=tri_rig.matrix_world@tri_rig.pose.bones['Torso'].head
 zs=[(body.matrix_world@v.co).z for v in e.data.vertices if abs((body.matrix_world@v.co).x-tw.x)<.9 and abs((body.matrix_world@v.co).y-tw.y)<.9];return Vector((tw.x,tw.y,max(zs) if zs else tw.z+1.2))
SEAT_OFFSET=.128
start_p,_=leo_run_pos(T['run'][1])
def leo_leap_pos(t):
 u=smooth((t-T['leap'][0])/(T['leap'][1]-T['leap'][0]));land_now=back_surface(F(t))-Vector((0,0,SEAT_OFFSET));p=start_p.lerp(land_now,u)+Vector((0,0,kit.ballistic(u,kit.flight_apex(T['leap'][1]-T['leap'][0]))));return p,tri_pos(F(t))[1]
def leo_state(t):
 if t<T['walk'][1]:return leo_walk_pos(t)
 if t<T['run'][0]:return PICK_ROOT,0.
 if t<T['run'][1]:return leo_run_pos(t)
 return leo_leap_pos(min(t,T['leap'][1]))
for f in range(1,F(T['leap'][1])+1,2):
 p,h=leo_state((f-1)/fps);leo_root.location=p;leo_root.rotation_euler=(0,0,h+math.pi/2);leo_root.keyframe_insert('location',frame=f);leo_root.keyframe_insert('rotation_euler',frame=f)
# from the landing on, Leo rides: a Child Of constraint to the triceratops torso whose inverse is taken at the landing frame, with a constant basis
fl=F(T['leap'][1]);p,h=leo_state(T['leap'][1])
for f in range(fl,frames+1,60):
 leo_root.location=p;leo_root.rotation_euler=(0,0,h+math.pi/2);leo_root.keyframe_insert('location',frame=f);leo_root.keyframe_insert('rotation_euler',frame=f)
leo_root.location=p;leo_root.rotation_euler=(0,0,h+math.pi/2);scene.frame_set(fl);bpy.context.view_layer.update()
con=leo_root.constraints.new('CHILD_OF');con.target=tri_rig;con.subtarget='Torso';con.inverse_matrix=(tri_rig.matrix_world@tri_rig.pose.bones['Torso'].matrix).inverted()
for t_,v in ((T['leap'][1]-.05,0.),(T['leap'][1],1.)):con.influence=v;con.keyframe_insert('influence',frame=F(t_))
bpy.context.view_layer.update()
# ---------------------------------------------------------------------------------------------------------- the egg (it is at the nest from the first frame)
import locations
nroot,nparts=locations.load_prop('egg_nest',dict(link=link,mat=mat,prim=prim),(NEST_EGG.x,NEST_EGG.y,NEST_EGG.z-.58));egg=nparts['egg']
GIVE=T['hatch']-1.5;GIVE_TO=APATO+Vector((-8.5,-3.4,.28));T_LIFT=9.5+1.3
scene.frame_set(F(GIVE));bpy.context.view_layer.update();give_from=LEOG['rig'].matrix_world@LEOG['rig'].pose.bones['mixamorig:RightHand'].head+Vector((0,0,-.05))
for f in range(1,frames+1,2):
 t=(f-1)/fps
 if t<T_LIFT:p=NEST_EGG
 else:
  scene.frame_set(f);bpy.context.view_layer.update();hand=LEOG['rig'].matrix_world@LEOG['rig'].pose.bones['mixamorig:RightHand'].head+Vector((0,0,-.05))
  if t<T_LIFT+.9:p=NEST_EGG.lerp(hand,smooth((t-T_LIFT)/.9))
  elif t<GIVE:p=hand
  else:u=smooth((t-GIVE)/1.2);p=give_from.lerp(GIVE_TO,u)+Vector((0,0,1.0*math.sin(math.pi*u)))
 egg.location=p-nroot.location;egg.keyframe_insert('location',frame=f)
glow=prim('sphere','EggGlow',GIVE_TO,(1,.95,.5),scale=(.01,.01,.01),emit=10.,subdivisions=2)
for tt,sc in ((T['hatch'],.01),(T['hatch']+.8,.9),(T['hatch']+2.6,2.2),(seconds,2.6)):glow.scale=(sc,sc,sc);glow.keyframe_insert('scale',frame=F(tt))
glow_light=bpy.data.objects.new('EggLight',bpy.data.lights.new('EggLight','POINT'));glow_light.location=GIVE_TO+Vector((0,0,1));link(glow_light);glow_light.data.color=(1,.9,.5)
for tt,e in ((T['hatch'],0),(T['hatch']+1,3000),(seconds,5000)):glow_light.data.energy=e;glow_light.data.keyframe_insert('energy',frame=F(tt))
# ---------------------------------------------------------------------------------------------------------- dust and splashes from foot contacts
bones_of={'tri':(tri,['FrontFoot.L','FrontFoot.R','BackFoot.L','BackFoot.R']),}
for k,(r,_,_) in enumerate(RAPTORS):bones_of['rap%d'%k]=(r,['BackFoot.L','BackFoot.R'])
contacts=[];last={}
for f in range(1,frames+1):
 scene.frame_set(f);bpy.context.view_layer.update();t=(f-1)/fps
 for key,(rig,names) in bones_of.items():
  if key=='tri':spd=tri_speed(t)
  else:spd=raptor_pos(int(key[3:]),t)[2]
  if spd<.5:
   for n in names:last[(key,n)]=False
   continue
  for n in names:
   p=rig.matrix_world@rig.pose.bones[n].head;low=p.z<.18*(rig.scale[0]/.4+.4)+rig.location.z*0;state=low
   if state and not last.get((key,n),False):contacts.append((f,p.x,p.y,spd,key))
   last[(key,n)]=state
puff=bpy.data.meshes.new('PuffMesh');bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.);bm.to_mesh(puff);bm.free()
for k,(f,x,y,v,key) in enumerate(contacts):
 water=42<x<98 and abs(y)<24;o=bpy.data.objects.new('Puff%d'%k,puff);link(o);o.data.materials.clear();o.data.materials.append(mat('Splash' if water else 'Dust',(.55,.72,.72) if water else (.55,.45,.32)));big=.55 if key=='tri' else .18
 for fr,sc,dr in ((f-1,.001,0),(f+3,big*(1+v/10),.25),(f+14,big*2.3,1.1),(f+30,.001,1.9)):
  o.location=(x-dr*.8,y,.15+dr*.35);o.scale=(sc,sc*.9,sc*.7);o.keyframe_insert('location',frame=fr);o.keyframe_insert('scale',frame=fr)
# ---------------------------------------------------------------------------------------------------------- cameras
def leo_pos(f):
 t=(f-1)/fps
 if t<T['walk'][1]:return leo_walk_pos(t)[0]
 if t<T['pick'][1]:return PICK_ROOT
 if t<T['run'][1]:return leo_run_pos(t)[0]
 return back_surface(f)
CUTS=[('1 Valley, volcano',0,6.),('2 The nest',6.,12.),('3 Raptors in the ferns',12.,16.),('4 Chase, alongside',16.,21.),('5 Leap onto the triceratops',21.,26.5),('6 Charge through the swamp',26.5,32.5),('7 The T-Rex roars',32.5,37.),('8 Arrival at the mother',37.,43.),('9 The egg is home',43.,seconds)]
CUTS=[c for c in CUTS if c[1]<seconds];cams=[]
for k,(name,a,b) in enumerate(CUTS):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=2500;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,4):
  u=(f-F(a))/max(1,F(b)-F(a));L=leo_pos(f);tp=tri_pos(f)[0]
  if k==0:p=Vector((-18+14*u,-22,9-3*u));q=Vector((20,0,5));cam.data.lens=30
  elif k==1:p=NEST+Vector((-3.5,-3.8,1.5));q=NEST+Vector((0,0,.8));cam.data.lens=40
  elif k==2:p=Vector((-8,-6,1.0));q=Vector((-14+u*12,4,1.4));cam.data.lens=35
  elif k==3:p=L+Vector((-2.5+u*1.5,-7,2.4));q=L+Vector((1.5,0,1.1));cam.data.lens=32
  elif k==4:p=tp+Vector((6,-9,2.2));q=tp+Vector((-3,0,2.2));cam.data.lens=30
  elif k==5:p=tp+Vector((-14,-5,6.5));q=tp+Vector((6,0,2.2));cam.data.lens=32
  elif k==6:
   p=Vector((TREX.x-12,TREX.y-14,RIDGE_TOP+1.2)) if u<.6 else tp+Vector((18,-6,2));q=Vector((TREX.x,TREX.y,RIDGE_TOP+3.2)) if u<.6 else tp+Vector((-6,0,1.2));cam.data.lens=28 if u<.6 else 35
  elif k==7:p=tp+Vector((-4,-16,5));q=Vector((APATO.x-6,APATO.y,5));cam.data.lens=30
  else:
   if u<.7:p=GIVE_TO+Vector((-5+2*u,-6,2.0));q=GIVE_TO+Vector((1.5,0,2.4));cam.data.lens=34
   else:p=GIVE_TO+Vector((-30*(u-.7)/.3-5,-28*(u-.7)/.3-5,6+18*(u-.7)/.3));q=VOL;q=Vector((VOL.x-40,VOL.y-40,30));cam.data.lens=28
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N=int(seconds*SR);tt=np.arange(N)/SR;adir=os.path.join(os.path.dirname(out),'audio_dino');os.makedirs(adir,exist_ok=True);nrng=np.random.default_rng(6)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
def lowpass(x,k):return np.convolve(x,np.ones(k)/k,mode='same')
foot_t=np.arange(int(.35*SR))/SR;thump=np.sin(2*np.pi*(55*foot_t-60*foot_t**2))*np.exp(-foot_t*9)+.3*nrng.standard_normal(len(foot_t))*np.exp(-foot_t*25)
patter_t=np.arange(int(.07*SR))/SR;patter=np.sin(2*np.pi*180*patter_t)*np.exp(-patter_t*60)
steps=np.zeros(N+len(foot_t))
for f,x,y,v,key in contacts:
 i=int((f-1)/fps*SR)
 if i<N:
  if key=='tri':steps[i:i+len(thump)]+=thump*min(1.,.5+v/12)
  else:steps[i:i+len(patter)]+=patter*.35
steps=steps[:N]
roar_t=np.arange(int(2.4*SR))/SR;f0=95+60*np.sin(2*np.pi*3.5*roar_t)*np.exp(-roar_t*.6)-18*roar_t
roar=(np.sin(2*np.pi*np.cumsum(f0)/SR)+.6*np.sin(4*np.pi*np.cumsum(f0)/SR)+.5*nrng.standard_normal(len(roar_t)))*np.minimum(roar_t/.15,1)*np.exp(-roar_t*1.1);roar=lowpass(roar,5)
roar_track=np.zeros(N+len(roar));i0=int(T['roar']*SR);roar_track[i0:i0+len(roar)]+=roar;roar_track=roar_track[:N]
rumble=lowpass(nrng.standard_normal(N),400)*(.4+.6*np.clip((tt-30)/20,0,1))+lowpass(nrng.standard_normal(N),60)*.15
jungle=lowpass(nrng.standard_normal(N),20)*.05*(1+np.sin(tt*13)*.4)
def note(freq,length,vel=1.):
 n=int(length*SR);t=np.arange(n)/SR;env=np.minimum(t/.03,1)*np.exp(-t*2.4/length);return (np.sin(2*np.pi*freq*t)+.35*np.sin(4*np.pi*freq*t))*env*vel
music=np.zeros(N+SR*3);prog=[(110,164.8,220),(98,146.8,196),(87.3,130.8,174.6),(82.4,123.5,164.8)];major=[(130.8,196,261.6),(98,146.8,196),(110,164.8,220),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 chord=major[ci%4] if ci*2.5>=T['hatch'] else prog[ci%4];t0=ci*2.5;chase=16<=t0<=40
 for j,f0 in enumerate(chord):
  step=.25 if chase else .5
  for rep in range(int(2.5/step)):
   i=int((t0+rep*step+.04*j)*SR)
   if i<N:n_=note(f0*(2 if rep%2 else 1),.5,.5 if chase else .3);music[i:i+len(n_)]+=n_
 if chase:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.18*SR))/SR;k_=np.sin(2*np.pi*(60*kt-100*kt**2))*np.exp(-kt*22)
   if i<N:music[i:i+len(k_)]+=k_*1.1
music=music[:N]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3.,1)
paths=[wav('footsteps.wav',steps,.95),wav('roar.wav',roar_track,.95),wav('lava_jungle.wav',rumble+jungle,.7),wav('music.wav',music,.6)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('footsteps','roar','lava rumble and jungle','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
kit.apply_params(scene,SUN,[o for o in bpy.data.objects if o.type=='MESH' and o.parent==LEOG['root']])   # SCENE_PARAMS: time of day and hero tint
issues=kit.audit(scene,bodies=[(tri,bpy.data.objects['Triceratops_mesh'])]+[(r,bpy.data.objects[r.name+'_mesh']) for r,_,_ in RAPTORS],floor_z=0.,skip=[],subjects=[tri,trex,apato]+[r for r,_,_ in RAPTORS]+[LEOG['root']],step=12)
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
issues2=kit.persistence_audit(scene)
for i in issues2:print(i)
print('PERSIST',len(issues2),'violations')
print('DINO_DONE',frames,'frames',len(contacts),'contacts')
for f in (F(30),F(36)):
 scene.frame_set(f);bpy.context.view_layer.update();print('CHK',f,'tri',tuple(round(v,1) for v in tri.matrix_world.translation),'sitroot',tuple(round(v,1) for v in LEOG['root'].matrix_world.translation),'torso',tuple(round(v,1) for v in (tri.matrix_world@tri.pose.bones['Torso'].head)))
