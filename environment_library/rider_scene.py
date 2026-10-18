"""Blender script: Rowan mounts a horse and gallops across a meadow beside a river toward the mountains, jumps a fence, with dust, chase cameras and sound.

blender -b --disable-autoexec --python rider_scene.py -- <Horse.blend> <rider.blend> <out.blend> [seconds=22] [rowan|lion]
(rider.blend: samples/mpfb-character/rowan.blend, or the scene.blend of any built lion shot for kind 'lion'; the lion rides with the same IK seat, tuned for his short legs and arms)

Pieces (all procedural, nothing downloaded beyond the CC0 horse):
  * horse: Quaternius Horse (rigged, actions Idle, Walk, Run, Jump) scaled 0.27, one NLA track pair with overlapping strips (idle -> walk -> gallop -> jump -> gallop)
  * path: an S curve; speed profile 0 -> walk -> gallop; the jump adds a height arc; the horse heads along the path tangent
  * rider: Rowan stands beside the horse, leaps into the saddle (arc keyed from the horse's saddle position), then a Child Of constraint keeps his body on the
           horse's torso bone; legs and arms are IK to stirrup and rein empties that follow the horse's bones; he leans into the gallop
  * dust: a puff at every hoof landing (found by sampling the hoof bones), growing and shrinking as it drifts back
  * cameras (cuts on markers): wide, walk-along, chase from behind, low side, ahead looking back at the jump, drone, rider point of view
  * sound: hooves at the real contact times, wind rising with speed, music; three WAVs added as sound strips"""
import bpy,math,random,sys,os,wave
import numpy as np
from mathutils import Vector,Matrix,Euler
args=sys.argv[sys.argv.index('--')+1:];horse_file,rowan_file,out=args[0],args[1],args[2];seconds=float(args[3]) if len(args)>3 else 22.;KIND=args[4] if len(args)>4 else 'rowan'
KINDS={'rowan':dict(coat=(.50,.25,.10),stirrup=(.46,.12,.50),knee=(.95,-.10,.95),rein=(.13,-.42,1.20),elbow=(.65,.15,1.30),lean=-.10,pov=.30),
 'lion':dict(coat=(.86,.86,.82),stirrup=(.44,.10,.80),knee=(.95,-.05,1.05),rein=(.15,-.16,1.30),elbow=(.65,.15,1.40),lean=-.12,pov=.55)}
K=KINDS[KIND]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
rnd=random.Random(9);H_SCALE=.27
def F(t):return 1+int(round(t*fps))
# ----------------------------------------------------------------------------------------------------- assets
with bpy.data.libraries.load(horse_file,link=False) as (src,dst):dst.objects=[n for n in src.objects];dst.actions=list(src.actions)
horse_rig=next(o for o in dst.objects if o.type=='ARMATURE');horse_mesh=next(o for o in dst.objects if o.type=='MESH');actions={a.name:a for a in dst.actions}
for o in (horse_rig,horse_mesh):scene.collection.objects.link(o)
horse_mesh.parent=horse_rig;horse_rig.scale=(H_SCALE,)*3;horse_rig.animation_data_clear()
coat=bpy.data.materials.new('Coat');coat.diffuse_color=(*K['coat'],1);coat.use_nodes=True;coat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*K['coat'],1)
slot=max(range(len(horse_mesh.data.materials)),key=lambda i:sum(1 for p in horse_mesh.data.polygons if p.material_index==i));horse_mesh.data.materials[slot]=coat
with bpy.data.libraries.load(rowan_file,link=False) as (src,dst):dst.objects=[n for n in src.objects]
rowan_objs=[]
for o in dst.objects:
 if o.type in ('CAMERA','LIGHT','EMPTY') or o.name=='Plane' or o.hide_render or (o.type=='MESH' and o.hide_viewport):bpy.data.objects.remove(o);continue
 scene.collection.objects.link(o);rowan_objs.append(o)
rowan=next(o for o in rowan_objs if o.type=='ARMATURE');rowan.animation_data_clear()
for pb_ in rowan.pose.bones:
 pb_.rotation_mode='QUATERNION';pb_.rotation_quaternion=(1,0,0,0);pb_.location=(0,0,0);pb_.scale=(1,1,1)
