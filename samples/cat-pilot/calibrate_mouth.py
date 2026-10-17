import bpy,math,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(H/'face-source.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;c=s.camera;out=[]
for x,y in [(320,265),(320,345),(220,345),(420,345),(320,410)]:
 tangent=math.tan(c.data.angle_x/2);d=c.matrix_world.to_quaternion()@Vector(((2*x/640-1)*tangent,(1-2*y/640)*tangent,-1)).normalized();hit,p,n,i,o,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),c.location,d)
 if hit:out.append({'pixel':[x,y],'world':[round(v,5) for v in p],'object':o.name})
print(json.dumps(out));(H/'mouth-landmarks.json').write_text(json.dumps(out,indent=2))
