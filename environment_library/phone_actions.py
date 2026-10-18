"""Phone call: the Phone_Call clip already brings one hand to the head; this adds the phone in that hand.

The phone is a small box skinned to the hand bone that gets closest to the head during the beat (parented to the
bone, so it moves with the clip). Check: distance from the phone to the nearest head vertex while held."""
import math
PHONE=dict(size_cm=(3.0,1.5,12.0))  # width, thickness, length
def feasibility(measures):return {'ok':True,'note':'prop only; the clip supplies the arm motion'}
def apply(scene,rig,body,timeline,fps,folder):
 """Add the phone to the closer hand and write phone-check.json. Needs Blender."""
 import bpy,json
 import numpy as np
 from mathutils import Matrix,Vector
 beats=[g for g in timeline if g['action']=='phone']
 if not beats:return None
 g=beats[0];frames=list(range(round(g['start']*fps)+1,round(g['end']*fps)+1,2))
 hands={side:next(b for b in rig.pose.bones if b.name.endswith(side+'Hand')) for side in ('Left','Right')}
 head=next(b for b in rig.pose.bones if b.name.endswith('Head'));names={x.index:x.name.split(':')[-1] for x in body.vertex_groups}
 mask=np.array([bool(v.groups) and names[max(v.groups,key=lambda x:x.weight).group].endswith(('Head','headfront')) for v in body.data.vertices])
 def head_vertices():
  e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());co=np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',co);W=np.array(e.matrix_world);return (co.reshape(-1,3)@W[:3,:3].T+W[:3,3])[mask]*100
 best=None
 for side,bone in hands.items():
  gaps=[]
  for f in frames:
   scene.frame_set(f);bpy.context.view_layer.update();p=np.array(rig.matrix_world@bone.head)*100;gaps.append(float(np.linalg.norm(head_vertices()-p,axis=1).min()))
  if best is None or min(gaps)<best[0]:best=(min(gaps),side,gaps)
 side=best[1];bone=hands[side];w,t,l=[v/100 for v in PHONE['size_cm']]
 bpy.ops.mesh.primitive_cube_add(size=1);phone=bpy.context.object;phone.name='Phone';phone.scale=(w,t,l)
 m=bpy.data.materials.new('Phone');m.diffuse_color=(.05,.05,.07,1);phone.data.materials.append(m)
 phone.parent=rig;phone.parent_type='BONE';phone.parent_bone=bone.name
 # In the bone's frame: centred on the palm, long side along the fingers (bone Y), a little toward the palm side.
 length=(bone.tail-bone.head).length;phone.matrix_parent_inverse=Matrix.Translation((0,-length,0));phone.location=(0,length*.5+l*.15,0);phone.rotation_euler=(0,0,0)
 phone.hide_render=False
 gaps=[];centre=[]
 for f in frames:
  scene.frame_set(f);bpy.context.view_layer.update();e=phone.evaluated_get(bpy.context.evaluated_depsgraph_get());c=np.array(e.matrix_world.translation)*100;gaps.append(float(np.linalg.norm(head_vertices()-c,axis=1).min()))
 report=dict(ok=min(gaps)<=9,hand=side,closest_to_head_cm=round(min(gaps),1),hand_to_head_closest_cm=round(best[0],1),held_frames=len(frames),scope='Phone box skinned to the hand bone; the clip supplies the arm motion')
 (folder/'phone-check.json').write_text(json.dumps(report));return report
