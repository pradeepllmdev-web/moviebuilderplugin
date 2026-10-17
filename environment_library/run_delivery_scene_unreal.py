"""Live Character movement, bound hit events, carry prop, facial tracks and shot direction."""
import unreal,json,time,math,traceback
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene'
plan=json.loads((D/'plan.json').read_text());clips=json.loads((D/'import.json').read_text())['states']
state={'status':'starting','time':0,'events':[],'samples':[],'started_wall':time.time(),'hit_delegate_bound':False}
runtime={};handle=None
def save(filename):
 (D/filename).write_text(json.dumps(state,indent=2))
def stop(error=None):
 global handle
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 state['status']='failed' if error else 'complete'
 if error:state['error']=error
 if state['samples']:
  first,last=state['samples'][0],state['samples'][-1]
  state['summary']={'crate_displacement_cm':math.dist(first['crate'],last['crate']),
   'cat_travel_cm':math.dist(first['cat'],last['cat']),'lion_travel_cm':math.dist(first['lion'],last['lion'])}
 save('simulation.json')
 unreal.GameplayStatics.set_game_paused(runtime['world'],True)
def play(name,action,rate=1):
 if runtime.get(name+'_action')==action:return
 actor=runtime[name];actor.mesh.override_animation_data(unreal.load_asset(clips[action]['animation']),True,True,0,rate)
 runtime[name+'_action']=action
 state['events'].append({'time':state['time'],'event':'animation_transition','character':name,'action':action})
def hit(actor,other,impulse,result):
 try:
  if not other or other.get_actor_label()!='DeliveryCrate':return
  now=state['time']
  if actor==runtime['cat'] and 'cat_hit_time' not in runtime:
   runtime['cat_hit_time']=now;runtime['cat'].character_movement.stop_movement_immediately()
   runtime['crate'].static_mesh_component.add_impulse(unreal.Vector(0,650,80),unreal.Name(),False)
   state['events'].append({'time':now,'event':'cat_crate_engine_hit','normal_impulse':list(impulse.to_tuple())})
  elif actor==runtime['lion'] and 'lion_hit_time' not in runtime:
   runtime['lion_hit_time']=now;runtime['lion'].character_movement.stop_movement_immediately()
   runtime['crate'].static_mesh_component.add_impulse(unreal.Vector(4000,0,100),unreal.Name(),False)
   state['events'].append({'time':now,'event':'lion_crate_engine_hit','normal_impulse':list(impulse.to_tuple())})
 except Exception:runtime['callback_error']=traceback.format_exc()
def move_toward(name,target):
 actor=runtime[name];pos=actor.get_actor_location();delta=unreal.Vector(target[0]-pos.x,target[1]-pos.y,0);distance=math.hypot(delta.x,delta.y)
 if distance<12:actor.character_movement.stop_movement_immediately();return False
 direction=unreal.Vector(delta.x/distance,delta.y/distance,0)
 actor.add_movement_input(direction,1,True)
 actor.set_actor_rotation(unreal.Rotator(yaw=math.degrees(math.atan2(direction.y,direction.x))-90),False)
 return True
