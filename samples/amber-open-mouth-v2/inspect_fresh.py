import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(H/'rigged.glb'));s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');r.animation_data_clear()
for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==r for m in o.modifiers)]
for o in s.objects:
 if o.type=='MESH' and o not in meshes:o.hide_render=True
points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box];low=min(p.z for p in points);height=max(p.z for p in points)-low;cx=(min(p.x for p in points)+max(p.x for p in points))/2;cy=(min(p.y for p in points)+max(p.y for p in points))/2;target=Vector((cx,cy,low+.8*height))
bpy.ops.object.camera_add();c=bpy.context.object;c.data.lens=55;s.camera=c
for position,power in [((2,-3,4),180),((-2,-2,3),100),((0,2,3),160)]:
 bpy.ops.object.light_add(type='AREA',location=position);a=bpy.context.object;a.data.energy=power;a.data.size=3;a.rotation_euler=(target-a.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Fresh Amber');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.2,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.3;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=s.render.resolution_y=640;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
for name,offset in [('front',(0,-height*.95,0)),('three-quarter',(.45*height,-.85*height,0))]:
 c.location=target+Vector(offset);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'fresh-model.blend'))
(H/'capabilities.json').write_text(json.dumps({'bones':list(r.pose.bones.keys()),'mesh_count':len(meshes),'shape_keys':{o.name:[k.name for k in o.data.shape_keys.key_blocks] for o in meshes if o.data.shape_keys},'facial_status':'requires fitting and visual review','old_geometry_reused':False},indent=2));print('FRESH_MODEL_READY')
