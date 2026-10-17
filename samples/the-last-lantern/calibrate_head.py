import bpy,json,math
from pathlib import Path
from mathutils import Euler
root=Path(__file__).parent.resolve()
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-body.blend'),load_ui=False,use_scripts=False)
bpy.context.scene.frame_set(1);out={}
for name,rig_name,controls,probe in [('snow','RIG-Snow',['Head','FK-Head'],'DEF-Head'),('jacob','Armature',['CTRL-HEAD'],'DEF-HEAD')]:
 rig=bpy.data.objects[rig_name];reference=rig.pose.bones[probe].matrix.to_quaternion().copy();results=[]
 for label in controls:
  b=rig.pose.bones[label];saved=b.matrix_basis.copy();mode=b.rotation_mode
  for axis in range(3):
   angles=[0,0,0];angles[axis]=math.radians(12)
   if mode=='QUATERNION':b.rotation_quaternion=Euler(angles,'XYZ').to_quaternion()
   else:b.rotation_euler=angles
   bpy.context.view_layer.update();q=rig.pose.bones[probe].matrix.to_quaternion()@reference.inverted()
   if q.w<0:q=-q
   results.append({'control':label,'axis':axis,'actual_degrees':math.degrees(q.angle),'world_axis':list(q.axis)})
   b.matrix_basis=saved;bpy.context.view_layer.update()
 out[name]=results
(root/'head-calibration.json').write_text(json.dumps(out,indent=2));print('HEAD_CALIBRATION',json.dumps(out),flush=True)
