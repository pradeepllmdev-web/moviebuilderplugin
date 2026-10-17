import bpy,json,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(H/'source/CatPilot.blend'),link=False) as (src,dst):
 dst.objects=['Armature','CatPilot'];dst.actions=['Walk','Run','Cheer']
for action in dst.actions:
 if action:action.use_fake_user=True
for o in dst.objects:
 if o:bpy.context.scene.collection.objects.link(o)
rig=bpy.data.objects['Armature'];cat=bpy.data.objects['CatPilot'];rig.animation_data_clear();cat.animation_data_clear();cat.data.shape_keys.animation_data_clear()
for image in bpy.data.images:
 if image.source=='FILE':image.filepath=str(H/'source/catPilotTex.png');image.reload()
cat.data.materials.clear();cat.data.materials.append(bpy.data.materials.new('Cat Pilot atlas'))
for polygon in cat.data.polygons:polygon.material_index=0
for mat in cat.data.materials:
 if mat:
  mat.use_nodes=True
  shader=mat.node_tree.nodes.get('Principled BSDF')
  if shader:
   texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(str(H/'source/catPilotTex.png'),check_existing=True);mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
   shader.inputs['Roughness'].default_value=.7
keys=cat.data.shape_keys.key_blocks
points=[cat.matrix_world@Vector(c) for c in cat.bound_box];low=min(p.z for p in points);high=max(p.z for p in points);height=high-low;center=sum(points,Vector())/8
s=bpy.context.scene;s.render.fps=24;s.frame_start=1;s.frame_end=192
bpy.ops.object.camera_add(location=center+Vector((0,-height*2.5,height*.2)));cam=bpy.context.object;cam.data.lens=50;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
for loc,power in [((2,-3,4),200),((-2,-2,3),100),((0,2,4),170)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(loc)*height*.5);light=bpy.context.object;light.data.energy=power;light.data.size=height*2;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=height*50,location=(0,0,low));floor=bpy.context.object;mat=bpy.data.materials.new('Floor');mat.diffuse_color=(.08,.12,.16,1);floor.data.materials.append(mat)
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.2,.25,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.4
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=s.render.resolution_y=512;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
rig.animation_data_create().action=bpy.data.actions['Walk']
s.frame_set(20)
for value,name in [(0,'eyes-0'),(1,'eyes-1')]:
 keys['Eyes'].value=value;s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'preview.blend'))
print('PREVIEW_READY',height)




