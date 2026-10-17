"""Isolated Rowan eyelid/gaze audition. Original character remains untouched."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent.parent
D=H/'samples/rowan-eye-test';D.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/mpfb-character/rowan.blend'),use_scripts=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
controls=['eyeBlinkLeft','eyeBlinkRight','eyeLookInLeft','eyeLookOutLeft','eyeLookInRight','eyeLookOutRight','eyeLookUpLeft','eyeLookUpRight','eyeLookDownLeft','eyeLookDownRight']
found={name:[] for name in controls}
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for name in controls:
   key=o.data.shape_keys.key_blocks.get(name)
   if key:found[name].append(key)
if not all(found.values()):raise RuntimeError('Missing human eye controls: '+str([n for n,v in found.items() if not v]))
for frame in range(s.frame_start,s.frame_end+1):
 # Two deliberate full closures, with held left/right gaze between them.
 blink=max(max(0,1-abs(frame-center)/3) for center in (36,100))
 gaze=.3*math.sin((frame-1)/s.render.fps*1.1)
 for name,keys in found.items():
  value=blink if 'Blink' in name else max(0,gaze) if name in ('eyeLookInLeft','eyeLookOutRight') else max(0,-gaze) if name in ('eyeLookOutLeft','eyeLookInRight') else 0
  for key in keys:key.value=value;key.keyframe_insert('value',frame=frame)
s.frame_set(1);bpy.context.view_layer.update()
head=rig.matrix_world@rig.pose.bones['mixamorig:Head'].head
camera=s.camera;camera.animation_data_clear();camera.location=head+Vector((0,-1.1,.06));camera.rotation_euler=(head+Vector((0,0,.03))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=55
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.cycles.samples=12
bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
for label,frame in [('open',1),('closed',36)]:
 s.frame_set(frame);s.render.filepath=str(D/(label+'.png'));bpy.ops.render.render(write_still=True)
(D/'check.json').write_text(json.dumps({'character':'Rowan','controls':{n:len(v) for n,v in found.items()},'blink_peak_frames':[36,100],'body_and_speech':'existing animation preserved','unreal_verified':False},indent=2))
