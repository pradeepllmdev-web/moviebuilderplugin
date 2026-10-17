"""Two-arm IK following the same scalar box trajectory as the Unreal prop.

The rig stays at the origin facing -Y in Blender (root motion goes to the route), so the box and
both grips are placed from the carrier-relative box coordinates: lateral -> +X, forward -> -Y."""
import bpy,math
import numpy as np
from mathutils import Vector,Quaternion,Matrix
HAND_GROUPS=('Hand','Thumb','Index','Middle','Ring','Pinky','ForeArm')

def solve_arm(rig,hand,target,weight,pole):
 fore=hand.parent;upper=fore.parent;inv=rig.matrix_world.inverted();h,k,a=upper.head.copy(),fore.head.copy(),hand.head.copy();t=a.lerp(inv@target,weight);first=(k-h).length;second=(a-k).length
 distance=min(max((t-h).length,1e-4),(first+second)*.999);direction=(t-h).normalized();hint=inv@pole-h;plane=hint-direction*hint.dot(direction);plane=plane.normalized() if plane.length>1e-6 else direction.orthogonal().normalized();cosine=max(-1,min(1,(first*first+distance*distance-second*second)/(2*first*distance)));elbow=h+direction*first*cosine+plane*first*math.sqrt(1-cosine*cosine)
 around=lambda point,q:Matrix.Translation(point)@q.to_matrix().to_4x4()@Matrix.Translation(-point)
 rotate_upper=around(h,(k-h).rotation_difference(elbow-h));upper_matrix=upper.matrix.copy();fore_matrix=fore.matrix.copy();a1=rotate_upper@a;rotate_fore=around(elbow,(a1-elbow).rotation_difference(h+direction*distance-elbow));upper.matrix=rotate_upper@upper_matrix;bpy.context.view_layer.update();fore.matrix=rotate_fore@rotate_upper@fore_matrix;bpy.context.view_layer.update()
 return upper,fore
def head_pitch(rig,head):
 """Forward tilt of the head bone axis in degrees (0 = upright, positive = nodding toward -Y)."""
 axis=(rig.matrix_world.to_quaternion()@head.matrix.to_quaternion())@Vector((0,1,0));return math.degrees(math.atan2(-axis.y,axis.z))
def grip(local,sign,carry):
 """Wrist target on the box side wall, toward its rear and slightly above centre."""
 w=carry['size_cm'][0];lateral,forward,height=local
 return Vector(((lateral+sign*(w/2+carry['grip_out_cm']))/100,-(forward-carry['grip_back_cm'])/100,(height+carry['grip_up_cm'])/100))
