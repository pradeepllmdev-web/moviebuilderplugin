"""Create independent spawnable shot copies and one continuous master preview."""
import unreal,json,uuid,traceback,re
from pathlib import Path
H=Path(__file__).resolve().parent
request=json.loads((H/'master-build-request.json').read_text()) if (H/'master-build-request.json').exists() else None
if request:
 if not re.fullmatch('[a-f0-9]{32}',request.get('movie_id','')) or not re.fullmatch('[a-f0-9]{32}',request.get('request_id','')):raise ValueError('Invalid master request')
 (H/'master-build-request.json').unlink()
D=H/'movie_jobs'/(request['movie_id'] if request else (H/'conversation-active.txt').read_text().strip())
output=D/('master-result-'+request['request_id']+'.json' if request else 'master-result.json')

try:
 if request and request.get('save_generated'):
  generated=json.loads((D/'ready.json').read_text())
  for item in generated['shots']:unreal.EditorAssetLibrary.save_directory(item['report']['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
 if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():raise RuntimeError('Unreal has unsaved changes. Save them before building the master. No level switched.')
 movie=json.loads((D/'ready.json').read_text());folder='/Game/StudioMovies/'+uuid.uuid4().hex
 unreal.EditorAssetLibrary.make_directory(folder)
 lib=unreal.LevelSequenceEditorBlueprintLibrary;sub=unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem);copies=[];checks=[]
 for i,item in enumerate(movie['shots']):
  r=item['report']
  if not unreal.EditorLoadingAndSavingUtils.load_map(r['level']):raise RuntimeError('Cannot load shot')
  seq=unreal.EditorAssetLibrary.duplicate_asset(r['sequence'],folder+'/Shot_'+str(i+1))
  lib.open_level_sequence(seq);lib.pause();converted=0
  for binding in list(seq.get_bindings()):
   if binding.get_parent().is_valid():continue
   result=sub.convert_to_spawnable(binding);converted+=len(result)
  if converted<len(r['characters'])+1:raise RuntimeError('Shot did not convert both characters and camera')
  for track in list(seq.get_tracks()):
   if isinstance(track,unreal.MovieSceneAudioTrack):seq.remove_track(track)
  unreal.EditorAssetLibrary.save_loaded_asset(seq);copies.append(seq);checks.append({'shot':i+1,'spawnables':converted})
 # Use a copy of the common forest, with the source performance actors removed.
 if not unreal.EditorLoadingAndSavingUtils.load_map(movie['shots'][0]['report']['level']):raise RuntimeError('Cannot load forest')
 level=folder+'/MasterLevel'
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if not unreal.EditorLoadingAndSavingUtils.save_map(world,level):raise RuntimeError('Cannot save master level')
 if not unreal.EditorLoadingAndSavingUtils.load_map(level):raise RuntimeError('Cannot open master copy')
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for actor in actors.get_all_level_actors():
  if actor.get_actor_label().startswith(('Performance_','Transferred_','WindCue_')):actors.destroy_actor(actor)
 master=unreal.AssetToolsHelpers.get_asset_tools().create_asset('Master',folder,unreal.LevelSequence,unreal.LevelSequenceFactoryNew());master.set_display_rate(unreal.FrameRate(24,1));master.set_playback_start(0)
 track=master.add_track(unreal.MovieSceneCinematicShotTrack);offset=0
 for seq,item in zip(copies,movie['shots']):
  count=round(item['report']['duration']*24);section=track.add_section();section.set_sequence(seq);section.set_range(offset,offset+count);section.set_shot_display_name(item['title']);offset+=count
 master.set_playback_end(offset)
 task=unreal.AssetImportTask();task.filename=str(D/'soundtrack.wav');task.destination_path=folder;task.destination_name='ConversationMix';task.automated=True;task.save=True
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);sound=unreal.load_asset(folder+'/ConversationMix')
 if not sound:raise RuntimeError('Cannot import mixed soundtrack')
 audio=master.add_track(unreal.MovieSceneAudioTrack).add_section();audio.set_sound(sound);audio.set_range(0,offset)
 unreal.EditorAssetLibrary.save_directory(folder,only_if_is_dirty=True,recursive=True);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 lib.open_level_sequence(master);lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(0)
 report={'ok':True,'level':level,'sequence':master.get_path_name().split('.')[0],'duration':offset/24,'shots':checks,'audio':'dialogue, twig snap and original procedural music'}
 movie['master']=report;(D/'ready.json').write_text(json.dumps(movie,indent=2));(D/'master-result.json').write_text(json.dumps(report,indent=2));output.write_text(json.dumps(report,indent=2))
except Exception:output.write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
