"""Blender worker for validated reusable performance plans. Model data stays local."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent.parent
D=Path(sys.argv[sys.argv.index('--')+1]);p=json.loads((D/'plan.json').read_text())
sys.path.insert(0,str(H.parent/'blendplugin-next/scene_pipeline'));sys.path.insert(0,str(H.parent/'3dobjectnew/server'))
from realistic_rig import build_nla,jump_action
from scene_spec import eased
sys.path.insert(0,str(H/'environment_library'))
from character_profiles import profile
profile_data=profile(p['character']);name=profile_data['name']
from speech_visemes import sapi_speak
from facerig import visemes
if p['character']=='cat' and profile_data['source'].endswith('DemoAmber.blend'):
 from realistic_rig import load_realistic
 bpy.ops.wm.read_factory_settings(use_empty=True)
 info=json.loads((H.parent/'blendplugin-next/scene_pipeline/catalog.json').read_text())[profile_data['catalog']]
 load_realistic(info)
else:bpy.ops.wm.open_mainfile(filepath=str(H/profile_data['source']))
s=bpy.context.scene;fps=24;frames=round(sum(g['duration'] for g in p['segments'])*fps);s.render.fps=fps;s.frame_end=frames
rig=next(o for o in s.objects if o.type=='ARMATURE');rig.hide_set(False);rig.hide_viewport=False;rig.animation_data_clear();rig.animation_data_create();rig.location=(0,0,0)
for b in rig.pose.bones:
 for c in list(b.constraints):b.constraints.remove(c)
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
native=json.loads((H.parent/'blendplugin-next/scene_pipeline/catalog.json').read_text())[profile_data['catalog'] or 'DemoAmber'];native['armature']=rig.name;native['gentle_conversation']=False
catalog={name:native}
if p['character']=='rowan':native.update(height_m=1.8,body='male',motion_defaults={'listen':'Idle_3','talk':'Talking','walk':'Meshy_Casual_Walk'})
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for side in ['Left','Right']:
 for a,b in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:
  first=next((x for x in rig.data.edit_bones if x.name.endswith(side+a)),None);second=next((x for x in rig.data.edit_bones if x.name.endswith(side+b)),None)
  if first and second:first.tail=second.head
bpy.ops.object.mode_set(mode='OBJECT')
from sit_actions import SIT_ACTIONS,SEATED,seated_span,segment as sit_segment
sitting=any(g['action'] in SIT_ACTIONS for g in p['segments'])
from sit_actions import DEFAULT_SEAT,back_fraction,starts_seated
seat_profile=dict(DEFAULT_SEAT,**profile_data.get('seat',{}))
segments=[];lines=[];timeline=[];t=0;y=0;rocks=[]
for i,g in enumerate(p['segments']):
 duration=g['duration'];action=g['action'];start=t;end=t+duration;start_y=y
 if action in ['walk','run','box_carry']:y+=g['distance_cm']
 if action=='box_back':y-=g['distance_cm']
 if action=='sit_down':y-=seat_profile['back_cm']
 if action=='stand_up':y+=seat_profile['back_cm']
 if action=='jump':
  y+=70+g['gap_cm'];rocks.extend([{'y':start_y,'height':25},{'y':y,'height':25}])
 # box_back gets its own placeholder strip (consecutive walks share one strip); it becomes a reversed walk below.
 base='walk' if action in ['turn','box_carry'] else 'idle' if action.startswith('box_') else 'run' if action=='circle' else 'idle' if action in ['jump','hold_ball'] else action
 travel=abs(math.radians(g['angle_deg']))*g['radius_cm']/100 if action=='turn' else g.get('distance_cm',0)/100 if action in ['walk','run','box_carry','box_back'] else 2*math.pi*g['radius_cm']/100 if action=='circle' else 0
 segment=dict(action=base,start=start,end=end,**{'from':[0,0,0],'to':[0,travel,0]},yaw_start=0,yaw_end=0,intensity=.3)
 if action in SIT_ACTIONS:segment.update(sit_segment(action))
 segments.append(segment)
 timeline.append(dict(g,start=start,end=end,start_y=start_y,end_y=y))
 if g['dialogue']:
  speech=sapi_speak(g['dialogue'],D/('speech-'+str(i)),'Microsoft David Desktop',1)
  import wave
  with wave.open(str(speech['wav'])) as audio:seconds=audio.getnframes()/audio.getframerate()
  if seconds>duration-.15:raise ValueError('Dialogue for action '+str(i+1)+' is longer than its duration; shorten text or lengthen action')
  lines.append(dict(speaker=name,to=name,text=g['dialogue'],start=start,end=start+seconds,audio=str(speech['wav']),tone='natural',manner='talk'))
 t=end
actor=dict(name=name,segments=segments);warnings=[];build_nla(rig,catalog[name],actor,fps,warnings,s.camera)
for i,g in enumerate(timeline):
 if g['action']!='jump':continue
 action=jump_action(rig,48,fps,'Prompt jump '+str(i),height=0)
 if action is None:raise RuntimeError('Jump controls unavailable')
 tr=rig.animation_data.nla_tracks.new();strip=tr.strips.new('Controlled jump',round(g['start']*fps)+1,action);strip.blend_type='REPLACE';strip.extrapolation='NOTHING';strip.blend_in=4;strip.blend_out=6
 if hasattr(strip,'action_slot') and action.slots:strip.action_slot=action.slots[0]
if warnings:raise RuntimeError('Animation selection needs review: '+'; '.join(warnings))
# A short back-step plays the walk clip in reverse on its own strip; the route moves the root backward.
for index,g in enumerate(timeline):
 if g['action']!='box_back':continue
 track=next((t for t in rig.animation_data.nla_tracks if t.name==f'{index:02d} idle'),None)
 walk=next((s.action for t in rig.animation_data.nla_tracks if t.name.endswith(' walk') for s in t.strips),None) or next((a for a in bpy.data.actions if 'Walk' in a.name and 'stride_m' in a),None)
 if track is None or not track.strips or walk is None:raise RuntimeError('Back-step needs a walk clip and its own strip')
 strip=track.strips[0];first,last=walk.frame_range;length=max(1,last-first)
 # Same speed rule as forward walks: stride matches travel, clamped to look natural.
 cruise=g['distance_cm']/100/max(.1,g['duration']-.5);scale=max(.6,min(1.6,walk.get('stride_m',.4)/cruise))
 strip.action=walk
 if hasattr(strip,'action_slot') and walk.slots:strip.action_slot=walk.slots[0]
 strip.action_frame_start,strip.action_frame_end=first,last;strip.scale=scale
 strip.repeat=max(.1,(1+g['end']*fps-strip.frame_start)/(length*scale));strip.use_reverse=True
if sitting:
 # Mocap sit clips are not in place: align each clip's feet to the previous one so the body never slides.
 from clip_stitch import stitch
 hips_target=Vector((seat_profile['hips_cm'][0]/100,-seat_profile['hips_cm'][1]/100,seat_profile['hips_cm'][2]/100)) if starts_seated(p['segments']) else None
 stitch_report=stitch(s,rig,first_hips=hips_target,first_feet=p['segments'][0]['action']=='sit_down')
from footlock import lock_feet
foot_reports=[]
for beat_index,g in enumerate(timeline):
 if g['action'] in ['idle','talk','hold_ball','box_pickup','box_hold','box_setdown','box_bump','sit','sit_talk']:
  start=round(g['start']*fps)+1
  # Let the incoming stance settle before selecting its planted-foot anchors.
  # Otherwise a stop may pin a lifted foot from the walk/idle crossfade.
  if beat_index and timeline[beat_index-1]['action'] in ['walk','run','circle','turn','box_carry','box_back']:start+=round(.65*fps)
  foot_reports.append(lock_feet(rig,start,round(g['end']*fps),fps))
box_path=None
if any(g['action'].startswith('box_') for g in timeline) or p.get('box_state'):
 from box_timeline import build as make_box_path
 box_path=make_box_path(p['segments'],p.get('actor_position_cm',[0,0]),p.get('box_state'),fps,p.get('facing_yaw_deg',0),profile_data.get('box'),p.get('box_scene_stands'))
if sitting:
 # Feet stay planted while the root eases back onto the seat (and forward again when standing up).
 old_action=rig.animation_data.action;old_slot=rig.animation_data.action_slot;rig.animation_data.action=None
 for f in range(frames):
  time=f/fps;g=next((g for g in timeline if g['start']<=time<g['end']),timeline[-1]);y=g['start_y']
  if g['action'] in ['sit_down','stand_up']:y+=(g['end_y']-g['start_y'])*(back_fraction('sit_down',time-g['start']) if g['action']=='sit_down' else 1-back_fraction('stand_up',time-g['start']))
  rig.location=(0,-y/100,0);rig.keyframe_insert('location',frame=f+1)
 for beat in timeline:
  if beat['action'] in ['sit_down','stand_up']:foot_reports.append({'moving_'+beat['action']:lock_feet(rig,round(beat['start']*fps)+1,round(beat['end']*fps),fps)})
 rig.animation_data.action=old_action
 if old_action and old_slot:rig.animation_data.action_slot=old_slot
 rig.location=(0,0,0);s.frame_set(1);bpy.context.view_layer.update()
if any(g['action'] in ['box_carry','box_back'] for g in timeline):
 old_action=rig.animation_data.action;old_slot=rig.animation_data.action_slot;rig.animation_data.action=None
 # Straight carries lock feet in the heading frame: signed travel along local forward (-Y).
 for row in box_path['rows']:
  rig.location=(0,-row['travel_cm']/100,0);rig.keyframe_insert('location',frame=row['frame']+1)
 for beat in timeline:
  if beat['action'] in ['box_carry','box_back']:foot_reports.append({'moving_'+beat['action']:lock_feet(rig,round(beat['start']*fps)+1,round(beat['end']*fps),fps)})
 rig.animation_data.action=old_action
 if old_action and old_slot:rig.animation_data.action_slot=old_slot
 rig.location=(0,0,0);s.frame_set(1);bpy.context.view_layer.update()
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  facial_names=json.loads((H/'samples/mpfb-character/face-profile.json').read_text())['mapping'].values() if p['character']=='rowan' else None
  for k in obj.data.shape_keys.key_blocks:
   # MPFB macro targets define the character's neutral anatomy, not expressions.
   if facial_names is None or k.name in facial_names:k.value=0
speech_shapes,amp=visemes(lines,frames,fps);previous=0
for f,v in enumerate(amp,1):
 previous+=max(-.18,min(.18,(1-math.exp(-1/(fps*(.065 if v>previous else .14))))*(v-previous)))
 for obj in s.objects:
  if obj.type!='MESH' or not obj.data.shape_keys:continue
  for name,value in [('JawOpen',previous*.8),('JawClose',1-previous*.8),('LipClose',max(0,1-previous*.8*3)),('LipSeal',max(0,1-previous*.8*3)),('jawOpen',previous*.8)]:
   key=obj.data.shape_keys.key_blocks.get(name)
   if key:key.value=value;key.keyframe_insert('value',frame=f)
  if p['character']=='rowan':
   from human_speech import speech_values
   for name,value in speech_values(speech_shapes,f-1,previous).items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=value;key.keyframe_insert('value',frame=f)
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
feet_bones=[b for b in rig.pose.bones if b.name.endswith(('LeftFoot','RightFoot'))];feet_rest=min((rig.matrix_world@b.bone.head_local).z for b in feet_bones)
route=[];previous_yaw=0
# Lion walking shots get the Tail bone too (see tail_rig.py); the old tail dragged below the feet and lifted the whole body.
tail_walk=p['character']=='lion' and not sitting and all(g['action'] in ('idle','talk','walk','run','circle') for g in timeline)
if tail_walk:
 import numpy as np
 from tail_rig import _tail_vertices
 tail_body=max(meshes,key=lambda o:len(o.data.vertices));tail_index,_rest=_tail_vertices(tail_body,np.array(rig.matrix_world@next(b for b in rig.pose.bones if b.name.endswith('Hips')).bone.head_local))
 keep=np.ones(len(tail_body.data.vertices),bool);keep[tail_index]=False;ground_levels={}
turn_path=None
if any(g['action']=='turn' for g in timeline) or p.get('motion_heading'):
 from turn_routes import route as make_turn_route
 turn_path=make_turn_route(p['segments'],fps,p.get('facing_yaw_deg',0))
for f in range(frames):
 time=f/fps;g=next((g for g in timeline if g['start']<=time<g['end']),timeline[-1]);u=max(0,min(1,(time-g['start'])/(g['end']-g['start'])));x=0;y=g['start_y'];yaw=0;arc=0;ground=0
 if g['action'] in ['walk','run','box_carry']:y+=(g['end_y']-y)*eased(segments,timeline.index(g),u)
 if g['action'] in ['sit_down','stand_up']:y+=(g['end_y']-y)*(1-back_fraction(g['action'],time-g['start']) if g['action']=='stand_up' else back_fraction(g['action'],time-g['start']))
 if g['action']=='circle':
  a=2*math.pi*u;x=g['radius_cm']*(1-math.cos(a));y+=g['radius_cm']*math.sin(a);yaw=-math.degrees(a)
 if g['action']=='jump':
  v=max(0,min(1,((time-g['start'])*fps-15)/15));y+=(g['end_y']-y)*v;arc=38*4*v*(1-v);ground=25
 if rocks and g['action']!='jump':
  ground=25 if any(abs(y-r['y'])<=35 for r in rocks) else 0
 if p.get('partner_gaze'):yaw=p['partner_gaze']['body_yaw_deg']
 else:yaw+=p.get('facing_yaw_deg',0)
 if turn_path:
  x,y=turn_path[f]['location_cm'][:2];yaw=turn_path[f]['yaw']
 # Unwrap heading so interpolation never spins the opposite way at 360 degrees.
 while yaw-previous_yaw>180:yaw-=360
 while yaw-previous_yaw< -180:yaw+=360
 previous_yaw=yaw
 s.frame_set(f+1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 if sitting:
  # Seated poses fold the tail and thighs below the feet: ground on the feet, not the lowest vertex.
  minimum=min((rig.matrix_world@b.head).z for b in feet_bones)-feet_rest
 elif tail_walk:
  # Ground on the body without the tail; the tail bone is solved against this level afterwards.
  e=tail_body.evaluated_get(deps);co=np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',co);Wm=np.array(e.matrix_world)
  minimum=min([float((co.reshape(-1,3)[keep]@Wm[2,:3]+Wm[2,3]).min())]+[min((o.evaluated_get(deps).matrix_world@Vector(v)).z for v in o.evaluated_get(deps).bound_box) for o in meshes if o is not tail_body]);ground_levels[f+1]=minimum
 else:minimum=min(min((o.evaluated_get(deps).matrix_world@Vector(v)).z for v in o.evaluated_get(deps).bound_box) for o in meshes)
 route.append({'frame':f,'location_cm':[x,y,ground+arc-minimum*100],'yaw':yaw})
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=1,frame_end=frames,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
for tr in rig.animation_data.nla_tracks:tr.mute=True
if sitting:
 # Seat height and position come from the evaluated seated body, so the bench always fits the clip.
 from sit_actions import measure_seat
 body=max(meshes,key=lambda o:len(o.data.vertices));seated=[f for g in timeline for span in [seated_span(g['action'],g['start'],g['end'])] if span for f in range(round(span[0]*fps)+1,round(span[1]*fps)+1,6)]
 seat=measure_seat(s,rig,body,seated);seat.update(frame=seated[0]-1 if seated else 0,stitch=stitch_report);(D/'seat.json').write_text(json.dumps(seat))
 from sit_actions import cap_lean
 lean=cap_lean(s,rig,[f for g in timeline if g['action'] in ['sit_down','stand_up'] for f in range(round(g['start']*fps)+1,round(g['end']*fps)+1)],{'Spine1':25,'Spine2':25,'Neck':15,'Head':30})
 seat['lean_capped_frames']=lean;(D/'seat.json').write_text(json.dumps(seat))
 # The tail must clear the ground and the bench (fixed in the world; the rig stays at the origin).
 import numpy as np
 from tail_rig import rig_tail
 anchor=route[seat['frame']]['location_cm'][1]
 def tail_floor(frame):
  centre_y=-(seat['forward_cm']-3)/100+(route[frame-1]['location_cm'][1]-anchor)/100;centre_x=seat['lateral_cm']/100;top=seat['top_cm']/100
  return lambda P:np.where((abs(P[:,0]-centre_x)<.37)&(abs(P[:,1]-centre_y)<.18),top,0.)
 tail_report=rig_tail(s,rig,body,list(range(1,frames+1)),tail_floor,fps=fps);(D/'tail-check.json').write_text(json.dumps(tail_report))
 # Body measurements for activity feasibility (cached per character) and the drink pose.
 import body_measures
 if seated:
  calm=next((g for g in timeline if g['action'] in ('drink','sit')),None);reference=round((calm['start']+.5)*fps)+1 if calm else seated[len(seated)//2];measures=body_measures.measure(s,rig,body,reference)
  if calm:body_measures.save(p['character'],measures)  # only a calm seated pose is representative; never cache a transition frame
  (D/'body-measures.json').write_text(json.dumps(measures))
  if any(g['action']=='drink' for g in timeline):
   import drink_actions
   solved=drink_actions.feasibility(measures)
   (D/'drink-feasibility.json').write_text(json.dumps(solved))
   if not solved.get('ok'):raise RuntimeError('Drinking is not feasible for this body: '+json.dumps({k:solved.get(k) for k in ('reason','hand_to_cup_cm','limits')}))
   drink_actions.apply(s,rig,body,timeline,fps,solved,D,reference)
if tail_walk:
 from tail_rig import rig_tail
 tail_report=rig_tail(s,rig,tail_body,list(range(1,frames+1)),lambda frame:(lambda P,level=ground_levels[frame]:np.full(len(P),level)),fps=fps);(D/'tail-check.json').write_text(json.dumps(tail_report))
from pose_continuity import blend_previous_pose,save_pose
blend_previous_pose(s,rig,p.get('carry_pose'),fps)
if any(g['action']=='hold_ball' for g in timeline):
 from hand_prop import hold_ball
 grip=hold_ball(s,rig,frames);(D/'grip-check.json').write_text(json.dumps(grip))
 if not grip['ok']:raise RuntimeError('Palm attachment check failed')
if box_path:
 from box_hands import apply as box_arms,body_clearance
 box=box_path
 # The body and independent prop share exact root positions and headings.
 for row,box_row in zip(route,box['rows']):row['location_cm'][:2]=box_row['root_cm'][:2];row['yaw']=box_row['yaw']
 report=box_arms(s,rig,box);(D/'box-contact-check.json').write_text(json.dumps(report))
 if not report['ok'] and any(row['contact'] for row in box['rows']):raise RuntimeError('Box wrist IK could not reach its contact targets')
 clearance=body_clearance(s,rig,box);clearance['stands']=box['stand_clearance'];(D/'box-clearance-check.json').write_text(json.dumps(clearance))
 if not clearance['ok']:raise RuntimeError('Box intersects the body by '+str(round(clearance['deepest']['depth_cm'],1))+'cm at frame '+str(clearance['deepest']['frame'])+'; adjust the carry profile')
 (D/'box-trajectory.json').write_text(json.dumps(box));(D/'box-end-state.json').write_text(json.dumps(box['end_state']))
# A point gaze uses the same scene coordinates for both characters.
from scene_gaze import partner_angles
for g in timeline:
 if g.get('look_at')=='point':
  target=g['look_target_cm'];angles=partner_angles(p.get('actor_position_cm',[0,0]),target[:2],p.get('facing_yaw_deg',0),profile_data.get('eye_height_cm',163 if p['character']=='lion' else 132),target[2])
  if angles['remaining_yaw_error_deg']>10:raise ValueError('Point target requires a body turn; choose a forward target or change facing_yaw_deg')
  g['look_yaw_deg']=-angles['head_yaw_deg'];g['look_pitch_deg']=-angles['head_pitch_deg']
  if g is timeline[0]:g['look_from_yaw_deg']=g['look_yaw_deg'];g['look_from_pitch_deg']=g['look_pitch_deg']
# Layer attention on the already baked pose; preserve root, arms and jaw.
# Convert semantic partner looks into bounded head offsets before the existing blend.
if p.get('partner_gaze'):
 for g in timeline:
  if g.get('look_at')=='partner':g['look_yaw_deg']=-p['partner_gaze']['head_yaw_deg'];g['look_pitch_deg']=-p['partner_gaze']['head_pitch_deg']
  elif g.get('look_at')=='forward':g['look_yaw_deg']=0;g['look_pitch_deg']=0
  if g is timeline[0] and g.get('look_at')=='partner':g['look_from_yaw_deg']=g['look_yaw_deg'];g['look_from_pitch_deg']=g['look_pitch_deg']
 (D/'gaze-check.json').write_text(json.dumps(p['partner_gaze']))

from scene_attention import attention
head=next((b for b in rig.pose.bones if b.name.endswith('Head')),None)
head_check=[];last_q=None
if head:
 for f in range(1,frames+1):
  s.frame_set(f);bpy.context.view_layer.update();yaw,pitch=attention(timeline,(f-1)/fps);base=head.rotation_quaternion.copy();world=(rig.matrix_world@head.matrix).to_quaternion();vertical=world.inverted()@Vector((0,0,1));right=world.inverted()@Vector((1,0,0));q=base@Quaternion(vertical,math.radians(yaw))@Quaternion(right,math.radians(pitch))
  if p.get('carry_pose') and p['character']!='rowan' and f<=round(.4*fps):
   u=(f-1)/max(1,round(.4*fps)-1);u=u*u*(3-2*u);q=base@Quaternion(vertical,math.radians(yaw*u))@Quaternion(right,math.radians(pitch*u))
  if last_q is not None and last_q.dot(q)<0:q=-q
  head.rotation_quaternion=q
  if p['character']=='rowan' and (p.get('partner_gaze') or any(g.get('look_at')=='point' for g in timeline)):
   # Aim the actual face-forward axis, cancelling inherited downward clip tilt.
   bpy.context.view_layer.update();local_forward=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,-1,0));current=head.matrix.to_quaternion()@local_forward
   desired=Vector((math.sin(math.radians(yaw))*math.cos(math.radians(pitch)),-math.cos(math.radians(yaw))*math.cos(math.radians(pitch)),-math.sin(math.radians(pitch))))
   matrix=current.rotation_difference(desired).to_matrix().to_4x4()@head.matrix;matrix.translation=head.head;head.matrix=matrix;bpy.context.view_layer.update();q=head.rotation_quaternion.copy()
  if last_q is not None and last_q.dot(q)<0:head.rotation_quaternion=-q;q=-q
  head.keyframe_insert('rotation_quaternion',frame=f);last_q=q.copy();head_check.append([yaw,pitch])
if head:blend_previous_pose(s,rig,p.get('carry_pose'),fps,bone_names={head.name})
(D/'attention-check.json').write_text(json.dumps({'ok':head is not None,'yaw_range_deg':[min((v[0] for v in head_check),default=0),max((v[0] for v in head_check),default=0)],'pitch_range_deg':[min((v[1] for v in head_check),default=0),max((v[1] for v in head_check),default=0)],'channels':'head rotation only; blink disabled'}))
if p['character']=='rowan':
 from human_face_controls import animate_eyes,prepare_export
 animate_eyes(s,frames,fps,timeline)
 prepare_export(s,rig,H)
else:
 from animal_expression_controls import animate as animal_expression
 (D/'facial-expression-check.json').write_text(json.dumps(animal_expression(s,frames,fps,timeline,speech_shapes)))
 if p.get('eye_life') and profile_data.get('eyes'):
  from eye_life import animate as eye_life
  (D/'eye-life-check.json').write_text(json.dumps(eye_life(s,frames,fps,timeline,p['title'],profile_data['eyes'])))

if any(g['action']=='hold_ball' for g in timeline):
 from safe_shape_join import join_animated_shapes
 from hand_prop import verify_joined_anchor
 joined=join_animated_shapes(s,rig,frames);grip['joined_anchor_error_cm']=verify_joined_anchor(s,rig,joined,grip['palm_offset_local'],frames);grip['ok']=grip['ok'] and grip['joined_anchor_error_cm']<.5;(D/'grip-check.json').write_text(json.dumps(grip))
 if not grip['ok']:raise RuntimeError('Export mesh join moved the prop')
from animation_safety import inspect_motion
safety=inspect_motion(s,rig,frames);(D/'motion-safety.json').write_text(json.dumps(safety))
if not safety['ok']:raise RuntimeError('Animation safety check failed: '+str(safety))
camera=s.camera
if camera is None:
 data=bpy.data.cameras.new('Performance Camera');camera=bpy.data.objects.new('Performance Camera',data);s.collection.objects.link(camera);s.camera=camera
camera.animation_data_clear();camera.data.animation_data_clear();camera.location=(4,-4,2);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=35
plan=dict(title=p['title'],scene_type='motion',duration=frames/fps,fps=fps,floor_size=[40,40],actors=[actor],obstacles=[],camera=dict(offset=[4,-4,2],lens_mm=35),lighting='day',set='field',lines=lines,events=p.get('events',[]))
(D/'catalog.json').write_text(json.dumps(catalog));(D/'scene.json').write_text(json.dumps(plan));(D/'route.json').write_text(json.dumps(route));(D/'rocks.json').write_text(json.dumps(rocks));(D/'build-check.json').write_text(json.dumps({'ok':True,'frames':frames,'warnings':warnings,'stationary_foot_lock':foot_reports,'blink':'native ARKit enabled' if p['character']=='rowan' else 'disabled: unverified Unreal deformation','grounding':'evaluated mesh bounds; no rigid-body physics'}))
save_pose(s,rig,D/'end-pose.json')
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
