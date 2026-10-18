"""Low-poly sets for previs (Blender): forest, river with a bridge, village, mountain steps, plus a mountain backdrop.

build(scene, sets, props, backdrop) where
  sets  = [{kind: 'forest'|'river'|'village'|'mountains', origin_cm: [x, y]}]   (world cm, Unreal-like axes: +Y forward)
  props = [{shape: 'box'|'cylinder', center_cm: [x,y,z], size_cm: [w,d,h] (box) | [radius,height] (cylinder), color: [r,g,b], yaw: deg}]
Everything is flat-coloured primitives so a whole story previews in seconds; each piece is meant to be replaced by a
proper Unreal set later."""
import bpy,math,random
_materials={}
def mat(name,color):
 if name not in _materials:
  m=bpy.data.materials.new(name);m.diffuse_color=(*color[:3],1);_materials[name]=m
 return _materials[name]
def box(center_m,size_m,color,name='Box',yaw=0.):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center_m);o=bpy.context.object;o.name=name;o.scale=size_m;o.rotation_euler=(0,0,math.radians(yaw));o.data.materials.append(mat(name+str(color),color));return o
def cylinder(center_m,radius_m,height_m,color,name='Cyl',vertices=8):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius_m,depth=height_m,location=center_m);o=bpy.context.object;o.name=name;o.data.materials.append(mat(name+str(color),color));return o
def cone(center_m,radius_m,height_m,color,name='Cone',vertices=7,yaw=0.):
 bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius_m,depth=height_m,location=center_m,rotation=(0,0,math.radians(yaw)));o=bpy.context.object;o.name=name;o.data.materials.append(mat(name+str(color),color));return o
def tree(x,y,h,rnd):
 cylinder((x,y,h*.2),.2,h*.4,(.3,.18,.08),'Trunk',6);cone((x,y,h*.4+h*.5),rnd.uniform(1.2,1.6),h,(.08+rnd.random()*.06,.3+rnd.random()*.1,.12),'Pine')
def forest(ox,oy,rnd,count=26,inner=7.,outer=22.):
 for i in range(count):
  a=rnd.uniform(0,6.283);r=rnd.uniform(inner,outer);tree(ox+math.cos(a)*r,oy+math.sin(a)*r,rnd.uniform(3,6.5),rnd)
 for i in range(6):
  a=rnd.uniform(0,6.283);r=rnd.uniform(4,10);bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=rnd.uniform(.3,.6),location=(ox+math.cos(a)*r,oy+math.sin(a)*r,.2));rock=bpy.context.object;rock.data.materials.append(mat('Rock',(.45,.45,.42)));rock.scale=(1,1,.6)
def flowers(ox,oy,rnd,count,spread):
 for i in range(count):
  a=rnd.uniform(0,6.283);r=rnd.uniform(1,spread);c=[(.9,.35,.5),(.95,.85,.3),(.7,.5,.9),(.95,.95,.95)][rnd.randrange(4)]
  cylinder((ox+math.cos(a)*r,oy+math.sin(a)*r,.08),.04,.16,(.2,.5,.2),'Stem',4);sphere((ox+math.cos(a)*r,oy+math.sin(a)*r,.18),.07,c,'Flower')
def log(x,y,yaw,length=2.2):
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.22,depth=length,location=(x,y,.22),rotation=(0,math.radians(90),math.radians(yaw)));o=bpy.context.object;o.name='Log';o.data.materials.append(mat('Log',(.42,.28,.15)))
def campfire(x,y):
 for k in range(8):
  a=k*math.pi/4;sphere((x+math.cos(a)*.5,y+math.sin(a)*.5,.12),.14,(.45,.45,.43),'FireStone')
 cone((x,y,.3),.25,.6,(1,.5,.12),'Flame',6);sphere((x,y,.5),.12,(1,.85,.4),'Ember')
def tent(x,y,yaw=0):
 cone((x,y,.8),1.4,1.6,(.75,.35,.25),'Tent',4,45+yaw);box((x,y-.9,.5),(.6,.05,1.0),(.2,.12,.08),'TentDoor',yaw)
