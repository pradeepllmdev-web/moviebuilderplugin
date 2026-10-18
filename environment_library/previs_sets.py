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
def river(ox,oy,rnd):
 forest(ox,oy,rnd,16,8,20)
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
 forest(ox,oy,rnd,10,14,24)
def mountains(ox,oy,rnd):
 forest(ox,oy,rnd,14,10,24)
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
  ox,oy=s['origin_cm'][0]/100,s['origin_cm'][1]/100;{'forest':forest,'river':river,'village':village,'mountains':mountains}[s['kind']](ox,oy,rnd)
 if use_backdrop:backdrop(rnd)
 for p in props:
  c=[v/100 for v in p['center_cm']];color=p.get('color',(.5,.35,.2))
  if p['shape']=='box':box(c,[v/100 for v in p['size_cm']],color,p.get('name','Prop'),p.get('yaw',0))
  else:cylinder(c,p['size_cm'][0]/100,p['size_cm'][1]/100,color,p.get('name','Prop'))
 scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.55,.72,.9)
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
