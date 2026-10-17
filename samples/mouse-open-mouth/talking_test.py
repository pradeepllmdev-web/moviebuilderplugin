import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent;ROOT=H.parents[1];P=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline');sys.path[:0]=[str(ROOT),str(P)]
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler
bpy.ops.wm.open_mainfile(filepath=str(H/'facial-test.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');meshes=[o for o in s.objects if o.type=='MESH' and o.data.shape_keys];body=next(o for o in meshes if 'JawClose' in o.data.shape_keys.key_blocks)
for o in meshes:
 o.data.shape_keys.animation_data_clear()
 for k in o.data.shape_keys.key_blocks:k.value=0
r.animation_data_clear()
profile={'schema':'body-retarget/1','anatomy':'biped','alignment_bone':'Chest','source_alignment':'Spine2','gesture_strength':.2,'max_angular_speed_degrees':90,'torso_limit_degrees':3,'mapping':{'Spine':'Spine','Spine2':'Chest','LeftArm':'LeftUpperArm','LeftForeArm':'LeftLowerArm','LeftHand':'LeftHand','RightArm':'RightUpperArm','RightForeArm':'RightLowerArm','RightHand':'RightHand'}}
with bpy.data.libraries.load(str(P/'assets/realistic/clips.blend'),link=False) as (src,dst):dst.actions=['clip|Listen']
adapter=BodyRetargeter(r,profile,RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz'),ClipSampler(dst.actions[0]))
base=H;track=json.loads((base/'track.json').read_text());weights=track['weights'];count=track['frames'];fps=track['fps'];head=r.pose.bones['Head'];q=head.bone.matrix_local.to_quaternion();axis=q.inverted()@(r.matrix_world.to_3x3().inverted()@Vector((0,0,1)));pitch=q.inverted()@(r.matrix_world.to_3x3().inverted()@Vector((1,0,0)))
for scene in bpy.data.scenes:
 if scene.sequence_editor is None:scene.sequence_editor_create()
for i in range(count):
 f=i+1;t=i/fps;s.frame_set(f);adapter.key(f,t,smooth_activity(t,[(.4,count/fps-.6)],fade=.6))
 opening=weights['jawOpen'][i]*.75;close=1-opening
 for o in meshes:
  for k in o.data.shape_keys.key_blocks:
   if k.name=='JawClose':k.value=close
   elif k.name=='MouthRound':k.value=weights.get('mouthPucker',[0]*count)[i]*.65
   elif k.name=='MouthWide':k.value=weights.get('mouthWide',[0]*count)[i]*.65
   elif k.name=='Smile':k.value=.08
   elif k.name=='BlinkL':k.value=weights['eyeBlinkLeft'][i]
   elif k.name=='BlinkR':k.value=weights['eyeBlinkRight'][i]
   else:continue
   k.keyframe_insert('value',frame=f)
 head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(3)*math.sin(t*.8))@Quaternion(pitch,math.radians(1)*math.sin(t*1.3));head.keyframe_insert('rotation_quaternion',frame=f)
s.frame_start=1;s.frame_end=count;s.render.fps=fps;s.render.resolution_x=s.render.resolution_y=512;s.render.engine='BLENDER_EEVEE';s.render.use_sequencer=False
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'fresh-talking.blend'))
(H/'application.json').write_text(json.dumps({'frames':count,'fps':fps,'audio':str(base/'voice.wav'),'lead':track['lead'],'source_sha256':hashlib.sha256((H/'rigged.glb').read_bytes()).hexdigest(),'fresh_geometry_only':True,'limitations':['rest pose still shows teeth; full lip seal pending','stylized jagged fur remains','eyelids are fitted overlays','prototype facial controls, not complete ARKit']},indent=2))
D=H/'frames';D.mkdir(exist_ok=True)
for f in range(1,count+1):
 s.frame_set(f);s.render.filepath=str(D/f'{f-1:05d}.png');bpy.ops.render.render(write_still=True)
print('FRESH_TALKING_READY')

