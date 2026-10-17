import bpy,math,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(H/'fresh-model.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render];points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box];low=min(p.z for p in points);h=max(p.z for p in points)-low;target=Vector(((min(p.x for p in points)+max(p.x for p in points))/2,(min(p.y for p in points)+max(p.y for p in points))/2,low+.8*h));c=s.camera;c.location=target+Vector((0,-h*.95,0));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update();results=[]
for x,y in [(320,312),(320,360),(320,426),(320,400),(220,370),(420,370)]:
 d=c.matrix_world.to_quaternion()@Vector(((2*x/640-1)*math.tan(c.data.angle_x/2),(1-2*y/640)*math.tan(c.data.angle_x/2),-1)).normalized();hit,p,n,i,o,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),c.location,d)
 if hit:results.append({'pixel':[x,y],'world':[round(v,5) for v in p]})
(H/'landmarks.json').write_text(json.dumps(results,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(H/'front-setup.blend'));print(json.dumps(results))

