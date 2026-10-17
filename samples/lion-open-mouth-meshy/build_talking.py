import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
BASE=Path(__file__).resolve().parent;H=BASE/'talking';ROOT=BASE.parents[1]
PLUGIN=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
sys.path[:0]=[str(ROOT),str(PLUGIN)]
bpy.ops.wm.open_mainfile(filepath=str(H/'mouth-ready.blend'),use_scripts=False,load_ui=False)
from movie_production.body import BodyRetargeter,ClipSampler,smooth_activity
from movie_production.performance_tracks import RecordedBodySampler
from movie_production.characters import speech_commands
from facerig import visemes
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');source=bpy.data.objects['char1']
meshes=[o for o in s.objects if o.type=='MESH' and o.data.shape_keys]
for o in meshes:o.data.shape_keys.animation_data_clear()
profile=json.loads((BASE/'body-profile.json').read_text())
with bpy.data.libraries.load(str(PLUGIN/'assets/realistic/clips.blend'),link=False) as (src,target):target.actions=['clip|Listen']
body=BodyRetargeter(rig,profile,RecordedBodySampler(ROOT/'samples/the-last-lantern/performance/talk_body.npz'),ClipSampler(target.actions[0]))
audio=PLUGIN.parent/'verification/lion-whisper/audio/voice_01.wav'
frames=192;fps=24;start=.55
vis,amp=visemes([{'text':'Tonight, I will try something stronger. A whisper.','audio':str(audio),'start':start,'end':4.2,'tone':'quiet','manner':'talk'}],frames,fps)
head=rig.pose.bones['Head'];axis=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1))
for scene in bpy.data.scenes:
 if scene.sequence_editor is None:scene.sequence_editor_create()
values=[]
for frame in range(1,frames+1):
 s.frame_set(frame);t=(frame-1)/fps;body.key(frame,t,smooth_activity(t,[(.55,4.3)],fade=.6))
 command=speech_commands(vis,amp,frame-1);jaw=max(0,min(.85,command['jaw']*.8));values.append(jaw)
 for o in meshes:
  key=o.data.shape_keys.key_blocks.get('JawOpen')
  if key:key.value=jaw;key.keyframe_insert('value',frame=frame)
 seal=source.data.shape_keys.key_blocks['LipSeal'];seal.value=1-jaw;seal.keyframe_insert('value',frame=frame)
 head.rotation_mode='QUATERNION';head.rotation_quaternion=Quaternion(axis,math.radians(5)*math.sin(t*.85));head.keyframe_insert('rotation_quaternion',frame=frame)
s.frame_start=1;s.frame_end=frames;s.render.fps=fps;s.cycles.samples=8;s.render.use_sequencer=False
# Medium close-up includes upper-body gestures.
c=s.camera;c.location=(0,-2.15,1.28);c.rotation_euler=(Vector((0,-.15,1.23))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=55
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'lion-talking.blend'))
(H/'application.json').write_text(json.dumps({'frames':frames,'fps':fps,'audio':str(audio),'audio_start':start,'jaw_max':max(values),'jaw_end':values[-1],'source_sha256':hashlib.sha256((BASE/'rigged.glb').read_bytes()).hexdigest(),'limitations':['mouth corners still require refinement','no eyelid rig or independent gaze','jaw-based speech approximation, not full visemes']},indent=2))
s.frame_set(values.index(max(values))+1);s.render.filepath=str(H/'talking-preview.png');bpy.ops.render.render(write_still=True)
