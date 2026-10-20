"""Blender script: build the walking clips the library lacked (the lion only had a run cycle and a very slow climb), one per gait, as leo_<gait>.blend actions in scenes/ship_assets.

blender -b --python build_walk_clips.py -- <ship_assets_dir> [gait ...]       (gait names come from gaits.GAITS; default all)

Technique: EVERY FOOT PLANTED BY CONSTRUCTION. Each ankle follows a stance line that moves backwards at exactly the gait's ground speed (stance fraction d of the cycle) and a swing arc with a lift; the hips bob and sway, the pelvis yaws against the
chest, the arms swing against the legs, the spine leans by the gait's lean. The pose is made with IK constraints (legs and arms) and copy-rotation constraints (pelvis, spine, head, feet kept flat with a toe-off pitch) driven by keyed
empties and baked to one action with visual keying, so the clip plays on the ordinary NLA like the other clips. After baking, the evaluated ankles are compared to their targets: a leg that cannot reach (the foot would slide) is reported as AUDIT and
the gait table gaits.py is the single place the numbers live. Output: leo_<gait>.blend (action leo_<gait>) and gait_report.json (measured planted-foot speed, reach error, hips height range)."""
import bpy,math,sys,os,json
from mathutils import Vector,Matrix,Euler
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gaits as G
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ASSETS=args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)),'scenes','ship_assets')
WANT=args[1:] or [g for g in G.GAITS if G.GAITS[g]['kind']=='built']
PI=math.pi
def load_rig():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (s,d):d.objects=[n for n in s.objects if n=='Armature'];d.actions=[n for n in s.actions if n=='leo_idle']
 rig=d.objects[0];bpy.context.scene.collection.objects.link(rig);act=d.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();return rig
