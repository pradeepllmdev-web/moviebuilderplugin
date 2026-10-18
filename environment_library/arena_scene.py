"""Blender script: 'The Arena' - Leo fights a bigger, darker rival lion in a ruined stone arena (52 s).

blender -b --disable-autoexec --python arena_scene.py -- <ship_assets_dir> <out.blend> [seconds=52]

New in this scene: BODY-TO-BODY CONTACT. A contact solver finds the instant a strike reaches full extension (hand or foot of the attacker, measured from the evaluated clip),
shifts the attacker's root so that hand or foot lands on the target bone, and starts the defender's reaction at that instant. In the grapple and the throw, both lions' arms are IK to
the other lion's shoulder bones (empties that copy the opponent's bone), so the hands stay on a moving body. The throw is a real arc over Leo's shoulder. An audit checks every strike
(distance hand to target) and that the two bodies do not overlap outside the grapple. Clips come from build_ship_assets.py."""
import bpy,math,random,sys,os,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1];seconds=float(args[2]) if len(args)>2 else 52.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames;rnd=random.Random(12)
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
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color,emit));return o
def hide_keys(o,windows):
 last=None
 for f in range(1,frames+1):
  v=any(a<=(f-1)/fps<b for a,b in windows)
  if v!=last:
   for prop in ('hide_viewport','hide_render'):setattr(o,prop,not v);o.keyframe_insert(prop,frame=f)
   last=v
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
 body=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices));return root,rig,body
