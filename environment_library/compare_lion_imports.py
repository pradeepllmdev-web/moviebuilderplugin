import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent.parent;records=[]
for folder in ('lion-run-lipsync','lion-run-blink'):
 record=json.loads((H/'samples'/folder/'native.json').read_text());char=record['characters'][0]
 mesh=unreal.load_asset(char['mesh']);anim=unreal.load_asset(char['animation'])
 names=unreal.AnimationLibrary.get_animation_track_names(anim)
 poses={}
 for n in names:
  t=unreal.AnimationLibrary.get_bone_pose_for_time(anim,n,100/24,False)
  poses[str(n)]=[round(v,5) for vec in (t.translation,t.rotation,t.scale3d) for v in ([vec.x,vec.y,vec.z,vec.w] if hasattr(vec,'w') else [vec.x,vec.y,vec.z])] 
 records.append(poses)
changed=[name for name in records[0] if records[0][name]!=records[1].get(name)]
(H/'samples/lion-run-blink/import-diagnosis.json').write_text(json.dumps({'different_bones_at_frame100':changed,'tracks':[len(r) for r in records]}))
