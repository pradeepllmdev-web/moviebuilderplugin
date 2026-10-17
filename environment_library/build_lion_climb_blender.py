import bpy,sys,json,math,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-climb';D.mkdir(exist_ok=True);sys.path.insert(0,str(H.parent/'blendplugin-next/scene_pipeline'))
from realistic_rig import build_nla,shared_clips
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-grip-ik/scene.blend'));s=bpy.context.scene;s.frame_end=240;s.render.fps=24
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False);rig.hide_viewport=False;rig.animation_data_clear();rig.animation_data_create()
for b in rig.pose.bones:
 for c in list(b.constraints):b.constraints.remove(c)
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
rig.location=(0,0,0);catalog=json.loads((H/'samples/lion-grip-ik/catalog.json').read_text());info=catalog['Leo'];info['motion_defaults']['climb']='Ladder_Climb'
if 'Ladder_Climb' not in shared_clips():raise RuntimeError('Ladder_Climb clip not installed')
actor=dict(name='Leo',segments=[dict(action='climb',start=0,end=10,**{'from':[0,0,0],'to':[0,0,0]},yaw_start=0,yaw_end=0,intensity=.4)])
warnings=[];build_nla(rig,info,actor,24,warnings,s.camera)
targets={};bones={};paths={};errors=[];by_limb={};holds={};worst={}
for side,sign in [('Left',1),('Right',-1)]:
 for limb,part in [('hand','Hand'),('foot','Foot')]:
  name=side+'_'+limb;bones[name]=next(b for b in rig.pose.bones if b.name.endswith(side+part));end=next(b for b in rig.pose.bones if b.name.endswith(side+('ForeArm' if limb=='hand' else 'Leg')))
  target=bpy.data.objects.new('Rock Contact '+name,None);s.collection.objects.link(target);targets[name]=target;paths[name]=[]
  ik=end.constraints.new('IK');ik.target=target;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
  base=1.10 if limb=='hand' else .35;phase={('Left','hand'):0,('Right','foot'):.5,('Right','hand'):1.,('Left','foot'):1.5}[(side,limb)]
  for f in range(1,241):
   t=min((f-1)/24,8);q=(t-phase)/2;step=math.floor(q);u=(q-step)*2
   if q<0:step=-1;u=0
   blend=max(0,min(1,u/.45));blend=blend*blend*(3-2*blend)
   z=base+.4*max(0,step+blend);x=sign*(.28 if limb=='hand' else .17);y=-.30 if limb=='hand' else -.20
   pos=Vector((x,y+.10*math.sin(math.pi*blend),z));paths[name].append(pos)
   holds[(name,round(base+.4*max(0,step),2))]=[x,y,base+.4*max(0,step)]
hips=next(b for b in rig.pose.bones if b.name.endswith('Hips'));hip_offset=hips.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-.12))/rig.matrix_world.to_scale().z
root=[]
for f in range(1,241):
 t=(f-1)/24;z=min(t,8)*.2;root.append({'frame':f-1,'z':z});rig.location.z=z;rig.keyframe_insert('location',frame=f);hips.location=hip_offset;hips.keyframe_insert('location',frame=f)
 for name,target in targets.items():target.location=paths[name][f-1]
 s.frame_set(f)
 for target in targets.values():target.update_tag()
 rig.update_tag();bpy.context.view_layer.update()
 for name in targets:
  error=(rig.matrix_world@bones[name].head-paths[name][f-1]).length;errors.append(error);by_limb.setdefault(name,[]).append(error)
  if name.endswith('hand') and error>worst.get(name,{}).get('error',0):
   side=name.split('_')[0];arm=next(b for b in rig.pose.bones if b.name.endswith(side+'Arm'));fore=next(b for b in rig.pose.bones if b.name.endswith(side+'ForeArm'));worst[name]={'error':error,'frame':f,'shoulder':list(rig.matrix_world@arm.head),'target':list(paths[name][f-1]),'wrist':list(rig.matrix_world@bones[name].head),'lengths':[arm.length*.01,fore.length*.01]}
for name,target in targets.items():
 for f,pos in enumerate(paths[name],1):target.location=pos;target.keyframe_insert('location',frame=f)
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for k in obj.data.shape_keys.key_blocks:k.value=0
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig

bpy.ops.nla.bake(frame_start=1,frame_end=240,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
for track in rig.animation_data.nla_tracks:track.mute=True
rig.location=(0,0,0)
camera=s.camera;camera.animation_data_clear();camera.data.animation_data_clear();camera.location=(3,-4,2);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=40
plan=dict(title='Leo — First Rock Climb',scene_type='motion',duration=10,fps=24,floor_size=[24,24],actors=[actor],obstacles=[],camera=dict(offset=[3,-4,2],lens_mm=40),lighting='day',set='field',lines=[])
(D/'scene.json').write_text(json.dumps(plan));(D/'catalog.json').write_text(json.dumps(catalog));(D/'route.json').write_text(json.dumps({'root':root,'holds':list(holds.values()),'contacts':{n:[list(p) for p in pp] for n,pp in paths.items()}}));(D/'contact-check.json').write_text(json.dumps({'clip':'Ladder_Climb','max_joint_contact_error_cm':max(errors)*100,'mean_error_cm':sum(errors)/len(errors)*100,'warnings':warnings,'height_m':1.6,'limb_max_cm':{n:max(v)*100 for n,v in by_limb.items()},'worst':worst}))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))


