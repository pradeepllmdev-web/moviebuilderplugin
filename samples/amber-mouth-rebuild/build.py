"""Amber-specific fitted jaw, preserving original muzzle and source files."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;saved_lids=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/implementation/character-workflow/amber-face-refinement/character-conservative.glb')
bpy.ops.wm.open_mainfile(filepath=str(H/'source.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');o=bpy.data.objects['char1'];w=o.matrix_world;inv=w.inverted();seam=1.279
# Extract only the already-tested lids from the comparison copy.
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(saved_lids));imported=set(bpy.data.objects)-existing
lid_source=next(x for x in imported if x.type=='MESH' and x.data.shape_keys)
polys=[p for p in lid_source.data.polygons if lid_source.data.materials[p.material_index].name.startswith('eyelids')]
indices=sorted({i for p in polys for i in p.vertices});lookup={old:i for i,old in enumerate(indices)}
data=bpy.data.meshes.new('Amber fitted lids');data.from_pydata([lid_source.matrix_world@lid_source.data.vertices[i].co for i in indices],[],[[lookup[i] for i in p.vertices] for p in polys]);data.update();lids=bpy.data.objects.new('Amber fitted eyelids',data);s.collection.objects.link(lids)
for name in ['Basis','eyeBlinkLeft','eyeBlinkRight','eyeLookDown']:
 source=lid_source.data.shape_keys.key_blocks.get(name)
 if not source:continue
 key=lids.shape_key_add(name=name,from_mix=False)
 for v,i in zip(key.data,indices):v.co=lid_source.matrix_world@source.data[i].co
 key.value=0
for x in imported:bpy.data.objects.remove(x,do_unlink=True)
mat=bpy.data.materials.new('Amber lid fur');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.39,.255,.17,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;lids.data.materials.append(mat)
def bind(a):
 world=a.matrix_world.copy();a.parent=r;a.matrix_world=world;g=a.vertex_groups.new(name='Head');g.add(list(range(len(a.data.vertices))),1,'REPLACE');mod=a.modifiers.new('Head skin','ARMATURE');mod.object=r
 for p in a.data.polygons:p.use_smooth=True
bind(lids)
# Remove recessed generated interior, preserving the front chin and muzzle.
bm=bmesh.new();bm.from_mesh(o.data)
interior=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.085 and 1.248<(w@f.calc_center_median()).z<seam and -.445<(w@f.calc_center_median()).y<-.29]
# Remove small bright generated tooth faces inside the opening; fitted teeth replace them.
uv_layer=bm.loops.layers.uv.active
image=next((node.image for mat in o.data.materials if mat and mat.use_nodes for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image),None)
if image and uv_layer:
 import numpy as np
 pixels=np.asarray(image.pixels[:],dtype=np.float32).reshape(image.size[1],image.size[0],4)
 for f in bm.faces:
  p=w@f.calc_center_median()
  if abs(p.x)<.08 and 1.249<p.z<1.277 and p.y<-.39:
   uv=sum((loop[uv_layer].uv for loop in f.loops),Vector((0,0)))/len(f.loops)
   rgb=pixels[min(image.size[1]-1,int((uv.y%1)*image.size[1])),min(image.size[0]-1,int((uv.x%1)*image.size[0])),:3]
   if float(rgb.min())>.72 and float(rgb.max()-rgb.min())<.2:interior.append(f)
interior=list(set(interior))
bmesh.ops.delete(bm,geom=interior,context='FACES_ONLY')
selected=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.13 and 1.23<(w@f.calc_center_median()).z<1.31 and (w@f.calc_center_median()).y<-.30]
geom=list(set(selected)|{e for f in selected for e in f.edges}|{v for f in selected for v in f.verts})
cut=bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=inv@Vector((0,0,seam)),plane_no=w.to_3x3().transposed()@Vector((0,0,1)))
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];bmesh.ops.split_edges(bm,edges=edges);bm.verts.index_update();lower={v.index for v in bm.verts if abs((w@v.co).z-seam)<1e-5 and v.link_faces and max((w@f.calc_center_median()).z for f in v.link_faces)<=seam+1e-5}
bm.to_mesh(o.data);bm.free();o.data.update()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
jaw_indices={v.index for v in o.data.vertices if (w@v.co).z<seam-1e-5 or v.index in lower}
# Closed rest pose raises only the lower lip/chin, below the upper muzzle.
for v in o.data.vertices:
 p=w@v.co
 if p.z<seam-1e-5 or v.index in lower:
  weight=smooth((.145-abs(p.x))/.045)*smooth((-.30-p.y)/.08)*smooth((p.z-1.16)/.065)
  rise=min(.027*weight,max(0,seam-.0005-p.z))
  v.co=inv@(p+Vector((0,0,rise)))
o.shape_key_add(name='Basis',from_mix=False);basis=o.data.shape_keys.key_blocks['Basis']
pivot=Vector((0,-.20,1.30));rot=Matrix.Rotation(math.radians(12),3,'X')
# Classification uses original rest height, not the raised seam positions.
for name in ['JawOpen','MouthRound','MouthWide','LipClose','Smile']:
 k=o.shape_key_add(name=name,from_mix=False)
 for i,(v,b) in enumerate(zip(k.data,basis.data)):
  p=w@b.co;lat=smooth((.145-abs(p.x))/.045)*smooth((-.30-p.y)/.08);delta=Vector()
  if name=='JawOpen' and i in jaw_indices:
   delta=(pivot+rot@(p-pivot)-p)*lat*smooth((p.z-1.15)/.07)
  elif name!='JawOpen':
   weight=lat*math.exp(-((p.z-seam)/.025)**2)
   if p.z>1.30:weight=0
   if name=='MouthRound':delta=Vector((-.18*p.x,-.004,0))*weight
   elif name=='MouthWide':delta=Vector((.12*p.x,0,0))*weight
   elif name=='LipClose':delta=Vector((0,0,.005 if p.z<seam else 0))*weight
   elif name=='Smile':delta=Vector((0,0,.005*min(1,abs(p.x)/.075)))*weight
  v.co=b.co+inv.to_3x3()@delta
# All oral components are recessed and bind to the head with synchronized jaw shapes.
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65;return m
lining=material('Amber oral lining',(.10,.018,.022));tongue=material('Amber tongue',(.40,.10,.13));ivory=material('Amber teeth',(.70,.63,.48));parts=[]
def part(name,location,scale,mat,moving):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=location);a=bpy.context.object;a.name=name;a.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.data.materials.append(mat);a.shape_key_add(name='Basis',from_mix=False);k=a.shape_key_add(name='JawOpen',from_mix=False)
 for v in k.data:
  p=a.matrix_world@v.co;v.co=a.matrix_world.inverted()@(p+moving(p)*(pivot+rot@(p-pivot)-p))
 k.value=0;bind(a);parts.append(a)
part('Amber mouth lining',(0,-.320,1.267),(.070,.020,.022),lining,lambda p:smooth((seam-p.z)/.03))
part('Amber tongue',(0,-.388,1.271),(.040,.030,.007),tongue,lambda p:1)
for x in [-.060,-.035,-.012,.012,.035,.060]:part('Amber upper tooth',(x,-.408+.12*abs(x),1.275),(.005,.006,.010 if abs(x)>.05 else .004),ivory,lambda p:0)
for x in [-.054,-.036,-.018,0,.018,.036,.054]:part('Amber lower tooth',(x,-.390+.18*abs(x),1.273),(.005,.006,.004),ivory,lambda p:1)
s.render.resolution_x=s.render.resolution_y=640;s.render.engine='CYCLES';s.cycles.samples=8
bpy.ops.wm.save_as_mainfile(filepath=str(H/'face-rig.blend'))
for name,values in [('neutral',{}),('AA',{'JawOpen':.8}),('OO',{'JawOpen':.45,'MouthRound':1}),('EE',{'JawOpen':.35,'MouthWide':1}),('MBP',{'LipClose':1}),('blink',{'eyeBlinkLeft':1,'eyeBlinkRight':1})]:
 for a in [o,lids]+parts:
  for k in a.data.shape_keys.key_blocks:k.value=values.get(k.name,0)
 s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
(H/'fit.json').write_text(json.dumps({'mouth_seam_z':seam,'cut_edges':len(edges),'removed_recessed_faces':len(interior),'oral_parts':len(parts),'status':'visual-review-required'},indent=2));print('AMBER_POSES_READY')