def apply(scene,rig,trajectory,position=None):
 carry=trajectory['carry'];targets=[];bones=[]
 spine=next((b for b in rig.pose.bones if b.name.endswith('Spine2')),None)
 if spine:
  for row in trajectory['rows']:
   scene.frame_set(row['frame']+1);spine.rotation_quaternion=spine.rotation_quaternion@Quaternion((1,0,0),math.radians(-4*row['reaction']));spine.keyframe_insert('rotation_quaternion',frame=row['frame']+1)
 # Some idle variants hunch (spine/neck) and nod the head ~35 degrees; a held box sits under the snout,
 # so cap each bone's forward tilt, parents first, while the hands are on the box.
 limits=carry.get('posture_pitch_limits_deg',{'Spine1':4,'Spine2':4,'Neck':2,'Head':15});capped={}
 chain=[(name,next((b for b in rig.pose.bones if b.name.split(':')[-1]==name),None)) for name in limits]
 for row in trajectory['rows']:
  if row['hand_weight']<=0:continue
  scene.frame_set(row['frame']+1);bpy.context.view_layer.update()
  for name,bone in chain:
   if bone is None:continue
   limit=limits[name];pitch=head_pitch(rig,bone)
   if pitch<=limit:continue
   world=rig.matrix_world.to_quaternion()@bone.matrix.to_quaternion();axis=world@Vector((0,1,0));r=math.hypot(axis.y,axis.z);target=Vector((axis.x,-r*math.sin(math.radians(limit)),r*math.cos(math.radians(limit))))
   delta=Quaternion().slerp(axis.rotation_difference(target),row['hand_weight']);matrix=rig.matrix_world.inverted()@delta.to_matrix().to_4x4()@rig.matrix_world@bone.matrix;matrix.translation=bone.head;bone.matrix=matrix;bpy.context.view_layer.update();bone.keyframe_insert('rotation_quaternion',frame=row['frame']+1);capped[name]=capped.get(name,0)+1
 for side,sign in [('Left',1),('Right',-1)]:
  hand=next(b for b in rig.pose.bones if b.name.endswith(side+'Hand'));bones.append(hand)
  target=bpy.data.objects.new('Box_'+side+'_Wrist',None);scene.collection.objects.link(target);targets.append(target)
  for row in trajectory['rows']:
   target.location=grip(row['local_cm'],sign,carry);target.keyframe_insert('location',frame=row['frame']+1)
 for row in trajectory['rows']:
  if row['hand_weight']<=0:continue
  scene.frame_set(row['frame']+1);bpy.context.view_layer.update()
  for index,(hand,target) in enumerate(zip(bones,targets)):
   sign=1 if index==0 else -1;fore=hand.parent;upper=fore.parent;old_upper=upper.rotation_quaternion.copy();old_fore=fore.rotation_quaternion.copy()
   # Elbows out to the side, slightly back and down: a hugging carry, not raised wings.
   solve_arm(rig,hand,target.location,1,Vector((sign*.9,.1,1.0)))
   new_upper=upper.rotation_quaternion.copy();new_fore=fore.rotation_quaternion.copy();upper.rotation_quaternion=old_upper.slerp(new_upper,row['hand_weight']);fore.rotation_quaternion=old_fore.slerp(new_fore,row['hand_weight'])
   upper.keyframe_insert('rotation_quaternion',frame=row['frame']+1);fore.keyframe_insert('rotation_quaternion',frame=row['frame']+1);bpy.context.view_layer.update()
 for row in trajectory['rows']:
  if row['hand_weight']<=0:continue
  scene.frame_set(row['frame']+1);bpy.context.view_layer.update()
  for hand in bones:
   base=hand.rotation_quaternion.copy();direction=(rig.matrix_world.to_quaternion()@hand.matrix.to_quaternion())@Vector((0,1,0));delta=direction.rotation_difference(Vector((0,-1,0)))
   matrix=rig.matrix_world.inverted()@delta.to_matrix().to_4x4()@rig.matrix_world@hand.matrix;matrix.translation=hand.head;hand.matrix=matrix;desired=hand.rotation_quaternion.copy();hand.rotation_quaternion=base.slerp(desired,row['hand_weight']);hand.keyframe_insert('rotation_quaternion',frame=row['frame']+1)
 errors=[];by_action={};worst=None
 for row in trajectory['rows']:
  if not row['contact'] or row['hand_weight']<.99:continue
  scene.frame_set(row['frame']+1);bpy.context.view_layer.update()
  for hand,target in zip(bones,targets):
   error=((rig.matrix_world@hand.head)-target.location).length*100;errors.append(error);by_action[row['action']]=max(by_action.get(row['action'],0),error)
   if worst is None or error>worst['error_cm']:worst={'frame':row['frame'],'action':row['action'],'hand':hand.name,'error_cm':error}
 maximum=max(errors,default=0)
 return {'ok':bool(errors) and maximum<5,'maximum_wrist_target_error_cm':maximum,'contact_samples':len(errors),'by_action_cm':by_action,'worst':worst,'grip':'side walls, '+str(carry['grip_back_cm'])+'cm in from the rear face','posture_capped_frames':capped,'posture_pitch_limits_deg':limits,'scope':'Wrist IK targets on the box sides; finger wrapping requires visual review'}
