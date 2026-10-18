"""Blender script: an aerial herd of galloping horses over a green meadow (like a drone photo), from the CC0 Quaternius horse.

blender -b --disable-autoexec --python horse_herd.py -- <Horse.blend> <out.blend> [count] [seconds]

The horse is already rigged (28 bones) and has a 20-frame 'Run' action, so no auto-rigging is needed: every horse gets its own copy of the
armature and mesh, plays 'Run' from an NLA strip (random phase, retimed so the legs match the ground speed) and travels along the herd's
heading with a little sideways wander. Coats follow the photo (white, grey, bay, black, chestnut, palomino) and about one in six is a
foal (smaller, quicker legs). The camera is a drone: high, tilted down, drifting forward slower than the herd.
Heading faces the model's forward axis (-Y in the asset): rotation = heading + 90 degrees."""
import bpy,math,random,sys
args=sys.argv[sys.argv.index('--')+1:];source,out=args[0],args[1];count=int(args[2]) if len(args)>2 else 64;seconds=float(args[3]) if len(args)>3 else 16.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
rnd=random.Random(5)
with bpy.data.libraries.load(source,link=False) as (src,dst):
 dst.objects=[n for n in src.objects];dst.actions=list(src.actions)
rig0=next(o for o in dst.objects if o.type=='ARMATURE');mesh0=next(o for o in dst.objects if o.type=='MESH');run=next(a for a in dst.actions if a.name=='Run')
for o in (rig0,mesh0):scene.collection.objects.link(o)
mesh0.parent=rig0
SCALE=.22        # model is ~10.7 units long; 0.22 gives a 2.3 m horse
SPEED=4.6        # m/s: matched to the Run cycle (foot sweep per cycle x playback)
PLAY=1.7         # playback speed of the 20-frame Run cycle (legs then roughly match the ground speed)
PALETTE=[('white',(.88,.88,.85),.20),('grey',(.52,.52,.53),.16),('bay',(.30,.14,.07),.20),('black',(.045,.04,.04),.14),('chestnut',(.52,.26,.10),.16),('palomino',(.80,.60,.34),.14)]
def pick():
 r=rnd.random();acc=0
 for name,color,weight in PALETTE:
  acc+=weight
  if r<=acc:return name,color
 return PALETTE[-1][0],PALETTE[-1][1]
coat_slot=max(range(len(mesh0.data.materials)),key=lambda i:sum(1 for p in mesh0.data.polygons if p.material_index==i))   # the material most faces use is the coat
def coat_material(name,color):
 m=bpy.data.materials.get('Coat_'+name)
 if m:return m
 m=bpy.data.materials.new('Coat_'+name);m.diffuse_color=(*color,1);m.use_nodes=True;bsdf=m.node_tree.nodes.get('Principled BSDF')
 if bsdf:bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.8
 return m
# herd layout: loose groups like the photo, with room between horses
heading=math.radians(158)   # running toward the upper left of the frame
centers=[(rnd.uniform(-16,16),rnd.uniform(-10,10)) for _ in range(6)];positions=[]
tries=0
while len(positions)<count and tries<20000:
 tries+=1;cx,cy=centers[rnd.randrange(len(centers))];p=(cx+rnd.gauss(0,8),cy+rnd.gauss(0,5.5))
 if all((p[0]-q[0])**2+(p[1]-q[1])**2>3.2**2 for q in positions):positions.append(p)
