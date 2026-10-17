import bpy,sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from realistic_rig import bone_curves
p=Path(r'C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin')
bpy.ops.wm.open_mainfile(filepath=str(p/'samples/the-last-lantern/the-last-lantern-body.blend'),load_ui=False,use_scripts=False)
from mathutils import Quaternion
out={}
for name,rigname in [('snow','RIG-Snow'),('jacob','Armature')]:
 r=bpy.data.objects[rigname];curves=bone_curves(r.animation_data.action);profile=json.loads((p/'movie_production/profiles'/f'{name}-body.json').read_text());bad=[]
 for bone in profile['mapping'].values():
  cs=curves[bone]['rotation_quaternion'];prev=None
  for i in range(len(cs[0].keyframe_points)):
   q=Quaternion([c.keyframe_points[i].co.y for c in cs]).normalized()
   if prev is not None and prev.dot(q)<0:bad.append({'bone':bone,'frame':cs[0].keyframe_points[i].co.x})
   prev=q
 out[name]=bad
print('QUATERNION_SEAMS',json.dumps(out),flush=True)
