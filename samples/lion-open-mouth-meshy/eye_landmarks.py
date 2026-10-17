import bpy,math,json
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'face-fit.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;c=s.camera;out=[]
for x,y in [(245,333),(395,333),(225,333),(265,333),(245,316),(245,349)]:
 d=c.matrix_world.to_quaternion()@Vector(((2*x/640-1)*math.tan(c.data.angle_x/2),(1-2*y/640)*math.tan(c.data.angle_x/2),-1)).normalized()
 hit,p,n,i,o,m=s.ray_cast(bpy.context.evaluated_depsgraph_get(),c.location,d)
 if hit:out.append({'pixel':[x,y],'world':[round(v,5) for v in p],'object':o.name})
(H/'eye-landmarks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

