"""Blender integration: reordered objects retain UV/weight vertex identity."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'environment_library'))
from safe_shape_join import join_preserving_shapes
bpy.ops.wm.read_factory_settings(use_empty=True)
objects=[];expected={}
for n,name in enumerate(['Z_eye','A_body','M_hair']):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
 obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);obj.location=(n*2,n,0)
 obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink');key.data[0].co.z=.1*(n+1)
 ids=mesh.attributes.new('qa_identity','INT','POINT')
 for i,v in enumerate(ids.data):v.value=n*3+i
 objects.append(obj)
active=objects[1];inverse=active.matrix_world.inverted();bpy.context.view_layer.update();inverse=active.matrix_world.inverted()
for obj in objects:
 transform=inverse@obj.matrix_world
 for i,v in enumerate(obj.data.vertices):expected[obj.data.attributes['qa_identity'].data[i].value]=(transform@v.co,transform@obj.data.shape_keys.key_blocks['Blink'].data[i].co)
joined=join_preserving_shapes(list(reversed(objects)),active)
for i,v in enumerate(joined.data.attributes['qa_identity'].data):
 basis,blink=expected[v.value]
 assert (joined.data.shape_keys.key_blocks[0].data[i].co-basis).length<1e-6
 assert (joined.data.shape_keys.key_blocks['Blink'].data[i].co-blink).length<1e-6
print('PASS: transformed shape keys retain vertex identity across reordered mesh joins')
from safe_shape_join import join_animated_shapes
data=bpy.data.armatures.new('QA rig');rig=bpy.data.objects.new('QA rig',data);bpy.context.scene.collection.objects.link(rig)
joined.modifiers.new('QA armature','ARMATURE').object=rig
blink=joined.data.shape_keys.key_blocks['Blink']
for frame,value in [(1,.2),(2,.8)]:blink.value=value;blink.keyframe_insert('value',frame=frame)
mesh=bpy.data.meshes.new('Other facial surface');mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)]);other=bpy.data.objects.new('Other facial surface',mesh);bpy.context.scene.collection.objects.link(other);other.modifiers.new('QA armature','ARMATURE').object=rig
other.shape_key_add(name='Basis');smile=other.shape_key_add(name='Smile');smile.data[0].co.z=.1
for frame,value in [(1,.4),(2,.7)]:smile.value=value;smile.keyframe_insert('value',frame=frame)
combined=join_animated_shapes(bpy.context.scene,rig,2)
for frame,expected in [(1,(.2,.4)),(2,(.8,.7))]:
 bpy.context.scene.frame_set(frame)
 assert abs(combined.data.shape_keys.key_blocks['Blink'].value-expected[0])<1e-5
 assert abs(combined.data.shape_keys.key_blocks['Smile'].value-expected[1])<1e-5
print('PASS: facial animation from separate surfaces survives the join')
