import bpy,json,math,sys,re
from pathlib import Path
from mathutils import Quaternion,Vector
H=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
movie_id=args[0] if args else '86837d3303914a2f98132afe7e4db318'
if not re.fullmatch('[a-f0-9]{32}',movie_id):raise ValueError('Invalid movie ID')
D=H/'movie_jobs'/movie_id;m=json.loads((D/'ready.json').read_text());rotation=0;location=0
for previous,current in zip(m['shots'],m['shots'][1:]):
 for actor in range(len(json.loads((H/'scene_jobs'/current['scene_id']/'profiles.json').read_text()))):
  old=json.loads((H/'scene_jobs'/previous['scene_id']/('actor_'+str(actor))/'end-pose.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(H/'scene_jobs'/current['scene_id']/('actor_'+str(actor))/'scene.blend'),use_scripts=False);bpy.context.scene.frame_set(1);rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
  for bone in rig.pose.bones:
   if bone.name not in old:continue
   diff=Quaternion(old[bone.name]['rotation']).rotation_difference(bone.rotation_quaternion);rotation=max(rotation,math.degrees(2*math.acos(min(1,abs(diff.w)))));location=max(location,(Vector(old[bone.name]['location'])-bone.location).length)
(D/'continuity-verification.json').write_text(json.dumps({'ok':rotation<1 and location<.001,'maximum_control_rotation_difference_deg':rotation,'maximum_local_location_difference':location,'scope':'Baked Blender control poses at shot boundaries; not full perceptual continuity'},indent=2))