CLIPS={}
for c in ('idle','climb','run','punch','block','hit','dodge','kick','jump','fall','getup','cele','bow','look'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
LR,Lrig,Lbody=load_char('Leo');RR,Rrig,Rbody=load_char('Rival',1.15,(.32,.27,.25))
FIG={'leo':dict(root=LR,rig=Lrig,body=Lbody,scale=1.),'riv':dict(root=RR,rig=Rrig,body=Rbody,scale=1.15)}
def nla(rig,sched):
 tracks=[rig.animation_data.nla_tracks.new() for _ in range(2)]
 for k,item in enumerate(sched):
  c,a,b,mode=item[:4]
  try:st=kit.add_strip(tracks[k%2],CLIPS[c],F(a)-(5 if k else 0),F(b),mode)
  except RuntimeError:print('NLA FAIL',rig.name,k,c,a,b);raise
  st.extrapolation='HOLD' if (k==0 or 'hold' in item[4:]) else 'NOTHING';st.blend_in=5 if k else 0;st.blend_out=5
nla(Lrig,[('idle',0,2,'loop'),('climb',2,6,'loop'),('idle',6,9.8,'loop'),('block',9.8,11.8,'fit'),('idle',11.8,12.2,'loop'),('punch',12.2,13.8,'fit'),('idle',13.8,15.0,'loop'),('climb',15.0,16.6,'loop'),('idle',16.6,22.2,'loop'),
 ('dodge',22.2,23.3,'fit'),('kick',23.3,24.8,'fit'),('climb',24.8,28.6,'loop'),('idle',28.6,38.6,'loop'),('cele',38.6,43.6,'fit'),('idle',43.6,44.2,'loop'),('bow',44.2,47.2,'fit'),('idle',47.2,seconds,'loop')])
nla(Rrig,[('idle',0,2,'loop'),('climb',2,6,'loop'),('idle',6,9,'loop'),('run',9,10.1,'loop'),('punch',10.1,11.7,'fit'),('idle',11.7,12.7,'loop'),('hit',12.7,15.0,'fit'),('idle',15.0,15.4,'loop'),('climb',15.4,16.6,'loop'),('idle',16.6,23.6,'loop'),
 ('fall',23.6,26.6,'fit','hold'),('getup',28.2,31.2,'fit'),('idle',31.2,32.6,'loop'),('run',32.6,34.9,'loop'),('jump',34.9,36.4,'fit'),('idle',36.4,42.0,'loop'),('getup',42.0,45.0,'fit'),('idle',45.0,46.4,'loop'),('bow',46.4,49.4,'fit'),('idle',49.4,seconds,'loop')])
# ---------------------------------------------------------------------------------------------------------- choreography: waypoint paths plus grapple and throw overrides
PI=math.pi
WP={'leo':[(0,-13,0,0),(2,-13,0,0),(6,-2.4,0,0),(10.5,-2.4,0,0),(10.9,-2.9,0,0),(15.0,-2.9,0,0),(16.6,-1.51,0,0),(22.2,-2.51,0,0),(23.0,-2.6,1.0,0),(24.8,-2.6,1.0,0),(25.4,-3.0,1.3,PI),(28.4,-6.5,.2,PI),(29.8,-6.5,.2,0),(36.5,-6.5,.2,0),(38.4,-4.6,.2,0),(seconds,-4.6,.2,0)],
 'riv':[(0,13,0,PI),(2,13,0,PI),(6,2.4,0,PI),(9.0,2.4,0,PI),(10.1,-1.9,0,PI),(12.0,-1.9,0,PI),(13.0,-1.9,0,PI),(13.7,-1.2,0,PI),(15.0,-1.2,0,PI),(16.6,-.89,0,PI),(22.2,-1.89,0,PI),(23.4,-1.89,0,PI),(24.6,-2.3,0,PI),(32.6,-2.3,0,PI),(34.6,-5.88,0,PI),(seconds,-5.88,0,PI)]}
def wp_state(key,t):
 w=WP[key]
 if t<=w[0][0]:return Vector((w[0][1],w[0][2],0)),w[0][3]
 for a,b in zip(w,w[1:]):
  if a[0]<=t<b[0]:
   u=smooth((t-a[0])/(b[0]-a[0]));dh=(b[3]-a[3]+PI)%(2*PI)-PI;return Vector((a[1]+(b[1]-a[1])*u,a[2]+(b[2]-a[2])*u,0)),a[3]+dh*u
 return Vector((w[-1][1],w[-1][2],0)),w[-1][3]
GM0=Vector((-1.2,0,0))
def grap(t):
 """Both lions face each other at 0.62 m, circle, then the rival drives Leo back."""
 phi=.5*math.sin((t-16.8)*1.1) if t>=16.8 else 0.
 push=smooth((t-20.2)/1.6);M=GM0+Vector((-1.0*push,0,0));ax=Vector((math.cos(phi),math.sin(phi),0))
 return M-ax*.31,phi,M+ax*.31,phi+PI,push
THROW=(34.9,36.4)
def throw_state(t):
 """Rival over Leo's shoulder: arc, 270 degree forward flip, lands on his back behind Leo."""
 lp,lh=wp_state('leo',t);u=smooth((t-THROW[0])/(THROW[1]-THROW[0]));start=Vector((lp.x+.62,lp.y,0));end=Vector((lp.x-1.15,lp.y,.0))
 pos=start.lerp(end,u);pos.z=2.3*math.sin(PI*u)+.30*u
 return pos
def fighter_state(key,t):
 """(root location, rotation euler) of a fighter at time t before contact offsets."""
 pos,h=wp_state(key,t);pitch=0.;rot=None
 if 16.0<=t<22.2:
  a=smooth((t-16.0)/.8)*(1-smooth((t-22.0)/.2));lp,lh,rp,rh,push=grap(t);gp,gh=(lp,lh) if key=='leo' else (rp,rh)
  pos=pos.lerp(gp,a);dh=(gh-h+PI)%(2*PI)-PI;h=h+dh*a;pitch=(.18+.12*push*(1 if key=='riv' else -1))*a
 if key=='leo' and THROW[0]-.6<=t<=THROW[1]+.6:pitch=.35*smooth((t-34.6)/.6)*(1-smooth((t-35.6)/.6))
 if key=='riv' and THROW[0]<=t<=THROW[1]:
  pos=throw_state(t);u=smooth((t-THROW[0])/(THROW[1]-THROW[0]));rot=(Matrix.Rotation(-1.5*PI*u,3,'Y')@Matrix.Rotation(PI+PI/2,3,'Z')).to_euler()
 if key=='riv' and t>THROW[1] and t<42.0:
  lp,lh=wp_state('leo',THROW[1]);pos=Vector((lp.x-1.15,lp.y,0));rot=(Matrix.Rotation(-1.5*PI,3,'Y')@Matrix.Rotation(PI+PI/2,3,'Z')).to_euler()
 if rot is None:rot=Euler((pitch,0,h+PI/2))
 return pos,rot
OFF={'leo':[],'riv':[]};ZL={'leo':{},'riv':{}}
def offset_at(key,t):
 o=Vector((0,0,0))
 for t0,tp,t1,v in OFF[key]:
  if t0<=t<tp:o+=v*smooth((t-t0)/(tp-t0))
  elif tp<=t<t1:o+=v*(1-smooth((t-tp)/(t1-tp)))
 return o
def state(key,t):
 p,r=fighter_state(key,t);p=p+offset_at(key,t)
 f=F(t);p=p+Vector((0,0,ZL[key].get(f-(f-1)%2,0.)));return p,r
def apply_all():
 prev={'leo':None,'riv':None}
 for f in range(1,frames+1,2):
  t=(f-1)/fps
  for key in FIG:
   p,r=state(key,t)
   if prev[key] is not None and isinstance(r,Euler):r=r.copy();r.make_compatible(prev[key])
   prev[key]=r;root=FIG[key]['root'];root.location=p;root.rotation_euler=r;root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
apply_all()
# ---------------------------------------------------------------------------------------------------------- IK grips on the opponent's shoulders
def make_ik(key,other):
 rig=FIG[key]['rig'];orig=FIG[other]['rig'];root=FIG[key]['root'];IK={}
 mapping={'LH':('LeftForeArm','RightShoulder' if key=='leo' else 'LeftShoulder'),'RH':('RightForeArm','LeftArm' if key=='leo' else 'RightArm')}
 # leo faces +x: his left hand meets the rival's right shoulder; the rival's left hand meets Leo's right shoulder
 if key=='riv':mapping={'LH':('LeftForeArm','RightShoulder'),'RH':('RightForeArm','LeftShoulder')}
 else:mapping={'LH':('LeftForeArm','RightShoulder'),'RH':('RightForeArm','LeftShoulder')}
 for limb,(bone,target_bone) in mapping.items():
  tg=bpy.data.objects.new('Grip_%s_%s'%(key,limb),None);tg.empty_display_size=.06;link(tg)
  cl=tg.constraints.new('COPY_LOCATION');cl.target=orig;cl.subtarget='mixamorig:'+target_bone;cl.head_tail=1.0   # the shoulder bone is not part of any IK chain, so the two rigs do not depend on each other in a cycle
  pole=bpy.data.objects.new('Pole_%s_%s'%(key,limb),None);link(pole);pole.parent=root;sgn=1 if limb=='LH' else -1;pole.location=(.55*sgn,.55,1.0)
  c=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');c.target=tg;c.pole_target=pole;c.pole_angle=math.radians(-90 if limb=='LH' else 90);c.chain_count=2;c.use_stretch=False;IK[limb]=c
 return IK
IKS={'leo':make_ik('leo','riv'),'riv':make_ik('riv','leo')}
GRIPS=[(16.3,16.8,22.2,22.5),(34.4,34.9,35.6,35.9)]
def grip_influence(t):
 v=0.
 for a,b,c,d in GRIPS:
  v=max(v,smooth((t-a)/(b-a))*(1-smooth((t-c)/(d-c))) if t>=a else 0.)
 return v
for f in range(1,frames+1,2):
 t=(f-1)/fps;v=grip_influence(t)
 for key in IKS:
  for c in IKS[key].values():c.influence=v;c.keyframe_insert('influence',frame=f)
# ---------------------------------------------------------------------------------------------------------- the contact solver
def bone_w(rig,name,tail=False):
 pb=rig.pose.bones['mixamorig:'+name];return rig.matrix_world@(pb.tail if tail else pb.head)
def settle(f):
 scene.frame_set(f);bpy.context.view_layer.update()
STRIKES=[dict(att='riv',bone='LeftHand',tgt='leo',tbone='Spine2',lag=0,win=(10.1,11.7),react=None,name='rival punch hits Leo\'s guard'),
 dict(att='leo',bone='LeftHand',tgt='riv',tbone='Spine2',win=(12.2,13.8),react=12.7,name='Leo\'s jab hits the rival chest'),
 dict(att='leo',bone='RightFoot',tgt='riv',tbone='RightFoot',win=(23.3,24.8),react=23.6,name='Leo\'s sweep hits the rival\'s legs')]
IMPACTS=[]
def measure(st):
 """time of full extension of the striking limb, hand position there and the target position just before."""
 att=FIG[st['att']];best=None
 for f in range(F(st['win'][0]),F(st['win'][1]),1):
  settle(f);t=(f-1)/fps;p,r=state(st['att'],t);fwd=Vector((0,-1,0));fwd.rotate(att['root'].rotation_euler);hp=bone_w(att['rig'],st['bone']);rel=hp-att['root'].matrix_world.translation
  ext=rel.dot(Vector((fwd.x,fwd.y,0)))
  if best is None or ext>best[0]:best=(ext,f,hp.copy())
 ext,f,hp=best;t=(f-1)/fps;settle(f-st.get('lag',3));center=bone_w(FIG[st['tgt']]['rig'],st['tbone']);tp,depth=kit.surface_target(FIG[st['tgt']]['body'],hp,center,bpy.context.evaluated_depsgraph_get());st['depth']=depth
 return t,hp,tp
for st in STRIKES:
 t_imp,hp,tp=measure(st);res=Vector((tp.x-hp.x,tp.y-hp.y,0));st['t']=t_imp;print('PASS1',st['att'],round(t_imp,2),tuple(round(x,2) for x in hp),tuple(round(x,2) for x in tp))
 OFF[st['att']].append((t_imp-.3,t_imp,t_imp+.5,res))
 IMPACTS.append(t_imp)
apply_all()
for st in STRIKES:
 t_imp,hp,tp=measure(st);print('PASS2',st['att'],round(t_imp,2),tuple(round(x,2) for x in hp),tuple(round(x,2) for x in tp));st['err']=(Vector((tp.x-hp.x,tp.y-hp.y,tp.z-hp.z))).length;print('PENETRATION',st['name'],'%.0f cm'%(st['depth']*100));st['t']=t_imp;print('STRIKE',st['name'],'t=%.2f'%t_imp,'miss %.0f cm'%(st['err']*100))
# the lying rival must rest on the ground
def lowest(f,key='riv'):
 settle(f);dg=bpy.context.evaluated_depsgraph_get();e=FIG[key]['body'].evaluated_get(dg);mw=e.matrix_world;return min((mw@v.co).z for v in list(e.data.vertices)[::4])
for key in FIG:
 low={f:lowest(f,key) for f in range(1,frames+1,2)}
 ZL[key].update(kit.ground_lift(low,0.,.01,1.,1))
apply_all()
# ---------------------------------------------------------------------------------------------------------- dust and impact bursts from sampled foot contacts
contacts=[];last={}
for f in range(1,frames+1):
 settle(f);t=(f-1)/fps
 for key in FIG:
  for foot in ('LeftFoot','RightFoot'):
   p=bone_w(FIG[key]['rig'],foot);prev=last.get((key,foot));lowz=p.z<.14*FIG[key]['scale']+.03
   speed=(p-prev[1]).length*fps if prev else 0.
   if lowz and prev and not prev[0] and speed<4 and (key=='leo' and (2<t<6 or 15<t<16.6 or 24.8<t<29 or 9<t<10.5) or key=='riv' and (2<t<6 or 9<t<10.1 or 15.4<t<16.6 or 32.6<t<34.7)):contacts.append((f,p.x,p.y,key))
   last[(key,foot)]=(lowz,p)
puff=bpy.data.meshes.new('PuffMesh');import bmesh
bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.);bm.to_mesh(puff);bm.free()
def burst(f,x,y,size):
 o=bpy.data.objects.new('Puff',puff);link(o);o.data.materials.clear();o.data.materials.append(mat('Dust',(.6,.5,.36)))
 for fr,sc,dr in ((f-1,.001,0),(f+3,size,.25),(f+14,size*2.2,1.0),(f+30,.001,1.7)):
  o.location=(x,y,.15+dr*.3);o.scale=(sc,sc*.9,sc*.7);o.keyframe_insert('location',frame=fr);o.keyframe_insert('scale',frame=fr)
