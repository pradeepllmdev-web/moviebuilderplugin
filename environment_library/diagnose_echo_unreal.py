import unreal,json,math
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';job=json.loads((D/'job-status.json').read_text());records=json.loads((D/'native-records.json').read_text());rows=[]
for shot,record in zip(job['result']['shots'],records):
 if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():raise RuntimeError('Unsaved map; stop diagnosis')
 unreal.EditorLoadingAndSavingUtils.load_map(shot['native_scene']);seq=unreal.load_asset(record['sequence']);unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
 bindings=[]
 for b in seq.get_bindings():
  bindings.append({'name':b.get_name(),'resolved':len(unreal.LevelSequenceEditorBlueprintLibrary.get_bound_objects(seq.get_binding_id(b)))})
 stats=[]
 for char in shot['transfer_characters']:
  anim=unreal.load_asset(char['animation']);names=unreal.AnimationLibrary.get_animation_track_names(anim);moving=0
  for name in names:
   first=unreal.AnimationLibrary.get_bone_pose_for_time(anim,name,0,False)
   last=unreal.AnimationLibrary.get_bone_pose_for_time(anim,name,2,False)
   if (first.translation-last.translation).length()>.01 or abs(first.rotation.x-last.rotation.x)+abs(first.rotation.y-last.rotation.y)+abs(first.rotation.z-last.rotation.z)>.001:moving+=1
  stats.append({'name':char['name'],'moving_imported_tracks':moving})
 rows.append({'shot':shot['shot_id'],'bindings':bindings,'animations':stats})
(D/'unreal-motion-diagnosis.json').write_text(json.dumps(rows,indent=2))

