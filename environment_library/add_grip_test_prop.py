import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-grip-ik';record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence'])
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder.Cylinder')
wood=unreal.load_asset('/Game/StudioProduction/f1596734e0254f07b3244639515253f0/BranchWood')
branch=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,40,28));branch.set_actor_label('FixedGripBranch')
branch.static_mesh_component.set_static_mesh(cylinder);branch.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
if wood:branch.static_mesh_component.set_material(0,wood)
section=sequence.add_possessable(branch).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,192);channels=section.get_all_channels()
for row in json.loads((D/'branch-path.json').read_text()):
 x,y,z=row['position']
 for channel,value in zip(channels,[x*100,-y*100,z*100,0,90,0,.11,.11,.95]):channel.add_key(unreal.FrameNumber(row['frame']),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
stand=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,40,11));stand.set_actor_label('LowPracticeStump')
stand.static_mesh_component.set_static_mesh(cylinder);stand.set_actor_scale3d(unreal.Vector(.38,.38,.22))
if wood:stand.static_mesh_component.set_material(0,wood)
unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(96)
(D/'prop-ready.json').write_text(json.dumps({'ok':True,'grip_points_cm':[[-28,40,32],[28,40,32]],'support':'low practice stump','duration':8}))
