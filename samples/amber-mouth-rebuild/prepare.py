import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent
src=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65/body-rig.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(src));s=bpy.context.scene
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.ops.object.camera_add(location=(0,-1.45,1.4));c=bpy.context.object;c.data.lens=60;c.rotation_euler=(Vector((0,0,1.4))-c.location).to_track_quat('-Z','Y').to_euler();s.camera=c;s.render.resolution_x=s.render.resolution_y=640
for loc,power in [((2,-3,4),180),((-2,-2,3),100),((0,2,3),160)]:
 bpy.ops.object.light_add(type='AREA',location=loc);a=bpy.context.object;a.data.energy=power;a.data.size=3;a.rotation_euler=(Vector((0,0,1.4))-a.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Amber studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.2,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.3
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.filepath=str(H/'source.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'source.blend'))
result=[]
for x,y in [(320,390),(320,468),(320,490),(250,470),(390,470)]:
 d=c.matrix_world.to_quaternion()@Vector(((2*x/640-1)*math.tan(c.data.angle_x/2),(1-2*y/640)*math.tan(c.data.angle_x/2),-1)).normalized()
 hit,p,n,i,o,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),c.location,d)
 if hit:result.append({'pixel':[x,y],'world':[round(v,5) for v in p]})
(H/'landmarks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
