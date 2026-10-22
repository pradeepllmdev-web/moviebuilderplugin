"""Atmosphere for the performance scenes (Blender side): floating dust, drifting leaves, fireflies, rain and snow, chosen from the time of day, the ambience and the place unless the scene names them ('fx': [...]).

    kinds = perf_fx.choose(time, ambience, preset, fog, spec_fx)        pure Python: the list of effects for a scene (testable without Blender)
    perf_fx.build(S, kinds, centre, seconds, seed)                         creates them round `centre` (x, y): small emissive solids with keyframed drift (so they play in the viewer and render exactly the same), rain and snow as particle systems

Effects are cheap on purpose: dust motes, leaves and fireflies are 30-80 small objects with a key every few frames; rain and snow are one particle system each with a pre-roll so the sky is already full at frame 1."""
import math,random
LEAF_PLACES=('meadow','forest_clearing','village_square','hilltop','courtyard','campfire_night','market')
def choose(time,ambience,preset,fog=0.,spec_fx=None):
 """the effects of a scene: the spec's own list, or dust by day, leaves in outdoor places, fireflies at dusk and night, rain when the ambience is rain"""
 if spec_fx is not None:return [k for k in spec_fx if k in KINDS]
 out=[]
 if ambience=='rain':return ['rain']
 if time in('day','dawn','overcast'):out.append('dust')
 if time in('dusk','night'):out.append('fireflies')
 if preset in LEAF_PLACES and time in('day','dawn','dusk') and ambience in('wind','market','crowd','night'):out.append('leaves')
 if preset in('room','hall','workshop','cave'):out=['dust']
 return out
KINDS=('dust','leaves','fireflies','rain','snow')
def _emit_material(name,color,strength):
 import bpy
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=strength
 return m
def _mesh(name,kind):
 import bpy,bmesh
 me=bpy.data.meshes.new(name);bm=bmesh.new()
 if kind=='sphere':bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1.)
 elif kind=='leaf':
  v=[bm.verts.new(p) for p in ((-.5,-.8,0),(.5,-.8,0),(.35,.8,0),(-.35,.8,0))];bm.faces.new(v)
 bm.to_mesh(me);bm.free();return me
def _wander(rnd,x0,y0,z0,seconds,fps,box,step=6,speed=.4,zr=(.2,5.),wob=.25):
 """positions every `step` frames: a slow random drift with a gentle wobble, kept inside the box"""
 pts=[];x,y,z=x0,y0,z0;vx,vy,vz=rnd.uniform(-1,1)*speed,rnd.uniform(-1,1)*speed,rnd.uniform(-1,1)*speed*.4;n=int(seconds*fps/step)+2
 for k in range(n):
  vx+=rnd.uniform(-1,1)*wob*.2;vy+=rnd.uniform(-1,1)*wob*.2;vz+=rnd.uniform(-1,1)*wob*.1
  vx=max(-speed,min(speed,vx));vy=max(-speed,min(speed,vy));vz=max(-speed*.4,min(speed*.4,vz))
  x+=vx*step/fps;y+=vy*step/fps;z+=vz*step/fps
  if abs(x-x0)>box:vx=-vx
  if abs(y-y0)>box:vy=-vy
  if not zr[0]<z<zr[1]:vz=-vz;z=max(zr[0],min(zr[1],z))
  pts.append((x,y,z))
 return pts
