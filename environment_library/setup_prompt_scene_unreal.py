"""Unreal scene adapter: transforms, camera, materials and optional jump platforms."""
import unreal,json,re,traceback,sys,math
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import importlib,character_profiles
importlib.reload(character_profiles)
from character_profiles import profile
request=json.loads((H/'demos/scene-active.json').read_text());D=H/'scene_jobs'/request['id']
try:
 r=json.loads((D/'native.json').read_text());p=json.loads((D/'plan.json').read_text());routes=json.loads((D/'routes.json').read_text());profile_map=json.loads((D/'profiles.json').read_text());route=next(iter(routes.values()));sequence=unreal.load_asset(r['sequence']);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.open_level_sequence(sequence)
 for character in r['characters']:
  if profile_map[character['name']]=='rowan':
   import human_eye_material
   importlib.reload(human_eye_material)
   (D/'eye-material-check.json').write_text(json.dumps(human_eye_material.apply_eye_material(character['mesh'])))
  key=profile_map[character['name']];reference=profile(key)['material'];mesh=unreal.load_asset(character['mesh']);old=unreal.load_asset(reference) if reference else None
  if old:
   normalize=lambda n:re.sub(r'_\d{3}$','',str(n));source={normalize(slot.material_slot_name):slot.material_interface for slot in old.get_editor_property('materials')};slots=list(mesh.get_editor_property('materials'))
   for slot in slots:
    if normalize(slot.material_slot_name) in source:slot.set_editor_property('material_interface',source[normalize(slot.material_slot_name)])
   mesh.set_editor_property('materials',slots);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 if p['camera'] in ['close','reaction'] and not p.get('focus'):
  speakers=[a['character'] for a in p.get('actors',[]) if any(g.get('dialogue') for g in a['segments'])]
  p['focus']=speakers[0] if speakers else p.get('character','lion')
 rocks=json.loads((D/'rocks.json').read_text())
 if rocks:
  asset=next(a for a in json.loads((H/'assets/prompt-catalog.json').read_text())['assets'] if a['id']=='rock.27e7c46097');scan=unreal.load_asset(asset['path']);folder=r['level'].rsplit('/',1)[0]
  task=unreal.AssetImportTask();task.filename=str(H.parent/'samples/lion-scramble/RockStep.fbx');task.destination_path=folder;task.destination_name='LandingRock';task.automated=True;task.save=True;ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH;ui.import_as_skeletal=False;ui.import_materials=False;task.options=ui;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);rock=unreal.load_asset(folder+'/LandingRock');rock.set_material(0,scan.get_material(0));unreal.EditorAssetLibrary.save_loaded_asset(rock)
  for row in rocks:
   a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(row.get('x',0),row['y'],12.5));a.set_actor_label('JumpPlatform');a.static_mesh_component.set_static_mesh(rock);a.set_actor_scale3d(unreal.Vector(1.2,.7,.25))
 if 'rowan' in profile_map.values():
  for actor_plan in p.get('actors',[]):
   x,y=actor_plan.get('position_cm',[0,0]);light=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='Acting_Fill_'+actor_plan['character']),None) or actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(x+160,y+100,235));light.set_actor_label('Acting_Fill_'+actor_plan['character']);light.set_actor_rotation(unreal.MathLibrary.make_rot_from_x(unreal.Vector(x,y,150)-light.get_actor_location()),False)
   light.light_component.set_editor_property('intensity',5);light.light_component.set_editor_property('source_width',160);light.light_component.set_editor_property('source_height',160)
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();ignore=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.SkeletalMeshActor)];ground_cache={};contact_warnings=[]
 for name,rows in routes.items():
  previous_ground=None;height=profile(profile_map[name])['height_cm'];last=None
  for row in rows:
   x,y,z=row['location_cm'];ground=0
   if p.get('environment_id'):
    key=(round(x/5),round(y/5))
    if key not in ground_cache:
     hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,1000),unreal.Vector(x,y,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,True)
     hit=hit.to_tuple() if hit is not None else (False,)
     if not hit[0]:raise RuntimeError('No collision ground below route; choose a different placement or enable environment collision')
     if hit[7].z<.7:raise RuntimeError('Route crosses a steep surface; edit the route before building')
     ground_cache[key]=hit[5].z
    ground=ground_cache[key]
    if previous_ground is not None and abs(ground-previous_ground)>18:raise RuntimeError('Route crosses a step over 18 cm; choose a clear ground path')
    row['location_cm'][2]+=ground;previous_ground=ground
   if row['frame']%8==0 and not rocks:
    point=unreal.Vector(x,y,ground+height/2+4)
    if last is not None:
     hit=unreal.SystemLibrary.capsule_trace_single(world,last,point,28,height/2-2,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore,unreal.DrawDebugTrace.NONE,True)
     hit=hit.to_tuple() if hit is not None else (False,)
     if hit[0]:raise RuntimeError('Route capsule intersects environment geometry. Move the character or shorten its route.')
    last=point
 (D/'environment-contact-check.json').write_text(json.dumps({'ok':True,'ground_samples':len(ground_cache),'checks':'ground trace, slope, step and capsule path sweep; not physical simulation'}))
 import wind_reaction_unreal
 importlib.reload(wind_reaction_unreal)
 (D/'wind-check.json').write_text(json.dumps(wind_reaction_unreal.add_wind_cues(sequence,actors,p.get('events',[]),r['level'].rsplit('/',1)[0],len(route))))
 import box_props_unreal
 importlib.reload(box_props_unreal)
 (D/'box-prop-check.json').write_text(json.dumps(box_props_unreal.apply(sequence,actors,r['level'].rsplit('/',1)[0],D,routes)))
 import sit_props_unreal
 importlib.reload(sit_props_unreal)
 (D/'seat-prop-check.json').write_text(json.dumps(sit_props_unreal.apply(sequence,actors,r['level'].rsplit('/',1)[0],D,routes)))
 import drink_props_unreal
 importlib.reload(drink_props_unreal)
 (D/'drink-prop-check.json').write_text(json.dumps(drink_props_unreal.apply(sequence,actors,r['level'].rsplit('/',1)[0],D,routes)))
 for camera_actor in actors.get_all_level_actors():
  if isinstance(camera_actor,unreal.CineCameraActor):
   component=camera_actor.get_cine_camera_component();film=component.get_editor_property('filmback');film.sensor_width=36;film.sensor_height=20.25;component.set_editor_property('filmback',film);component.set_editor_property('aspect_ratio',16/9)
 for binding in sequence.get_bindings():
  for track in binding.get_tracks():
   if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
    for section in track.get_sections():
     for key in section.get_all_channels()[0].get_keys():key.set_value(32 if p['camera']=='full' else 42 if p['camera'] in ['close','reaction'] else 40)
 camera_samples=[]
 from camera_checks import in_frame
 # Box shots: a heading-relative side camera on the side where the box never covers the face.
 box_view=None;box_files=list(D.glob('actor_*/box-trajectory.json'))
 if box_files and len(routes)==1:
  import box_camera
  importlib.reload(box_camera)
  box_data=json.loads(box_files[0].read_text());box_view=box_camera.choose(route,box_data,p['camera'],135)
  (D/'box-camera-check.json').write_text(json.dumps(box_view))
 for b in sequence.get_bindings():
  character_name=b.get_name().removeprefix('Performance_')
  if character_name not in routes and b.get_name()!='Transferred_Camera':continue
  for t in list(b.get_tracks()):
   if isinstance(t,unreal.MovieScene3DTransformTrack):b.remove_track(t)
   if isinstance(t,unreal.MovieSceneFloatTrack) and str(t.get_property_name())=='CurrentFocalLength':
    for sec in t.get_sections():
     for k in sec.get_all_channels()[0].get_keys():k.set_value(32 if p['camera']=='full' else 42 if p['camera'] in ['close','reaction'] else 40)
  sec=b.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,len(route));channels=sec.get_all_channels()
  selected=routes[character_name] if character_name in routes else route
  for row in selected:
   x,y,z=row['location_cm']
   if character_name in routes:values=[x,y,z,0,0,row['yaw'],1,1,1]
   else:
    focused=[rows for name,rows in routes.items() if p.get('focus','both')=='both' or profile_map[name]==p.get('focus')] or list(routes.values());cx=sum(rows[row['frame']]['location_cm'][0] for rows in focused)/len(focused);cy=sum(rows[row['frame']]['location_cm'][1] for rows in focused)/len(focused);close=p['camera'] in ['close','reaction'];lion_close=close and (p.get('focus')=='lion' or (not p.get('focus') and p.get('character')=='lion'));scale=1.3 if lion_close else 1;pos=unreal.Vector(cx+(230*scale if close else 520 if len(routes)>1 else 420),cy+(150*scale if close else 220),(175 if lion_close else 180) if close else 230);target=unreal.Vector(cx,cy,(135 if lion_close else 145) if close else 105)
    if any(g['action']=='hold_ball' for a in p.get('actors',[]) for g in a['segments']):pos=unreal.Vector(cx-200,cy+180,130);target=unreal.Vector(cx,cy,105)
    if box_view:
     position,aim=box_camera.view(route[row['frame']]['location_cm'],route[row['frame']]['yaw'],p['camera'],box_view['side']);pos=unreal.Vector(*position);target=unreal.Vector(*aim)
    focused_actor=next((a for a in p.get('actors',[]) if a['character']==p.get('focus')),None)
    if close and focused_actor and any(g.get('look_at') in ['partner','point'] for g in focused_actor['segments']):
     other=next(a for a in p['actors'] if a['character']!=focused_actor['character']);dx=other['position_cm'][0]-focused_actor['position_cm'][0];dy=other['position_cm'][1]-focused_actor['position_cm'][1];length=math.hypot(dx,dy);side=1 if dx>=0 else -1;pos=unreal.Vector(cx+dx/length*(280 if focused_actor['character']=='lion' else 140)-dy/length*(210 if focused_actor['character']=='lion' else 120)*side,cy+dy/length*(280 if focused_actor['character']=='lion' else 140)+dx/length*(210 if focused_actor['character']=='lion' else 120)*side,165);target.z=120 if focused_actor['character']=='lion' else 145 if focused_actor['character']=='rowan' else 132
    if row['frame']%12==0 and not any(e['type']=='branch_fall' for e in p.get('events',[])):
     for actor_name,actor_rows in routes.items():
      if close and profile_map[actor_name]!=p.get('focus'):continue
      root=actor_rows[row['frame']]['location_cm'];height=profile(profile_map[actor_name])['height_cm'];focal=42 if close else 32 if p['camera']=='full' else 40
      head=[root[0],root[1],root[2]+height*.9];feet=[root[0],root[1],root[2]+5]
      camera_samples.append({'actor':actor_name,'frame':row['frame'],'head_visible':in_frame(head,[pos.x,pos.y,pos.z],[target.x,target.y,target.z],focal),'feet_visible':in_frame(feet,[pos.x,pos.y,pos.z],[target.x,target.y,target.z],focal) if not close else None,'head_visible_wide':in_frame(head,[pos.x,pos.y,pos.z],[target.x,target.y,target.z],28),'feet_visible_wide':in_frame(feet,[pos.x,pos.y,pos.z],[target.x,target.y,target.z],28)})
    rot=unreal.MathLibrary.make_rot_from_x(target-pos);values=[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]
   for c,v in zip(channels,values):c.add_key(unreal.FrameNumber(row['frame']),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 import branch_event_unreal
 importlib.reload(branch_event_unreal)
 branch_event_unreal.frame_camera(sequence,p.get('events',[]),len(route))
 adaptive_focal=None
 if p['camera']=='full' and any(not v['head_visible'] or v['feet_visible'] is False for v in camera_samples):
  adaptive_focal=28
  for binding in sequence.get_bindings():
   for track in binding.get_tracks():
    if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='CurrentFocalLength':
     for section in track.get_sections():
      for key in section.get_all_channels()[0].get_keys():key.set_value(adaptive_focal)
  for sample in camera_samples:sample['head_visible']=sample['head_visible_wide'];sample['feet_visible']=sample['feet_visible_wide']
 if p.get('lookdev')=='soft_portrait':
  for actor_name,rows in routes.items():
   light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector());light.set_actor_label('Performance_Portrait_'+actor_name);light.light_component.set_editor_property('intensity',.5);light.light_component.set_editor_property('source_width',180);light.light_component.set_editor_property('source_height',180)
   section=sequence.add_possessable(light).add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,len(route));channels=section.get_all_channels()
   for row in rows:
    x,y,z=row['location_cm'];pos=unreal.Vector(x+160,y+140,z+230);target=unreal.Vector(x,y,z+145);rot=unreal.MathLibrary.make_rot_from_x(target-pos)
    for channel,value in zip(channels,[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):channel.add_key(unreal.FrameNumber(row['frame']),value)
 (D/'appearance-check.json').write_text(json.dumps({'preset':p.get('lookdev','default'),'new_scene_lighting_only':True,'source_character_modified':False,'note':'Lighting improves readability; fur topology, teeth and eyelids still depend on the source rig'}))
 (D/'camera-check.json').write_text(json.dumps({'samples':len(camera_samples),'adaptive_focal_mm':adaptive_focal,'head_outside_samples':sum(not v['head_visible'] for v in camera_samples),'feet_outside_samples':sum(v['feet_visible'] is False for v in camera_samples),'scope':'Approximate profile-height framing; branch-specific camera requires visual review; no occlusion or silhouette check'}))
 for a in actors.get_all_level_actors():
  if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',4);a.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=-135,roll=0),False)
  if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',2)
 unreal.EditorAssetLibrary.save_directory(r['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.set_current_time(0);lib.set_lock_camera_cut_to_viewport(True)
 (D/'ready.json').write_text(json.dumps({'ok':True,'level':r['level'],'sequence':r['sequence'],'duration':len(route)/24,'characters':list(profile_map),'camera':p['camera'],'warnings':['Animation grounding only; no collision simulation','Rowan native eyelids enabled; lion/cat blinks disabled']}))
except Exception:
 error=traceback.format_exc()
 # Preserve this newly generated copy on a rejected path; never discard user work.
 try:
  if 'r' in globals() and r['level'].startswith('/Game/StudioProduction/'):
   unreal.EditorAssetLibrary.save_directory(r['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
   unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 except Exception:pass
 (D/'ready.json').write_text(json.dumps({'ok':False,'error':error}))