bpy.context.view_layer.update()
HIPS_LOCAL=(rowan.matrix_world@next(b for b in rowan.pose.bones if b.name.endswith('Hips')).head)-rowan.matrix_world.translation   # the hips bone in the rider's own space, whatever the rig's scale
for o in rowan_objs:
 if o.animation_data:o.animation_data_clear()
# ----------------------------------------------------------------------------------------------------- path and gait
GAIT=[('Idle',0.,4.,1.,0.),('Walk',4.,6.5,1.5,1.7),('Run',6.5,13.3,2.4,7.6),('Jump',13.3,14.8,1.,7.6),('Run',14.8,seconds,2.4,7.6)]
JUMP=(13.3,14.8)
def speed_at(t):
 if t<4:return 0.
 if t<6.5:return 1.7*(t-4)/2.5
 if t<8.5:return 1.7+(7.6-1.7)*(t-6.5)/2.
 if t>seconds-1.5:return 7.6*max(.35,(seconds-t)/1.5)
 return 7.6
dt=1/fps;S=[0.];
for i in range(frames):S.append(S[-1]+speed_at(i*dt)*dt)
def path(s):return (s,9*math.sin(s/45.))
def heading(s):
 dy=9/45.*math.cos(s/45.);return math.atan2(dy,1.)
HEIGHT=lambda t:(.85*math.sin(math.pi*(t-JUMP[0]-.15)/1.2) if JUMP[0]+.15<t<JUMP[0]+1.35 else 0.)
def horse_state(f):
 t=(f-1)/fps;s=S[min(f-1,frames)];x,y=path(s);return (x,y,HEIGHT(t)),heading(s)
for f in range(1,frames+1,2):
 (x,y,z),h=horse_state(f);horse_rig.location=(x,y,z);horse_rig.rotation_euler=(0,0,h+math.pi/2);horse_rig.keyframe_insert('location',frame=f);horse_rig.keyframe_insert('rotation_euler',frame=f)
horse_rig.animation_data_create();tracks=[horse_rig.animation_data.nla_tracks.new(),horse_rig.animation_data.nla_tracks.new()]
for k,(name,a,b,play,spd) in enumerate(GAIT):
 act=actions[name];start=F(a)-(6 if k else 0);strip=tracks[k%2].strips.new(name+str(k),start,act);strip.scale=1/play;strip.extrapolation='HOLD' if k==0 else 'NOTHING'
 length=act.frame_range[1]-act.frame_range[0]+1;cycle=length/play;strip.repeat=max(1.,(F(b)-start)/cycle) if name!='Jump' else 1.;strip.blend_in=6 if k else 0;strip.blend_out=6;strip.use_sync_length=False
# ----------------------------------------------------------------------------------------------------- anchors on the horse (horse-local metres, forward is -Y)
scene.frame_set(1);bpy.context.view_layer.update()
def local_world(m,frame=1):
 scene.frame_set(frame);bpy.context.view_layer.update();return horse_rig.matrix_world@Vector((m[0]/H_SCALE,m[1]/H_SCALE,m[2]/H_SCALE))
def attach(obj,bone,frame=1):
 """Child Of constraint onto a horse bone that keeps obj's world pose at `frame`."""
 scene.frame_set(frame);bpy.context.view_layer.update();w=obj.matrix_world.copy()
 con=obj.constraints.new('CHILD_OF');con.target=horse_rig;con.subtarget=bone;pb=horse_rig.pose.bones[bone];con.inverse_matrix=(horse_rig.matrix_world@pb.matrix).inverted();obj.matrix_basis=w;return con
def empty(name,m,bone):
 e=bpy.data.objects.new(name,None);e.empty_display_size=.08;scene.collection.objects.link(e);e.location=local_world(m);bpy.context.view_layer.update();attach(e,bone);return e