def build(S,kinds,centre,seconds,seed=1,fps=24):
 """create the effects; returns the number of objects"""
 import bpy
 rnd=random.Random(seed*7919+len(kinds));cx,cy=centre;made=0;step=6
 def link(o):
  bpy.context.scene.collection.objects.link(o);return o
 def key(o,pts,rot=None):
  for k,p in enumerate(pts):
   o.location=p;o.keyframe_insert('location',frame=1+k*step)
   if rot:o.rotation_euler=rot(k);o.keyframe_insert('rotation_euler',frame=1+k*step)
 for kind in kinds:
  if kind=='dust':
   me=_mesh('DustMesh','sphere');mat=_emit_material('Dust',(1.,.95,.8),1.4);me.materials.append(mat)
   for i in range(70):
    o=bpy.data.objects.new('Dust%d'%i,me);o.scale=(.02,.02,.02);link(o);key(o,_wander(rnd,cx+rnd.uniform(-12,12),cy+rnd.uniform(-12,12),rnd.uniform(.3,4.5),seconds,fps,12,speed=.18,zr=(.2,5.)));made+=1
  elif kind=='fireflies':
   me=_mesh('FlyMesh','sphere');mat=_emit_material('Firefly',(.9,1.,.35),9.);me.materials.append(mat)
   for i in range(55):
    o=bpy.data.objects.new('Fly%d'%i,me);link(o);pts=_wander(rnd,cx+rnd.uniform(-13,13),cy+rnd.uniform(-13,13),rnd.uniform(.4,3.),seconds,fps,13,speed=.5,zr=(.3,3.5),wob=.5)
    for k,p in enumerate(pts):    # they blink: size pulses with its own rhythm
     o.location=p;s=.03*(.35+.65*abs(math.sin(k*.5+i)));o.scale=(s,s,s);o.keyframe_insert('location',frame=1+k*step);o.keyframe_insert('scale',frame=1+k*step)
    made+=1
  elif kind=='leaves':
   me=_mesh('LeafMesh','leaf');cols=((.75,.45,.15),(.85,.6,.2),(.6,.3,.1),(.55,.5,.15))
   for i in range(30):
    mat=_emit_material('Leaf%d'%i,cols[i%4],.12);m2=bpy.data.meshes.new('Leaf%d'%i);m2.from_pydata([v.co[:] for v in me.vertices],[],[p.vertices[:] for p in me.polygons]);m2.materials.append(mat)
    o=bpy.data.objects.new('Leaf%d'%i,m2);o.scale=(.1,.1,.1);link(o);x,y=cx+rnd.uniform(-14,14),cy+rnd.uniform(-14,14);z=rnd.uniform(.5,8.);ph=rnd.uniform(0,6);pts=[]
    for k in range(int(seconds*fps/step)+2):
     t=k*step/fps;z-=.9*step/fps;x+=math.sin(t*1.3+ph)*.5*step/fps+.15*step/fps;y+=math.cos(t*.9+ph)*.4*step/fps
     if z<.05:z=rnd.uniform(6,9);x=cx+rnd.uniform(-14,14);y=cy+rnd.uniform(-14,14)
     pts.append((x,y,z))
    key(o,pts,lambda k,ph=ph:(k*.45+ph,math.sin(k*.3+ph)*.8,k*.3));made+=1
  elif kind in('rain','snow'):
   made+=_precip(S,kind,cx,cy,seed)
 return made
def _precip(S,kind,cx,cy,seed):
 """rain or snow: one particle system on a plane high above the scene, with a pre-roll so the sky is full from the first frame"""
 import bpy
 me=bpy.data.meshes.new('PrecipPlane');me.from_pydata([(-16,-16,0),(16,-16,0),(16,16,0),(-16,16,0)],[],[(0,1,2,3)]);em=bpy.data.objects.new('Precip',me);em.location=(cx,cy,11.);bpy.context.scene.collection.objects.link(em)
 inst=bpy.data.objects.new('DropMesh',_mesh('Drop','sphere'));bpy.context.scene.collection.objects.link(inst)
 if kind=='rain':inst.scale=(.012,.012,.28);inst.data.materials.append(_emit_material('Rain',(.75,.85,1.),.8))
 else:inst.scale=(.04,.04,.04);inst.data.materials.append(_emit_material('Snow',(1.,1.,1.),1.2))
 inst.hide_render=False;inst.hide_viewport=True
 em.modifiers.new('Precip','PARTICLE_SYSTEM');st=em.particle_systems[0].settings
 st.count=1600 if kind=='rain' else 900;st.frame_start=-80;st.frame_end=4000;st.lifetime=60 if kind=='rain' else 220;st.emit_from='FACE';st.physics_type='NEWTON';st.render_type='OBJECT';st.instance_object=inst
 st.normal_factor=0.;st.object_factor=0.;st.factor_random=0.;st.particle_size=1.;st.size_random=.3
 st.effector_weights.gravity=1.4 if kind=='rain' else .06;st.drag_factor=0. if kind=='rain' else .6;st.brownian_factor=0. if kind=='rain' else .25
 st.show_unborn=False;st.use_dead=False;em.show_instancer_for_render=False;em.show_instancer_for_viewport=False
 return 1