for f,x,y,k in contacts:burst(f,x,y,.22 if k=='leo' else .3)
for ti in IMPACTS:
 lp,_=state('riv',ti);burst(F(ti),lp.x,lp.y,.45)
lt=wp_state('leo',THROW[1]);burst(F(THROW[1]),lt[0].x-1.15,lt[0].y,.8)
burst(F(25.0),-2.1,0.6,.6);burst(F(33.0),-3.5,0,.4)
# ---------------------------------------------------------------------------------------------------------- arena: sand, ruined stone ring, crowd, torches, sky
bpy.ops.mesh.primitive_circle_add(vertices=48,radius=14,fill_type='NGON',location=(0,0,0));sand=bpy.context.object;sand.name='Sand';sand.data.materials.append(mat('Sand',(.72,.6,.38)))
bpy.ops.mesh.primitive_plane_add(size=300,location=(0,0,-.1));ou=bpy.context.object;ou.name='Ground';ou.data.materials.append(mat('Ground',(.3,.28,.22)))
for ring,(r0,h,col) in enumerate(((14.5,1.2,(.55,.5,.42)),(17.5,2.4,(.5,.45,.38)),(20.5,3.6,(.46,.42,.35)))):
 for i in range(60):
  a=i*2*PI/60
  if ring==0 and abs(math.sin(a))<.12:continue
  if rnd.random()<.08:continue
  prim('cube','Tier',(math.cos(a)*(r0+1.2),math.sin(a)*(r0+1.2),h/2),col,scale=(1.4,1.7,h/2*rnd.uniform(.8,1.0)),rot=(0,0,a))