SADDLE=(0.,.10,1.13)
sx,sy,sz=K['stirrup'];stirrup={'L':empty('StirrupL',(sx,sy,sz),'Torso'),'R':empty('StirrupR',(-sx,sy,sz),'Torso')}   # outside the horse's flanks (the body is ~0.7 m wide)
kx,ky,kz=K['knee'];knee={'L':empty('KneePoleL',(kx,ky,kz),'Torso'),'R':empty('KneePoleR',(-kx,ky,kz),'Torso')}
rx,ry,rz=K['rein'];rein={'L':empty('ReinL',(rx,ry,rz),'Shoulders'),'R':empty('ReinR',(-rx,ry,rz),'Shoulders')}
ex,ey,ez=K['elbow'];elbow={'L':empty('ElbowPoleL',(ex,ey,ez),'Torso'),'R':empty('ElbowPoleR',(-ex,ey,ez),'Torso')}
mouth=empty('Mouth',(0,-1.12,1.33),'Head')
# saddle, blanket, stirrups, reins (visual)
def box(name,size,color,loc,bone=None):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.scale=size;o.location=loc;m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);o.data.materials.append(m)
 if bone:bpy.context.view_layer.update();attach(o,bone)
 return o
box('Saddle',(.34,.46,.07),(.28,.14,.07),local_world((0,.10,1.045)),'Torso');box('Blanket',(.40,.62,.03),(.55,.1,.1),local_world((0,.10,1.0)),'Torso')
for side_,e in stirrup.items():box('StirrupBox'+side_,(.06,.1,.04),(.55,.55,.55),e.matrix_world.translation.copy(),'Torso')
for side_ in 'LR':
 bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.008,depth=1);r=bpy.context.object;r.name='Rein'+side_;m=bpy.data.materials.new('Rein');m.diffuse_color=(.1,.06,.03,1);r.data.materials.append(m)
 for v in r.data.vertices:v.co=(v.co.x,v.co.z+.5,v.co.y)   # a rod along +Y from the origin, so Stretch To can aim and stretch it from the hand to the mouth
 cp=r.constraints.new('COPY_LOCATION');cp.target=rein[side_];sc=r.constraints.new('STRETCH_TO');sc.target=mouth;sc.rest_length=1.
# ----------------------------------------------------------------------------------------------------- rider
seat_world=local_world(SADDLE)
MOUNT=(2.3,3.7)
standing=local_world((0.95,0.10,0.0));standing.z=0.
rowan.rotation_euler=(0,0,horse_state(1)[1]+math.pi/2)
seat_loc=seat_world-Vector((0,0,HIPS_LOCAL.z))
for f in range(F(0),F(MOUNT[0])):
 pass
# mount: the object travels on an arc from beside the horse to the saddle (saddle position taken from the horse at each frame), then a Child Of takes over
def saddle_world(f):return local_world(SADDLE,f)-Vector((0,0,HIPS_LOCAL.z))
m0,m1=F(MOUNT[0]),F(MOUNT[1])
for f in range(1,m1+1,1):
 if f<m0:p=standing
 else:
  u=(f-m0)/max(1,m1-m0);u=u*u*(3-2*u);end=saddle_world(f);p=standing.lerp(end,u)+Vector((0,0,.55*math.sin(math.pi*u)))
 rowan.location=p;rowan.keyframe_insert('location',frame=f)
for f in range(1,m1+1):rowan.rotation_euler=(0,0,horse_state(f)[1]+math.pi/2);rowan.keyframe_insert('rotation_euler',frame=f)
scene.frame_set(m1);bpy.context.view_layer.update();w=rowan.matrix_world.copy()
con=rowan.constraints.new('CHILD_OF');con.target=horse_rig;con.subtarget='Torso';pb=horse_rig.pose.bones['Torso'];con.inverse_matrix=(horse_rig.matrix_world@pb.matrix).inverted()
con.influence=0;con.keyframe_insert('influence',frame=m1-1);con.influence=1;con.keyframe_insert('influence',frame=m1)
for fc in ([] ):pass
# IK for legs and arms: influence ramps up as the rider lands
def bone_of(name):return rowan.pose.bones['mixamorig:'+name]
ik=[]
for s_,name in (('L','Left'),('R','Right')):
 leg=rowan.pose.bones['mixamorig:%sLeg'%name];c=leg.constraints.new('IK');c.target=stirrup[s_];c.pole_target=knee[s_];c.pole_angle=math.radians(-90 if s_=='L' else 90);c.chain_count=2;c.use_stretch=False;ik.append(c)
 fore=rowan.pose.bones['mixamorig:%sForeArm'%name];c=fore.constraints.new('IK');c.target=rein[s_];c.pole_target=elbow[s_];c.pole_angle=math.radians(-90 if s_=='L' else 90);c.chain_count=2;c.use_stretch=False;ik.append(c)
