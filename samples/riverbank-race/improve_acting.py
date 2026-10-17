"""Scene-specific attention and expression pass; original race is preserved."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent;plan=json.loads((H/'plan.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(H/'riverbank-race.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
reports={}
for name,sign,finish,height in [('lion',-1,12.1,1.85),('cat',1,11.5,1.5)]:
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE');meshes=[o for o in rig.children_recursive if o.type=='MESH' and o.data.shape_keys]
 body=max(meshes,key=lambda o:len(o.data.vertices));head=rig.pose.bones['mixamorig:Head']
 s.frame_set(1);bpy.context.view_layer.update()
 # Infer brow regions from the fitted eyelid geometry, not hard-coded species coordinates.
 eyes=[]
 for o in meshes:
  keys=o.data.shape_keys.key_blocks
  if len(o.data.vertices)>2000:continue
  key=next((k for k in keys if k.name in ('BlinkL','BlinkR')),None)
  if key:
   points=[o.matrix_world@v.co for v in key.data];eyes.append(sum(points,Vector())/len(points))
 # Crease and lid may supply duplicate centers; use the two outer sides.
 eyes=sorted(eyes,key=lambda p:p.x)
 if len(eyes)>=2:
  centers=[eyes[0],eyes[-1]];basis=body.data.shape_keys.key_blocks[0];inv=body.matrix_world.inverted().to_3x3()
  for side,center in zip(('L','R'),centers):
   key=body.shape_key_add(name='ActingBrow'+side,from_mix=False)
   for v,b in zip(key.data,basis.data):
    p=body.matrix_world@b.co;dx=(p.x-center.x)/(height*.043);dz=(p.z-center.z-height*.038)/(height*.027)
    weight=math.exp(-dx*dx-dz*dz)*smooth((center.y+height*.07-p.y)/(height*.05))
    v.co=b.co+inv@Vector((0,0,height*.009*weight))
 samples=[]
 for f in range(1,s.frame_end+1):
  s.frame_set(f);samples.append((root.location.copy(),root.rotation_euler.copy(),head.rotation_quaternion.copy()))
 max_yaw=0;max_jaw=0
 for f,(location,rotation,headq) in enumerate(samples,1):
  t=(f-1)/24;s.frame_set(f);before=1-smooth((t-3.15)/.65);after=smooth((t-finish)/.8);idle=max(before,after)
  # Separate the conversational staging; retain the original race paths.
  root.location=location+Vector((-sign*.58*idle,0,0));root.rotation_euler=rotation;root.rotation_euler.z+=sign*math.radians(20)*idle
  root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
  line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None)
  active=bool(line);jaw=roundness=wide=0
  if line:
   tr=line['track'];i=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*24)));weights=tr['weights'];jaw=min(.9,weights['jawOpen'][i]*1.08);roundness=weights.get('mouthPucker',[0]*tr['frames'])[i]*.85;wide=weights.get('mouthWide',[0]*tr['frames'])[i]*.85
  # Held partner attention, a course glance before launch, and a finish nod.
  yaw=sign*math.radians(16)*idle+math.radians(2)*math.sin(t*.8)
  if 2.9<t<3.8:yaw+=sign*math.radians(9)*math.sin(math.pi*(t-2.9)/.9)
  nod=math.radians(2.5)*math.sin(t*2.1)*idle
  if t>13:nod+=math.radians(3)*math.sin((t-13)*2.5)*math.exp(-(t-13)*.5)
  q=head.bone.matrix_local.to_quaternion();world=rig.matrix_world.to_3x3().inverted();zaxis=q.inverted()@(world@Vector((0,0,1)));xaxis=q.inverted()@(world@Vector((1,0,0)))
  head.rotation_quaternion=headq@Quaternion(zaxis,yaw)@Quaternion(xaxis,nod);head.keyframe_insert('rotation_quaternion',frame=f)
  for o in meshes:
   for k in o.data.shape_keys.key_blocks:
    if k.name=='JawOpen':k.value=jaw
    elif k.name in ('JawClose','LipSeal'):k.value=1-jaw
    elif k.name=='MouthRound':k.value=roundness
    elif k.name=='MouthWide':k.value=wide
    elif k.name=='Smile':k.value=.18+.22*after+.08*before
    elif k.name.startswith('ActingBrow'):k.value=.15+(.35 if active else .12)*idle+.3*after+(.1 if k.name.endswith('L') else 0)*before
    else:continue
    k.keyframe_insert('value',frame=f)
  max_yaw=max(max_yaw,abs(math.degrees(yaw)));max_jaw=max(max_jaw,jaw)
 reports[name]={'added_head_yaw_degrees':max_yaw,'jaw_max':max_jaw,'brow_regions':min(2,len(eyes))}
# Dialogue cuts show expressions more clearly; wide running shots are retained.
camera=s.camera;camera_samples=[]
for f in range(1,s.frame_end+1):s.frame_set(f);camera_samples.append((camera.location.copy(),camera.rotation_euler.copy()))
for f,(location,rotation) in enumerate(camera_samples,1):
 t=(f-1)/24;s.frame_set(f)
 if .5<t<2.4:
  target=bpy.data.objects['cat race path'].location+Vector((0,0,1.2));location=target+Vector((.7,-2.9,.45));rotation=(target-location).to_track_quat('-Z','Y').to_euler()
 elif 2.4<=t<3.45 or 13<=t<16.9:
  target=bpy.data.objects['lion race path'].location+Vector((0,0,1.4));location=target+Vector((-.7,-3.25,.45));rotation=(target-location).to_track_quat('-Z','Y').to_euler()
 camera.location=location;camera.rotation_euler=rotation;camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'riverbank-race-acting.blend'))
(H/'acting-report.json').write_text(json.dumps({'characters':reports,'limitations':['No independent pupil gaze controls','Prototype mouth and eyelid shapes','Brow fitting requires visual review']},indent=2))
for f,label in [(36,'acting-cat'),(72,'acting-lion'),(350,'acting-finish')]:
 s.frame_set(f);s.render.filepath=str(H/(label+'.png'));bpy.ops.render.render(write_still=True)
print('ACTING_PASS_READY '+json.dumps(reports))
