"""Prop-contact and two-character activities, all solved from the evaluated body (no per-character numbers):

  pick_up       cup on a crate: the clip's hand goes down, the cup rests there until grasped, then follows the palm
  open_door     hinged door that follows the hand that reaches out (hinge placed to fit the hand path)
  carry_walk    walk with a cup in one hand held at the hip (arm IK over the walk)
  climb_stairs  walk up three steps (root rises with the stairs; check reports feet vs step surface)
  handshake     two actors, right hands meet at the midpoint
  hug           two actors, arms around each other's sides

Contact checks write <activity>-check.json next to the build; two-actor ones also write contact-track.json so
pair_check() can compare both actors' hands without Blender. World convention: yaw 0 faces +Y, positive yaw turns
toward -X; the rig faces -Y at the origin (forward = -rig_y, right = -rig_x)."""
import json,math
CUP=dict(radius_cm=4.,height_cm=9.)
STEP=dict(rise_cm=10.,tread_cm=30.,first_cm=40.,count=3)
CONTACT=('handshake','hug')
REACH_LIMIT_CM={'handshake':72,'hug':46}   # largest actor spacing the lion's arms can close; shorter-armed bodies need less
def stairs_height(travelled_cm):
 """Smooth three-step profile (cm) over distance walked from the foot of the stairs."""
 h=0.
 for k in range(STEP['count']):
  u=max(0.,min(1.,(travelled_cm-(STEP['first_cm']+k*STEP['tread_cm']))/12.));h+=STEP['rise_cm']*u*u*(3-2*u)
 return h
def feasibility(measures):return {'ok':True,'note':'solved from the evaluated body at build time'}
def facing(a,b):
 """Yaw (deg) that turns an actor at a to face b (same convention as scene_gaze)."""
 return math.degrees(math.atan2(-(b[0]-a[0]),b[1]-a[1]))
def pair_inputs(actors,index,heights):
 """Extra plan fields for a two-actor contact beat: partner info and the automatic facing."""
 if len(actors)!=2 or not any(g['action'] in CONTACT for g in actors[index]['segments']):return {}
 me,other=actors[index],actors[1-index];a=me.get('position_cm',[0,0]);b=other.get('position_cm',[0,0])
 action=next(g['action'] for g in me['segments'] if g['action'] in CONTACT);spacing=math.dist(a,b)
 if spacing>REACH_LIMIT_CM[action] or spacing<25:raise ValueError(f'{action} needs the actors {25}..{REACH_LIMIT_CM[action]} cm apart (now {spacing:.0f})')
 if [g['action'] for g in me['segments']]!=[g['action'] for g in other['segments']]:raise ValueError(f'Both actors need the same {action} beat at the same time')
 return {'partner_contact':dict(position_cm=b,height_cm=heights[other['character']],own_height_cm=heights[me['character']]),'facing_yaw_deg':me.get('facing_yaw_deg',facing(a,b))}
def to_rig(point_world,root,yaw):
 """World cm (x,y,z) -> rig-space metres for an actor at root facing yaw."""
 f=(-math.sin(math.radians(yaw)),math.cos(math.radians(yaw)));r=(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)))
 dx,dy=point_world[0]-root[0],point_world[1]-root[1]
 return (-(dx*r[0]+dy*r[1])/100,-(dx*f[0]+dy*f[1])/100,point_world[2]/100)
def to_world(rig_cm,root,yaw):
 """Rig-space cm -> world cm."""
 f=(-math.sin(math.radians(yaw)),math.cos(math.radians(yaw)));r=(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)))
 forward,right=-rig_cm[1],-rig_cm[0]
 return (root[0]+forward*f[0]+right*r[0],root[1]+forward*f[1]+right*r[1],rig_cm[2])
def envelope(seconds,duration,ramp=.8):
 u=max(0.,min(seconds/ramp,(duration-seconds)/ramp,1.));return u*u*(3-2*u)

