"""Sitting on a seat: clip choices, feet grounding and seat measurement. Model data stays local.

Measured on the lion: Stand_To_Sit shuffles for ~2 s before it sits, so it starts 2 s in; the seated hips
sit ~24 cm lower and ~10 cm further back than standing. The seat is placed from the evaluated seated body
(lowest pelvis/thigh vertex under the hips), so its height always matches the clip on this body."""
import math
import activities
SIT_ACTIONS={'sit_down','sit','sit_talk','stand_up'}|set(activities.extra_actions())
CLIPS={'sit_down':dict(action='sit_down',clip='Stand_To_Sit',clip_start=2.),'sit':dict(action='sit',clip='Sit_Idle'),
 'sit_talk':dict(action='sit',clip='Mixamo_Sitting_Talking'),'stand_up':dict(action='stand_up',clip='Sit_To_Stand_M')}
CLIPS.update(activities.beats())
SEATED=activities.seated_beats()
# Retargeted onto short legs the hips drop almost straight down, so the root eases back onto the seat while
# the feet stay planted: during the descent of sit_down (clip 2.5-3.5 s, i.e. 0.5-1.5 s into the beat) and
# the rise of stand_up (1.5-2.7 s). The seated hips sit at a fixed spot so every shot puts the seat in one place.
DEFAULT_SEAT=dict(back_cm=25,hips_cm=[-2.5,15.2,37.6])
def seated_span(action,start,end):
 """Seconds of a beat in which the lion is fully on the seat (None if never): all of sit/sit_talk, after the
 descent of sit_down, before the rise of stand_up. A shot that opens seated and only stands up still has a seat."""
 if action in SEATED:return start,end
 if action=='sit_down':return (min(start+1.8,end),end) if end-start>1.8 else None
 if action=='stand_up':return start,min(start+.4,end)
 return None
def back_fraction(action,seconds):
 """How far (0..1) the root has eased back onto the seat, seconds into a sit_down / stand_up beat."""
 window=(.4,1.6) if action=='sit_down' else (1.4,2.8)
 u=max(0.,min(1.,(seconds-window[0])/(window[1]-window[0])));u=u*u*(3-2*u)
 return u if action=='sit_down' else 1-u
def segment(action):
 """NLA segment fields for a sit action (clip and its base action)."""
 return dict(CLIPS[action])
def starts_seated(segments):
 """A shot continues a seated pose when its first sit-related beat is not sit_down."""
 first=next((g['action'] for g in segments if g['action'] in SIT_ACTIONS),None)
 return first is not None and first!='sit_down'
def validate(segments,seated=None):
 """Order of sit beats; seated defaults to what the shot implies. Returns whether it ends seated."""
 seated=starts_seated(segments) if seated is None else seated
 for beat in segments:
  action=beat['action']
  if action=='sit_down':
   if seated:raise ValueError('Already seated; stand_up before sitting down again')
   seated=True
  elif action in SEATED and not seated:raise ValueError(action+' needs sit_down first')
  elif action=='stand_up':
   if not seated:raise ValueError('stand_up needs sit_down first')
   seated=False
  elif seated and action not in SEATED:raise ValueError(action+' while seated; stand_up first')
 return seated
def seat_vertices(body):
 """Indices of pelvis/thigh-weighted vertices, excluding the tail (behind and below the hips at rest)."""
 import numpy as np
 names={g.index:g.name for g in body.vertex_groups};W=np.array(body.matrix_world);rest=np.array([v.co for v in body.data.vertices])@W[:3,:3].T+W[:3,3]
 dominant=[names[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices]
 hips=rest[[i for i,n in enumerate(dominant) if n.endswith('Hips')]].mean(0)
 pelvis=np.array([n.endswith(('Hips','Spine','UpLeg')) for n in dominant]);tail=(rest[:,1]>hips[1]+.15)&(rest[:,2]<hips[2]-.2)
 return np.where(pelvis&~tail)[0],np.where(tail)[0]
def measure_seat(scene,rig,body,frames):
 """Seat top (cm) and position (Blender local, forward is -Y) from the seated frames: the lowest pelvis/thigh
 vertex within the hips' footprint. Returns the median over frames and its spread."""
 import bpy,numpy as np
 seat,_=seat_vertices(body);heights=[];centres=[]
 for frame in frames:
  scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
  W=np.array(body.matrix_world);co=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',co);P=co.reshape(-1,3)[seat]@W[:3,:3].T+W[:3,3];evaluated.to_mesh_clear()
  hips=rig.matrix_world@next(b for b in rig.pose.bones if b.name.endswith('Hips')).head
  under=P[(abs(P[:,0]-hips.x)<.15)&(abs(P[:,1]-hips.y)<.15)]
  if len(under):heights.append(float(under[:,2].min()));centres.append((float(hips.x),float(hips.y)))
 if not heights:raise RuntimeError('No seated pelvis vertices found')
 order=np.argsort(heights);mid=order[len(order)//2]
 return {'top_cm':round(heights[mid]*100,1),'spread_cm':round((max(heights)-min(heights))*100,1),'lateral_cm':round(centres[mid][0]*100,1),'forward_cm':round(-centres[mid][1]*100,1)}
def cap_lean(scene,rig,frames,limits):
 """Limit forward tilt (degrees) of spine/neck/head, parents first. The lion's big head turns the clip's
 natural forward lean while sitting down into a deep bow. Returns frames changed per bone."""
 import bpy,math
 from mathutils import Quaternion,Vector
 from box_hands import head_pitch
 chain=[(name,next((b for b in rig.pose.bones if b.name.split(':')[-1]==name),None)) for name in limits];changed={}
 for frame in frames:
  scene.frame_set(frame);bpy.context.view_layer.update()
  for name,bone in chain:
   if bone is None or head_pitch(rig,bone)<=limits[name]:continue
   world=rig.matrix_world.to_quaternion()@bone.matrix.to_quaternion();axis=world@Vector((0,1,0));r=math.hypot(axis.y,axis.z);limit=math.radians(limits[name])
   delta=axis.rotation_difference(Vector((axis.x,-r*math.sin(limit),r*math.cos(limit))));matrix=rig.matrix_world.inverted()@delta.to_matrix().to_4x4()@rig.matrix_world@bone.matrix;matrix.translation=bone.head
   bone.matrix=matrix;bpy.context.view_layer.update();bone.keyframe_insert('rotation_quaternion',frame=frame);changed[name]=changed.get(name,0)+1
 return changed
