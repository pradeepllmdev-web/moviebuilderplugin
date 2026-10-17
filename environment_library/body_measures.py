"""Body measurements (cm, rig space: forward is -Y) taken from the evaluated seated body, cached per character.

Everything an activity needs from the body comes from here, so a new character is a profile entry plus one
measuring pass, and feasibility checks run from the cache without Blender."""
import json
from pathlib import Path
CACHE=Path(__file__).resolve().parent/'body_measures'
def load(character):
 path=CACHE/(character+'.json');return json.loads(path.read_text()) if path.exists() else None
def save(character,measures):
 CACHE.mkdir(exist_ok=True);(CACHE/(character+'.json')).write_text(json.dumps(measures,indent=1))
def measure(scene,rig,body,frame):
 """Seated-frame measurements; needs Blender."""
 import bpy,numpy as np
 scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps)
 co=np.empty(len(evaluated.data.vertices)*3);evaluated.data.vertices.foreach_get('co',co);W=np.array(evaluated.matrix_world);P=(co.reshape(-1,3)@W[:3,:3].T+W[:3,3])*100
 names={g.index:g.name.split(':')[-1] for g in body.vertex_groups}
 dominant=np.array([names[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices])
 def bone(name):
  b=next(x for x in rig.pose.bones if x.name.endswith(name));return [round(float(v),2) for v in np.array(rig.matrix_world@b.head)*100]
 def region(mask):
  q=P[mask];return dict(y_front=round(float(q[:,1].min()),1),z_top=round(float(q[:,2].max()),1),z_bottom=round(float(q[:,2].min()),1)) if len(q) else None
 head=np.char.endswith(dominant,'Head')|np.char.endswith(dominant,'headfront');q=P[head];tip=q[q[:,1].argmin()]
 up,fore,hand=np.array(bone('RightArm')),np.array(bone('RightForeArm')),np.array(bone('RightHand'))
 return dict(frame=frame,bones={n:bone(n) for n in ['Hips','Spine','Spine1','Spine2','Neck','Head','RightArm','RightForeArm','RightHand']},
  snout_tip=[round(float(v),1) for v in tip],arm_reach=round(float(np.linalg.norm(fore-up)+np.linalg.norm(hand-fore)),1),
  torso=region(np.isin(dominant,['Hips','Spine','Spine1','Spine2'])),thighs=region(np.char.endswith(dominant,'UpLeg')),
  lower_legs=region(np.char.endswith(dominant,'Leg')&~np.char.endswith(dominant,'UpLeg')),feet=region(np.char.endswith(dominant,'Foot')|np.char.endswith(dominant,'ToeBase')))