class Context:
 """Shared Blender handles for one build."""
 def __init__(self,scene,rig,body,timeline,fps,folder,plan,route):
  import bpy,numpy as np
  self.bpy,self.np,self.scene,self.rig,self.body,self.timeline,self.fps,self.folder,self.plan,self.route=bpy,np,scene,rig,body,timeline,fps,folder,plan,route
  self.hands={side:next(b for b in rig.pose.bones if b.name.endswith(side+'Hand')) for side in ('Left','Right')}
  names={g.index:g.name.split(':')[-1] for g in body.vertex_groups}
  self.skip=np.array([bool(v.groups) and any(k in names[max(v.groups,key=lambda x:x.weight).group] for k in ('Hand','ForeArm','Thumb','Index','Middle','Ring','Pinky')) for v in body.data.vertices])
 def beat(self,action):return next((g for g in self.timeline if g['action']==action),None)
 def frames(self,g,step=1):return list(range(round(g['start']*self.fps)+1,round(g['end']*self.fps)+1,step))
 def at(self,frame):
  self.scene.frame_set(frame);self.bpy.context.view_layer.update()
 def palm(self,side,frame=None):
  """Palm centre (cm, rig space)."""
  if frame:self.at(frame)
  b=self.hands[side];return self.np.array(self.rig.matrix_world@(b.head+(b.tail-b.head)*.5))*100
 def body_points(self):
  e=self.body.evaluated_get(self.bpy.context.evaluated_depsgraph_get());co=self.np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',co);W=self.np.array(e.matrix_world)
  return ((co.reshape(-1,3)@W[:3,:3].T+W[:3,3])*100)[~self.skip]
 def box(self,name,size_cm,color,location_cm=(0,0,0)):
  self.bpy.ops.mesh.primitive_cube_add(size=1);o=self.bpy.context.object;o.name=name;o.scale=[v/100 for v in size_cm];o.location=[v/100 for v in location_cm]
  m=self.bpy.data.materials.new(name);m.diffuse_color=color;o.data.materials.append(m);return o
 def cup(self,name='Cup'):
  self.bpy.ops.mesh.primitive_cylinder_add(radius=CUP['radius_cm']/100,depth=CUP['height_cm']/100);o=self.bpy.context.object;o.name=name
  m=self.bpy.data.materials.new(name);m.diffuse_color=(.8,.25,.2,1);o.data.materials.append(m);return o
 def key(self,obj,frame,location_cm,rotation=None):
  obj.location=[v/100 for v in location_cm];obj.keyframe_insert('location',frame=frame)
  if rotation is not None:obj.rotation_euler=rotation;obj.keyframe_insert('rotation_euler',frame=frame)
 def reach(self,arms,frames,weight_at,freeze=False):
  """Arm IK for one or two arms in a single pass. arms = [(side, target_at(frame)->rig metres, pole)]; eased by weight_at(frame).
  With freeze the body holds its pose at the first frame (the idle sway would twist the solved forearm). Returns the worst wrist error (cm) over fully weighted frames."""
  from box_hands import solve_arm
  from mathutils import Vector
  errors=[];previous={};frozen=None
  if freeze:
   self.at(frames[0]);frozen={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in self.rig.pose.bones}
  for frame in frames:
   self.at(frame);w=weight_at(frame)
   if frozen:
    for b in self.rig.pose.bones:
     loc,rot=frozen[b.name]
     if rot.dot(b.rotation_quaternion)<0:rot=rot.copy();rot.negate()
     b.location=b.location.lerp(loc,w);b.rotation_quaternion=b.rotation_quaternion.slerp(rot,w)
    self.bpy.context.view_layer.update()
   solved=[]
   for side,target_at,pole in arms:
    hand=self.hands[side];fore=hand.parent;upper=fore.parent;ou,of=upper.rotation_quaternion.copy(),fore.rotation_quaternion.copy();target=Vector(target_at(frame))
    solve_arm(self.rig,hand,target,1,Vector(pole))
    nu,nf=upper.rotation_quaternion.copy(),fore.rotation_quaternion.copy()
    if nu.dot(ou)<0:nu.negate()
    if nf.dot(of)<0:nf.negate()
    upper.rotation_quaternion=ou.slerp(nu,w);fore.rotation_quaternion=of.slerp(nf,w)
    for q,key in ((upper,'u'),(fore,'f')):
     p=previous.get((side,key))
     if p is not None and q.rotation_quaternion.dot(p)<0:q.rotation_quaternion.negate()
     previous[(side,key)]=q.rotation_quaternion.copy()
    self.bpy.context.view_layer.update();solved.append((hand,upper,fore,target))
   for hand,upper,fore,target in solved:
    if w>.99:errors.append(float((self.rig.matrix_world@hand.head-target).length*100))
   for b in (self.rig.pose.bones if frozen else [x for h,u,f,t in solved for x in (u,f)]):
    if frozen:b.keyframe_insert('location',frame=frame)
    b.keyframe_insert('rotation_quaternion',frame=frame)
  return max(errors) if errors else None
 def slab_depth(self,centre_xy,size_xy,z_low,z_high,frames):
  """Deepest body vertex (hands and forearms excluded) inside an axis-aligned slab, cm."""
  worst=0.
  for f in frames:
   self.at(f);P=self.body_points();inside=self.np.minimum.reduce([size_xy[0]/2-abs(P[:,0]-centre_xy[0]),size_xy[1]/2-abs(P[:,1]-centre_xy[1]),z_high-P[:,2],P[:,2]-z_low]);worst=max(worst,float(inside.max()))
  return round(max(0.,worst),1)
 def write(self,name,report):
  (self.folder/name).write_text(json.dumps(report,default=lambda o:o.item() if hasattr(o,'item') else str(o)));return report