def signpost(x,y,text_color=(.5,.35,.18)):
 cylinder((x,y,.8),.05,1.6,(.35,.22,.1),'SignPole',6);box((x+.3,y,1.4),(.8,.05,.25),text_color,'SignBoard');box((x-.3,y,1.1),(.8,.05,.25),text_color,'SignBoard')
def river(ox,oy,rnd):
 forest(ox,oy,rnd,16,8,20);flowers(ox,oy,rnd,14,9);box((ox-4.5,oy+3.2,.12),(3.2,.9,.06),(.5,.35,.2),'Dock');box((ox-5.2,oy+3.2,.2),(1.8,.8,.3),(.55,.3,.2),'Boat')   # dock and a rowing boat on the river
 for k in range(10):cylinder((ox+rnd.uniform(-9,9),oy+rnd.choice((1.7,4.7)),.4),.03,.8,(.35,.5,.25),'Reed',4)
 signpost(ox+2.5,oy-1.5)
 box((ox,oy+3.2,.0),(22,2.6,.02),(.15,.4,.75),'River')                       # river across the walking direction, y 1.9..4.5 m
 box((ox,oy+3.2,.04),(2.2,3.6,.05),(.55,.38,.2),'Bridge')                     # bridge deck, x +-1.1 m
 for sx in (-1,1):box((ox+sx*1.1,oy+3.2,.35),(.08,3.6,.06),(.4,.26,.12),'Rail');
 for sx in (-1,1):
  for dy in (-1.6,0,1.6):cylinder((ox+sx*1.1,oy+3.2+dy,.18),.04,.36,(.4,.26,.12),'Post',5)
 box((ox-3.0,oy+.4,.25),(.9,.9,.5),(.5,.5,.48),'StoneTable')
def village(ox,oy,rnd):
 spots=[(-9,6,0),(-3,9,15),(5,9,-10),(11,5,0),(-10,-4,90),(10,-4,-90)]
 for k,(x,y,yaw) in enumerate(spots):
  w,d,h=rnd.uniform(3.6,4.6),rnd.uniform(3.4,4.2),rnd.uniform(2.4,3)
  box((ox+x,oy+y,h/2),(w,d,h),[(.85,.78,.62),(.8,.7,.55),(.75,.72,.68)][k%3],'House',yaw)
  cone((ox+x,oy+y,h+.8),max(w,d)*.78,1.6,(.65,.2,.15),'Roof',4,45+yaw)
  box((ox+x+(-.0 if yaw==0 else 0),oy+y-d/2-.01,.85),(.9,.06,1.7),(.35,.2,.1),'Door',yaw) if yaw==0 else None
 cylinder((ox+4,oy-1,.4),.6,.8,(.5,.5,.5),'Well',8);cone((ox+4,oy-1,1.9),1.0,.9,(.6,.18,.12),'WellRoof',6)
 for i in range(14):
  x=-12+i*1.85;box((ox+x,oy-9,.35),(.08,.08,.7),(.5,.38,.2),'FencePost');box((ox+x,oy-9,.5),(1.85,.05,.08),(.5,.38,.2),'FenceRail')
 forest(ox,oy,rnd,10,14,24);flowers(ox,oy,rnd,16,12);box((ox-10,oy+12,.9),(3,1.6,1.8),(.6,.4,.25),'Stall');box((ox-10,oy+11,2.0),(3.4,1.9,.1),(.85,.2,.2),'StallAwning');box((ox+9,oy-7,.45),(1.4,1.4,.9),(.8,.7,.3),'HayBale');box((ox+10.6,oy-7.4,.45),(1.4,1.4,.9),(.8,.7,.3),'HayBale')
