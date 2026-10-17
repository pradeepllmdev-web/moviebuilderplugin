import bpy,json,math
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';job=json.loads((D/'job-status.json').read_text());out=[]
for shot in job['result']['shots']:
 bpy.ops.wm.open_mainfile(filepath=str(Path(shot['workspace'])/'blender/render/shot_001/scene.blend'),use_scripts=False,load_ui=False)
 for rig in [o for o in bpy.context.scene.objects if o.type=='ARMATURE']:
  series={name:[] for name in ['mixamorig:Head','mixamorig:Spine2','mixamorig:LeftArm'] if name in rig.pose.bones}
  for frame in range(1,193):
   bpy.context.scene.frame_set(frame)
   for name in series:series[name].append(rig.pose.bones[name].matrix.to_quaternion().copy())
  summary={}
  for name,values in series.items():
   angles=[]
   for a,b in zip(values,values[1:]):
    angle=a.rotation_difference(b).angle;angles.append(math.degrees(min(angle,abs(2*math.pi-angle))))
   summary[name]={'max_deg_per_frame':max(angles),'p95_deg_per_frame':sorted(angles)[round(len(angles)*.95)]}
  out.append({'shot':shot['shot_id'],'rig':rig.name,'joints':summary})
(D/'jitter-diagnosis.json').write_text(json.dumps(out,indent=2))