for c in ik:
 c.influence=0;c.keyframe_insert('influence',frame=m0);c.influence=1;c.keyframe_insert('influence',frame=m1)
for n in ('Spine','Spine1','Spine2'):   # lean into the gallop after the mount, upright again as the horse slows
 pbn=bone_of(n);pbn.rotation_mode='XYZ';pbn.rotation_euler=(0,0,0);pbn.keyframe_insert('rotation_euler',frame=m1)
 pbn.rotation_euler=(K['lean'],0,0);pbn.keyframe_insert('rotation_euler',frame=F(8.5));pbn.keyframe_insert('rotation_euler',frame=F(seconds-1.5));pbn.rotation_euler=(-.02,0,0);pbn.keyframe_insert('rotation_euler',frame=frames)
# ----------------------------------------------------------------------------------------------------- environment
def material(name,color):
 m=bpy.data.materials.get(name)
 if m:return m
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
 return m
def ribbon(name,line,width,z,mat):
 verts=[];faces=[]
 for i,(x,y) in enumerate(line):
  j=min(i+1,len(line)-1);k=max(i-1,0);dx,dy=line[j][0]-line[k][0],line[j][1]-line[k][1];n=math.hypot(dx,dy) or 1;nx,ny=-dy/n,dx/n;verts+=[(x+nx*width/2,y+ny*width/2,z),(x-nx*width/2,y-ny*width/2,z)]
 faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(line)-1)];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.data.materials.append(mat);return o
bpy.ops.mesh.primitive_plane_add(size=1);g=bpy.context.object;g.name='Meadow';g.scale=(1600,700,1);g.location=(S[-1]*.4,0,-.02);gm=material('Meadow',(.16,.36,.08));g.data.materials.append(gm)
total=S[-1]+120;line=[(x,-30+9*math.sin(x/45.)) for x in np.linspace(-60,total,80)]
ribbon('RiverBank',line,26,.01,material('Bank',(.36,.30,.16)));ribbon('River',line,15,.04,material('Water',(.12,.35,.62)))
def cone(x,y,h,r,mat,verts=6):
 bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,depth=h,location=(x,y,h/2),rotation=(0,0,rnd.uniform(0,1)));o=bpy.context.object;o.data.materials.append(mat);return o
for i in range(70):
 x=rnd.uniform(-40,total);y=rnd.choice((1,-1))*rnd.uniform(24,60)+(-30 if rnd.random()<.5 else 0)
 if abs(y+30-9*math.sin(x/45.))<12:continue
 bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.18,depth=4,location=(x,y,2));t=bpy.context.object;t.data.materials.append(material('Trunk',(.3,.2,.1)));cone(x,y,6.5,2.0,material('Pine',(.08,.28,.12)),7).location.z=6
for i in range(34):
 x=rnd.uniform(total*.55,total+260);y=rnd.uniform(-260,260);h=rnd.uniform(35,95);m=cone(x,y,h,h*rnd.uniform(.8,1.2),material('Mountain',(.38,.4,.45)))
 if h>55:cone(x,y,h*.28,h*.26,material('Snow',(.95,.96,.98))).location.z=h*.86
for i in range(16):
 x=rnd.uniform(-150,total);y=rnd.choice((1,-1))*rnd.uniform(150,320);h=rnd.uniform(8,22);cone(x,y,h,h*1.7,material('Hill',(.18,.36,.12)))
# the fence the horse jumps
s_jump=S[F(JUMP[0]+.75)-1];fx,fy=path(s_jump);fh=heading(s_jump)
for k in range(-6,7):
 px=fx+(-math.sin(fh))*k*.7;py=fy+math.cos(fh)*k*.7
 bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.07,depth=1.0,location=(px,py,.5));p=bpy.context.object;p.data.materials.append(material('FencePost',(.42,.28,.15)))