def sphere(center_m,radius_m,color,name='Ball',scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=radius_m,location=center_m);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat(name+str(color),color));return o
def cafe(ox,oy,rnd):
 """A small street cafe: striped awning, counter, round tables with chairs, sign, flower pots, houses and trees around."""
 box((ox,oy-5.5,1.5),(8,5,3),(.92,.86,.7),'CafeWalls');box((ox,oy-5.5,3.2),(8.6,5.6,.3),(.55,.18,.14),'CafeRoof')
 for k in range(8):box((ox-3.5+k,oy-2.7,2.45),(1,1.5,.1),(.85,.15,.15) if k%2==0 else (.95,.92,.88),'Awning')
 box((ox,oy-3.05,3.0),(3.2,.12,.7),(.25,.15,.08),'Sign')
 box((ox,oy-3.4,.5),(4.2,.6,1.0),(.45,.3,.18),'Counter');box((ox-2.4,oy-3.4,1.15),(.5,.4,.3),(.8,.8,.8),'Machine')
 for sx in (-2.8,2.8):cylinder((ox+sx,oy-3.1,.25),.22,.5,(.7,.35,.2),'Pot',8);cone((ox+sx,oy-3.1,.75),.3,.5,(.2,.55,.2),'Plant',6)
 for tx,ty in ((-3,.2),(3,.2),(0,3)):
  cylinder((ox+tx,oy+ty,.7),.55,.05,(.8,.7,.55),'TableTop',10);cylinder((ox+tx,oy+ty,.35),.06,.7,(.4,.3,.2),'TableLeg',6)
  for cx,cy in ((.8,0),(-.8,0),(0,.8)):box((ox+tx+cx,oy+ty+cy,.25),(.4,.4,.5),(.55,.35,.2),'Chair')
 for x,y,yaw in ((-8,-4,90),(8,-4,-90),(-9,3,90)):
  box((ox+x,oy+y,1.3),(3.6,3.8,2.6),(.8,.74,.6),'House',yaw);cone((ox+x,oy+y,3.2),3,1.6,(.6,.2,.15),'Roof',4,45)
 forest(ox,oy,rnd,10,14,24)
def mountains(ox,oy,rnd):
 forest(ox,oy,rnd,14,10,24);campfire(ox+4.5,oy-2.2);tent(ox+6.5,oy-1.5,20);log(ox+4.5,oy-1.0,40);log(ox+3.6,oy-3.4,-20);signpost(ox-3,oy-3.5);flowers(ox,oy,rnd,8,6)
 box((ox+0,oy+1.2,.05),(2.4,2.4,.1),(.6,.6,.58),'SummitPad')
def backdrop(rnd):
 """Distant mountains behind the action, on the -Y side (cameras sit on +Y looking back)."""
 for i in range(26):
  x=-60+i*(rnd.uniform(9,13)+3)*1.0;h=rnd.uniform(18,34);r=h*rnd.uniform(.9,1.3)
  cone((x,-90-rnd.uniform(0,25),h/2),r,h,(.38,.4,.45),'Mountain',6,rnd.uniform(0,60));cone((x,-90-rnd.uniform(0,0),h*.88),r*.24,h*.26,(.95,.96,.98),'Snow',6)
def build(scene,sets,props,use_backdrop=True):
 rnd=random.Random(11)
 bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-.02));g=bpy.context.object;g.name='Ground';g.scale=(900,260,1);g.location=(0,0,-.02);g.data.materials.append(mat('Ground',(.22,.38,.16)))
 for s in sets:
  ox,oy=s['origin_cm'][0]/100,s['origin_cm'][1]/100;{'forest':forest,'river':river,'village':village,'mountains':mountains,'cafe':cafe}[s['kind']](ox,oy,rnd)
  if s['kind']=='forest':flowers(ox,oy,rnd,22,8);log(ox+3,oy+3,30);log(ox-4,oy-2,-60)   # a clearing: wild flowers and fallen logs
 if use_backdrop:backdrop(rnd)
 for p in props:
  c=[v/100 for v in p['center_cm']];color=p.get('color',(.5,.35,.2))
  if p['shape']=='sphere':o=sphere(c,p['size_cm'][0]/100,color,p.get('name','Prop'),p.get('scale',(1,1,1)))
  else:o=box(c,[v/100 for v in p['size_cm']],color,p.get('name','Prop'),p.get('yaw',0)) if p['shape']=='box' else cylinder(c,p['size_cm'][0]/100,p['size_cm'][1]/100,color,p.get('name','Prop'))
  if p.get('frames'):   # visible only between these frames
   for prop_name in ('hide_viewport','hide_render'):
    for frame,value in ((max(0,p['frames'][0]-1),True),(p['frames'][0],False),(p['frames'][1]+1,True)):
     setattr(o,prop_name,value);o.keyframe_insert(prop_name,frame=frame)
 scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.55,.72,.9)
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