def tick(delta):
 try:
  if not runtime:
   world=unreal.EditorLevelLibrary.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)}
   if not all('Delivery_'+n in actors for n in ['cat','lion']):return
   runtime.update(world=world,cat=actors['Delivery_cat'],lion=actors['Delivery_lion'],crate=actors['DeliveryCrate'],parcel=actors['DeliveryParcel'],zero=unreal.GameplayStatics.get_time_seconds(world))
   for name in ['cat','lion']:
    actor=runtime[name];actor.on_actor_hit.add_callable(hit)
    actor.character_movement.set_editor_property('enable_physics_interaction',False)
    actor.character_movement.max_walk_speed=clips[name+'_walk']['speed_cm_s']*1.3
    names=[str(actor.mesh.get_bone_name(i)) for i in range(actor.mesh.get_num_bones())]
    runtime[name+'_hands']={side:next(n for n in names if n.endswith(side+'Hand')) for side in ['Left','Right']}
    runtime[name+'_morphs']={str(n) for n in actor.mesh.get_editor_property('skeletal_mesh_asset').get_all_morph_target_names()}
   state['hit_delegate_bound']=True
  if runtime.get('callback_error'):raise RuntimeError(runtime['callback_error'])
  now=unreal.GameplayStatics.get_time_seconds(runtime['world'])-runtime['zero'];state['time']=now;state['status']='running'
  cat,lion=runtime['cat'],runtime['lion']
  if now<1:play('cat','cat_idle')
  elif 'cat_hit_time' not in runtime:
   walking=move_toward('cat',[285,-350]);play('cat','cat_walk' if walking else 'cat_idle',1.3)
  elif now-runtime['cat_hit_time']<1.1:
   cat.character_movement.stop_movement_immediately();play('cat','cat_recoil')
  else:cat.character_movement.stop_movement_immediately();play('cat','cat_idle')
  if now<8.5:play('lion','lion_idle')
  elif 'lion_hit_time' not in runtime:
   cp=runtime['crate'].get_actor_location()
   target=[180,-425] if lion.get_actor_location().y<-440 else [cp.x,cp.y-25]
   walking=move_toward('lion',target);play('lion','lion_walk' if walking else 'lion_help',1.3)
  else:
   lion.character_movement.stop_movement_immediately();play('lion','lion_help' if now-runtime['lion_hit_time']<2.5 else 'lion_idle')
  # Carry follows the actual wrist bones. Recoil retains the parcel instead of faking a pickup.
  hands=runtime['cat_hands'];left=cat.mesh.get_socket_location(hands['Left']);right=cat.mesh.get_socket_location(hands['Right'])
  parcel=runtime['parcel'];parcel.set_actor_location((left+right)*.5+unreal.Vector(0,0,8),False,False)
  parcel.set_actor_rotation(cat.get_actor_rotation(),False)
  for name,actor in [('cat',cat),('lion',lion)]:
   line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=now<l['start']+l['duration']),None)
   jaw=roundness=wide=0
   if line:
    tr=line['track'];i=min(tr['frames']-1,max(0,round((now-line['start']+tr['lead'])*24)))
    jaw=tr['weights']['jawOpen'][i];roundness=tr['weights']['mouthPucker'][i]*.5;wide=tr['weights']['mouthWide'][i]*.5
   blink=max(0,1-abs((now+(0 if name=='cat' else .7))%3.6-1.6)/.13)
   for morph in runtime[name+'_morphs']:
    value=jaw if morph=='JawOpen' else 1-jaw if morph in ('JawClose','LipSeal') else blink if morph.startswith('Blink') else roundness if morph in ('MouthRound','Round') else wide if morph in ('MouthWide','Wide') else .15 if morph=='Smile' else 0
    actor.mesh.set_morph_target(morph,value,False)
  if now<4:camera=unreal.Vector(800,-1200,390);target=unreal.Vector(250,-570,100);shot='arrival'
  elif now<8.5:camera=unreal.Vector(620,-370,215);target=cat.get_actor_location()+unreal.Vector(0,0,35);shot='cat reaction'
  elif now<15:camera=unreal.Vector(650,-680,220);target=lion.get_actor_location()+unreal.Vector(0,0,35);shot='lion helps'
  else:camera=unreal.Vector(650,-350,220);target=(cat.get_actor_location()+lion.get_actor_location())*.5+unreal.Vector(0,0,25);shot='together'
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(camera,unreal.MathLibrary.find_look_at_rotation(camera,target),unreal.Name())
  if not state['samples'] or now-state['samples'][-1]['time']>.1:
   state['samples'].append({'time':now,'cat':list(cat.get_actor_location().to_tuple()),'lion':list(lion.get_actor_location().to_tuple()),
    'crate':list(runtime['crate'].get_actor_location().to_tuple()),'cat_speed':cat.get_velocity().length(),
    'lion_speed':lion.get_velocity().length(),'cat_action':runtime['cat_action'],'lion_action':runtime['lion_action'],'shot':shot,
    'cat_falling':cat.character_movement.is_falling(),
    'cat_rotation':list(cat.get_actor_rotation().to_tuple()),'lion_rotation':list(lion.get_actor_rotation().to_tuple()),
    'crate_rotation':list(runtime['crate'].get_actor_rotation().to_tuple()),
    'parcel':list(parcel.get_actor_location().to_tuple()),'parcel_rotation':list(parcel.get_actor_rotation().to_tuple()),
    'camera':list(camera.to_tuple()),'camera_target':list(target.to_tuple())})
   save('progress.json')
  if now>=plan['duration']:stop()
 except Exception:stop(traceback.format_exc())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
handle=unreal.register_slate_post_tick_callback(tick)
