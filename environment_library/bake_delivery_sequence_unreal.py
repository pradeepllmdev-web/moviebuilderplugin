"""Bake measured live motion and voiced facial curves into a deterministic Sequencer shot."""
import unreal,json,math,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'delivery_scene';report={'ok':False}
try:
 sim=json.loads((D/'simulation.json').read_text());assert sim['status']=='complete' and sim['hit_delegate_bound']
 scene=json.loads((D/'scene.json').read_text());plan=json.loads((D/'plan.json').read_text());clips=json.loads((D/'import.json').read_text())
 editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert editor.load_level(scene['level'])
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);mapping={a.get_actor_label():a for a in actors.get_all_level_actors()}
 folder=clips['folder']+'/Baked_'+time.strftime('%H%M%S');tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.AnimationLibrary
 fps=24;count=round(plan['duration']*fps);times=[i/fps for i in range(count)]
 sequence=tools.create_asset('Delivery',folder,unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
 sequence.set_display_rate(unreal.FrameRate(fps,1));sequence.set_playback_start(0);sequence.set_playback_end(count)
 for name in ['cat','lion']:
  actor=mapping['Delivery_'+name];actor.character_movement.disable_movement();comp=actor.mesh
  bones=[str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())]
  source=unreal.load_asset(clips['states'][name+'_idle']['animation'])
  animation=unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),folder+'/'+name+'_Performance')
  controller=animation.get_editor_property('controller');controller.open_bracket('Bake recorded delivery performance',False)
  try:
   controller.set_frame_rate(unreal.FrameRate(fps,1),False);controller.set_number_of_frames(unreal.FrameNumber(count-1),False)
   events=[e for e in sim['events'] if e['event']=='animation_transition' and e['character']==name]
   sampled=[]
   for t in times:
    event=next((e for e in reversed(events) if e['time']<=t),events[0]);key=event['action'];entry=clips['states'][key]
    src=unreal.load_asset(entry['animation']);phase=max(0,t-event['time'])*(1.3 if key.endswith('_walk') else 1)
    sampled.append((src,phase%max(.001,entry['duration'])))
   for bone in bones:
    poses=[lib.get_bone_pose_for_time(src,unreal.Name(bone),phase,False) for src,phase in sampled]
    controller.set_bone_track_keys(unreal.Name(bone),[p.get_editor_property('translation') for p in poses],
      [p.get_editor_property('rotation') for p in poses],[p.get_editor_property('scale3d') for p in poses],False)
   morphs={str(n) for n in comp.get_editor_property('skeletal_mesh_asset').get_all_morph_target_names()}
   values={m:[] for m in morphs}
   for t in times:
    line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None)
    jaw=roundness=wide=0
    if line:
     tr=line['track'];i=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*24)))
     jaw=tr['weights']['jawOpen'][i];roundness=tr['weights']['mouthPucker'][i]*.5;wide=tr['weights']['mouthWide'][i]*.5
    blink=max(0,1-abs((t+(0 if name=='cat' else .7))%3.6-1.6)/.13)
    for m in morphs:values[m].append(jaw if m=='JawOpen' else 1-jaw if m in ('JawClose','LipSeal') else blink if m.startswith('Blink') else roundness if m in ('MouthRound','Round') else wide if m in ('MouthWide','Wide') else .15 if m=='Smile' else 0)
   for m,v in values.items():
    if lib.does_curve_exist(animation,m,unreal.RawCurveTrackTypes.RCT_FLOAT):lib.remove_curve(animation,m)
    lib.add_curve(animation,m,unreal.RawCurveTrackTypes.RCT_FLOAT,False);lib.add_float_curve_keys(animation,m,times,v)
  finally:controller.close_bracket(False)
  unreal.EditorAssetLibrary.save_loaded_asset(animation)
  from unreal_bridge.characters import _add_anim_section
  _add_anim_section(sequence.add_possessable(comp),animation,0,count,1)
 def transforms(actor,rows):
  scale=actor.get_actor_scale3d()
  binding=sequence.add_possessable(actor);section=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,count)
  channels=section.get_all_channels();previous=None
  for t,position,rotation in rows:
   frame=min(count-1,max(0,round(t*fps)));rotation=list(rotation)
   if previous:rotation=[r+360*round((p-r)/360) for r,p in zip(rotation,previous)]
   previous=rotation
   for channel,value in zip(channels,list(position)+rotation+[scale.x,scale.y,scale.z]):channel.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  return binding
 samples=sim['samples']
 for key,label in [('cat','Delivery_cat'),('lion','Delivery_lion'),('crate','DeliveryCrate'),('parcel','DeliveryParcel')]:
  actor=mapping[label]
  if isinstance(actor,unreal.StaticMeshActor):actor.static_mesh_component.set_simulate_physics(False)
  transforms(actor,[(s['time'],s[key],s[key+'_rotation']) for s in samples])
 # One cine camera per shot avoids interpolating across editorial cuts.
 cuts=sequence.add_track(unreal.MovieSceneCameraCutTrack)
 groups=[]
 for s in samples:
  if not groups or groups[-1][0]!=s['shot']:groups.append((s['shot'],[]))
  groups[-1][1].append(s)
 for index,(label,rows) in enumerate(groups):
  camera=actors.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(*rows[0]['camera']));camera.set_actor_label('DeliveryShot_'+str(index))
  comp=camera.get_cine_camera_component();fb=comp.get_editor_property('filmback');fb.sensor_width=23.76;fb.sensor_height=13.365;comp.set_editor_property('filmback',fb);comp.set_editor_property('current_focal_length',11.88)
  focus=comp.get_editor_property('focus_settings');focus.focus_method=unreal.CameraFocusMethod.DISABLE;comp.set_editor_property('focus_settings',focus)
  keys=[]
  for s in rows:
   rotation=unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*s['camera']),unreal.Vector(*s['camera_target']))
   keys.append((s['time'],s['camera'],[rotation.roll,rotation.pitch,rotation.yaw]))
  binding=transforms(camera,keys);cut=cuts.add_section();start=0 if index==0 else round(rows[0]['time']*fps)
  end=round(groups[index+1][1][0]['time']*fps) if index+1<len(groups) else count
  cut.set_range(start,end);cut.set_camera_binding_id(sequence.get_binding_id(binding))
 unreal.EditorAssetLibrary.save_loaded_asset(sequence)
 level=scene['level']+'_Baked';version=1
 while unreal.EditorAssetLibrary.does_asset_exist(level):
  version+=1;level=scene['level']+'_Baked_v'+str(version)
 assert unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),level)
 unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
 unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem).fix_actor_references()
 unreal.EditorAssetLibrary.save_loaded_asset(sequence)
 report.update(ok=True,level=level,sequence=sequence.get_path_name(),frames=count,fps=fps,shots=len(groups),method='Measured live Character/rigid-body motion baked to Sequencer; full-rate sampled skeletal and facial curves')
except Exception:report['error']=traceback.format_exc()
(D/'sequence.json').write_text(json.dumps(report,indent=2))
