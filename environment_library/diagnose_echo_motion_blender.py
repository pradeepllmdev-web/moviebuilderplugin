import bpy,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';job=json.loads((D/'job-status.json').read_text());rows=[]
for shot in job['result']['shots']:
 path=Path(shot['workspace'])/'blender/render/shot_001/scene.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False,load_ui=False)
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];stats=[]
 for rig in rigs:
  matrices=[]
  for f in [1,24,48,96,144,192]:
   bpy.context.scene.frame_set(f);matrices.append([tuple(b.matrix.to_quaternion()) for b in rig.pose.bones])
  moving=sum(max(abs(m[i][j]-matrices[0][i][j]) for m in matrices for j in range(4))>1e-4 for i in range(len(matrices[0])))
  stats.append({'rig':rig.name,'moving_bones':moving,'nla_tracks':len(rig.animation_data.nla_tracks) if rig.animation_data else 0})
 manifest=json.loads((Path(shot['performance_package'])/'manifest.json').read_text())
 facial=[{'name':c['name'],'active_channels':sum(max(v['values'])-min(v['values'])>.001 for v in c['facial_channels']),'max_range':max(max(v['values'])-min(v['values']) for v in c['facial_channels'])} for c in manifest['characters']]
 rows.append({'shot':shot['shot_id'],'source':stats,'exported_face':facial})
(D/'motion-diagnosis.json').write_text(json.dumps(rows,indent=2));print('Motion diagnostic summary saved')