sections=[bpy.data.objects.new('Sec%d'%i,None) for i in range(12)]
for s in sections:link(s)
for ring,(r0,h) in enumerate(((16.0,1.2),(19.0,2.4),(22.0,3.6))):
 for i in range(48):
  a=i*2*PI/48+rnd.uniform(-.02,.02);sec=sections[int(a/(2*PI)*12)%12]
  if abs(math.sin(a))<.1 and abs(math.cos(a))>.9 and ring==0:continue
  col=(rnd.uniform(.3,.9),rnd.uniform(.2,.7),rnd.uniform(.2,.6));x,y=math.cos(a)*(r0+rnd.uniform(-.3,.3)),math.sin(a)*(r0+rnd.uniform(-.3,.3))
  b=prim('cone','Fan',(x,y,h+.55),col,scale=(.28,.28,.55),vertices=6,radius1=1,depth=2);hd=prim('sphere','FanHead',(x,y,h+1.2),(.85,.7,.55),scale=(.2,.2,.2),subdivisions=1);b.parent=sec;hd.parent=sec
for a in np.linspace(0,2*PI,12,endpoint=False):
 x,y=math.cos(a)*14.4,math.sin(a)*14.4;h=rnd.uniform(6,9);prim('cyl','Pillar',(x,y,h/2),(.58,.54,.46),scale=(.6,.6,h/2),vertices=8,radius=1,depth=2);prim('cone','Torch',(x,y,h+.4),(1,.55,.15),scale=(.25,.25,.4),vertices=6,radius1=1,depth=2,emit=8.)
