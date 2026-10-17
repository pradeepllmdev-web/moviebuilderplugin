import unreal,json,math
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library');poses=[]
for key in ['82af6b137d4a495ab8643983461627b2','940944df98d34181912600bb1644fa09']:
 m=json.loads((H/'movie_jobs'/key/'ready.json').read_text());r=json.loads((H/'scene_jobs'/m['shots'][0]['scene_id']/'native.json').read_text());row={}
 for c in r['characters']:
  anim=unreal.load_asset(c['animation']);name=next(n for n in unreal.AnimationLibrary.get_animation_track_names(anim) if str(n).lower().endswith('head'));q=unreal.AnimationLibrary.get_bone_pose_for_time(anim,name,2,False).rotation;row[c['name']]=[q.x,q.y,q.z,q.w]
 poses.append(row)
result={name:math.degrees(2*math.acos(min(1,abs(sum(a*b for a,b in zip(poses[0][name],poses[1][name])))))) for name in poses[0]}
(H/'partner-head-import-check.json').write_text(json.dumps({'head_pose_difference_deg':result}))