forward=(math.cos(heading),math.sin(heading));side=(-forward[1],forward[0])
horses=[]
for i,(px,py) in enumerate(positions):
 rig=rig0.copy();rig.data=rig0.data.copy();rig.name='HorseRig.%03d'%i;rig.animation_data_clear();scene.collection.objects.link(rig)   # a copy would share the template's action and every horse would get the same keys
 body=mesh0.copy();body.data=mesh0.data.copy();body.name='Horse.%03d'%i;scene.collection.objects.link(body);body.parent=rig
 for mod in body.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 coat,color=pick();body.data.materials[coat_slot]=coat_material(coat,color)
 if coat in ('white','grey','palomino'):   # light horses have a light mane too
  for k,m in enumerate(body.data.materials):
   if k!=coat_slot:body.data.materials[k]=coat_material(coat+'_mane',tuple(min(1,c*1.1) for c in color))
 foal=rnd.random()<.17;s=SCALE*(.62 if foal else 1.)*rnd.uniform(.95,1.05);rig.scale=(s,s,s)
 phase=rnd.uniform(0,20);play=PLAY*(1.45 if foal else 1.)*rnd.uniform(.94,1.06)
 rig.animation_data_create();track=rig.animation_data.nla_tracks.new();strip=track.strips.new('run',1,run)
 strip.scale=1/play;strip.frame_start=1-phase/play;cycle=20/play;strip.repeat=max(1.,math.ceil((frames+phase/play)/cycle)+1);strip.extrapolation='HOLD'
 speed=SPEED*rnd.uniform(.92,1.08)*(.9 if foal else 1.);wobble=rnd.uniform(.3,.9);wphase=rnd.uniform(0,6.28)
 rig.rotation_euler=(0,0,heading+math.pi/2)
 for f in range(1,frames+1,6):
  t=(f-1)/fps;ahead=speed*t;lateral=wobble*math.sin(t*.9+wphase)
  rig.location=(px+forward[0]*ahead+side[0]*lateral,py+forward[1]*ahead+side[1]*lateral,0)
  rig.rotation_euler=(0,0,heading+math.pi/2+.04*math.cos(t*.9+wphase));rig.keyframe_insert('location',frame=f);rig.keyframe_insert('rotation_euler',frame=f)
 horses.append(rig)
for o in (rig0,mesh0):bpy.data.objects.remove(o)   # the originals were only templates
# meadow
bpy.ops.mesh.primitive_plane_add(size=1);ground=bpy.context.object;ground.name='Meadow';ground.scale=(600,600,1)
gm=bpy.data.materials.new('Meadow');gm.diffuse_color=(.13,.32,.07,1);gm.use_nodes=True;nt=gm.node_tree;bsdf=nt.nodes.get('Principled BSDF')
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.35;noise.inputs['Detail'].default_value=8
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.07,.22,.04,1);ramp.color_ramp.elements[1].color=(.2,.42,.09,1)
nt.links.new(noise.outputs['Fac'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=1
ground.data.materials.append(gm)
scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.6,.75,.9)
sun=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sun.data.energy=3.2;sun.rotation_euler=(math.radians(50),0,math.radians(-35));scene.collection.objects.link(sun)
# ---------------------------------------------------------------------------------------------------------------------
# river, mountains, camera cuts and a synthesised soundtrack
import numpy as np,wave,os
RIVER_SIDE=-1   # the river lies on the side away from the first (drone) camera
def poly_material(name,color):
 m=bpy.data.materials.get(name)
 if m:return m
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
 return m
def strip_mesh(name,centerline,width,z,material):
 """A flat ribbon following a list of (x,y) points."""
 verts=[];faces=[]
 for i,(x,y) in enumerate(centerline):
  j=min(i+1,len(centerline)-1);k=max(i-1,0);dx,dy=centerline[j][0]-centerline[k][0],centerline[j][1]-centerline[k][1];n=math.hypot(dx,dy) or 1;nx,ny=-dy/n,dx/n
  verts+=[(x+nx*width/2,y+ny*width/2,z),(x-nx*width/2,y-ny*width/2,z)]
 for i in range(len(centerline)-1):faces.append((2*i,2*i+1,2*i+3,2*i+2))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.data.materials.append(material);return obj
cx0=sum(p[0] for p in positions)/len(positions);cy0=sum(p[1] for p in positions)/len(positions)
def herd_centre(t):return (cx0+forward[0]*SPEED*t,cy0+forward[1]*SPEED*t)
def at(centre,ahead,lateral):return (centre[0]+forward[0]*ahead+side[0]*lateral,centre[1]+forward[1]*ahead+side[1]*lateral)
# river: a meandering ribbon alongside the herd's path, 48 m to the river side, with banks, rocks and pines
length=SPEED*seconds+260;line=[]
for i in range(60):
 s=-120+i*length/59;line.append(at((cx0,cy0),s,RIVER_SIDE*48+7*math.sin(s*.035)))
strip_mesh('RiverBank',line,26,.01,poly_material('Bank',(.36,.30,.16)));strip_mesh('River',line,15,.04,poly_material('Water',(.12,.35,.62)))
for i in range(46):
 x,y=line[rnd.randrange(len(line))];off=rnd.choice((-1,1))*rnd.uniform(9,16);px,py=x+side[0]*off,y+side[1]*off
 if rnd.random()<.55:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=rnd.uniform(.4,1.1),location=(px,py,.3));r=bpy.context.object;r.name='RiverRock';r.scale=(1,1,.6);r.data.materials.append(poly_material('RiverRock',(.5,.5,.48)))
 else:
  bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.18,depth=5,location=(px,py,2.5));tr=bpy.context.object;tr.name='Trunk';tr.data.materials.append(poly_material('Trunk',(.3,.2,.1)))
  bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=2.2,depth=7,location=(px,py,6.5));pine=bpy.context.object;pine.name='Pine';pine.data.materials.append(poly_material('Pine',(.08,.28,.12)))
