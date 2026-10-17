from pathlib import Path
p=Path('implementation/character-workflow/render_amber_face.py');t=p.read_text();t=t[:t.index("s.render.filepath=str(out/(kind+'-neutral.png'))")]
t=t.replace("kind=sys.argv[sys.argv.index('--')+1]","kind='conservative'")
t+='''
track=json.loads((root/'demo/standing/track.json').read_text());frames=out/'talking-frames';frames.mkdir(exist_ok=True)
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=512
rig=next(o for o in s.objects if o.type=='ARMATURE');head=rig.pose.bones.get('Head')
from mathutils import Quaternion
import math
for i in range(track['frames']):
 for obj in s.objects:
  if obj.type=='MESH' and obj.data.shape_keys:
   for name,values in track['weights'].items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=float(values[i])
 if head:
  axis=head.bone.matrix_local.to_quaternion().inverted()@(rig.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
  head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(3)*math.sin(i/24*1.3))
 s.render.filepath=str(frames/f'{i:05d}.png');bpy.ops.render.render(write_still=True)
print('CLOSEUP_READY')
'''
Path('implementation/character-workflow/render_amber_talking.py').write_text(t)
