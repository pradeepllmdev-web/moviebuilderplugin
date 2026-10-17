import bpy,json,math
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';job=json.loads((D/'job-status.json').read_text());rows=[]
for shot in job['result']['shots']:
 bpy.ops.wm.open_mainfile(filepath=str(Path(shot['workspace'])/'blender/render/shot_001/scene.blend'),use_scripts=False,load_ui=False)
 for rig in [o for o in bpy.context.scene.objects if o.type=='ARMATURE']:
  stats={}
  for name in ['mixamorig:Head','mixamorig:Neck','mixamorig:LeftArm','mixamorig:RightArm']:
   if name not in rig.pose.bones:continue
   scales=[];positions=[]
   for f in range(1,193):
    bpy.context.scene.frame_set(f);bone=rig.pose.bones[name];scale=bone.matrix.to_scale();scales.append(list(scale));positions.append(list((rig.matrix_world@bone.matrix).translation))
   stats[name]={'scale_min':[min(s[i] for s in scales) for i in range(3)],'scale_max':[max(s[i] for s in scales) for i in range(3)]}
  rows.append({'shot':shot['shot_id'],'rig':rig.name,'rig_scale':list(rig.scale),'bones':stats})
(D/'deformation-diagnosis.json').write_text(json.dumps(rows,indent=2))
