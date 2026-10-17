import bpy
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-scramble'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1)
o=bpy.context.object;bevel=o.modifiers.new('Soft rock edges','BEVEL');bevel.width=.06;bevel.segments=3;bpy.ops.object.modifier_apply(modifier=bevel.name)
bpy.ops.export_scene.fbx(filepath=str(D/'RockStep.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',bake_anim=False)
