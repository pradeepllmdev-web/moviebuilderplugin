"""Drinking from a cup on a low table, seated: the cup stays put, a hand rests beside it and the lion nods
until the muzzle meets the rim.

Why not lift the cup: on the lion the snout is ~52 cm ahead of the head pivot and the arm reaches ~48 cm, so a
hand cannot bring a cup to the mouth. The layout is solved from measurements (pure Python, see feasibility);
the Blender part nods Neck/Head and reaches the right arm with an envelope over each drink beat."""
import math
CUP=dict(radius_cm=4.,height_cm=9.)
TABLE=dict(width_cm=80.,depth_cm=70.,thickness_cm=4.)
NECK_SHARE=.5  # nod split: Neck takes this share, Head the rest
def rotate(point,pivot,degrees):
 """Nod down by degrees about the sideways axis through pivot (points ahead, at -y, drop)."""
 a=math.radians(degrees);y,z=point[1]-pivot[1],point[2]-pivot[2]
 return [point[0],pivot[1]+y*math.cos(a)-z*math.sin(a),pivot[2]+y*math.sin(a)+z*math.cos(a)]
def nodded_tip(m,nod):
 b=m['bones'];first=nod*NECK_SHARE;second=nod-first;head_pivot=rotate(b['Head'],b['Neck'],first)
 return rotate(rotate(m['snout_tip'],b['Neck'],first),head_pivot,second)
def layout(m,nod):
 """Cup, table and hand target for a nod angle."""
 tip=nodded_tip(m,nod);cup=[tip[0],tip[1]+CUP['radius_cm'],tip[2]-CUP['height_cm']/2]  # muzzle over the far rim
 top=cup[2]-CUP['height_cm']/2
 near=min(m[k]['y_front'] for k in ('torso','thighs','lower_legs'))-4
 table=dict(top_cm=round(top,1),center=[round(cup[0],1),round(near-TABLE['depth_cm']/2,1)],size_cm=[TABLE['width_cm'],TABLE['depth_cm']],thickness_cm=TABLE['thickness_cm'],near_edge_y=round(near,1))
 shoulder=m['bones']['RightArm'];want=[cup[0]-7,cup[1]+5,top+3]
 gap=math.dist(shoulder,want)-m['arm_reach']*.98
 if gap>0:  # out of reach: the hand rests as far toward it as the arm goes
  k=(m['arm_reach']*.98)/math.dist(shoulder,want);want=[s+(w-s)*k for s,w in zip(shoulder,want)]
 return dict(nod_deg=nod,tip_hold=[round(v,1) for v in tip],cup_cm=[round(v,1) for v in cup],table=table,hand_target=[round(v,1) for v in want],
  hand_to_cup_cm=round(max(0,math.hypot(want[0]-cup[0],want[1]-cup[1])-CUP['radius_cm']),1),reach_shortfall_cm=round(max(0,gap),1))
def feasibility(m,preferred_nod=25,nod_range=(10,45)):
 """Pick the nod nearest the preferred one whose layout works: table top between the feet and the shoulder,
 hand beside the cup (within 6 cm of its side) with the arm reaching it."""
 best=None
 for nod in range(nod_range[0],nod_range[1]+1,1):
  l=layout(m,nod);top=l['table']['top_cm']
  l['ok']=m['feet']['z_top']+4<=top<=m['bones']['RightArm'][2]-2 and l['hand_to_cup_cm']<=6 and l['reach_shortfall_cm']==0
  if l['ok'] and (best is None or abs(nod-preferred_nod)<abs(best['nod_deg']-preferred_nod)):best=l
 if best is None:return dict(layout(m,preferred_nod),ok=False,reason='no nod gives a table below the shoulder with the hand beside the cup')
 best['limits']='table top between feet+4 and shoulder-2, hand within 6 cm of the cup side, arm reaches'
 return best
def envelope(seconds,duration,ramp=1.1):
 """0..1 over a beat: dip in, hold, sit back."""
 u=max(0.,min(seconds/ramp,(duration-seconds)/ramp,1.));return u*u*(3-2*u)
