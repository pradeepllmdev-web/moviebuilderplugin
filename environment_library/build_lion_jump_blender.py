import bpy,json,sys,math,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-jump';D.mkdir(exist_ok=True);sys.path.insert(0,str(H.parent/'blendplugin-next/scene_pipeline'));sys.path.insert(0,str(H.parent/'3dobjectnew/server'))
from realistic_rig import build_nla,shared_clips,jump_action
from speech_visemes import sapi_speak
from facerig import visemes
bpy.ops.wm.open_mainfile(filepath=str(H/'samples/lion-grip-ik/scene.blend'));s=bpy.context.scene;s.render.fps=24;s.frame_end=288
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False);rig.hide_viewport=False;rig.animation_data_clear();rig.animation_data_create();rig.location=(0,0,0)
for b in rig.pose.bones:
 for c in list(b.constraints):b.constraints.remove(c)
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
catalog=json.loads((H/'samples/lion-grip-ik/catalog.json').read_text());clip='Procedural anticipation / tuck / landing';duration=2.;end=3.
def seg(action,start,finish,**extra):return dict(action=action,start=start,end=finish,**{'from':[0,0,0],'to':[0,0,0]},yaw_start=0,yaw_end=0,intensity=.35,**extra)
actor=dict(name='Leo',segments=[seg('idle',0,1),seg('jump',1,3),seg('idle',3,8),seg('talk',8,12)])
base=dict(actor,segments=[seg('idle',0,8),seg('talk',8,12)]);warnings=[];build_nla(rig,catalog['Leo'],base,24,warnings,s.camera)
action=jump_action(rig,48,24,'Leo controlled jump',height=0)
if action is None:raise RuntimeError('Corrected rig does not support jump controls')
track=rig.animation_data.nla_tracks.new();track.name='Single controlled jump';strip=track.strips.new('Anticipate takeoff land',25,action);strip.blend_type='REPLACE';strip.extrapolation='NOTHING';strip.blend_in=4;strip.blend_out=6
if hasattr(strip,'action_slot') and action.slots:strip.action_slot=action.slots[0]
feet=[next(b for b in rig.pose.bones if b.name.endswith(side+'Foot')) for side in ('Left','Right')];head=next(b for b in rig.pose.bones if b.name.endswith('Head'))
samples=[]
for f in range(1,289):
 s.frame_set(f);bpy.context.view_layer.update();points=[rig.matrix_world@b.head for b in feet]
 samples.append({'frame':f-1,'feet':[list(p) for p in points],'min_z':min(p.z for p in points)})
takeoff=40;landing=55
route=[]
for row in samples:
 f=row['frame'];u=max(0,min(1,(f-takeoff)/(landing-takeoff)));travel=-60+110*u;arc=.38*4*u*(1-u)
 z=25+10-row['min_z']*100+arc*100
 route.append({'frame':f,'location_cm':[0,travel,z],'u':u,'foot_clearance_cm':arc*100})
speech=sapi_speak('That looked closer from over there.',D/'dialogue','Microsoft David Desktop',1)
lines=[dict(speaker='Leo',to='Leo',text='That looked closer from over there.',start=8,end=11.8,audio=str(speech['wav']),tone='natural',manner='talk')]
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for k in obj.data.shape_keys.key_blocks:k.value=0
_,amp=visemes(lines,288,24);previous=0
for f,v in enumerate(amp,1):
 previous+=max(-.18,min(.18,(1-math.exp(-1/(24*(.065 if v>previous else .14))))*(v-previous)))
 for obj in s.objects:
  if obj.type!='MESH' or not obj.data.shape_keys:continue
  for name,value in [('JawOpen',previous*.8),('LipSeal',max(0,1-previous*.8*3))]:
   key=obj.data.shape_keys.key_blocks.get(name)
   if key:key.value=value;key.keyframe_insert('value',frame=f)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=1,frame_end=288,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
for t in rig.animation_data.nla_tracks:t.mute=True
camera=s.camera;camera.animation_data_clear();camera.data.animation_data_clear();camera.location=(4,-4,2);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=35
plan=dict(title='Leo — The Small Leap',scene_type='motion',duration=12,fps=24,floor_size=[24,24],actors=[actor],obstacles=[],camera=dict(offset=[4,-4,2],lens_mm=35),lighting='day',set='field',lines=lines)
(D/'scene.json').write_text(json.dumps(plan));(D/'catalog.json').write_text(json.dumps(catalog));(D/'route.json').write_text(json.dumps(route));(D/'jump-check.json').write_text(json.dumps({'clip':clip,'clip_duration':duration,'takeoff_frame':takeoff,'landing_frame':landing,'flight_seconds':(landing-takeoff)/24,'max_foot_arc_cm':38,'root_travel_cm':110,'gap_between_rocks_cm':40,'warnings':warnings,'clearance_model':'lowest ankle plus 10 cm sole offset; visual landing check required'},indent=2))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
