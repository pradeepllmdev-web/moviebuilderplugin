import bpy,json,math
from pathlib import Path
H=Path(__file__).resolve().parent
def sample(file):
 bpy.ops.wm.open_mainfile(filepath=str(H/file),use_scripts=False,load_ui=False);s=bpy.context.scene;data={}
 for name in ('lion','cat'):
  root=bpy.data.objects[name+' race path'];r=next(o for o in root.children_recursive if o.type=='ARMATURE');meshes=[o for o in r.children_recursive if o.type=='MESH' and o.data.shape_keys];body=max(meshes,key=lambda o:len(o.data.vertices));jaw=body.data.shape_keys.key_blocks.get('JawOpen') or body.data.shape_keys.key_blocks.get('JawClose')
  rows=[]
  for f in range(1,s.frame_end+1):
   s.frame_set(f);rows.append({'arms':[tuple(r.pose.bones['mixamorig:'+b].rotation_quaternion) for b in ('LeftArm','LeftForeArm','RightArm','RightForeArm')],'jaw':jaw.value if jaw.name=='JawOpen' else 1-jaw.value,'head':r.pose.bones['mixamorig:Head'].rotation_quaternion.copy(),'root':root.location.copy()})
  data[name]=rows
 return data
old=sample('riverbank-race.blend');new=sample('riverbank-race-acting.blend');report={}
for name in old:
 a=old[name];b=new[name];arm_error=max(abs(x-y) for aa,bb in zip(a,b) for qa,qb in zip(aa['arms'],bb['arms']) for x,y in zip(qa,qb));assert arm_error<1e-6
 race_path_error=max((a[i]['root']-b[i]['root']).length for i in range(92,276));assert race_path_error<1e-5
 assert max(v['jaw'] for v in b)>max(v['jaw'] for v in a)*1.4
 assert abs(b[0]['jaw'])<1e-5 and abs(b[-1]['jaw'])<1e-5
 report[name]={'running_arm_pose_error':arm_error,'shared_race_path_error_m':race_path_error,'old_max_jaw':max(v['jaw'] for v in a),'new_max_jaw':max(v['jaw'] for v in b),'max_added_head_rotation_degrees':max(math.degrees(aa['head'].rotation_difference(bb['head']).angle) for aa,bb in zip(a,b)),'silent_boundaries_passed':True}
(H/'acting-verification.json').write_text(json.dumps(report,indent=2));print('ACTING_VERIFIED '+json.dumps(report))
