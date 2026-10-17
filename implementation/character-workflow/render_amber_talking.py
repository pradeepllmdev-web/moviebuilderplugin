import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;out=H/'amber-face-refinement';root=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65')
kind='conservative'
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

track=json.loads((root/'demo/standing/track.json').read_text());frames=out/'talking-frames';frames.mkdir(exist_ok=True)
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=512
rig=next(o for o in s.objects if o.type=='ARMATURE');head=rig.pose.bones.get('Head')
from mathutils import Quaternion
import math
for i in range(track['frames']):
 for obj in s.objects:
  if obj.type=='MESH' and obj.data.shape_keys:
   for name,values in track['weights'].items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=float(values[i])
 if head:
  axis=head.bone.matrix_local.to_quaternion().inverted()@(rig.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
  head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(3)*math.sin(i/24*1.3))
 s.render.filepath=str(frames/f'{i:05d}.png');bpy.ops.render.render(write_still=True)
print('CLOSEUP_READY')
