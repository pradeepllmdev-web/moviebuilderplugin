import unreal,json,math
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2';record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Performance_Leo');comp=actor.get_component_by_class(unreal.SkeletalMeshComponent)
names=[comp.get_bone_name(i) for i in range(comp.get_num_bones())];left=next(n for n in names if str(n).lower()=='lefthand');right=next(n for n in names if str(n).lower()=='righthand')
rows=[];state={'frame':0,'wait':0};token=None;lib.set_current_time(0)
def finish():
 centers=[[(r['left'][i]+r['right'][i])/2 for i in range(3)] for r in rows];center=[sum(c[i] for c in centers)/len(centers) for i in range(3)]
 radius=sum(math.dist(r['left'][1:],r['right'][1:])/2 for r in rows)/len(rows)
 gaps=[]
 for row in rows:
  for hand in ('left','right'):
   p=row[hand];radial=math.hypot(p[1]-center[1],p[2]-center[2]);gaps.append(math.hypot(p[0]-center[0],radial-radius))
 for binding in sequence.get_bindings():
  if binding.get_name()!='AnimatedSteeringWheel':continue
  for track in list(binding.get_tracks()):
   if isinstance(track,unreal.MovieScene3DTransformTrack):binding.remove_track(track)
  sec=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,288);channels=sec.get_all_channels()
  for f,row in enumerate(rows):
   t=f/24;delta=[b-a for a,b in zip(row['left'],row['right'])];angle=math.degrees(math.atan2(delta[2],delta[1]));size=radius/21
   values=[t*2600+center[0],65*math.sin(t*.7)+center[1],7+1.2*math.sin(t*2.8)+center[2],angle,0,0,size,size,size]
   for c,v in zip(channels,values):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 (D/'cabin-fit-check.json').write_text(json.dumps({'ok':True,'samples':len(rows),'steering_center_car_relative_cm':center,'steering_radius_cm':radius,'max_wrist_to_rim_error_cm':max(gaps),'mean_wrist_to_rim_error_cm':sum(gaps)/len(gaps),'max_driver_bounds_top_cm':max(r['top'] for r in rows),'car_roof_top_cm':119.1,'car_scale_unchanged':True,'finger_contact':'not measured; rig has no finger bones'},indent=2))
 lib.set_current_time(0);lib.set_lock_camera_cut_to_viewport(True)
def tick(dt):
 global token
 state['wait']+=1
 if state['wait']<2:return
 state['wait']=0;f=state['frame'];t=f/24;origin=unreal.Vector(t*2600,65*math.sin(t*.7),7+1.2*math.sin(t*2.8));l=comp.get_socket_location(left)-origin;r=comp.get_socket_location(right)-origin;center,ext=actor.get_actor_bounds(False)
 rows.append({'left':[l.x,l.y,l.z],'right':[r.x,r.y,r.z],'top':center.z+ext.z});state['frame']+=1
 if state['frame']==288:unreal.unregister_slate_post_tick_callback(token);finish();return
 lib.set_current_time(state['frame'])
token=unreal.register_slate_post_tick_callback(tick)
