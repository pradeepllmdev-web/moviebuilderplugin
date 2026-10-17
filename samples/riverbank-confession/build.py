"""Emotional two-character acting test; model geometry stays inside Blender."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
H=Path(__file__).resolve().parent;ROOT=H.parents[1];P=json.loads((H/'plan.json').read_text());count=round(P['duration']*24)
R=ROOT/'samples/riverbank-race'
bpy.ops.wm.open_mainfile(filepath=str(R/'riverbank-race.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;s.frame_set(1)
neutral={name:next(o for o in bpy.data.objects[name+' race path'].children_recursive if o.type=='ARMATURE').pose.bones['mixamorig:Head'].rotation_quaternion.copy() for name in ('lion','cat')}
bpy.ops.wm.open_mainfile(filepath=str(R/'riverbank-race-acting.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;s.frame_set(1)
for o in list(s.objects):
 if any(term in o.name for term in ('Finish pole','Finish pennant','Race line')):bpy.data.objects.remove(o,do_unlink=True)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
actors={};report={}
for name,sign,x,height in [('lion',1,15.05,1.85),('cat',-1,17.15,1.5)]:
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE');meshes=[o for o in rig.children_recursive if o.type=='MESH' and o.data.shape_keys];body=max(meshes,key=lambda o:len(o.data.vertices));head=rig.pose.bones['mixamorig:Head']
 held={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones};held[head.name]=(held[head.name][0],neutral[name]);rig.animation_data_clear();root.animation_data_clear();root.location.x=x;root.location.y=-.45;root.rotation_euler.z=sign*math.radians(32)
 for o in meshes:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=1 if k.name in ('JawClose','LipSeal') else 0
 bpy.context.view_layer.update();invroot=root.matrix_world.inverted();transform=invroot@body.matrix_world;inv=transform.inverted().to_3x3();basis=body.data.shape_keys.key_blocks[0];hl=height/root.scale.x
 eyes=[]
 for o in meshes:
  if len(o.data.vertices)>2000:continue
  key=next((k for k in o.data.shape_keys.key_blocks if k.name in ('BlinkL','BlinkR')),None)
  if key:
   pts=[invroot@o.matrix_world@v.co for v in key.data];eyes.append(sum(pts,Vector())/len(pts))
 eyes=sorted(eyes,key=lambda p:p.x);assert len(eyes)>=2
 centers=[eyes[0],eyes[-1]];gap=centers[1].x-centers[0].x;mid=(centers[0]+centers[1])/2
 # Narrow, bounded eye-surface morphs: a small iris-region shift, not a
 # replacement eyeball. The outer eye rim remains fixed by the falloff.
 for keyname,direction in [('GazeLeft',-1),('GazeRight',1),('GazeDown',0)]:
  key=body.shape_key_add(name=keyname,from_mix=False)
  for v,b in zip(key.data,basis.data):
   p=transform@b.co;weight=0
   for eye in centers:
    dx=(p.x-eye.x)/(gap*.22);dz=(p.z-eye.z)/(gap*.18)
    weight=max(weight,math.exp(-dx**4-dz**4)*smooth((eye.y+hl*.035-p.y)/(hl*.03)))
   delta=Vector((gap*.035*direction,0,-gap*.025 if direction==0 else 0))*weight;v.co=b.co+inv@delta
 concern=body.shape_key_add(name='Concern',from_mix=False)
 brows=[k for k in body.data.shape_keys.key_blocks if k.name.startswith('ActingBrow')]
 for i,(v,b) in enumerate(zip(concern.data,basis.data)):
  p=transform@b.co;inner=max(0,min(1,1-abs(p.x-mid.x)/(gap*.65)));delta=sum((k.data[i].co-b.co for k in brows),Vector());v.co=b.co+delta*(inner*1.5-.22)
 mouth_top=mid.z-hl*(.095 if name=='lion' else .075);mouth_width=gap*1.1
 closed=body.data.shape_keys.key_blocks.get('JawClose') or body.data.shape_keys.key_blocks.get('LipSeal')
 for keyname in ('LipPress','Round','Wide','LowerLipBite','Frown','WarmSmile'):
  key=body.shape_key_add(name=keyname,from_mix=False)
  for i,(v,b) in enumerate(zip(key.data,basis.data)):
   p=transform@(closed.data[i].co if closed else b.co);dx=(p.x-mid.x)/mouth_width;dz=(p.z-mouth_top)/(hl*.035)
   weight=math.exp(-dx**4*5-dz*dz)*smooth((mid.y+hl*.08-p.y)/(hl*.05))
   if p.z>mouth_top+hl*.015:weight=0
   if keyname in ('Frown','WarmSmile'):
    corner=math.exp(-((abs(p.x-mid.x)-mouth_width*.55)/(mouth_width*.28))**2-((p.z-mouth_top)/(hl*.035))**2)*smooth((mid.y+hl*.08-p.y)/(hl*.05))
    if p.z>mouth_top+hl*.035:corner=0
    delta=Vector((0,0,hl*(-.022 if keyname=='Frown' else .015)))*corner
   elif keyname=='Round':delta=Vector((-(p.x-mid.x)*.1,-hl*.002,0))*weight
   elif keyname=='Wide':delta=Vector(((p.x-mid.x)*.1,0,0))*weight
   else:
    lower=math.exp(-((p.z-(mouth_top-hl*.017))/(hl*.012))**2);delta=Vector((0,0,hl*(.008 if keyname=='LipPress' else .005)))*weight*lower
   v.co=b.co+inv@delta
 strong=body.shape_key_add(name='ConcernStrong',from_mix=False)
 for v,b in zip(strong.data,basis.data):
  p=transform@b.co;weight=0
  for eye in centers:
   weight=max(weight,math.exp(-((p.x-eye.x)/(gap*.33))**2-((p.z-eye.z-hl*.045)/(hl*.027))**2)*smooth((eye.y+hl*.055-p.y)/(hl*.04)))
  inner=max(0,min(1,1-abs(p.x-mid.x)/(gap*.7)));v.co=b.co+inv@Vector((0,0,hl*(.024*inner-.006)*weight))
 actors[name]=(root,rig,meshes,body,held,sign,height)
 report[name]={'eye_direction':'bounded eye-surface morph; limited range','controls':['Concern','GazeLeft','GazeRight','GazeDown','LipPress','Round','Wide','LowerLipBite']}
release=P['lines'][4]['start'];forgiveness=P['lines'][5]['start'];disappointment=P['lines'][1]['start']
for f in range(1,count+1):
 t=(f-1)/24;s.frame_set(f)
 for name,(root,rig,meshes,body,held,sign,height) in actors.items():
  line=next((l for l in P['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None);active=bool(line);reconnect=smooth((t-release)/2);warm=smooth((t-forgiveness)/1.2)
  if name=='cat':
   concern=.75*(1-reconnect)+.1;smile=.02+.42*warm;down=.6*(1-reconnect);head_yaw=sign*(10+13*reconnect);pitch=10*(1-reconnect)-3*reconnect;gaze=sign*(.3+.4*reconnect)
  else:
   disappointed=smooth((t-disappointment)/1.1)*(1-warm);concern=.08+.5*disappointed;smile=.08+.38*warm;down=.08+.16*disappointed;head_yaw=sign*(19+3*warm);pitch=3;gaze=sign*.65
   if P['lines'][1]['start']+P['lines'][1]['duration']<t<P['lines'][3]['start']:head_yaw=-4;pitch=9;gaze=-.25
  # Brief look-away during confession, then held attention rather than a sine-wave stare.
  if name=='cat' and P['lines'][0]['start']+2<t<P['lines'][0]['start']+P['lines'][0]['duration']+.5:head_yaw=sign*3;gaze=-sign*.35;down=.7
  nod=0
  for center,strength in [(release+1,.7),(forgiveness+.5,1),(forgiveness+3,.55)]:
   if abs(t-center)<.5:nod+=math.sin((t-center+.5)*2*math.pi)*strength*3
  for b in rig.pose.bones:b.location=held[b.name][0];b.rotation_mode='QUATERNION';b.rotation_quaternion=held[b.name][1]
  head=rig.pose.bones['mixamorig:Head'];q=head.bone.matrix_local.to_quaternion();world=rig.matrix_world.to_3x3().inverted();axis=q.inverted()@(world@Vector((0,0,1)));paxis=q.inverted()@(world@Vector((1,0,0)))
  head.rotation_quaternion=head.rotation_quaternion@Quaternion(axis,math.radians(head_yaw))@Quaternion(paxis,math.radians(pitch+nod+(1.1 if active else .3)*math.sin(t*2.0)))
  # Restrained chest breath; hands and feet retain the quiet held pose.
  chest=rig.pose.bones.get('mixamorig:Spine2')
  if chest:
   cq=chest.bone.matrix_local.to_quaternion();bodyright=root.matrix_world.to_3x3()@Vector((1,0,0));caxis=cq.inverted()@(rig.matrix_world.to_3x3().inverted()@bodyright)
   slump=(4*(1-reconnect) if name=='cat' else 4.5*disappointed)
   chest.rotation_quaternion=chest.rotation_quaternion@Quaternion(caxis,math.radians(slump+.35*math.sin(t*1.6)))
  for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  jaw=roundness=wide=press=bite=0
  if line:
   tr=line['track'];i=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*24)));w=tr['weights'];jaw=min(.85,w['jawOpen'][i]*1.03);roundness=w['mouthPucker'][i];wide=w['mouthWide'][i];press=w['mouthClose'][i];bite=w['lowerLipBite'][i]
  blink=max([max(0,1-abs(t-b)/.12) for b in ([2.4,6.9,10.8,15.6,20.5,25.3,30.6,34] if name=='lion' else [1.4,5.3,9.2,14,18.3,23.8,29,33])])
  for o in meshes:
   for k in o.data.shape_keys.key_blocks:
    if k.name=='JawOpen':k.value=jaw
    elif k.name in ('JawClose','LipSeal'):k.value=1-jaw
    elif k.name.startswith('Blink'):k.value=min(1,blink+(0 if blink else .12*concern))
    elif k.name in ('Smile',):k.value=smile
    elif k.name.startswith('ActingBrow'):k.value=.08+.2*warm
    elif k.name=='Concern':k.value=concern
    elif k.name=='ConcernStrong':k.value=concern
    elif k.name=='Frown':k.value=(.78 if name=='cat' else .65)*concern
    elif k.name=='WarmSmile':k.value=.55*warm
    elif k.name=='GazeLeft':k.value=max(0,-gaze)
    elif k.name=='GazeRight':k.value=max(0,gaze)
    elif k.name=='GazeDown':k.value=down
    elif k.name in ('MouthRound','Round'):k.value=roundness*(.45 if k.name=='MouthRound' else .65)
    elif k.name in ('MouthWide','Wide'):k.value=wide*(.45 if k.name=='MouthWide' else .65)
    elif k.name=='LipPress':k.value=press
    elif k.name=='LowerLipBite':k.value=bite
    else:continue
    k.keyframe_insert('value',frame=f)
# Golden-hour faces with a soft key; keep the stylized river set behind them.
for o in s.objects:
 if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=1.7
def area(name,location,target,energy,color,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Dialogue soft key',(16,-4,5),(16,0,1.4),550,(1,.8,.58),5);area('River rim',(16,3,4),(16,0,1.4),500,(.55,.75,1),4)
cam=s.camera;cam.animation_data_clear();cam.data.lens=58;shots=[]
boundaries=[0]+[l['start']-.15 for l in P['lines']]+[P['duration']-1.3]
for f in range(1,count+1):
 t=(f-1)/24;s.frame_set(f)
 line=next((l for l in reversed(P['lines']) if t>=l['start']-.15),None)
 if t<.85 or t>P['duration']-1.3:
  target=Vector((16.1,0,1.0));pos=Vector((16.1,-6.6,2.4));label='Together'
 else:
  name=line['actor'] if line else 'cat';root,rig,meshes,body,held,sign,height=actors[name]
  # Stay on one side of the conversational axis. The partner remains an edge shoulder.
  target=Vector((root.location.x,-.35,height*.79));pos=target+Vector((sign*.65,-3.25,.2));label=name+' dialogue'
  # Two held reaction inserts while the other character speaks.
  if P['lines'][0]['start']+3<t<P['lines'][0]['start']+4.15 or P['lines'][3]['start']+1.7<t<P['lines'][3]['start']+3.0:
   name='lion' if t<P['lines'][1]['start'] else 'cat';root,rig,meshes,body,held,sign,height=actors[name];target=Vector((root.location.x,-.35,height*.79));pos=target+Vector((sign*.65,-3.25,.2));label=name+' listening reaction'
  pos+=Vector((0,-.06*math.sin(t*.07),0))
 if not shots or shots[-1]['name']!=label:shots.append({'frame':f,'name':label})
 cam.location=pos;cam.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
s.frame_start=1;s.frame_end=count;s.render.fps=24;s.render.resolution_x=960;s.render.resolution_y=540;s.view_settings.exposure=0
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'no-shortcuts.blend'))
(H/'application.json').write_text(json.dumps({'frames':count,'fps':24,'controls':report,'shots':shots,'meshy_calls':0,'limitations':['Eye-surface morphs have limited range, not separate eyeballs','Lip contact and tongue performance remain approximate','Offline synthesized voices lack directed emotional delivery','Procedural stylized environment']},indent=2))
for time,label in [(3,'confession'),(P['lines'][1]['start']+1,'disappointment'),(forgiveness+2,'forgiveness')]:
 s.frame_set(round(time*24)+1);s.render.filepath=str(H/(label+'.png'));bpy.ops.render.render(write_still=True)
print('EMOTIONAL_SCENE_READY '+json.dumps({'frames':count,'shots':len(shots),'duration':count/24}))