for a in (0,PI):prim('cube','GateL',(math.cos(a)*14.5,0,3),(.5,.46,.4),scale=(1,.4,3),rot=(0,0,0));
scene.world=bpy.data.worlds.new('Dusk');scene.world.color=(.75,.5,.38)
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));link(sun);sun.data.energy=3.2;sun.data.color=(1,.72,.5);sun.rotation_euler=(math.radians(58),0,math.radians(40))
# a few spectators are real cloned lions (shared mesh data, own armature, random clip phase) to show that crowds of animated characters work
import time
t_a=time.perf_counter()
for i in range(24):
 a=(i+.5)*2*PI/24;
 if abs(math.sin(a))<.12 and abs(math.cos(a))>.9:continue
 r0=15.9;root,crig,cbody=kit.clone_character(Lrig,Lbody,'CrowdLion%d'%i,(math.cos(a)*r0,math.sin(a)*r0,1.2),a+PI,.8+.15*rnd.random(),(rnd.uniform(.7,1.1),rnd.uniform(.6,1.0),rnd.uniform(.5,.9)))
 tr=[crig.animation_data.nla_tracks.new(),crig.animation_data.nla_tracks.new()]
 s1=kit.add_strip(tr[0],CLIPS['idle'],1-rnd.randint(0,90),F(10.0),'loop');s2=kit.add_strip(tr[1],CLIPS['cele'],F(10.0)-5-rnd.randint(0,100)*0,frames,'loop');s2.blend_in=5;s1.blend_out=5;s1.extrapolation='HOLD'
 for f in range(1,frames+1,6):pass
scene.frame_set(1);t_b=time.perf_counter();scene.frame_set(60);print('CROWD clones',sum(1 for o in bpy.data.objects if o.name.startswith('CrowdLion') and o.type=='ARMATURE'),'frame eval %.2fs'%(time.perf_counter()-t_b))
# crowd reaction to every impact and the final victory
CHEER=[(t,1.) for t in IMPACTS]+[(THROW[1],1.5),(40.0,1.8),(48.0,1.2)]
def cheer(t):return .12+sum(a*math.exp(-(t-t0)/1.4) for t0,a in CHEER if t>=t0)
for si,s in enumerate(sections):
 for f in range(1,frames+1,3):
  t=(f-1)/fps;s.location=(0,0,cheer(t)*.22*abs(math.sin(2*PI*(t*2.1+si*.37))));s.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