def apply_pick_up(c):
 """Pick a cup from a side table: the right arm reaches it (arm IK), the cup follows the palm from the grasp, then it is lifted to the chest and held."""
 g=c.beat('pick_up');frames=c.frames(g);side='Right';np=c.np;length=g['end']-g['start']
 c.at(frames[0]);arm=next(b for b in c.rig.pose.bones if b.name.endswith('RightArm'));hips=next(b for b in c.rig.pose.bones if b.name.endswith('Hips'))
 shoulder=np.array(c.rig.matrix_world@arm.head);h0=np.array(c.rig.matrix_world@hips.head)
 top=float(shoulder[2]*100-33);cup_rest=np.array([shoulder[0]*100-12,shoulder[1]*100-22,top+CUP['height_cm']/2])   # front-right of the shoulder, clear of the hanging arm and the belly
 hold=np.array([shoulder[0]*100-4,shoulder[1]*100-24,shoulder[2]*100-18])
 table=c.box('SideTable',(16,16,top),(.45,.3,.15,1),(cup_rest[0],cup_rest[1],top/2));cup=c.cup()
 reach_end,grasp_end,lift_end=.30,.42,.75
 def target(f):
  u=(f-frames[0])/c.fps/length
  if u<=reach_end:p=cup_rest
  elif u<=grasp_end:p=cup_rest
  elif u<=lift_end:
   k=(u-grasp_end)/(lift_end-grasp_end);k=k*k*(3-2*k);p=cup_rest+(hold-cup_rest)*k
  else:p=hold
  return tuple(p/100)
 weight=lambda f:envelope((f-frames[0])/c.fps,length,.9)
 error=c.reach([(side,target,(-.9,.1,1.0))],frames,weight,freeze=True);grasp=frames[0]+round(grasp_end*length*c.fps)
 for f in range(1,c.scene.frame_end+1):
  if f<grasp:c.key(cup,f,tuple(cup_rest))
  else:c.key(cup,f,tuple(c.palm(side,f)))
 lifted=max(c.palm(side,f)[2] for f in range(grasp,c.scene.frame_end+1))-cup_rest[2]
 c.at(grasp);grasp_gap=float(np.linalg.norm(c.palm(side,grasp)-cup_rest))
 depth=c.slab_depth((cup_rest[0],cup_rest[1]),(16,16),0,top,frames[::3])
 return c.write('pick-up-check.json',dict(ok=error is not None and error<4 and lifted>=10 and depth<=2 and grasp_gap<=6,hand=side,table_top_cm=round(top,1),hand_to_target_cm=None if error is None else round(error,1),palm_to_cup_at_grasp_cm=round(grasp_gap,1),lifted_cm=round(float(lifted),1),body_in_table_cm=depth,scope='Cup on a side table; arm IK reaches, grasps, lifts to the chest and holds'))