for z in (.45,.8):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(fx,fy,z),rotation=(0,0,fh+math.pi/2));r=bpy.context.object;r.scale=(.06,9.,.07);r.data.materials.append(material('FenceRail',(.5,.35,.18)))
scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.6,.75,.9)
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sun.data.energy=3.2;sun.rotation_euler=(math.radians(50),0,math.radians(-35));scene.collection.objects.link(sun)
# ----------------------------------------------------------------------------------------------------- dust from hoof landings
hoof_bones=['FrontFoot.L','FrontFoot.R','BackFoot.L','BackFoot.R'];contacts=[];last={b:False for b in hoof_bones};prev_z={b:9. for b in hoof_bones}
for f in range(1,frames+1):
 scene.frame_set(f);bpy.context.view_layer.update();t=(f-1)/fps
 for b in hoof_bones:
  p=horse_rig.matrix_world@horse_rig.pose.bones[b].head;low=p.z<.12+horse_rig.location.z and speed_at(t)>.5
  if low and not last[b]:contacts.append((f,p.x,p.y,speed_at(t)))
  last[b]=low
dust_mat=material('Dust',(.72,.64,.50));bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1);template=bpy.context.object;template.data.materials.append(dust_mat);template.hide_render=True;template.hide_viewport=True
for k,(f,x,y,v) in enumerate(contacts):
 o=bpy.data.objects.new('Dust%d'%k,template.data);scene.collection.objects.link(o);h=horse_state(f)[1];back=(-math.cos(h),-math.sin(h));size=.05+.012*v
 for fr,sc_,drift in ((f-1,0.001,0),(f+3,size,.2),(f+14,size*1.9,1.0),(f+28,0.001,1.8)):
  o.location=(x+back[0]*drift,y+back[1]*drift,.12+drift*.25);o.scale=(sc_,sc_*.9,sc_*.7);o.keyframe_insert('location',frame=fr);o.keyframe_insert('scale',frame=fr)
# ----------------------------------------------------------------------------------------------------- cameras
def at_frame(f):
 (x,y,z),h=horse_state(f);return Vector((x,y,0)),h
def rel(f,ahead,lateral,height,lag=0):
 c,h=at_frame(max(1,f-lag));fwd=Vector((math.cos(h),math.sin(h),0));sd=Vector((-math.sin(h),math.cos(h),0));return c+fwd*ahead+sd*lateral+Vector((0,0,height))
