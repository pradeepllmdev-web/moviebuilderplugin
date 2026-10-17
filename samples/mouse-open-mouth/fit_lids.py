import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(H/'jaw-test.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');surface=next(o for o in s.objects if o.type=='MESH' and o.data.shape_keys);c=s.camera;bpy.context.view_layer.update()
# Locate this new model's eyes from its own front view.
centers=[]
for x,y in [(230,250),(410,250)]:
 d=c.matrix_world.to_quaternion()@Vector(((2*x/640-1)*math.tan(c.data.angle_x/2),(1-2*y/640)*math.tan(c.data.angle_x/2),-1)).normalized()
 hit,p,n,i,obj,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),c.location,d);assert hit;centers.append(p)
mods=[(m,m.show_viewport) for m in surface.modifiers]
for m,_ in mods:m.show_viewport=False
bpy.context.view_layer.update();inv=surface.matrix_world.inverted();world=surface.matrix_world
mat=bpy.data.materials.new('Fresh Amber eyelid fur');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.28,.24,.21,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
made=[]
for side,center in zip(('L','R'),centers):
 points=[];closed=[];faces=[];rows=12;cols=28;rx=.026;rz=.027
 def front(x,z):
  hit,p,n,i=surface.ray_cast(inv@Vector((x,-1,z)),inv.to_3x3()@Vector((0,1,0)))
  if not hit:raise ValueError('Fresh eyelid fit missed face')
  p=world@p;p.y-=.002;return p
 for row in range(rows+1):
  v=row/rows
  for col in range(cols+1):
   u=-1+2*col/cols;arc=math.sqrt(max(0,1-u*u));x=center.x+rx*u;z=center.z+rz*arc*(1-2*v)
   closed.append(front(x,z));rest=front(x,center.z+rz*arc+.001);rest.y+=.005+v*.001;points.append(rest)
   if row<rows and col<cols:
    a=row*(cols+1)+col;faces.append((a,a+cols+1,a+cols+2,a+1))
 data=bpy.data.meshes.new('Fresh fitted eyelid');data.from_pydata(points,[],faces);data.update();obj=bpy.data.objects.new('Fresh lid '+side,data);s.collection.objects.link(obj);data.materials.append(mat)
 obj.shape_key_add(name='Basis',from_mix=False);key=obj.shape_key_add(name='Blink'+side,from_mix=False)
 for v,p in zip(key.data,closed):v.co=p
 key.value=0;obj.parent=r;obj.matrix_world=Matrix.Identity(4);g=obj.vertex_groups.new(name='Head');g.add(list(range(len(data.vertices))),1,'REPLACE');mod=obj.modifiers.new('Fresh head binding','ARMATURE');mod.object=r
 for p in data.polygons:p.use_smooth=True
 made.append(obj)
crease_mat=bpy.data.materials.new('Fresh lid crease');crease_mat.use_nodes=True;crease_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.07,.06,.055,1)
for side,center in zip(('L','R'),centers):
 points=[];closed=[];faces=[];cols=28
 for row in range(2):
  for col in range(cols+1):
   u=-1+2*col/cols;x=center.x+.022*u
   p=front(x,center.z+.002*u*u+(row-.5)*.001);p.y-=.003;closed.append(p)
   rest=front(x,center.z+.027*math.sqrt(max(0,1-u*u))+.001);rest.y+=.006;points.append(rest)
   if row==0 and col<cols:faces.append((col,col+cols+1,col+cols+2,col+1))
 data=bpy.data.meshes.new('Fresh eyelid crease');data.from_pydata(points,[],faces);data.update();a=bpy.data.objects.new('Fresh crease '+side,data);s.collection.objects.link(a);data.materials.append(crease_mat);a.shape_key_add(name='Basis',from_mix=False);key=a.shape_key_add(name='Blink'+side,from_mix=False)
 for v,p in zip(key.data,closed):v.co=p
 key.value=0;a.parent=r;a.matrix_world=Matrix.Identity(4);g=a.vertex_groups.new(name='Head');g.add(list(range(len(data.vertices))),1,'REPLACE');m=a.modifiers.new('Head binding','ARMATURE');m.object=r;made.append(a)
for m,enabled in mods:m.show_viewport=enabled
s.render.engine='CYCLES';s.cycles.samples=8
bpy.ops.wm.save_as_mainfile(filepath=str(H/'facial-test.blend'))
for a in made:a.data.shape_keys.key_blocks['Blink'+a.name[-1]].value=1
s.render.filepath=str(H/'blink.png');bpy.ops.render.render(write_still=True)
(H/'eyelid-fit.json').write_text(json.dumps({'centers_world':[[round(v,5) for v in p] for p in centers],'new_model_only':True,'status':'visual-review-required'},indent=2))


