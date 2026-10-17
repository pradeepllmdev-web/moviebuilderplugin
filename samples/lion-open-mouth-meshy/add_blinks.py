"""Calibrated Meshy-lion closure lids; no mesh arrays are emitted."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent;H=BASE/'talking-blink';H.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'talking/lion-talking.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;s.frame_set(1);rig=next(o for o in s.objects if o.type=='ARMATURE');surface=bpy.data.objects['char1']
mods=[(m,m.show_viewport) for m in surface.modifiers]
for m,_ in mods:m.show_viewport=False
bpy.context.view_layer.update();inv=surface.matrix_world.inverted();world=surface.matrix_world
mat=bpy.data.materials.new('Lion eyelid fur');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.52,.35,.20,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
crease_mat=bpy.data.materials.new('Lion eyelid crease');crease_mat.use_nodes=True;crease_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.065,.025,1)
def front(x,z):
 hit,p,n,i=surface.ray_cast(inv@Vector((x,-1,z)),inv.to_3x3()@Vector((0,1,0)))
 if not hit:raise ValueError('Eyelid fit missed face')
 p=world@p;p.y-=.0025;return p
lids=[]
for side,cx in [('L',-.089),('R',.089)]:
 cz=1.3858;rx=.038;rz=.028
 for crease in (False,True):
  points=[];closed=[];faces=[];cols=32;rows=1 if crease else 12
  for row in range(rows+1):
   v=row/rows
   for col in range(cols+1):
    u=-1+2*col/cols;arc=math.sqrt(max(0,1-u*u));x=cx+rx*u
    top=cz+rz*arc+.001
    if crease:z=cz+.002*u*u+(v-.5)*.001
    else:z=cz+rz*arc*(1-2*v)
    p=front(x,z)
    if crease:p.y-=.005
    closed.append(p);rest=front(x,top);rest.y+=.006+v*.001;points.append(rest)
    if row<rows and col<cols:
     a=row*(cols+1)+col;faces.append((a,a+1,a+cols+2,a+cols+1))
  data=bpy.data.meshes.new('Closure lid');data.from_pydata(points,[],faces);data.update()
  obj=bpy.data.objects.new(('Crease ' if crease else 'Lid ')+side,data);s.collection.objects.link(obj)
  obj.data.materials.append(crease_mat if crease else mat)
  for f in data.polygons:f.use_smooth=True
  obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink'+side,from_mix=False)
  for v,p in zip(key.data,closed):v.co=p
  obj.parent=rig;obj.matrix_world.identity()
  group=obj.vertex_groups.new(name='Head');group.add(list(range(len(points))),1,'REPLACE')
  mod=obj.modifiers.new('Head binding','ARMATURE');mod.object=rig
  for f,value in [(1,0),(26,0),(28,1),(29,1),(33,0),(76,0),(79,1),(80,1),(84,0),(142,0),(145,1),(146,1),(150,0),(192,0)]:
   key.value=value;key.keyframe_insert('value',frame=f)
  lids.append(obj)
for m,enabled in mods:m.show_viewport=enabled
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'lion-talking.blend'))
plan=json.loads((BASE/'talking/application.json').read_text());plan['limitations']=['mouth corners still require refinement','fitted eyelid overlays; no independent gaze','jaw-based speech approximation, not full visemes'];plan['blink_frames']=[28,79,145]
(H/'application.json').write_text(json.dumps(plan,indent=2))
# Fixed camera diagnostic at rest isolates coverage from body/head movement.
rig.animation_data_clear()
from mathutils import Matrix
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
c=s.camera;c.location=(0,-1.55,1.4);c.rotation_euler=(Vector((0,0,1.4))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=60
for frame,name in [(1,'eyes-open'),(28,'eyes-closed')]:
 s.frame_set(frame);s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
# Screen coverage rays on neutral rig at full closure must hit a fitted lid.
s.frame_set(28);bpy.context.view_layer.update();probes=[]
for cx in (-.08202,.08203):
 for dx,dz in [(0,0),(-.012,0),(.012,0),(0,-.010),(0,.010)]:
  hit,p,n,i,obj,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((cx+dx,-1,1.3858+dz)),Vector((0,1,0)))
  probes.append(bool(hit and (obj.name.startswith('Lid ') or obj.name.startswith('Crease '))))
assert all(probes),'Pupil coverage incomplete'
(H/'blink-verification.json').write_text(json.dumps({'coverage_probes':len(probes),'all_covered':all(probes),'blink_frames':plan['blink_frames'],'original_rigged_source_unchanged':hashlib.sha256((BASE/'rigged.glb').read_bytes()).hexdigest()==plan['source_sha256']},indent=2))


