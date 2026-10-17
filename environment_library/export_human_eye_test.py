"""Export an isolated MPFB eye audition without altering its source."""
import bpy,sys,json
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent;D=ROOT/'samples/rowan-eye-test'
sys.path.insert(0,str(ROOT/'samples/mpfb-character'))
from bootstrap import initialize
initialize()
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False)
from mpfb.services.exportservice import ExportService
mesh=bpy.data.objects['Rowan-Body'];rig=bpy.data.objects['Rowan-Rig']
bpy.context.scene.frame_set(1)
actions={o.name:(o.data.shape_keys.animation_data.action,o.data.shape_keys.animation_data.action_slot) for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data and o.data.shape_keys.animation_data.action}
ExportService.bake_modifiers_remove_helpers(mesh,bake_masks=True,bake_subdiv=False,remove_helpers=True,also_proxy=True)
for name,(action,slot) in actions.items():
 keys=bpy.data.objects[name].data.shape_keys
 if keys:
  keys.animation_data_create();keys.animation_data.action=action
  if slot:keys.animation_data.action_slot=slot
sys.path.insert(0,str(H))
from safe_shape_join import join_preserving_shapes
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and (o in list(rig.children_recursive) or any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))]
join_preserving_shapes(meshes,mesh)
sys.path.insert(0,str(ROOT.parent/'blendplugin-next/scene_pipeline'))
from export_performance import export
export(D/'performance',{'actors':[{'name':'Rowan'}],'lines':[]},False,{'Rowan':{'armature':rig.name}})
