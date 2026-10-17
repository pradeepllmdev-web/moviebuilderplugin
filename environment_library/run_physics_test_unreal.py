"""Live simulation telemetry; no teleported movement or fabricated collision results."""
import unreal,json,time,traceback,math
from pathlib import Path
H=Path(__file__).resolve().parent/'physics_lab'
state={'status':'starting','samples':[],'events':[],'started_wall':time.time()}
handle=None
def finish(error=None):
 global handle
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 if error:state.update(status='failed',error=error)
 else:
  state['status']='complete'
  first,last=state['samples'][0],state['samples'][-1]
  state['summary']={'travel_cm':{name:last['characters'][name]['location'][0]-first['characters'][name]['location'][0] for name in ['lion','cat']},
                    'crate_displacement_cm':math.dist(first['crate'],last['crate']),
                    'samples':len(state['samples'])}
 (H/'simulation.json').write_text(json.dumps(state,indent=2))
 # Leave simulation paused for inspection/capture; a separate explicit command ends it.
 unreal.GameplayStatics.set_game_paused(unreal.EditorLevelLibrary.get_game_world(),True)
def tick(delta):
 try:
  world=unreal.EditorLevelLibrary.get_game_world()
  if not world:
   if time.time()-state['started_wall']>30:finish('No simulation world created')
   return
  if 'actors' not in state:
   allactors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
   mapping={a.get_actor_label():a for a in allactors}
   if not all(k in mapping for k in ['Physics_lion','Physics_cat','LabPhysicsCrate']):return
   state['actors']={k:mapping[k] for k in ['Physics_lion','Physics_cat','LabPhysicsCrate']}
   state['time_zero']=unreal.GameplayStatics.get_time_seconds(world);state['status']='running'
  now=unreal.GameplayStatics.get_time_seconds(world)-state['time_zero']
  a=state['actors'];sample={'time':now,'characters':{},'crate':list(a['LabPhysicsCrate'].get_actor_location().to_tuple())}
  for name in ['lion','cat']:
   actor=a['Physics_'+name];move=actor.character_movement
   actor.add_movement_input(unreal.Vector(1,0,0),1,True)
   capsule=actor.capsule_component
   pos=actor.get_actor_location()
   sample['characters'][name]={'location':list(pos.to_tuple()),'velocity':list(actor.get_velocity().to_tuple()),
    'falling':move.is_falling(),'capsule_bottom':pos.z-capsule.get_scaled_capsule_half_height()}
  lion=a['Physics_lion'];crate=a['LabPhysicsCrate'];lp=lion.get_actor_location();cp=crate.get_actor_location()
  cat_pos=a['Physics_cat'].get_actor_location();center=unreal.Vector((lp.x+cat_pos.x)/2,0,(lp.z+cat_pos.z)/2)
  camera=center+unreal.Vector(-350,-1100,430)
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(camera,unreal.MathLibrary.find_look_at_rotation(camera,center),unreal.Name())
  # Trigger a one-time physical impulse only after capsule contact stops forward travel.
  gap=cp.x-70-(lp.x+lion.capsule_component.get_scaled_capsule_radius())
  if not state['events'] and 0<=gap<3 and abs(lp.y-cp.y)<100 and abs(lion.get_velocity().x)<30:
   crate.static_mesh_component.add_impulse(unreal.Vector(5000,0,500),unreal.Name(),False)
   state['events'].append({'time':now,'event':'crate_contact_impulse','contact_gap_cm':gap,'impulse_kg_cm_per_s':[5000,0,500]})
  if not state['samples'] or now-state['samples'][-1]['time']>=.1:
   state['samples'].append(sample)
   # Keep actor references private to the callback, never serialize UObject data.
   serial={k:v for k,v in state.items() if k!='actors'}
   (H/'simulation-progress.json').write_text(json.dumps(serial,indent=2))
  if now>14:
   state.pop('actors',None);finish()
 except Exception:
  state.pop('actors',None);finish(traceback.format_exc())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
handle=unreal.register_slate_post_tick_callback(tick)
