"""Tiny screen-space fit diagnostics; no geometry arrays emitted."""
import bpy,math,json
from mathutils import Vector
from pathlib import Path
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'lion-talking.blend'),use_scripts=False,load_ui=False)
rig=bpy.data.objects['Lion_Realistic'];scene=bpy.context.scene;values=[]
for frame in range(1,193):scene.frame_set(frame);values.append(rig.pose.bones['Repair-Jaw'].rotation_quaternion.angle)
scene.frame_set(max(range(192),key=lambda i:values[i])+1);cam=scene.camera;results=[]
for x,y in [(320,370),(310,380),(325,385),(320,360)]:
    tangent=math.tan(cam.data.angle_x/2)
    direction=cam.matrix_world.to_quaternion()@Vector(((2*x/640-1)*tangent,(1-2*y/640)*tangent,-1)).normalized()
    hit,point,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction)
    if hit:
        results.append({'pixel':[x,y],'object':obj.name,'fit_point':[round(v,4) for v in rig.matrix_world.inverted()@point],
            'rest_face_center':[round(v,4) for v in rig.matrix_world.inverted()@obj.matrix_world@obj.original.data.polygons[index].center] if obj.type=='MESH' else None})
(HERE/'mouth-fit-probe.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))