def apply_open_door(c):
 import numpy as np
 g=c.beat('open_door');frames=c.frames(g)
 reach={s:min((c.palm(s,f)[1],f) for f in frames) for s in c.hands};side=min(reach,key=lambda s:reach[s][0]);r=reach[side][1]
 handle=c.palm(side,r);path=[c.palm(side,f) for f in frames if f>=r]
 best=None
 for sign in (1,-1):
  for L in range(30,141,10):
   hinge=np.array([handle[0]+sign*L,handle[1]]);v0=np.array(handle[:2])-hinge;gaps=[];angles=[]
   for p in path:
    v=np.array(p[:2])-hinge;a=math.atan2(v[1],v[0])-math.atan2(v0[1],v0[0]);a=(a+math.pi)%(2*math.pi)-math.pi;angles.append(a)
    gaps.append(abs(np.linalg.norm(v)-L))
   if best is None or max(gaps)<best[0]:best=(max(gaps),sign,L,angles)
 gap,sign,L,angles=best;hinge=(handle[0]+sign*L,handle[1],0.)
 pivot=c.bpy.data.objects.new('DoorHinge',None);c.scene.collection.objects.link(pivot);pivot.location=[v/100 for v in hinge]
 width=L+12;centre_dir=-sign   # the panel extends from the hinge past the handle
 door=c.box('Door',(width,4,200),(.35,.2,.1,1),(centre_dir*width/2,0,100));door.parent=pivot;door.location=[centre_dir*width/200,0,1.0];door.matrix_parent_inverse=pivot.matrix_world.inverted()
 for f in range(1,c.scene.frame_end+1):
  a=0. if f<r else angles[min(f-r,len(angles)-1)];pivot.rotation_euler=(0,0,a);pivot.keyframe_insert('rotation_euler',frame=f)
 depth=0.
 swing=math.degrees(max(abs(a) for a in angles))
 return c.write('door-check.json',dict(ok=gap<=8 and swing>=15,hand=side,hinge_distance_cm=L,handle_to_hand_cm=round(float(gap),1),swing_deg=round(swing,1),scope='Door hinge fitted to the hand path; handle follows the hand within the reported gap'))
def apply_carry_walk(c):
 g=c.beat('carry_walk');frames=c.frames(g);side='Right';hips=next(b for b in c.rig.pose.bones if b.name.endswith('Hips'))
 def target(f):
  c.at(f);h=c.np.array(c.rig.matrix_world@hips.head);return (h[0]-.26,h[1]-.24,h[2]+.03)
 weight=lambda f:envelope((f-frames[0])/c.fps,g['end']-g['start'],.6)
 error=c.reach([(side,target,(-.9,.1,1.0))],frames,weight);cup=c.cup()
 for f in range(1,c.scene.frame_end+1):c.key(cup,f,tuple(c.palm(side,f)))
 depth=0.
 for f in frames[::6]:
  c.at(f);P=c.body_points();centre=c.palm(side,f);d=c.np.linalg.norm(P-centre,axis=1).min();depth=max(depth,CUP['radius_cm']-float(d))
 return c.write('carry-walk-check.json',dict(ok=error is not None and error<4 and depth<=2,hand=side,hand_to_target_cm=None if error is None else round(error,1),cup_in_body_cm=round(max(0.,depth),1),scope='Cup held at the hip by arm IK for the whole walk'))
def apply_stairs(c):
 g=c.beat('climb_stairs');frames=c.frames(g,2);feet=[b for b in c.rig.pose.bones if b.name.endswith(('LeftFoot','RightFoot'))]
 sink=1e9;floating=-1e9;start_y=g['start_y']
 for f in frames:
  c.at(f);row=c.route[f-1];z0=row['location_cm'][2];ry=row['location_cm'][1];frame_low=1e9
  for b in feet:
   p=c.np.array(c.rig.matrix_world@b.head)*100;surface=stairs_height(ry+(-p[1])-start_y);clearance=p[2]+z0-surface-5   # 5 cm: ankle bone above the sole
   frame_low=min(frame_low,clearance);sink=min(sink,clearance)
  floating=max(floating,frame_low);frame_low=1e9
 (c.folder/'stairs.json').write_text(json.dumps(dict(step=STEP,start_y_cm=start_y)))
 return c.write('stairs-check.json',dict(ok=sink>=-4 and floating<=10,lowest_foot_clearance_cm=round(sink,1),lowest_foot_float_cm=round(floating,1),scope='Root rises with the steps; feet checked against the step surface (stance feet are not IK-planted)'))
