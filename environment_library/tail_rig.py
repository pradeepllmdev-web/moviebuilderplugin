"""A tail bone for the lion, on the job copy only.

The lion has no tail bones: its tail (lying on the ground behind it at rest) is weighted to the leg and foot
bones, so it swings with the legs, drags through the floor when walking and sinks 25-45 cm into it when
seated. Here the tail vertices move to a new 'Tail' bone under the hips (blended near the root). Each frame the
bone gets the smallest lift that keeps every tail point above the floor (and above a seat it passes over),
smoothed, with a slow sway. Solved in numpy from rest coordinates, so no per-candidate scene updates."""
import math
import numpy as np

def _tail_vertices(body,hips_rest):
 """Tail: behind and well below the hips at rest (Blender: +Y is backward), grown along edges into the
 connected leg-weighted vertices behind the hips so the tail root moves with the tail, not the legs."""
 W=np.array(body.matrix_world);rest=np.array([v.co for v in body.data.vertices])@W[:3,:3].T+W[:3,3]
 names={g.index:g.name for g in body.vertex_groups}
 leggy=np.array([bool(v.groups) and names[max(v.groups,key=lambda g:g.weight).group].endswith(('UpLeg','Leg','Foot','ToeBase')) for v in body.data.vertices])
 mask=(rest[:,1]>hips_rest[1]+.15)&(rest[:,2]<hips_rest[2]-.2);grow=leggy&(rest[:,1]>hips_rest[1]+.05)
 edges=np.array([e.vertices[:] for e in body.data.edges]);changed=True
 while changed:
  touch=mask[edges[:,0]]|mask[edges[:,1]];add=np.zeros(len(mask),bool);add[edges[touch].ravel()]=True;add&=grow&~mask;changed=add.any();mask|=add
 return np.where(mask)[0],rest
def rig_tail(scene,rig,body,frames,floor,clearance=.02,sway_deg=6.,fps=24):
 """floor(frame) -> function(points Nx3 world) giving the minimum allowed z per point. Returns a report."""
 import bpy
 from mathutils import Matrix,Quaternion,Vector
 hips=next(b for b in rig.pose.bones if b.name.endswith('Hips'));hips_rest=np.array(rig.matrix_world@hips.bone.head_local)
 index,rest=_tail_vertices(body,hips_rest)
 if len(index)<20:return {'ok':False,'reason':'no tail vertices found'}
 tail=rest[index];base=tail[np.argmin(tail[:,1])];tip=tail[np.argmax(tail[:,1])];along=np.clip((tail-base)@(tip-base)/np.dot(tip-base,tip-base),0,1)
 # Bone along the tail; blend weights in over the first ~15% so the root stays attached to the body.
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');inverse=rig.matrix_world.inverted()
 bone=rig.data.edit_bones.new('Tail');bone.head=inverse@Vector(base);bone.tail=inverse@Vector(base+(tip-base)*.3);bone.parent=rig.data.edit_bones[hips.name]
 bpy.ops.object.mode_set(mode='OBJECT')
 groups={g.name:g for g in body.vertex_groups};tail_group=groups.get('Tail') or body.vertex_groups.new(name='Tail');hips_group=groups.get(hips.name) or body.vertex_groups.new(name=hips.name)
 for g in body.vertex_groups:
  if g not in (tail_group,hips_group):g.remove([int(i) for i in index])
 for i,u in zip(index,along):
  w=float(min(1,u/.15));tail_group.add([int(i)],w,'REPLACE');hips_group.add([int(i)],1-w,'REPLACE')
 pose=rig.pose.bones['Tail'];pose.rotation_mode='QUATERNION';rest_matrix=np.array(rig.matrix_world@rig.data.bones['Tail'].matrix_local)
 # Tail points in the bone's rest frame (only fully weighted ones decide the lift).
 sample=tail[along>.15][::max(1,int((along>.15).sum()//60))];local=(np.linalg.inv(rest_matrix)@np.c_[sample,np.ones(len(sample))].T).T[:,:3]
 axis_armature=np.array([1.,0,0]);axis=np.linalg.inv(np.array(rig.data.bones['Tail'].matrix_local)[:3,:3])@axis_armature;axis/=np.linalg.norm(axis)
 def rotation(theta):
  c,s=math.cos(theta),math.sin(theta);K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);return np.eye(3)+s*K+(1-c)*K@K
 lifts=[];pose.rotation_quaternion=Quaternion()
 # Which sign lifts the tip upward at rest.
 sign=1 if (rotation(.3)@local[np.argmax(local[:,1])])[2]-(local[np.argmax(local[:,1])])[2]>=0 else -1
 for frame in frames:
  scene.frame_set(frame);bpy.context.view_layer.update();M=np.array(rig.matrix_world@pose.matrix)
  minimum=floor(frame);best=math.radians(100)
  for degrees in range(0,101,2):
   R=rotation(sign*math.radians(degrees));points=(M[:3,:3]@(R@local.T)).T+M[:3,3]
   if (points[:,2]>=minimum(points)+clearance).all():best=math.radians(degrees);break
  lifts.append(best)
 # Smooth: rise quickly, settle slowly, never below the needed lift; add a slow sway.
 smooth=[];current=lifts[0]
 for need in lifts:current=max(need,current-math.radians(1.5));smooth.append(current)
 for k in range(len(smooth)-2,-1,-1):smooth[k]=max(smooth[k],smooth[k+1]-math.radians(3))
 for frame,theta in zip(frames,smooth):
  sway=math.radians(sway_deg)*math.sin(2*math.pi*frame/(fps*2.6))
  q=Quaternion(Vector(axis),sign*theta)@Quaternion(Vector((0,0,1)),sway);pose.rotation_quaternion=q;pose.keyframe_insert('rotation_quaternion',frame=frame)
 return {'ok':True,'tail_vertices':int(len(index)),'max_lift_deg':round(math.degrees(max(lifts)),1),'scope':'Tail bone added on the job copy; floor and seat clearance from sampled tail points'}
