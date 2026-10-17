"""Opt-in facial controls on CC0 Cat Pilot. Geometry stays inside Blender."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;OUT=H/'talking';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(H/'face-source.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=bpy.data.objects['Armature'];o=bpy.data.objects['CatPilot'];r.animation_data_clear();o.data.shape_keys.animation_data_clear()
for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
for k in o.data.shape_keys.key_blocks:k.value=0
w=o.matrix_world;inv=w.inverted();seam=1.725
saved=[(k.name,[p.co.copy() for p in k.data]) for k in o.data.shape_keys.key_blocks]
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();layers={}
for name,coords in saved:
 layer=bm.verts.layers.shape.get(name) or bm.verts.layers.shape.new(name);layers[name]=layer
 for v,p in zip(bm.verts,coords):v[layer]=p
selected=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.24 and 1.55<(w@f.calc_center_median()).z<1.81 and (w@f.calc_center_median()).y<-.25]
bmesh.ops.subdivide_edges(bm,edges=list({e for f in selected for e in f.edges}),cuts=5,use_grid_fill=True)
selected=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.155 and 1.67<(w@f.calc_center_median()).z<1.78 and (w@f.calc_center_median()).y<-.3]
geom=list(set(selected)|{e for f in selected for e in f.edges}|{v for f in selected for v in f.verts})
cut=bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=inv@Vector((0,0,seam)),plane_no=w.to_3x3().transposed()@Vector((0,0,1)))
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];assert edges
bmesh.ops.split_edges(bm,edges=edges);bm.verts.index_update()
lower={v.index for v in bm.verts if abs((w@v.co).z-seam)<1e-5 and v.link_faces and max((w@f.calc_center_median()).z for f in v.link_faces)<=seam+1e-5}
transferred={name:[v[layer].copy() for v in bm.verts] for name,layer in layers.items()}
o.shape_key_clear();bm.to_mesh(o.data);bm.free();o.data.update()
for name,coords in transferred.items():
 k=o.shape_key_add(name=name,from_mix=False)
 for p,co in zip(k.data,coords):p.co=co
 k.value=0
basis=o.data.shape_keys.key_blocks['Basis']
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
pivot=Vector((0,-.19,1.76));rot=Matrix.Rotation(math.radians(18),3,'X')
for name in ['JawOpen','MouthRound','MouthWide','LipClose','Smile']:
 key=o.shape_key_add(name=name,from_mix=False)
 for index,(p,b) in enumerate(zip(key.data,basis.data)):
  q=w@b.co;lat=smooth((.17-abs(q.x))/.04)*smooth((-.29-q.y)/.09);delta=Vector()
  if name=='JawOpen' and (q.z<seam-1e-5 or index in lower):
   weight=smooth((.16-abs(q.x))/.08)*smooth((-.29-q.y)/.09)*smooth((q.z-1.54)/.08)
   delta=(pivot+rot@(q-pivot)-q)*weight
  else:
   weight=lat*math.exp(-((q.z-seam)/.045)**2)
   if q.z>1.78:weight=0
   if name=='MouthRound':delta=Vector((-.22*q.x,-.009,0))*weight
   elif name=='MouthWide':delta=Vector((.16*q.x,0,0))*weight
   elif name=='LipClose':delta=Vector((0,0,.009 if q.z<seam else 0))*weight
   elif name=='Smile':delta=Vector((0,0,.012*min(1,abs(q.x)/.12)))*weight
  p.co=b.co+inv.to_3x3()@delta
# Oral lining is recessed behind the original muzzle.
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;sh=m.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=(*color,1);sh.inputs['Roughness'].default_value=.65;return m
lining=material('Pilot oral tissue',(.09,.014,.018));tongue=material('Pilot tongue',(.44,.12,.15));ivory=material('Pilot teeth',(.7,.63,.48))
parts=[]
def part(name,loc,scale,mat,moving):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc);a=bpy.context.object;a.name=name;a.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.data.materials.append(mat)
 for p in a.data.polygons:p.use_smooth=True
 a.shape_key_add(name='Basis',from_mix=False);key=a.shape_key_add(name='JawOpen',from_mix=False)
 for v in key.data:
  p=a.matrix_world@v.co;weight=moving(p);v.co=a.matrix_world.inverted()@(p+weight*(pivot+rot@(p-pivot)-p))
 a.parent=r;a.matrix_world=Matrix.Translation(Vector(loc))
 group=a.vertex_groups.new(name='Head');group.add(list(range(len(a.data.vertices))),1,'REPLACE');mod=a.modifiers.new('Head binding','ARMATURE');mod.object=r;parts.append(a)
part('Pilot mouth interior',(0,-.385,1.705),(.125,.025,.03),lining,lambda p:smooth((seam-p.z)/.04))
part('Pilot tongue',(0,-.405,1.704),(.05,.028,.009),tongue,lambda p:1)
for x in (-.075,-.035,.035,.075):
 part('Pilot upper tooth',(x,-.400,1.718),(.009,.009,.014 if abs(x)>.07 else .006),ivory,lambda p:0)
for x in (-.05,-.017,.017,.05):part('Pilot lower tooth',(x,-.385,1.708),(.009,.008,.006),ivory,lambda p:1)
for obj in [o]+parts:
 for k in obj.data.shape_keys.key_blocks:k.value=0
s.frame_start=1;s.frame_end=192;s.render.engine='CYCLES';s.cycles.samples=8
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'face-rig.blend'))
for name,values in [('neutral',{}),('AA',{'JawOpen':.8}),('OO',{'JawOpen':.45,'MouthRound':1}),('EE',{'JawOpen':.35,'MouthWide':1}),('MBP',{'LipClose':1}),('smile',{'Smile':1})]:
 for obj in [o]+parts:
  for k in obj.data.shape_keys.key_blocks:k.value=values.get(k.name,0)
 s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'fit.json').write_text(json.dumps({'seam_world_z':seam,'lip_edges':len(edges),'speech_keys':['JawOpen','MouthRound','MouthWide','LipClose','Smile'],'oral_parts':len(parts),'source_eyes_preserved':True,'status':'visual-review-required'},indent=2));print('POSES_READY')


