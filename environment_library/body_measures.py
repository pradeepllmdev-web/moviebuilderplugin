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
def measure_standing(scene,rig,meshes,frame=1):
 """Standing-body dimensions (cm, rig space, forward is -Y) used to space two actors: torso front/back/half width and arm reach.
 Uses the skinned mesh with the most torso-weighted vertices (clothing can be a separate mesh) in its rest shape."""
 import bpy,numpy as np
 scene.frame_set(frame);bpy.context.view_layer.update();torso=['Hips','Spine','Spine1','Spine2','Neck']
 best=None
 for body in (meshes if isinstance(meshes,(list,tuple)) else [meshes]):
  names={g.index:g.name.split(':')[-1] for g in body.vertex_groups}
  dominant=np.array([names[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices])
  mask=np.isin(dominant,torso)|np.char.endswith(dominant,'Shoulder')
  if best is None or mask.sum()>best[0].sum():best=(mask,body)
 mask,body=best;co=np.empty(len(body.data.vertices)*3);body.data.vertices.foreach_get('co',co);Wb=np.array(body.matrix_world);P=(co.reshape(-1,3)@Wb[:3,:3].T+Wb[:3,3])*100;q=P[mask]
 def bone(n):
  b=next(x for x in rig.pose.bones if x.name.endswith(n));return np.array(rig.matrix_world@b.head)*100
 up,fore,hand=bone('RightArm'),bone('RightForeArm'),bone('RightHand')
 whole=[]
 for obj in (meshes if isinstance(meshes,(list,tuple)) else [meshes]):   # everything ahead of the chest incl. head and mane, arms excluded
  nm={g.index:g.name for g in obj.vertex_groups};cc=np.empty(len(obj.data.vertices)*3);obj.data.vertices.foreach_get('co',cc);Wo=np.array(obj.matrix_world);PP=(cc.reshape(-1,3)@Wo[:3,:3].T+Wo[:3,3])*100
  keep=[bool(v.groups) and any(k in nm.get(max(v.groups,key=lambda g:g.weight).group,'') for k in ('Hips','Spine','Neck','Head','head')) and 'Arm' not in nm.get(max(v.groups,key=lambda g:g.weight).group,'') for v in obj.data.vertices]
  if any(keep):whole.append(float(-PP[keep][:,1].min()))
 return dict(whole_front_cm=round(max(whole),1) if whole else round(float(-q[:,1].min()),1),front_cm=round(float(-q[:,1].min()),1),back_cm=round(float(q[:,1].max()),1),half_width_cm=round(float(np.abs(q[:,0]).max()),1),
  arm_reach=round(float(np.linalg.norm(fore-up)+np.linalg.norm(hand-fore)),1),shoulder_z=round(float(up[2]),1),height_cm=round(float(P[:,2].max()),1))
def load_standing(character):
 return load(character+'-standing')
def ensure_standing_in_build(character,scene,rig,body):
 if not (CACHE/(character+'-standing.json')).exists():save(character+'-standing',measure_standing(scene,rig,body))
