import unreal,json,math
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library');rows={}
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if not actor.get_actor_label().startswith('Performance_'):continue
 comp=actor.get_component_by_class(unreal.SkeletalMeshComponent)
 if not comp:continue
 names=[str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())];head=next(n for n in names if n.lower().endswith('head'));front=next(n for n in names if n.lower().endswith('headfront'));a=comp.get_socket_location(head);b=comp.get_socket_location(front);rows[actor.get_actor_label()]={'head':[a.x,a.y,a.z],'forward':[b.x-a.x,b.y-a.y,b.z-a.z]}
keys=list(rows)
for i,name in enumerate(keys):
 a=rows[name];b=rows[keys[1-i]];dx=b['head'][0]-a['head'][0];dy=b['head'][1]-a['head'][1];fx,fy=a['forward'][:2];a['forward_yaw']=math.degrees(math.atan2(fy,fx));a['target_yaw']=math.degrees(math.atan2(dy,dx));a['yaw_error_deg']=(a['target_yaw']-a['forward_yaw']+180)%360-180
(H/'partner-facing-check.json').write_text(json.dumps(rows))
