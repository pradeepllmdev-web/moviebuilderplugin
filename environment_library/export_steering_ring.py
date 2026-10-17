import bpy,math
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-drive-v2'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_torus_add(major_radius=.21,minor_radius=.025,major_segments=40,minor_segments=10,rotation=(0,math.pi/2,0))
o=bpy.context.object;m=bpy.data.materials.new('SteeringRubber');m.diffuse_color=(.025,.025,.025,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.025,.025,.025,1);o.data.materials.append(m)
bpy.ops.export_scene.fbx(filepath=str(D/'SteeringRing.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',path_mode='COPY',embed_textures=True,bake_anim=False)
