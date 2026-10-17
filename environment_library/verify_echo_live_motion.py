import unreal,json,traceback
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';record=json.loads((D/'native-records.json').read_text())[0]
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():raise RuntimeError('Save unsaved map changes before playback verification')
unreal.EditorLoadingAndSavingUtils.load_map(record['level'])
sequence=unreal.load_asset(record['sequence']);unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
actors={a.get_actor_label().removeprefix('Performance_'):a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label().startswith('Performance_')}
frames=list(range(192));rows=[];state={'index':0,'wait':0};token=None
unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(frames[0])
def tick(delta):
 global token
 try:
  state['wait']+=1
  if state['wait']<2:return
  state['wait']=0;frame=frames[state['index']];values={}
  for name,actor in actors.items():
   comp=actor.get_component_by_class(unreal.SkeletalMeshComponent);jaw='JawOpen' if name=='Leo' else 'JawClose';hand_name=next((comp.get_bone_name(i) for i in range(comp.get_num_bones()) if 'LeftHand' in str(comp.get_bone_name(i))),None);hand=comp.get_socket_location(hand_name) if hand_name else comp.get_world_location()
   values[name]={'jaw_curve':comp.get_curve_value(jaw,-1),'jaw_override':comp.get_morph_target(jaw),'blink_curve':comp.get_curve_value('BlinkL',-1),'left_hand_cm':[hand.x,hand.y,hand.z]}
  rows.append({'frame':frame,'characters':values});state['index']+=1
  if state['index']>=len(frames):
   summary={}
   for name in actors:
    samples=[row['characters'][name] for row in rows];jaw=[v['jaw_curve'] for v in samples];blink=[v['blink_curve'] for v in samples];hand=[v['left_hand_cm'] for v in samples];origin=hand[0]
    summary[name]={'jaw_min':min(jaw),'jaw_max':max(jaw),'blink_max':max(blink),'hand_max_travel_cm':max(sum((a-b)**2 for a,b in zip(pos,origin))**.5 for pos in hand)}
   (D/'live-motion-check.json').write_text(json.dumps({'ok':True,'frames_checked':len(rows),'summary':summary},indent=2));unreal.unregister_slate_post_tick_callback(token);return
  unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(frames[state['index']])
 except Exception:
  (D/'live-motion-check.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}));unreal.unregister_slate_post_tick_callback(token)
token=unreal.register_slate_post_tick_callback(tick)
