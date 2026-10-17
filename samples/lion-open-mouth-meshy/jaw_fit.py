"""Asset-specific jaw fit. Mesh data stays inside Blender."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'face-fit.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;o=bpy.data.objects['char1'];w=o.matrix_world.copy();inv=w.inverted();z=1.224
bm=bmesh.new();bm.from_mesh(o.data)
inside=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.095 and -.535<(w@f.calc_center_median()).y<-.43 and 1.195<(w@f.calc_center_median()).z<1.24]
bmesh.ops.delete(bm,geom=inside,context='FACES_ONLY')
selected=[f for f in bm.faces if abs((w@f.calc_center_median()).x)<.16 and (w@f.calc_center_median()).y<-.43 and 1.16<(w@f.calc_center_median()).z<1.26]
g=list(set(selected)|{e for f in selected for e in f.edges}|{v for f in selected for v in f.verts})
cut=bmesh.ops.bisect_plane(bm,geom=g,dist=1e-6,plane_co=inv@Vector((0,0,z)),plane_no=w.to_3x3().transposed()@Vector((0,0,1)))
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
bmesh.ops.split_edges(bm,edges=edges);bm.verts.index_update()
lower={v.index for v in bm.verts if abs((w@v.co).z-z)<1e-5 and v.link_faces and max((w@f.calc_center_median()).z for f in v.link_faces)<=z+1e-5}
bm.to_mesh(o.data);bm.free();o.data.update()
o.shape_key_add(name='Basis');key=o.shape_key_add(name='JawOpen')
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
pivot=Vector((0,-.36,1.24));rot=Matrix.Rotation(math.radians(16),3,'X');affected=0;protected_error=0
for index,v in enumerate(key.data):
 p=w@v.co
 weight=smooth((.17-abs(p.x))/.05)*smooth((-.40-p.y)/.06)*smooth((p.z-1.06)/.07)
 if p.z>z+1e-5:weight=0
 # All lower-lip and existing lower teeth follow the same jaw transform.
 if weight>0:v.co=inv@(p+weight*(pivot+rot@(p-pivot)-p));affected+=1
 if p.z>1.27:protected_error=max(protected_error,(w@v.co-p).length)
# Build a recessed lining and tongue, with matching jaw morphs.
rig=next(x for x in s.objects if x.type=='ARMATURE')
def mat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);return m
lining=mat('Oral lining',(.12,.018,.025));tongue=mat('Tongue tissue',(.48,.13,.15))
added=[]
def anatomy(name,loc,scale,material,move):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc);a=bpy.context.object;a.name=name;a.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.data.materials.append(material)
 a.shape_key_add(name='Basis');k=a.shape_key_add(name='JawOpen')
 for v in k.data:
  p=a.matrix_world@v.co;weight=move(p)
  v.co=a.matrix_world.inverted()@(p+weight*(pivot+rot@(p-pivot)-p))
 for f in a.data.polygons:f.use_smooth=True
 added.append(a)
 return a
anatomy('Fitted oral interior',(0,-.455,1.203),(.075,.020,.029),lining,lambda p:smooth((z-p.z)/.035))
anatomy('Fitted tongue',(0,-.485,1.204),(.040,.022,.007),tongue,lambda p:1)
ivory=mat('Fitted ivory',(.75,.68,.52))
for x in (-.052,-.028,-.010,.010,.028,.052):
 anatomy('Upper tooth', (x,-.546,1.224),(.007,.007,.014 if abs(x)>.05 else .006),ivory,lambda p:0)
for x in (-.05,-.03,-.01,.01,.03,.05):
 anatomy('Lower tooth',(x,-.540,1.213),(.008,.008,.006),ivory,lambda p:1)
for a in added:
 world=a.matrix_world.copy();a.parent=rig;a.matrix_world=world
 group=a.vertex_groups.new(name='Head');group.add(list(range(len(a.data.vertices))),1,'REPLACE')
 mod=a.modifiers.new('Head binding','ARMATURE');mod.object=rig
# Identical jaw timing on the original chin and new anatomy.
for frame,value in [(1,0),(12,1),(24,0),(36,.65),(48,0)]:
 for a in [o]+added:
  k=a.data.shape_keys.key_blocks['JawOpen'];k.value=value;k.keyframe_insert('value',frame=frame)
s.frame_start=1;s.frame_end=48;s.render.fps=24
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'jaw-fit.blend'))
for f,name in [(1,'mouth-closed'),(12,'mouth-open')]:
 s.frame_set(f);s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'seam_world_z':z,'cut_edges':len(edges),'jaw_vertices':affected,'upper_face_max_change_m':protected_error,'status':'visual-review-required','facial_controls':['JawOpen'],'limitations':['eyes not rigged','phoneme controls not fitted','mouth corners need topology refinement']}
(H/'jaw-fit.json').write_text(json.dumps(report,indent=2))







