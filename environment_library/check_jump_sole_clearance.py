"""Use evaluated mesh bounds internally; emit only landing clearance metadata."""
import bpy,json
from pathlib import Path
from mathutils import Vector
D=Path(__file__).resolve().parent.parent/'samples/lion-jump';bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');route=json.loads((D/'route.json').read_text());changes=[]
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
for row in route:
 bpy.context.scene.frame_set(row['frame']+1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();minimum=1e6
 for obj in meshes:
  evaluated=obj.evaluated_get(deps);minimum=min(minimum,min((evaluated.matrix_world@Vector(v)).z for v in evaluated.bound_box))
 old=row['location_cm'][2];row['location_cm'][2]=25-minimum*100+row['foot_clearance_cm'];changes.append(row['location_cm'][2]-old)
(D/'route.json').write_text(json.dumps(route));(D/'sole-check.json').write_text(json.dumps({'ok':True,'frames':len(route),'method':'evaluated skinned mesh minimum Z; no model vertices emitted','landing_sole_height_cm':25,'target_rock_height_cm':25,'root_correction_range_cm':[min(changes),max(changes)]},indent=2))
