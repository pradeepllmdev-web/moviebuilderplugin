import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent;D=H/'talking';bpy.ops.wm.open_mainfile(filepath=str(D/'face-rig.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=bpy.data.objects['Armature'];cat=bpy.data.objects['CatPilot'];track=json.loads((D/'track.json').read_text());weights=track['weights'];meshes=[o for o in s.objects if o.type=='MESH' and o.data.shape_keys]
for o in meshes:
 o.data.shape_keys.animation_data_clear()
 for k in o.data.shape_keys.key_blocks:k.value=0
r.animation_data_clear();fps=track['fps'];s.frame_start=1;s.frame_end=track['frames'];s.render.fps=fps
mapping={'MouthRound':'mouthPucker','MouthWide':'mouthWide','LipClose':'mouthClose','Smile':'mouthSmile'}
values=[]
for i in range(track['frames']):
 f=i+1;t=i/fps;s.frame_set(f)
 close=weights.get('mouthClose',[0]*track['frames'])[i];jaw=min(.9,weights['jawOpen'][i])*(1-min(.95,close));values.append(jaw)
 for obj in meshes:
  for k in obj.data.shape_keys.key_blocks:
   if k.name=='JawOpen':k.value=jaw
   elif k.name=='Eyes':k.value=max(weights.get('eyeBlinkLeft',[0]*track['frames'])[i],weights.get('eyeBlinkRight',[0]*track['frames'])[i])
   elif k.name in mapping:k.value=float(weights.get(mapping[k.name],[0]*track['frames'])[i])
   else:continue
   k.keyframe_insert('value',frame=f)
 for name,yaw,nod in [('Head',3,1.5),('Neck',.5,.5),('Chest',.4,.6)]:
  bone=r.pose.bones[name];q=bone.bone.matrix_local.to_quaternion();axis=q.inverted()@Vector((0,0,1));pitch=q.inverted()@Vector((1,0,0))
  bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion(axis,math.radians(yaw)*math.sin(t*.8))@Quaternion(pitch,math.radians(nod)*math.sin(t*1.5));bone.keyframe_insert('rotation_quaternion',frame=f)
 for side,phase in [('L',0),('R',1.4)]:
  b=r.pose.bones['Forearm.'+side];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((1,0,0),.04*math.sin(t*.9+phase));b.keyframe_insert('rotation_quaternion',frame=f)
c=s.camera;c.location=(0,-2.5,1.83);c.data.lens=65;c.rotation_euler=(Vector((0,0,1.83))-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=s.render.resolution_y=512;s.render.engine='BLENDER_EEVEE'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'cat-pilot-talking.blend'))
# Nose/upper-muzzle speech displacements must remain zero.
keys=cat.data.shape_keys.key_blocks;basis=keys['Basis'];protected=[i for i,v in enumerate(basis.data) if (cat.matrix_world@v.co).z>1.79]
error=max((keys[name].data[i].co-basis.data[i].co).length for name in ['JawOpen','MouthRound','MouthWide','LipClose','Smile'] for i in protected);assert error<1e-7
assert max(values)>.2 and values[-1]<.01
(D/'verification.json').write_text(json.dumps({'frames':track['frames'],'fps':fps,'protected_upper_face_error_m':error,'jaw_peak':max(values),'jaw_at_end':values[-1],'source_sha256':hashlib.sha256((H/'source/CatPilot.blend').read_bytes()).hexdigest(),'voice':'offline Windows SAPI','limitations':['original painted smile remains','single shared blink control','no full brow rig','mouth corners require visual review']},indent=2))
frames=D/'frames';frames.mkdir(exist_ok=True)
for f in range(1,s.frame_end+1):
 s.frame_set(f);s.render.filepath=str(frames/f'{f-1:05d}.png');bpy.ops.render.render(write_still=True)
print('TALKING_READY')
