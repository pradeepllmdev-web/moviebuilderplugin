import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2';record=json.loads((D/'native.json').read_text())
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world.get_path_name().split('.')[0]!=record['level']:raise RuntimeError('Open improved supercar scene first')
lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_lock_camera_cut_to_viewport(False);lib.set_current_time(0);state={'n':0};token=None
def tick(dt):
 global token
 state['n']+=1
 if state['n']<3:return
 report={}
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  if a.get_actor_label() not in ('Performance_Leo','Supercar_Body','AnimatedSteeringWheel'):continue
  center,extent=a.get_actor_bounds(False);entry={'location':list(a.get_actor_location().to_tuple()),'bounds_center':list(center.to_tuple()),'bounds_extent':list(extent.to_tuple())}
  if a.get_actor_label()=='Performance_Leo':
   c=a.get_component_by_class(unreal.SkeletalMeshComponent);names=[c.get_bone_name(i) for i in range(c.get_num_bones())]
   entry['joints']={str(n):list(c.get_socket_location(n).to_tuple()) for n in names if str(n).lower() in ('hips','head','lefthand','righthand')}
  report[a.get_actor_label()]=entry
 (D/'fit-before.json').write_text(json.dumps(report,indent=2));unreal.unregister_slate_post_tick_callback(token)
token=unreal.register_slate_post_tick_callback(tick)