SHOTS=[('1 Wide, mounting',0,4.),('2 Walking out',4.,6.5),('3 Chase, behind and above',6.5,10.5),('4 Low, alongside',10.5,13.),('5 Ahead, the jump',13.,15.5),('6 Drone, mountains ahead',15.5,19.),('7 Rider point of view',19.,seconds)]
SHOTS=[s for s in SHOTS if s[1]<seconds]
cams=[]
for k,(name,a,b) in enumerate(SHOTS):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=3000;scene.collection.objects.link(cam);cams.append(cam)
 aim=bpy.data.objects.new('Aim%d'%k,None);scene.collection.objects.link(aim);aim.hide_viewport=True
 if k==len(SHOTS)-1 and name.startswith('7'):   # rider point of view: attached to Rowan's head bone, looking ahead
  cam.data.lens=24;scene.frame_set(F(a));bpy.context.view_layer.update();hb=rowan.pose.bones['mixamorig:Head'];hw=rowan.matrix_world@hb.head
  hh=horse_state(F(a))[1];cam.location=hw+Vector((math.cos(hh)*K['pov'],math.sin(hh)*K['pov'],.04));   # just in front of the face, so the camera is not inside the head
  cam.rotation_euler=Euler((math.radians(90),0,horse_state(F(a))[1]-math.pi/2),'XYZ')   # looks along the horse's heading
  bpy.context.view_layer.update();wcam=cam.matrix_world.copy();c=cam.constraints.new('CHILD_OF');c.target=rowan;c.subtarget='mixamorig:Spine2';c.inverse_matrix=(rowan.matrix_world@rowan.pose.bones['mixamorig:Spine2'].matrix).inverted();cam.matrix_basis=wcam
  scene.timeline_markers.new(name,frame=F(a)).camera=cam;continue
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,4):
  u=(f-F(a))/max(1,F(b)-F(a))
  if k==0:p=rel(1,-1.5,7-2*u,1.7);q=(horse_state(1)[0][0]+.4,horse_state(1)[0][1],1.1);cam.data.lens=40;p.x=p.x
  elif k==1:p=rel(f,3.5,3.8,1.6);q=tuple(rel(f,0,0,1.15));cam.data.lens=45
  elif k==2:p=rel(f,-6.5-1.5*u,.8,3.2,lag=6);q=tuple(rel(f,2,0,1.1));cam.data.lens=34
  elif k==3:p=rel(f,-2+4*u,7.5,1.1);q=tuple(rel(f,0,0,.9));cam.data.lens=50
  elif k==4:p=rel(1,0,0,0);cx,cy=fx,fy;fwd=Vector((math.cos(fh),math.sin(fh),0));p=Vector((cx,cy,.9))+fwd*(7-9*u)+Vector((-math.sin(fh),math.cos(fh),0))*1.8;q=tuple(rel(f,0,0,1.4));cam.data.lens=30
  else:p=rel(f,-14+20*u,-26,26-8*u);q=tuple(rel(f,10,0,1));cam.data.lens=32
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f)
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
# ----------------------------------------------------------------------------------------------------- sound
SR=22050;N=int(seconds*SR);tt=np.arange(N)/SR;adir=os.path.join(os.path.dirname(out),'audio_rider');os.makedirs(adir,exist_ok=True);nrng=np.random.default_rng(4)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
thud_t=np.arange(int(.16*SR))/SR;thud=np.sin(2*np.pi*(110*thud_t-200*thud_t**2))*np.exp(-thud_t*30)+.4*nrng.standard_normal(len(thud_t))*np.exp(-thud_t*60)
hoof=np.zeros(N+len(thud))
for f,x,y,v in contacts:
 i=int((f-1)/fps*SR);amp=min(1.,.25+v/9)
 if i<N:hoof[i:i+len(thud)]+=thud*amp
hoof=hoof[:N]
def lowpass(x,k):return np.convolve(x,np.ones(k)/k,mode='same')
spd=np.array([speed_at(t) for t in tt[::SR//50]]);spd=np.interp(tt,tt[::SR//50],spd)
wind=lowpass(nrng.standard_normal(N),150)*(.1+spd/7.6*.9);river=(lowpass(nrng.standard_normal(N),12)-lowpass(nrng.standard_normal(N),90))*.25
def note(freq,length,vel=1.):
 n=int(length*SR);t=np.arange(n)/SR;env=np.minimum(t/.02,1)*np.exp(-t*3/length);return (np.sin(2*np.pi*freq*t)+.4*np.sin(4*np.pi*freq*t))*env*vel
music=np.zeros(N+SR*3);prog=[(146.83,220,293.66),(116.54,174.61,233.08),(87.31,174.61,261.63),(130.81,196,261.63)]
for ci in range(int(seconds/2.5)+1):
 chord=prog[ci%4];t0=ci*2.5;gallop=t0>=6.5
 for j,f0 in enumerate(chord):
  step=.25 if gallop else .5
  for rep in range(int(2.5/step)):
   i=int((t0+rep*step+.06*j)*SR)
   if i<N:n_=note(f0*(2 if rep%2 else 1),.5,.5 if gallop else .3);music[i:i+len(n_)]+=n_
 if gallop:
  for beat in range(10):
   i=int((t0+beat*.25)*SR);kt=np.arange(int(.12*SR))/SR;k=np.sin(2*np.pi*(70*kt-120*kt**2))*np.exp(-kt*30)
   if i<N:music[i:i+len(k)]+=k*(.9 if beat%2==0 else .45)
music=music[:N]*np.minimum(tt/1.5,1)*np.minimum((seconds-tt)/2.,1)*(.3+.7*np.clip((tt-4)/4,0,1))
paths=[wav('hooves.wav',hoof,.95),wav('wind_river.wav',wind+river,.7),wav('music.wav',music,.6)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('hooves','wind and river','music')),start=1):strips.new_sound(n,p,ch,1)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('RIDER_DONE',frames,'frames',len(contacts),'hoof contacts')
