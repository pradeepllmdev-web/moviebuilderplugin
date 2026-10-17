"""Preserve driving performance; solve paw centers onto calibrated steering grips."""
import bpy,sys,json,math,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-driver-talk';D.mkdir(exist_ok=True);P=H.parent/'blendplugin-next/scene_pipeline';sys.path.insert(0,str(P));sys.path.insert(0,str(H.parent/'3dobjectnew/server'))
from speech_visemes import sapi_speak
from facerig import visemes
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-drive-v2/scene.blend'));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False);rig.hide_viewport=False;rig.hide_render=False;rig.data.pose_position='POSE'
plan=json.loads((H/'samples/lion-drive-v2/scene.json').read_text());lines=[]
for i,(at,text) in enumerate([(0,'A little heat will not stop this lion. We are getting through!'),(8,'Still with me? Good. Eyes back on the road!')]):
 speech=sapi_speak(text,D/f'voice-{i}','Microsoft David Desktop',1);lines.append(dict(speaker='Leo',to='Leo',text=text,start=at,end=min(12,at+5.8),audio=str(speech['wav']),tone='natural',manner='talk'))
plan['lines']=lines;head=next(b for b in rig.pose.bones if b.name.endswith('Head'));samples=[]
for f in range(1,289):s.frame_set(f);samples.append(head.rotation_quaternion.copy())
for b in rig.pose.bones:
 for constraint in list(b.constraints):b.constraints.remove(constraint)
palms={};targets={};bones={}
for side in ('Left','Right'):
 hand=next(b for b in rig.pose.bones if b.name.endswith(side+'Hand'));bones[side]=hand;points=[]
 for obj in s.objects:
  if obj.type!='MESH' or not any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers):continue
  group=obj.vertex_groups.get(hand.name)
  if not group:continue
  transform=rig.matrix_world.inverted()@obj.matrix_world
  for v in obj.data.vertices:
   if any(g.group==group.index and g.weight>.7 for g in v.groups):points.append(transform@v.co)
 if not points:raise RuntimeError('No weighted paw surface for '+side)
 center=sum(points,Vector())/len(points);palms[side]=hand.bone.matrix_local.inverted()@center
 target=bpy.data.objects.new('Calibrated Paw '+side,None);s.collection.objects.link(target);targets[side]=target
 fore=next(b for b in rig.pose.bones if b.name.endswith(side+'ForeArm'));ik=fore.constraints.new('IK');ik.target=target;ik.chain_count=2;ik.use_stretch=False;ik.iterations=128
cal=json.loads((H/'samples/lion-drive-v2/seat-calibration.json').read_text());wheel=json.loads((H/'samples/lion-drive-v2/cabin-fit-check.json').read_text());scale=cal['scale']*100;offset=cal['actor_offset_cm'];wc=wheel['steering_center_car_relative_cm'];radius=wheel['steering_radius_cm']/scale
target_keys=[]
center=Vector((-(wc[1]-offset[1])/scale,-(wc[0]-offset[0])/scale,(wc[2]-offset[2])/scale));errors=[]
def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
for f in range(1,289):
 s.frame_set(f);t=(f-1)/24;angle=.08*math.sin(t*.7)
 glance=ease((t-2.2)/.45)*(1-ease((t-3.3)/.5))+ease((t-8.1)/.4)*(1-ease((t-9.1)/.5))
 axis=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1));head.rotation_quaternion=samples[f-1]@Quaternion(axis,math.radians(12)*glance);head.keyframe_insert('rotation_quaternion',frame=f)
 for side,sign in [('Left',1),('Right',-1)]:
  desired=center+Vector((sign*radius*math.cos(angle),0,sign*radius*math.sin(angle)))
  target=targets[side];target.location=rig.matrix_world@bones[side].head
  for iteration in range(10):
   bpy.context.view_layer.update();evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=evaluated.matrix_world@evaluated.pose.bones[bones[side].name].matrix@palms[side];target.location+=desired-actual;target.update_tag();rig.update_tag(refresh={'OBJECT','DATA','TIME'})
  bpy.context.view_layer.update()
  if f==96:(D/('palm-debug-'+side+'.json')).write_text(json.dumps({'actual':list(rig.matrix_world@bones[side].matrix@palms[side]),'desired':list(desired),'wrist':list(rig.matrix_world@bones[side].head),'local_palm':list(palms[side]),'target':list(target.location)}))
  evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());errors.append(((evaluated.matrix_world@evaluated.pose.bones[bones[side].name].matrix@palms[side])-desired).length)
  target_keys.append((side,f,target.location.copy()))
for side,f,location in target_keys:
 targets[side].location=location;targets[side].keyframe_insert('location',frame=f)
_,amp=visemes(lines,288,24);prev=0
for f,v in enumerate(amp,1):
 prev+=max(-.18,min(.18,(1-math.exp(-1/(24*(.065 if v>prev else .14))))*(v-prev)))
 for obj in s.objects:
  if obj.type!='MESH' or not obj.data.shape_keys:continue
  for name,value in [('JawOpen',prev*.8),('LipSeal',max(0,1-prev*.8*3))]:
   key=obj.data.shape_keys.key_blocks.get(name)
   if key:key.value=value;key.keyframe_insert('value',frame=f)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for bone in rig.data.bones:bone.select=True
bpy.ops.nla.bake(frame_start=1,frame_end=288,step=1,only_selected=True,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
(D/'scene.json').write_text(json.dumps(plan));shutil.copyfile(H/'samples/lion-drive-v2/catalog.json',D/'catalog.json');(D/'palm-check.json').write_text(json.dumps({'max_palm_center_error_cm':max(errors)*100,'mean_error_cm':sum(errors)/len(errors)*100,'samples':len(errors),'camera_glances_seconds':[[2.2,3.8],[8.1,9.6]],'finger_curl':'unavailable: no finger bones'}))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))






