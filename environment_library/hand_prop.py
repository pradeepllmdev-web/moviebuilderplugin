"""Isolated lion palm-anchor audition; no simulated grasp or finger solver."""
import bpy,math
from mathutils import Vector
def hold_ball(scene,rig,frames):
 hand=next(b for b in rig.pose.bones if b.name.endswith('RightHand'));fore=next(b for b in rig.pose.bones if b.name.endswith('RightForeArm'))
 target=bpy.data.objects.new('Ball hold wrist target',None);scene.collection.objects.link(target);target.location=Vector((-.45,-.25,1.0))
 pole=bpy.data.objects.new('Ball hold elbow pole',None);scene.collection.objects.link(pole);pole.location=(-.9,.1,.95)
 ik=fore.constraints.new('IK');ik.target=target;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
 scene.frame_set(1);best=None
 for angle in [0,math.pi/2,-math.pi/2,math.pi]:
  ik.pole_angle=angle;bpy.context.view_layer.update();score=-(rig.matrix_world@fore.head).x
  if best is None or score>best[0]:best=(score,angle)
 ik.pole_angle=best[1]
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.nla.bake(frame_start=1,frame_end=frames,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=True,bake_types={'POSE'})
 scene.frame_set(1);bpy.context.view_layer.update()
 # Calibrate against the evaluated hand surface locally, not the imported bone tail.
 unit=abs(rig.matrix_world.to_scale().z)
 from prop_units import world_length_to_local
 points=[];deps=bpy.context.evaluated_depsgraph_get()
 for obj in scene.objects:
  if obj.type!='MESH' or not any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers):continue
  group=obj.vertex_groups.get(hand.name)
  if not group:continue
  evaluated=obj.evaluated_get(deps)
  if len(evaluated.data.vertices)!=len(obj.data.vertices):continue
  for vertex in obj.data.vertices:
   if any(g.group==group.index and g.weight>.7 for g in vertex.groups):points.append(evaluated.matrix_world@evaluated.data.vertices[vertex.index].co)
 if len(points)<20:raise RuntimeError('Insufficient hand-skin samples for palm calibration')
 palm=sum(points,Vector())/len(points);torso=rig.matrix_world@next(b for b in rig.pose.bones if b.name.endswith('Spine2')).head;outward=palm-torso;outward.z=0
 if outward.length<.01:outward=rig.matrix_world.to_quaternion()@Vector((0,-1,0))
 outward.normalize();extent=max((point-palm).dot(outward) for point in points)
 if not 0<extent<.3:raise RuntimeError('Hand surface calibration exceeds supported size')
 desired=palm+outward*(extent+.045);offset=hand.matrix.inverted()@(rig.matrix_world.inverted()@desired);rest=rig.data.bones[hand.name];center=rest.head_local+rest.matrix_local.to_quaternion()@offset
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=world_length_to_local(.05,unit),location=center);ball=bpy.context.object;ball.name='Palm test ball';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ball.parent=rig;ball.matrix_world=rig.matrix_world
 group=ball.vertex_groups.new(name=hand.name);group.add(list(range(len(ball.data.vertices))),1,'REPLACE');modifier=ball.modifiers.new('Palm skin attachment','ARMATURE');modifier.object=rig
 marker=ball.data.attributes.new('prop_anchor_qa','INT','POINT')
 for value in marker.data:value.value=1
 material=bpy.data.materials.new('Palm test blue');material.diffuse_color=(.025,.15,.8,1);material.use_nodes=True;material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.025,.15,.8,1);ball.data.materials.append(material)
 error=0
 for frame in range(1,frames+1):
  scene.frame_set(frame);bpy.context.view_layer.update();evaluated=ball.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=sum((evaluated.matrix_world@v.co for v in evaluated.data.vertices),Vector())/len(evaluated.data.vertices);expected=rig.matrix_world@(hand.matrix@offset);error=max(error,(actual-expected).length*100)
 return {'ok':error<.5,'maximum_anchor_error_cm':error,'hand':hand.name,'palm_offset_local':list(offset),'palm_offset_m':list(offset*unit),'radius_cm':5,'rig_metres_per_unit':unit,'hand_surface_extent_cm':extent*100,'hand_samples':len(points),'scope':'Stationary lion surface-calibrated palm-anchor test; finger contact still needs review. No pickup, release or physical grasp.'}

def verify_joined_anchor(scene,rig,mesh,offset,frames):
 hand=next(b for b in rig.pose.bones if b.name.endswith('RightHand'));marker=mesh.data.attributes.get('prop_anchor_qa')
 if not marker:raise RuntimeError('Prop identity metadata lost in mesh join')
 ids=[i for i,value in enumerate(marker.data) if value.value==1];error=0
 if not ids:raise RuntimeError('Prop vertices missing in joined mesh')
 for frame in range(1,frames+1):
  scene.frame_set(frame);bpy.context.view_layer.update();evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=sum((evaluated.matrix_world@evaluated.data.vertices[i].co for i in ids),Vector())/len(ids);expected=rig.matrix_world@(hand.matrix@Vector(offset));error=max(error,(actual-expected).length*100)
 return error
