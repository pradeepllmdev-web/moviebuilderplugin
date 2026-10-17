import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;out=H/'amber-face-refinement';root=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65')
kind=sys.argv[sys.argv.index('--')+1]
path=root/'body-rig.glb' if kind=='source' else root/'character.glb' if kind=='previous' else out/('character-conservative.glb' if kind=='conservative' else 'character.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));s=bpy.context.scene
for obj in s.objects:
 obj.animation_data_clear()
 if obj.type=='ARMATURE':
  for b in obj.pose.bones:b.matrix_basis=Matrix.Identity(4)
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for k in obj.data.shape_keys.key_blocks:k.value=0
bpy.ops.object.camera_add(location=(0,-1.45,1.40));c=bpy.context.object;c.data.lens=60;c.rotation_euler=(Vector((0,0,1.40))-c.location).to_track_quat('-Z','Y').to_euler();s.camera=c
for loc,power in [((2,-3,4),180),((-2,-2,3),100),((0,2,3),160)]:
 bpy.ops.object.light_add(type='AREA',location=loc);a=bpy.context.object;a.data.energy=power;a.data.size=3;a.rotation_euler=(Vector((0,0,1.4))-a.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Face check');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.2,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.3
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=s.render.resolution_y=640;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.render.filepath=str(out/(kind+'-neutral.png'));bpy.ops.render.render(write_still=True)
if kind!='source':
 for obj in s.objects:
  if obj.type=='MESH' and obj.data.shape_keys:
   key=obj.data.shape_keys.key_blocks.get('jawOpen')
   if key:key.value=.55
 s.render.filepath=str(out/(kind+'-speech.png'));bpy.ops.render.render(write_still=True)