def apply(scene,rig,body,timeline,fps,plan,folder,reference_frame):
 """Pose Neck/Head and the right arm over every drink beat; plan is a layout() result. Writes drink.json and drink-check.json."""
 import json,bpy
 import numpy as np
 from mathutils import Quaternion,Vector
 from box_hands import solve_arm
 beats=[g for g in timeline if g['action']=='drink']
 if not beats:return None
 b={n:next(x for x in rig.pose.bones if x.name.endswith(n)) for n in ('Neck','Head','RightHand')}
 def nod_bone(bone,degrees):
  matrix=rig.matrix_world.inverted()@Quaternion((1,0,0),math.radians(degrees)).to_matrix().to_4x4()@rig.matrix_world@bone.matrix;matrix.translation=bone.head;bone.matrix=matrix
 target=bpy.data.objects.new('Drink hand target',None);scene.collection.objects.link(target);target.location=[v/100 for v in plan['hand_target']]
 hand=b['RightHand'];fore=hand.parent;upper=fore.parent;hold=[]
 # The seated idle clip drifts (head and chest sway by ~15 cm), but cup and table are fixed in space: during a drink
 # beat the body eases to its pose at reference_frame (where the layout was measured) and back.
 scene.frame_set(reference_frame);bpy.context.view_layer.update();frozen={bone.name:(bone.location.copy(),bone.rotation_quaternion.copy()) for bone in rig.pose.bones}
 for g in beats:
  first,last=round(g['start']*fps)+1,round(g['end']*fps)
  for frame in range(first,last+1):
   w=envelope((frame-first)/fps,g['end']-g['start']);scene.frame_set(frame);bpy.context.view_layer.update()
   for bone in rig.pose.bones:
    location,rotation=frozen[bone.name];bone.location=bone.location.lerp(location,w);bone.rotation_quaternion=bone.rotation_quaternion.slerp(rotation,w)
    bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame)
   bpy.context.view_layer.update()
   bob=1.5*math.sin(2*math.pi*(frame-first)/fps/1.8)*w
   oldu,oldf=upper.rotation_quaternion.copy(),fore.rotation_quaternion.copy()
   solve_arm(rig,hand,target.location,1,Vector((-.9,.1,1.0)))
   upper.rotation_quaternion=oldu.slerp(upper.rotation_quaternion,w);fore.rotation_quaternion=oldf.slerp(fore.rotation_quaternion,w)
   upper.keyframe_insert('rotation_quaternion',frame=frame);fore.keyframe_insert('rotation_quaternion',frame=frame);bpy.context.view_layer.update()
   nod_bone(b['Neck'],plan['nod_deg']*NECK_SHARE*w+bob);bpy.context.view_layer.update();nod_bone(b['Head'],plan['nod_deg']*(1-NECK_SHARE)*w)
   for bone in (b['Neck'],b['Head']):bone.keyframe_insert('rotation_quaternion',frame=frame)
   if w>.99 and (frame-first)%6==0:hold.append(frame)
 # Check: muzzle to rim and hand to target over the held frames.
 names={g.index:g.name.split(':')[-1] for g in body.vertex_groups};mask=np.array([bool(v.groups) and names[max(v.groups,key=lambda x:x.weight).group].endswith(('Head','headfront')) for v in body.data.vertices])
 rim=np.array([plan['cup_cm'][0],plan['cup_cm'][1]-CUP['radius_cm'],plan['cup_cm'][2]+CUP['height_cm']/2]);tip_gaps=[];hand_gaps=[]
 for frame in hold:
  scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();e=body.evaluated_get(deps);co=np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',co);W=np.array(e.matrix_world);P=(co.reshape(-1,3)@W[:3,:3].T+W[:3,3])*100
  q=P[mask];tip=q[q[:,1].argmin()];tip_gaps.append(float(np.linalg.norm(tip-rim)));hand_gaps.append(float(np.linalg.norm(np.array(rig.matrix_world@hand.head)*100-np.array(plan['hand_target']))))
 clearance=slab_clearance(scene,rig,body,plan,hold)
 (folder/'drink.json').write_text(json.dumps(dict(cup_cm=plan['cup_cm'],table=plan['table'],cup=CUP)))
 report=dict(ok=bool(hold) and max(tip_gaps)<6 and clearance<1.5,held_samples=len(hold),muzzle_to_rim_cm=round(max(tip_gaps),1) if hold else None,hand_to_target_cm=round(max(hand_gaps),1) if hold else None,nod_deg=plan['nod_deg'],table_top_cm=plan['table']['top_cm'],hand_to_cup_cm=plan['hand_to_cup_cm'],body_in_table_cm=clearance,scope='Cup stays on the table; muzzle dips to the rim, hand rests beside it')
 (folder/'drink-check.json').write_text(json.dumps(report));return report
def slab_clearance(scene,rig,body,plan,frames):
 """Deepest body vertex (hands and forearms excluded: they rest on the table) inside the table slab, cm."""
 import bpy,numpy as np
 names={g.index:g.name.split(':')[-1] for g in body.vertex_groups};skip=np.array([bool(v.groups) and any(k in names[max(v.groups,key=lambda x:x.weight).group] for k in ('Hand','ForeArm','Thumb','Index','Middle','Ring','Pinky')) for v in body.data.vertices])
 t=plan['table'];cx,cy=t['center'];hw,hd=t['size_cm'][0]/2,t['size_cm'][1]/2;top=t['top_cm'];low=top-t['thickness_cm'];worst=0.
 for frame in frames:
  scene.frame_set(frame);e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());co=np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',co);W=np.array(e.matrix_world);P=((co.reshape(-1,3)@W[:3,:3].T+W[:3,3])*100)[~skip]
  inside=np.minimum.reduce([hw-abs(P[:,0]-cx),hd-abs(P[:,1]-cy),top-P[:,2],P[:,2]-low]);worst=max(worst,float(inside.max()))
 return round(max(0.,worst),1)
