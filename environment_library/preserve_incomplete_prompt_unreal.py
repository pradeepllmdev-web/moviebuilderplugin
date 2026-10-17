import unreal,time
# Preserve the incomplete map created by the failed unified-test build.
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
labels=[a.get_actor_label() for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()]
if world.get_path_name().split('.')[0].startswith('/Temp/') and any(label.startswith('Kit_building_') for label in labels):
 unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/EnvironmentDemos/IncompletePromptTest_'+time.strftime('%Y%m%d_%H%M%S'))
else:raise RuntimeError('Unexpected map; preserve user work and stop')