def lp_(t):return state('leo',t)[0]
def rp_(t):return state('riv',t)[0]
CUTS=[('1 The arena',0,3.5),('2 They enter',3.5,6),('3 Face off',6,9),('4 The charge',9,11.8),('5 Counter',11.8,14.4),('6 Closing in',14.4,16.8),('7 The grapple',16.8,22.4),('8 The sweep',22.4,25.2),('9 Rival down',25.2,31.5),
 ('10 Charge again',31.5,34.7),('11 The throw',34.7,36.8),('12 Aftermath',36.8,42),('13 Victory roar',42,47),('14 The bow',47,seconds)]
cams=[]
for k,(name,a,b) in enumerate(CUTS):
 if a>=seconds:break
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=2500;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(min(b,seconds))+1,2):
  t=(f-1)/fps;u=(t-a)/(b-a);L=lp_(t);R=rp_(t);mid=(L+R)/2+Vector((0,0,1.0));cam.data.lens=32
  if k==0:ang=math.radians(-80+50*u);p=Vector((math.cos(ang)*32,math.sin(ang)*32,14));q=Vector((0,0,2));cam.data.lens=26
  elif k==1:p=Vector((0,-9,1.4));q=mid;cam.data.lens=28
  elif k==2:p=Vector((0,-7.5,1.5));q=mid;cam.data.lens=36
  elif k==3:p=Vector((mid.x,-5,1.3));q=mid;cam.data.lens=34
  elif k==4:p=Vector((mid.x-.3,-4.4,1.4));q=mid+Vector((0,0,.1));cam.data.lens=32
  elif k==5:p=Vector((mid.x,-5.5,1.4));q=mid
  elif k==6:lp,phi,rp,rh,push=grap(t);M=(lp+rp)/2;ang=math.radians(-100)+u*math.radians(160);p=Vector((M.x+math.cos(ang)*3.4,M.y+math.sin(ang)*3.4,1.5));q=M+Vector((0,0,1.0));cam.data.lens=34
  elif k==7:p=Vector((mid.x+.5,-3.8,.9));q=mid;cam.data.lens=34
  elif k==8:p=Vector((-3,-9,2.2));q=Vector((-3.5,0,.6));cam.data.lens=30
  elif k==9:p=Vector((mid.x+1.5,-5.6,1.2));q=mid;cam.data.lens=32
  elif k==10:p=Vector((mid.x+.2,-4.4,1.6));q=Vector((mid.x,0,1.5));cam.data.lens=32
  elif k==11:p=Vector((L.x+3,-6,1.8));q=(L+R)/2+Vector((0,0,.6));cam.data.lens=30
  elif k==12:p=Vector((L.x+2.2,-4.6,.7));q=L+Vector((0,0,1.0));cam.data.lens=30
  else:p=Vector((-6+u*4,-8+u*-6,1.5+u*8));q=Vector((-6.5,0,1.0+u*3));cam.data.lens=30
  sh=sum(a_*math.exp(-abs(t-t0)*5) for t0,a_ in [(x,.07) for x in IMPACTS+[THROW[1]]] if abs(t-t0)<.6)
  cam.location=p+Vector((rnd.uniform(-1,1),rnd.uniform(-1,1),rnd.uniform(-1,1)))*sh;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
for st in STRIKES:
 if st['err']>.20:issues.append('AUDIT contact: %s misses by %.0f cm'%(st['name'],st['err']*100))
 if st['depth']>.06:issues.append('AUDIT penetration: %s goes %.0f cm inside the other lion'%(st['name'],st['depth']*100))
worst=(9,0)
for f in range(1,frames+1,6):
 t=(f-1)/fps
 if 16.0<=t<22.6 or 34.3<=t<42.1 or 23.2<=t<28.6:continue
 settle(f);pa=[bone_w(Lrig,b.name[10:]) for b in Lrig.pose.bones if b.name.startswith('mixamorig:') and 'Hand' not in b.name and 'Foot' not in b.name and 'Toe' not in b.name and 'Arm' not in b.name]
 pb=[bone_w(Rrig,b.name[10:]) for b in Rrig.pose.bones if b.name.startswith('mixamorig:') and 'Hand' not in b.name and 'Foot' not in b.name and 'Toe' not in b.name and 'Arm' not in b.name]
 d=min((a-b).length for a in pa for b in pb)
 if d<worst[0]:worst=(d,t)