# mountains: low-poly ranges ahead of the herd and beyond the river, snow on the high ones, foothills around
rock=poly_material('Mountain',(.38,.4,.45));snow=poly_material('Snow',(.95,.96,.98));hill=poly_material('Hill',(.18,.36,.12))
def mountain(x,y,h,r,mat=rock,cap=True):
 bpy.ops.mesh.primitive_cone_add(vertices=rnd.choice((5,6,7)),radius1=r,depth=h,location=(x,y,h/2),rotation=(0,0,rnd.uniform(0,1)));m=bpy.context.object;m.name='Mountain';m.data.materials.append(mat)
 if cap:
  bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=r*.26,depth=h*.28,location=(x,y,h*.86));c=bpy.context.object;c.name='Snow';c.data.materials.append(snow)
ahead=SPEED*seconds+200
for i in range(26):   # the range the herd runs toward
 a=(i-12.5)*.19;dist=rnd.uniform(ahead,ahead+120)
 h=rnd.uniform(35,95);mountain(cx0+forward[0]*dist*math.cos(a)+side[0]*dist*math.sin(a),cy0+forward[1]*dist*math.cos(a)+side[1]*dist*math.sin(a),h,h*rnd.uniform(.8,1.2),cap=h>55)
for i in range(18):
 a=rnd.uniform(0,6.283);dist=rnd.uniform(130,260);h=rnd.uniform(8,22);mountain(cx0+math.cos(a)*dist,cy0+math.sin(a)*dist,h,h*1.7,hill,False)
for i in range(14):   # a range beyond the river
 s=rnd.uniform(-60,length-100);p=at((cx0,cy0),s,RIVER_SIDE*rnd.uniform(120,230));mountain(p[0],p[1],rnd.uniform(40,80),rnd.uniform(40,80))
# camera cuts: (start s, end s, name, lens)
SHOTS=[(0,4,'1 Drone, wide',38),(4,7.5,'2 Low, alongside',50),(7.5,10,'3 Ahead, looking back',35),(10,12.5,'4 Overhead',30),(12.5,16,'5 River bank, mountains behind',32)]
SHOTS=[(a,min(b,seconds),n,l) for a,b,n,l in SHOTS if a<seconds]
def camera_path(index,t):
 """Camera position and aim at time t for shot `index` (world metres)."""
 c=herd_centre(t)
 if index==0:p=at(c,-14,-24*RIVER_SIDE);return (p[0],p[1],34),(c[0],c[1],0)                          # drone, high, tilted down
 if index==1:p=at(c,-6,-19*RIVER_SIDE);return (p[0],p[1],3.6),(c[0],c[1],1.4)                       # low, alongside, moving with the herd
 if index==2:p=at(c,32+(t-7.5)*SPEED*.2,5);return (p[0],p[1],3.0),(c[0],c[1],1.2)                   # ahead of the herd, looking back
 if index==3:p=at(c,4,0);return (p[0],p[1],72),(c[0],c[1],0)                                         # overhead
 p=at(c,-8,RIVER_SIDE*34);q=at(c,40,0);return (p[0],p[1],5.5),(q[0],q[1],16)                        # from the river bank, mountains behind
cams=[]
for k,(a,b,name,lens) in enumerate(SHOTS):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.lens=lens;cam.data.clip_end=2000;scene.collection.objects.link(cam)
 aimk=bpy.data.objects.new('Aim%d'%k,None);scene.collection.objects.link(aimk);aimk.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aimk;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for t in [a+(b-a)*u/6 for u in range(7)]:
  f=1+int(t*fps);p,q=camera_path(k,t);cam.location=p;cam.keyframe_insert('location',frame=f);aimk.location=q;aimk.keyframe_insert('location',frame=f)
 m=scene.timeline_markers.new(name,frame=1+int(a*fps));m.camera=cam;cams.append(cam)
