"""Blender script: an aerial herd of galloping horses over a green meadow (like a drone photo), from the CC0 Quaternius horse.

blender -b --disable-autoexec --python horse_herd.py -- <Horse.blend> <out.blend> [count] [seconds]

The horse is already rigged (28 bones) and has a 20-frame 'Run' action, so no auto-rigging is needed: every horse gets its own copy of the
armature and mesh, plays 'Run' from an NLA strip (random phase, retimed so the legs match the ground speed) and travels along the herd's
heading with a little sideways wander. Coats follow the photo (white, grey, bay, black, chestnut, palomino) and about one in six is a
foal (smaller, quicker legs). The camera is a drone: high, tilted down, drifting forward slower than the herd.
Heading faces the model's forward axis (-Y in the asset): rotation = heading + 90 degrees."""
import bpy,math,random,sys
args=sys.argv[sys.argv.index('--')+1:];source,out=args[0],args[1];count=int(args[2]) if len(args)>2 else 64;seconds=float(args[3]) if len(args)>3 else 12.
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
# drone camera: high, tilted down, drifting forward slower than the herd
cx=sum(p[0] for p in positions)/len(positions);cy=sum(p[1] for p in positions)/len(positions)
cam=bpy.data.objects.new('DroneCam',bpy.data.cameras.new('DroneCam'));cam.data.lens=42;scene.collection.objects.link(cam);scene.camera=cam
aim=bpy.data.objects.new('DroneAim',None);scene.collection.objects.link(aim);aim.hide_viewport=True
con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
for f in range(1,frames+1,12):
 t=(f-1)/fps;drift=SPEED*.7*t;gx,gy=cx+forward[0]*drift,cy+forward[1]*drift
 aim.location=(gx,gy,0);aim.keyframe_insert('location',frame=f);cam.location=(gx-forward[0]*14+side[0]*24,gy-forward[1]*14+side[1]*24,34);cam.keyframe_insert('location',frame=f)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1584;scene.render.resolution_y=1037
scene.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('HERD_DONE',len(horses),'horses',frames,'frames')