if worst[0]<.10:issues.append('AUDIT overlap: the two lions come within %.0f cm (body bones) at t=%.1f s'%(worst[0]*100,worst[1]))
print('MINDIST %.2f at %.1f'%worst)
issues+=kit.audit(scene,bodies=[(Lrig,Lbody),(Rrig,Rbody)],floor_z=0.,skip=[(23.2,28.6),(34.3,42.1)],subjects=[LR,RR],step=12)
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);tt=np.arange(N_)/SR;adir=os.path.join(os.path.dirname(out),'audio_arena');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(9)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
cr=np.array([cheer(t) for t in tt[::200]]);cr=np.interp(tt,tt[::200],cr);crowd=lp(nr.standard_normal(N_),9)*(.15+.8*cr)*(1+.3*np.sin(tt*5.))
hits=np.zeros(N_+SR)
for ti in IMPACTS+[THROW[1]]:
 n=int(.6*SR);k=np.arange(n)/SR;x=(lp(nr.standard_normal(n),25)*np.exp(-k*9)+np.sin(2*PI*(80-50*k)*k)*np.exp(-k*7))*1.2;i=int(ti*SR);hits[i:i+n]+=x
hits=hits[:N_]
foot=np.zeros(N_+SR);ft=np.arange(int(.2*SR))/SR;step=np.sin(2*PI*(70-40*ft)*ft)*np.exp(-ft*20)+lp(nr.standard_normal(len(ft)),20)*np.exp(-ft*25)
for f,x,y,k in contacts:
 i=int((f-1)/fps*SR)
 if i<N_:foot[i:i+len(step)]+=step*(.7 if k=='leo' else 1.0)
foot=foot[:N_]
def roar(t0,length,f0,amp=1.):
 n=int(length*SR);k=np.arange(n)/SR;f=f0+60*np.sin(2*PI*5*k)*np.exp(-k)-20*k;ph=2*PI*np.cumsum(f)/SR;x=(np.sin(ph)+.6*np.sin(2*ph)+.4*np.sin(3*ph)+.6*nr.standard_normal(n))*np.minimum(k/.08,1)*np.exp(-k*.9);x=lp(x,4);tr=np.zeros(N_);i=int(t0*SR);tr[i:i+n]=x[:max(0,min(n,N_-i))]*amp;return tr
voice=roar(7.4,1.6,120,.7)+roar(8.4,1.2,150,.6)+roar(16.2,.9,170,.5)+roar(21.8,1.0,150,.7)+roar(39.0,2.4,190,1.1)
torch=lp(nr.standard_normal(N_),60)*.06*(1+np.sin(tt*9)*.5)
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.4*np.sin(4*PI*f*k))*np.minimum(k/.15,1)*np.exp(-k*1.6/d)*v)(np.arange(int(d*SR))/SR)
music=np.zeros(N_+SR*5);minor=[(110,130.8,164.8),(98,116.5,146.8),(103.8,123.5,155.6),(98,123.5,146.8)];major=[(130.8,164.8,196),(98,123.5,146.8),(110,138.6,164.8),(87.3,130.8,174.6)]
for ci in range(int(seconds/2.5)+1):
 t0=ci*2.5;chord=major[ci%4] if t0>=38.5 else minor[ci%4];vol=.5 if t0<8 else .8 if t0<38 else .6
 for j,f0 in enumerate(chord):
  n_=note(f0,2.6,vol*.5);i=int(t0*SR)
  if i<N_:music[i:i+len(n_)]+=n_
 if 8<=t0<=38:
  for b in range(5):
   i=int((t0+b*.5)*SR);kt=np.arange(int(.2*SR))/SR;kk=np.sin(2*PI*(55*kt-90*kt**2))*np.exp(-kt*20)
   if i<N_:music[i:i+len(kk)]+=kk*1.5
music=music[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('crowd.wav',crowd+torch,.7),wav('impacts.wav',hits,.95),wav('footsteps.wav',foot,.7),wav('roars.wav',voice,.85),wav('music.wav',music,.5)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('crowd and torches','impacts','footsteps','roars','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('ARENA_DONE',frames,'frames')