def body_clearance(scene,rig,trajectory,step=4):
 """Deepest evaluated body vertex inside the box (hands and forearms excluded: they grip it)."""
 carry=trajectory['carry'];half=np.array(carry['size_cm'],dtype=float)/200;limit=carry['penetration_limit_cm']
 meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
 masks={}
 for obj in meshes:
  names={g.index:g.name for g in obj.vertex_groups};mask=np.zeros(len(obj.data.vertices),dtype=bool)
  for v in obj.data.vertices:
   if v.groups:
    best=max(v.groups,key=lambda g:g.weight);mask[v.index]=any(part in names.get(best.group,'') for part in HAND_GROUPS)
  masks[obj.name]=~mask
 worst={'depth_cm':0.,'frame':None,'object':None};samples=0;by_action={};posture={}
 for row in trajectory['rows'][::step]:
  local=row['local_cm']
  if local is None or abs(local[0])>100 or not -50<local[1]<150:continue
  scene.frame_set(row['frame']+1);depsgraph=bpy.context.evaluated_depsgraph_get();samples+=1
  for name in ('Hips','Spine2'):
   bone=next((b for b in rig.pose.bones if b.name.endswith(name)),None)
   if bone:key=row['action']+'_'+name+'_forward_cm';posture[key]=max(posture.get(key,-99),round(-(rig.matrix_world@bone.head).y*100,1))
  head=next((b for b in rig.pose.bones if b.name.endswith('Head')),None)
  for bone in (b for b in rig.pose.bones if b.name.endswith(('Spine','Spine1','Spine2','Neck','Head'))):
   key=row['action']+'_'+bone.name.split(':')[-1]+'_max_pitch_deg';posture[key]=max(posture.get(key,-99),round(head_pitch(rig,bone),1))
  center=np.array([local[0]/100,-local[1]/100,local[2]/100]);angle=math.radians(row['box_yaw']-row['yaw']);c,s=math.cos(angle),math.sin(angle)
  for obj in meshes:
   evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
   try:
    if len(mesh.vertices)!=len(masks[obj.name]):continue
    co=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',co);co=co.reshape(-1,3)[masks[obj.name]]
    matrix=np.array(obj.matrix_world);co=co@matrix[:3,:3].T+matrix[:3,3]-center
    # Blender yaw about Z is the negated route yaw delta.
    x=co[:,0]*c-co[:,1]*s;y=co[:,0]*s+co[:,1]*c;inside=np.minimum.reduce([half[0]-np.abs(x),half[1]-np.abs(y),half[2]-np.abs(co[:,2])])
    if not len(inside):continue
    deepest=int(inside.argmax());depth=float(inside[deepest])*100;by_action[row['action']]=max(by_action.get(row['action'],-99),depth)
    # Box-local point from the box centre: x lateral, +y toward the carrier, +z up.
    if depth>worst['depth_cm']:
     vertex=obj.data.vertices[int(np.nonzero(masks[obj.name])[0][deepest])];group=max(vertex.groups,key=lambda g:g.weight).group if vertex.groups else None
     worst={'depth_cm':depth,'frame':row['frame'],'object':obj.name,'action':row['action'],'bone_group':obj.vertex_groups[group].name if group is not None else None,'box_local_cm':[round(float(x[deepest])*100,1),round(float(y[deepest])*100,1),round(float(co[deepest,2])*100,1)]}
   finally:evaluated.to_mesh_clear()
 return {'ok':worst['depth_cm']<=limit,'limit_cm':limit,'samples':samples,'deepest':worst,'by_action_cm':by_action,'posture_max_forward_cm':posture,'scope':'Evaluated skinned body vertices (hands/forearms excluded) against the box volume every '+str(step)+' frames'}