scene.camera=cams[0]
# soundtrack, synthesised here (no downloads): hooves, wind and river, and a short piece of music
SR=22050;N=int(seconds*SR);tt=np.arange(N)/SR;audio_dir=os.path.join(os.path.dirname(out),'audio');os.makedirs(audio_dir,exist_ok=True)
def gain_curve(levels,fade=.35):
 g=np.zeros(N)
 for (a,b,name,lens),level in zip(SHOTS,levels):g[(tt>=a)&(tt<b)]=level
 k=int(fade*SR);return np.convolve(g,np.ones(k)/k,mode='same')
def write_wav(name,x,peak=.85):
 x=x/(np.max(np.abs(x))+1e-9)*peak;path=os.path.join(audio_dir,name)
 with wave.open(path,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return path
def lowpass(x,k):return np.convolve(x,np.ones(k)/k,mode='same')
nrng=np.random.default_rng(3)
thud_t=np.arange(int(.14*SR))/SR;thud=np.sin(2*np.pi*(95*thud_t-180*thud_t**2))*np.exp(-thud_t*38)+.35*nrng.standard_normal(len(thud_t))*np.exp(-thud_t*70)
hooves=np.zeros(N+len(thud));cycle=20/fps/PLAY
for h in range(len(positions)):   # every horse lands four hooves per stride, at its own phase
 phase=nrng.uniform(0,cycle);amp=nrng.uniform(.25,1)
 for c in range(int(seconds/cycle)+2):
  for off in (0,.07,.16,.25):
   i=int((phase+c*cycle+off*cycle*2)*SR)
   if 0<=i<N:hooves[i:i+len(thud)]+=thud*amp*nrng.uniform(.7,1)
hooves=hooves[:N]*gain_curve([.30,.85,1.0,.28,.5][:len(SHOTS)])
wind=lowpass(nrng.standard_normal(N),180)*(.7+.3*np.sin(2*np.pi*tt*.13))
river_noise=lowpass(nrng.standard_normal(N),12)-lowpass(nrng.standard_normal(N),90)
ambience=wind*.6+river_noise*(.12+.9*gain_curve([0]*(len(SHOTS)-1)+[1]))*.9
def note(freq,length,vel=1.):
 n=int(length*SR);t=np.arange(n)/SR;env=np.minimum(t/.03,1)*np.exp(-t*2.2/length)
 return (np.sin(2*np.pi*freq*t)+.4*np.sin(4*np.pi*freq*t)+.2*np.sin(6*np.pi*freq*t))*env*vel
music=np.zeros(N+SR*3);D,Bb,F,C=(146.83,220,293.66),(116.54,174.61,233.08),(87.31,174.61,261.63),(130.81,196,261.63);chord_len=4.
for ci,chord in enumerate([D,Bb,F,C]*8):   # Dm - Bb - F - C: arpeggios over a slow pad
 t0=ci*chord_len
 if t0>=seconds:break
 for j,f0 in enumerate(chord):
  for rep in range(int(chord_len/.5)):
   i=int((t0+rep*.5+.125*j)*SR);arp=note(f0*(1 if rep%2==0 else 2),.9,.5 if j else .8)
   if i<N:music[i:i+len(arp)]+=arp[:max(0,len(music)-i)]
  n=int(chord_len*SR);t=np.arange(n)/SR;env=np.minimum(t/.8,1)*np.minimum((chord_len-t)/.8,1);i=int(t0*SR)
  if i+n<=len(music):music[i:i+n]+=(np.sin(2*np.pi*f0*t)+np.sin(2*np.pi*f0*1.004*t))*env*.3
melody=[(293.66,1),(349.23,1),(440,2),(392,1),(349.23,1),(293.66,2),(466.16,1),(440,1),(392,2),(349.23,1),(392,1),(523.25,2)]
t=1.;idx=0
while t<seconds-.5:
 f0,beats=melody[idx%len(melody)];n=note(f0,beats*.55,.55);i=int(t*SR);m=min(len(n),len(music)-i);music[i:i+m]+=n[:m];t+=beats*.55;idx+=1
music=music[:N]*np.minimum(tt/1.5,1)*np.minimum((seconds-tt)/2.,1)
paths=[write_wav('hooves.wav',hooves,.9),write_wav('ambience_wind_river.wav',ambience,.7),write_wav('music.wav',music,.6)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,name) in enumerate(zip(paths,('hooves','wind and river','music')),start=1):strips.new_sound(name,p,ch,1)
scene.render.ffmpeg.audio_codec='AAC' if hasattr(scene.render,'ffmpeg') else None

scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1584;scene.render.resolution_y=1037
scene.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('HERD_DONE',len(horses),'horses',frames,'frames')
