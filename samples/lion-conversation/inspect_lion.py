"""Inspect prepared lion controls internally, never print geometry arrays."""
import bpy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/verification/lion-detailed/authored_probe.blend')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False,load_ui=False)
rig=bpy.data.objects['Lion_Realistic']
meshes=[obj for obj in rig.children_recursive if obj.type=='MESH']
report={'source':str(SOURCE),'bones':list(rig.pose.bones.keys()),'face_version':rig.get('lion_face_version'),
    'face_marks':dict(rig.get('face_marks',{})),
    'meshes':[{'name':obj.name,'shape_keys':list(obj.data.shape_keys.key_blocks.keys()) if obj.data.shape_keys else [],
               'armature_bound':any(mod.type=='ARMATURE' for mod in obj.modifiers)} for obj in meshes]}
(HERE/'inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
bpy.context.scene.frame_set(1);scene=bpy.context.scene
scene.render.resolution_x=768;scene.render.resolution_y=432;scene.render.resolution_percentage=100
scene.render.filepath=str(HERE/'source-preview.png');bpy.ops.render.render(write_still=True)