def W(rig,name):return rig.matrix_world@rig.pose.bones['mixamorig:'+name].head
def WM(rig,name):return rig.matrix_world@rig.pose.bones['mixamorig:'+name].matrix
def ss(u):u=max(0.,min(1.,u));return u*u*(3-2*u)
def build(name,P):
 rig=load_rig();pb=rig.pose.bones;T=P['cycle'];d=P['stance'];A=P['amp'];lift=P['lift'];bob=P['bob'];crouch=P['crouch'];lean=math.radians(P['lean']);sw=P['arm_swing'];yaw=math.radians(P['pelvis_yaw'])
 H0=W(rig,'Hips');base={n:WM(rig,n) for n in ('Hips','Spine','Spine1','Spine2','Neck','Head','LeftFoot','RightFoot','LeftHand','RightHand')}
 ankle0={s:W(rig,s+'Foot') for s in ('Left','Right')};hand0={s:W(rig,s+'Hand') for s in ('Left','Right')};shoulder={s:W(rig,s+'Arm') for s in ('Left','Right')}
 # keep the idle pose of every bone as the base (breathing frozen at frame 1), then drop the idle action
 pose={b.name:(b.rotation_mode,Euler(b.rotation_euler),b.rotation_quaternion.copy(),b.location.copy()) for b in pb}
 rig.animation_data_clear()
 for b in pb:b.rotation_mode=pose[b.name][0];b.rotation_euler=pose[b.name][1];b.rotation_quaternion=pose[b.name][2];b.location=pose[b.name][3]
 bpy.context.view_layer.update()
 def emp(n):
  e=bpy.data.objects.new(n,None);bpy.context.scene.collection.objects.link(e);return e
 E={n:emp('E_'+n) for n in ('Hips','Spine','Spine1','Spine2','Neck','Head','LF','RF','LFlat','RFlat','LH','RH','LHFlat','RHFlat','PoleLK','PoleRK','PoleLE','PoleRE')}
 def lim(bone,kind,tgt,infl=1.):
  c=pb['mixamorig:'+bone].constraints.new(kind);c.target=E[tgt];c.target_space='WORLD';c.owner_space='WORLD';c.influence=infl;return c
 lim('Hips','COPY_LOCATION','Hips');lim('Hips','COPY_ROTATION','Hips')
 for n in ('Spine','Spine1','Spine2','Neck','Head'):lim(n,'COPY_ROTATION',n)
 for s,sg in (('Left',1),('Right',-1)):
  lim(s+'Foot','COPY_ROTATION',s[0]+'Flat');lim(s+'Hand','COPY_ROTATION',s[0]+'HFlat')
  k=pb['mixamorig:'+s+'Leg'].constraints.new('IK');k.target=E[s[0]+'F'];k.pole_target=E['Pole'+s[0]+'K'];k.chain_count=2;k.use_stretch=False;k.pole_angle=math.radians(P.get('knee_pole',-90))
  k=pb['mixamorig:'+s+'ForeArm'].constraints.new('IK');k.target=E[s[0]+'H'];k.pole_target=E['Pole'+s[0]+'E'];k.chain_count=2;k.use_stretch=False;k.pole_angle=math.radians(P.get('elbow_pole',90))
 sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=T;Rz=lambda a:Matrix.Rotation(a,4,'Z');Rx=lambda a:Matrix.Rotation(a,4,'X')
 def put(e,loc=None,rot=None,f=1):
  if loc is not None:e.location=loc;e.keyframe_insert('location',frame=f)
  if rot is not None:e.rotation_euler=rot.to_euler();e.keyframe_insert('rotation_euler',frame=f)
 def foot_x(ph,d_):   # forward offset of the ankle in metres, ph in [0,1): stance goes back, swing comes forward
  if ph<d_:return A-2*A*ph/d_
  return -A+2*A*ss((ph-d_)/(1-d_))
 def foot_z(ph,d_):
  if ph<d_:return 0.
  u=(ph-d_)/(1-d_);return lift*math.sin(PI*u)**.8
 targets=[]
 for f in range(1,T+1):
  t=(f-1)/T;hz=H0.z-crouch+bob*math.cos(4*PI*(t-d/2));hx=P['sway']*math.sin(2*PI*t)*-1;ya=yaw*math.sin(2*PI*t)
  Hm=Rz(ya)@Rx(-lean*.25)@base['Hips'].to_3x3().to_4x4();put(E['Hips'],Vector((H0.x+hx,H0.y,hz)),Hm,f)
  for k,(n,share) in enumerate((('Spine',.3),('Spine1',.35),('Spine2',.35))):
   cum=sum(s for _,s in (('Spine',.3),('Spine1',.35),('Spine2',.35))[:k+1])
   M=Rz(ya*(1-1.8*cum))@Rx(-lean*cum)@base[n].to_3x3().to_4x4();put(E[n],None,M,f)
  put(E['Neck'],None,Rz(-ya*.2)@Rx(-lean*.9)@base['Neck'].to_3x3().to_4x4(),f);put(E['Head'],None,Rx(-lean*.5)@base['Head'].to_3x3().to_4x4(),f)
  rec={}
  for s,off in (('Left',0.),('Right',.5)):
   ph=(t+off)%1.;fx=foot_x(ph,d);fz=foot_z(ph,d);a0=ankle0[s];tgt=Vector((a0.x+(.0),a0.y-fx,a0.z+fz-0.));tgt.x=a0.x+hx*.0
   E[s[0]+'F'].location=tgt;E[s[0]+'F'].keyframe_insert('location',frame=f);rec[s]=(tgt,ph<d)
   pitch=0.
   if ph<d:pitch=math.radians(P['toe_off'])*ss((ph/d-.75)/.25)
   else:u=(ph-d)/(1-d);pitch=-math.radians(P['toe_up'])*math.sin(PI*u)+math.radians(P['toe_off'])*(1-ss(u*3))
   put(E[s[0]+'Flat'],None,Rx(pitch)@base[s+'Foot'].to_3x3().to_4x4(),f)
   E['Pole'+s[0]+'K'].location=Vector((a0.x*1.1,a0.y-.9,a0.z+.6+.0));E['Pole'+s[0]+'K'].keyframe_insert('location',frame=f)
   # arm opposite to the same-side leg
   hs=shoulder[s];h0=hand0[s];ang=2*PI*(t+off+.5);sy=sw*math.sin(ang);sg=1 if s=='Left' else -1
   E[s[0]+'H'].location=Vector((h0.x+sg*P['arm_out'],h0.y-sy,h0.z+P['arm_up']+.04*abs(math.sin(ang))));E[s[0]+'H'].keyframe_insert('location',frame=f)
   put(E[s[0]+'HFlat'],None,Rx(-.3*sy/max(.01,sw))@base[s+'Hand'].to_3x3().to_4x4(),f)
   E['Pole'+s[0]+'E'].location=Vector((hs.x+sg*.5,hs.y+.9,hs.z-.1));E['Pole'+s[0]+'E'].keyframe_insert('location',frame=f)
  targets.append((f,rec))
 bpy.context.view_layer.update()
 # calibrate the knee and elbow pole angles on frame 1: knees must point forward (-Y), elbows back
 def knee_forward(frame,ang):
  sc.frame_set(frame)
  for s in ('Left','Right'):pb['mixamorig:'+s+'Leg'].constraints[0].pole_angle=math.radians(ang)
  bpy.context.view_layer.update();return sum(((W(rig,s+'Leg').y)-(W(rig,s+'UpLeg').y)) for s in ('Left','Right'))
 best=min((-90,-45,0,45,90,135,180,-135),key=lambda a:knee_forward(3,a));P['knee_pole']=best
 for s in ('Left','Right'):pb['mixamorig:'+s+'Leg'].constraints[0].pole_angle=math.radians(best)
 def elbow_back(frame,ang):
  sc.frame_set(frame)
  for s in ('Left','Right'):pb['mixamorig:'+s+'ForeArm'].constraints[0].pole_angle=math.radians(ang)
  bpy.context.view_layer.update();return -sum(((W(rig,s+'ForeArm').y)-(W(rig,s+'Arm').y)) for s in ('Left','Right'))
 beste=min((-90,-45,0,45,90,135,180,-135),key=lambda a:elbow_back(3,a))
 for s in ('Left','Right'):pb['mixamorig:'+s+'ForeArm'].constraints[0].pole_angle=math.radians(beste)
 # bake
 for o in bpy.data.objects:o.select_set(False)
 rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.nla.bake(frame_start=1,frame_end=T,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
 act=rig.animation_data.action;act.name='leo_'+name;act.use_fake_user=True
 # audit on the baked pose: ankle error against the target and planted-foot speed
 issues=[];err=0.;plant=[];hz=[]
 prev=None
 for f,rec in targets:
  sc.frame_set(f);bpy.context.view_layer.update();hz.append(W(rig,'Hips').z)
  for s in ('Left','Right'):
   tg,stance=rec[s];got=W(rig,s+'Foot');e=(got-tg).length;err=max(err,e)
 for s in ('Left','Right'):
  ys=[]
  for f,rec in targets:
   sc.frame_set(f);bpy.context.view_layer.update();ys.append((rec[s][1],W(rig,s+'Foot').y))
  v=[(ys[i][1]-ys[i-1][1])*24. for i in range(1,len(ys)) if ys[i][0] and ys[i-1][0]];plant+=v
 speed=2*A/(d*T/24.);meas=sum(plant)/max(1,len(plant))
 if err>.06:issues.append('AUDIT gait %s: ankle misses its target by %.3f m (the leg cannot reach; lower amp or crouch less)'%(name,err))
 if abs(meas-speed)>.12*speed:issues.append('AUDIT gait %s: planted foot moves at %.2f m/s, ground speed %.2f m/s'%(name,meas,speed))
 for i in issues:print(i)
 print('GAIT',name,'cycle',T,'frames','speed %.2f'%speed,'planted %.2f'%meas,'reach error %.3f'%err,'hips z %.2f..%.2f'%(min(hz),max(hz)))
 for o in list(bpy.data.objects):bpy.data.objects.remove(o)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ASSETS,'leo_%s.blend'%name),compress=True)
 return dict(name=name,cycle=T,speed=round(speed,3),planted=round(meas,3),reach_error=round(err,4),hips=[round(min(hz),3),round(max(hz),3)],issues=issues)
rep=[]
for n in WANT:rep.append(build(n,dict(G.GAITS[n])))
p=os.path.join(ASSETS,'gait_report.json')
old=json.load(open(p)) if os.path.exists(p) else {}
for r in rep:old[r['name']]=r
json.dump(old,open(p,'w'),indent=1);print('WALK_CLIPS_DONE',[r['name'] for r in rep])