def apply_pair(c):
 plan=c.plan;partner=plan['partner_contact'];g=next(x for x in c.timeline if x['action'] in CONTACT);frames=c.frames(g);action=g['action']
 own=plan.get('actor_position_cm',[0,0]);mid=[(own[0]+partner['position_cm'][0])/2,(own[1]+partner['position_cm'][1])/2]
 height=min(partner['height_cm'],partner['own_height_cm'])*.55
 def root(f):
  r=c.route[f-1];return (own[0]+r['location_cm'][0],own[1]+r['location_cm'][1]),r['yaw']
 weight=lambda f:envelope((f-frames[0])/c.fps,g['end']-g['start'],.8);track=[];errors=[]
 if action=='handshake':
  sides={'Right':lambda f:(mid[0],mid[1],height)}
  pole={'Right':(-.9,.1,1.0)}
 else:
  u=(partner['position_cm'][0]-own[0],partner['position_cm'][1]-own[1]);n=math.hypot(*u);u=(u[0]/n,u[1]/n);r=(u[1],-u[0])   # right-hand side of the actor facing the partner
  sides={'Right':lambda f:(partner['position_cm'][0]+r[0]*26,partner['position_cm'][1]+r[1]*26,height),'Left':lambda f:(partner['position_cm'][0]-r[0]*26,partner['position_cm'][1]-r[1]*26,height)}
  pole={'Right':(-.9,.1,1.0),'Left':(.9,.1,1.0)}
 arms=[]
 for side,world_target in sides.items():
  def rig_target(f,wt=world_target):
   rt,yaw=root(f);return to_rig(wt(f),rt,yaw)
  arms.append((side,rig_target,pole[side]))
 errors.append(c.reach(arms,frames,weight,freeze=True))
 for f in frames:
  rt,yaw=root(f);track.append(dict(frame=f,weight=weight(f),**{s.lower()+'_palm_world':list(to_world(tuple(c.palm(s,f)),rt,yaw)) for s in sides},**{s.lower()+'_wrist_world':list(to_world(tuple(c.np.array(c.rig.matrix_world@c.hands[s].head)*100),rt,yaw)) for s in sides},**{s.lower()+'_target_world':list(sides[s](f)) for s in sides}))
 (c.folder/'contact-track.json').write_text(json.dumps(dict(action=action,own_position_cm=own,partner_position_cm=partner['position_cm'],track=track),default=lambda o:o.item() if hasattr(o,'item') else str(o)))
 worst=max((e for e in errors if e is not None),default=None)
 return c.write(action+'-check.json',dict(ok=worst is not None and worst<5,hand_to_target_cm=None if worst is None else round(worst,1),spacing_cm=round(math.dist(own,partner['position_cm']),1),scope='Each actor reaches the shared contact point; pair_check compares both actors'))
def pair_check(folder_a,folder_b):
 """Compare two actors' contact tracks: handshake palms together, hug palms on the partner's sides."""
 a,b=[json.loads((f/'contact-track.json').read_text()) for f in (folder_a,folder_b)]
 if a['action']!=b['action']:return dict(ok=False,reason='different contact actions')
 gaps=[]
 for ra,rb in zip(a['track'],b['track']):
  if min(ra['weight'],rb['weight'])<.99:continue
  if a['action']=='handshake':gaps.append(math.dist(ra['right_wrist_world'],rb['right_wrist_world']))   # wrists meet; palms then overlap
  else:
   gaps+=[math.dist(ra['right_palm_world'],rb['left_palm_world']) if False else 0.]
 if a['action']=='hug':
  best=[]
  for ra,rb in zip(a['track'],b['track']):
   if min(ra['weight'],rb['weight'])<.99:continue
   best.append(max(math.dist(ra[s+'_palm_world'][:2],ra[s+'_target_world'][:2]) for s in ('right','left')))
  gaps=best
 if not gaps:return dict(ok=False,reason='no held frames')
 limit=6 if a['action']=='handshake' else 8
 return dict(ok=max(gaps)<=limit,action=a['action'],worst_gap_cm=round(max(gaps),1),limit_cm=limit,held_samples=len(gaps))
def apply_all(scene,rig,body,timeline,fps,folder,plan,route):
 """Run whichever contact activities this shot contains."""
 c=Context(scene,rig,body,timeline,fps,folder,plan,route);out={}
 for action,fn in (('pick_up',apply_pick_up),('open_door',apply_open_door),('carry_walk',apply_carry_walk),('climb_stairs',apply_stairs)):
  if c.beat(action):out[action]=fn(c)
 if plan.get('partner_contact') and any(g['action'] in CONTACT for g in timeline):out['pair']=apply_pair(c)
 return out
