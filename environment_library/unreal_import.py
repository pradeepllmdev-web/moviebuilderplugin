"""Unreal Editor script: rebuild an exported scene as a Level Sequence with real assets.

In the Unreal Editor (Python enabled):
    import unreal_import; unreal_import.run(r'<export_dir>/ruins.ue.json', map_path=r'<repo>/environment_library/unreal_asset_map.json')
Outside Unreal (dry run, prints what it would build):
    python unreal_import.py <export_dir>/ruins.ue.json [map.json]

What it builds: a LevelSequence '/Game/Movie/LS_<scene>' at the scene's frame rate and range; for every actor a spawnable/possessable with a transform track keyed from the exported (already
Unreal-axis, centimetre) keys; characters get a skeletal-animation section per NLA clip (play rate = 1/strip scale) with the animation asset from the map; cameras are CineCameraActors with
focal-length keys and a camera-cut track from the cut list; lights keep colour/intensity (with keys when animated); audio strips become audio sections. Placeholder ids that have no entry in
unreal_asset_map.json fall back to the proxy FBX meshes imported from the export, so the scene always plays; adding a mapping upgrades that one thing without touching anything else.
The Unreal API calls are written against 5.3+ (LevelSequence, MovieScene tracks, EditorActorSubsystem) and have not been run inside Unreal yet; the DryRun backend exercises all the logic around them."""
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ue_common as ub
def unique_name(exists,base,folder='/Game/Movie'):
 """never overwrite: LS_<scene>, LS_<scene>_2, ... first name whose asset does not exist"""
 n=0
 while True:
  name=base if n==0 else '%s_%d'%(base,n+1)
  if not exists('%s/%s'%(folder,name)):return name
  n+=1
def guard(u,environ=None):
 """refuse to touch the editor unless it is the verification project with nothing unsaved (same rules as open_saved_unreal.py / build_prompt_unreal.py)"""
 env=environ if environ is not None else os.environ
 mark=env.get('UNREAL_PROJECT_MARK','LatestSceneVerification')
 if env.get('UNREAL_IMPORT_ANY_PROJECT')!='1' and mark not in str(u.Paths.get_project_file_path()):
  raise RuntimeError('wrong project: expected %r in the project path (set UNREAL_IMPORT_ANY_PROJECT=1 to override)'%mark)
 lib=u.EditorLoadingAndSavingUtils
 if lib.get_dirty_map_packages() or lib.get_dirty_content_packages():raise RuntimeError('save or discard the unsaved Unreal changes first; nothing was imported')
class DryRun:
 """records what would be created; same interface as the Unreal backend"""
 def __init__(self):self.log=[];self.counts={'actors':0,'transform_keys':0,'anim_sections':0,'cuts':0,'audio':0,'unmapped':[],'mapped':[]}
 def sequence(self,name,fps,start,end):self.log.append(('sequence',name,fps,start,end))
 def spawn(self,a,asset,mapped):
  self.counts['actors']+=1;(self.counts['mapped'] if mapped else self.counts['unmapped']).append(a['asset_key']);self.log.append(('spawn',a['name'],a['role'],asset))
  return a['id']
 def transform_keys(self,h,frames,loc,rot,scale):self.counts['transform_keys']+=len(frames)
 def lens_keys(self,h,frames,lens,sensor=None):self.log.append(('lens',h,len(frames)))
 def light(self,h,light):self.log.append(('light',h,light['type']))
 def anim_section(self,h,asset,start,end,rate,mapped):self.counts['anim_sections']+=1;(self.counts['mapped'] if mapped else self.counts['unmapped']).append(os.path.basename(asset))
 def camera_cut(self,name,h,start,end):self.counts['cuts']+=1
 def audio(self,name,path,start,vol):self.counts['audio']+=1
 def save(self):self.log.append(('save',))
 def environment(self,doc):pass
 self_fit={}
 def ensure_characters(self,doc):pass
 def character_asset(self,tag):return None
 def clip_asset(self,tag,clip):return None
 sequence_path=None
class UnrealBackend:
 """thin wrapper over the Unreal editor Python API (see the module docstring for the version note)"""
 def __init__(self,check=True):
  import unreal;self.u=unreal
  if check:guard(unreal)   # the editor bridge passes check=False: it has its own busy/undo rules and never overwrites
  self.seq=None;self.bind={};self.sequence_path=None;self.warnings=[];self.spawned=[];self.tag=None;self.scene=None;self.character_assets={};self.clip_assets={};self.actors={};self.self_fit={}
 def sequence(self,name,fps,start,end):
  u=self.u;self.scene=name;self.tag='moviebuilder:%s'%name;self.purge()
  tools=u.AssetToolsHelpers.get_asset_tools();self.seq=tools.create_asset(unique_name(u.EditorAssetLibrary.does_asset_exist,'LS_%s'%name),'/Game/Movie',u.LevelSequence,u.LevelSequenceFactoryNew())
  self.sequence_path=self.seq.get_path_name();self.seq.set_display_rate(u.FrameRate(fps,1));self.seq.set_playback_start(start);self.seq.set_playback_end(end+1);self.fps=fps
 def environment(self,doc):
  """place the joined environment mesh (one static mesh holding every static object at its world position) at the origin"""
  u=self.u;name=(doc.get('environment') or {}).get('mesh')
  if not name:return
  sub=u.get_editor_subsystem(u.EditorActorSubsystem)
  tries=[(n,s) for n in (name,'environment') for s in ('','1','2')]   # a single-mesh FBX import is named after the file
  for n,suffix in tries:
   path='/Game/Proxy/%s/%s%s'%(self.scene,n,suffix)
   if not u.EditorAssetLibrary.does_asset_exist(path):continue
   obj=u.load_asset(path)
   if not isinstance(obj,u.StaticMesh):continue
   actor=sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));actor.set_actor_label('%s/Environment'%self.scene);actor.tags=[u.Name(self.tag)]
   try:actor.set_folder_path('MovieBuilder/%s'%self.scene)
   except Exception:pass
   actor.static_mesh_component.set_static_mesh(obj);self.spawned.append(actor);return
  self.warnings.append('environment mesh %s was not found under /Game/Proxy/%s (import environment.fbx first)'%(name,self.scene))
 def autoplay_actor(self):
  """a LevelSequenceActor in the level that plays the sequence automatically when Play is pressed (and can be scrubbed in the editor)"""
  u=self.u
  try:
   sub=u.get_editor_subsystem(u.EditorActorSubsystem);act=sub.spawn_actor_from_class(u.LevelSequenceActor,u.Vector(0,0,0));act.set_actor_label('%s/Player'%self.scene);act.tags=[u.Name(self.tag)]
   try:act.set_folder_path('MovieBuilder/%s'%self.scene)
   except Exception:pass
   act.set_sequence(self.seq)
   ps=act.get_editor_property('playback_settings');ps.set_editor_property('auto_play',True);act.set_editor_property('playback_settings',ps)
   self.spawned.append(act)
  except Exception as e:self.warnings.append('auto-play actor not created: %s %s'%(type(e).__name__,str(e)[:100]))
 def purge(self):
  """remove the actors a previous import of this scene left in the level (they carry the moviebuilder:<scene> tag); nothing else is touched"""
  u=self.u;sub=u.get_editor_subsystem(u.EditorActorSubsystem);n=0
  for act in sub.get_all_level_actors():
   if any(str(t)==self.tag for t in act.tags):sub.destroy_actor(act);n+=1
  return n
 def abort(self):
  """undo a failed import: destroy the actors spawned so far and delete the half-built sequence"""
  u=self.u;sub=u.get_editor_subsystem(u.EditorActorSubsystem)
  for act in self.spawned:
   try:sub.destroy_actor(act)
   except Exception:pass
  if self.sequence_path:
   try:u.EditorAssetLibrary.delete_asset(self.sequence_path.split('.')[0])
   except Exception:pass
 def ensure_characters(self,doc):
  """import each character's skeletal mesh and every clip it uses (once; existing assets are kept) and remember where they ended up"""
  u=self.u;folder=doc.get('_dir')
  if not folder:return
  lib=u.EditorAssetLibrary
  for c in doc['characters']:
   tag=c['name'];mesh_dir='/Game/Characters/%s'%tag;mesh_path='%s/character_%s'%(mesh_dir,tag);skel_path='%s/character_%s_Skeleton'%(mesh_dir,tag)
   try:
    if not lib.does_asset_exist(mesh_path):
     self._import(os.path.join(folder,c['skeletal_mesh']),mesh_dir,mesh=True)
    self.character_assets[tag]=mesh_path if lib.does_asset_exist(mesh_path) else None
    skel=u.load_asset(skel_path) if lib.does_asset_exist(skel_path) else None
    for clip in sorted({s.get('anim_file') or 'anim_%s'%s['clip'] for s in c['clips']}):
     target='/Game/Anim/%s'%tag
     if skel is None:self.warnings.append('no skeleton for %s: animation %s not imported'%(tag,clip));continue
     before=set(lib.list_assets(target,recursive=True,include_folder=False)) if lib.does_directory_exist(target) else set()
     f=os.path.join(folder,'%s.fbx'%clip)
     got=self._import(f,target,mesh=False,skeleton=skel,name=clip)
     anims=[p for p in got if isinstance(u.load_asset(p),u.AnimSequence)] if got else []
     if anims:self.clip_assets[(tag,clip)]=anims[0]
     else:self.warnings.append('animation %s imported nothing'%clip)
   except Exception as e:self.warnings.append('character %s import failed: %s %s'%(tag,type(e).__name__,str(e)[:120]))
 def _import(self,filename,dest,mesh,skeleton=None,name=None):
  u=self.u;task=u.AssetImportTask();task.set_editor_property('filename',filename);task.set_editor_property('destination_path',dest);task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',False)
  if name:task.set_editor_property('destination_name',name)
  o=u.FbxImportUI();o.set_editor_property('automated_import_should_detect_type',False)
  if mesh:
   o.set_editor_property('import_mesh',True);o.set_editor_property('import_as_skeletal',True);o.set_editor_property('import_animations',False);o.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_SKELETAL_MESH)
  else:
   o.set_editor_property('import_mesh',False);o.set_editor_property('import_animations',True);o.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_ANIMATION);o.set_editor_property('skeleton',skeleton)
  task.set_editor_property('options',o);u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);return [str(p) for p in task.get_editor_property('imported_object_paths')]
 def character_asset(self,tag):return self.character_assets.get(tag)
 def clip_asset(self,tag,clip):return self.clip_assets.get((tag,clip))
 def proxy_candidates(self,a):
  """paths of the proxy meshes imported from props.fbx for this actor: Unreal turns '.' into '_' and adds a digit when a material already has the name"""
  out=[]
  for m in a.get('meshes',[])[:1]:
   n=m.replace('.','_')
   for suffix in ('','1','2','3'):out.append('/Game/Proxy/%s/%s%s'%(self.scene,n,suffix))
  return out
 def _class_for(self,role):
  u=self.u
  return {'camera':u.CineCameraActor,'light':u.PointLight,'character':u.SkeletalMeshActor}.get(role,u.StaticMeshActor)
 def find_mesh(self,mesh_name,want):
  """the imported proxy asset of the given class for a Blender mesh name: Unreal turns '.' into '_' and appends a digit when a material already has the name"""
  u=self.u;n=mesh_name.replace('.','_')
  for suffix in ('','1','2','3'):
   path='/Game/Proxy/%s/%s%s'%(self.scene,n,suffix)
   if u.EditorAssetLibrary.does_asset_exist(path):
    obj=u.load_asset(path)
    if isinstance(obj,want):return obj
  return None
 def fit_of(self,mesh,dims_cm):
  """per-axis scale that makes the imported mesh the size the Blender object had (independent of whether the FBX import baked the object scale)"""
  try:
   e=mesh.get_bounds().box_extent;nat=(e.x*2,e.y*2,e.z*2)
  except Exception:return (1.,1.,1.)
  return tuple(max(.001,min(1000.,(d/n) if n>1e-3 and d>1e-3 else 1.)) for d,n in zip(dims_cm,nat))
 def _tag(self,actor,label):
  u=self.u;actor.set_actor_label(label);actor.tags=[u.Name(self.tag)]
  try:actor.set_folder_path('MovieBuilder/%s'%self.scene)
  except Exception:pass
  try:actor.root_component.set_mobility(u.ComponentMobility.MOVABLE)   # Sequencer moves these: a Static component is not re-rendered when its transform changes
  except Exception:pass
  self.spawned.append(actor)
 def spawn(self,a,asset,mapped):
  u=self.u;sub=u.get_editor_subsystem(u.EditorActorSubsystem);cls=self._class_for(a['role'])
  if a['role']=='light':
   cls={'SUN':u.DirectionalLight,'SPOT':u.SpotLight}.get(a['light']['type'],u.PointLight)
  actor=sub.spawn_actor_from_class(cls,u.Vector(0,0,0));self._tag(actor,'%s/%s'%(self.scene,a['name']));self.actors[a['id']]=actor
  parts=a.get('parts') or []
  if a['role']=='character':
   obj=u.load_asset(asset) if u.EditorAssetLibrary.does_asset_exist(asset) else None
   if isinstance(obj,u.SkeletalMesh):actor.skeletal_mesh_component.set_skeletal_mesh(obj)
  elif a['role'] in ('prop','effect'):
   if parts:
    for p in parts:
     mesh=self.find_mesh(p['mesh'],u.StaticMesh)
     if mesh is None:self.warnings.append('no imported mesh for %s'%p['mesh']);continue
     fit=self.fit_of(mesh,p['dims_cm'])
     if p['self']:
      actor.static_mesh_component.set_static_mesh(mesh);self.self_fit[a['id']]=fit
     else:
      ch=sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));self._tag(ch,'%s/%s/%s'%(self.scene,a['name'],p['mesh']));ch.static_mesh_component.set_static_mesh(mesh)
      ch.attach_to_actor(actor,'',u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,False)
      ch.set_actor_relative_location(u.Vector(*p['loc']),False,False);ch.set_actor_relative_rotation(u.Rotator(p['rot'][0],p['rot'][1],p['rot'][2]),False,False);ch.set_actor_relative_scale3d(u.Vector(*fit))
   else:
    for path in [asset]+self.proxy_candidates(a):
     if not u.EditorAssetLibrary.does_asset_exist(path):continue
     obj=u.load_asset(path)
     if isinstance(obj,u.StaticMesh):actor.static_mesh_component.set_static_mesh(obj);break
  b=self.seq.add_possessable(actor);self.bind[a['id']]=b;return a['id']
 def transform_keys(self,h,frames,loc,rot,scale):
  u=self.u;b=self.bind[h];tr=b.add_track(u.MovieScene3DTransformTrack);sec=tr.add_section();sec.set_range(frames[0],frames[-1]+1);ch=sec.get_all_channels()
  for i,f in enumerate(frames):
   fn=u.FrameNumber(f);vals=loc[i]+[rot[i][0],rot[i][1],rot[i][2]]+scale[i]
   for c in range(9):
    try:ch[c].add_key(fn,vals[c],0.0,u.SequenceTimeUnit.DISPLAY_RATE,u.MovieSceneKeyInterpolation.LINEAR)
    except Exception:ch[c].add_key(fn,vals[c])
 def lens_keys(self,h,frames,lens,sensor=None):
  u=self.u;act=self.actors.get(h)
  try:
   comp=act.get_cine_camera_component();comp.set_editor_property('current_focal_length',float(lens[0]))
   try:     # Blender's 36 mm sensor (Unreal's default 23.76 mm would crop the picture to two thirds), and no depth of field (Blender's focus distance is not exported, so a manual focus would blur the actors)
    fb=u.CameraFilmbackSettings();fb.sensor_width=float(sensor or 36.);fb.sensor_height=fb.sensor_width*9./16.;comp.set_editor_property('filmback',fb)
    fs=comp.get_editor_property('focus_settings');fs.focus_method=u.CameraFocusMethod.DISABLE;comp.set_editor_property('focus_settings',fs)
   except Exception as e:self.warnings.append('filmback/focus not set: %s'%type(e).__name__)
  except Exception as e:self.warnings.append('lens not set: %s'%type(e).__name__)
 def light(self,h,light):
  act=self.actors.get(h);u=self.u
  try:
   comp=act.get_component_by_class(u.LightComponent);t=light['type']
   comp.set_editor_property('intensity',light['energy']*(ub.SUN_LUX_PER_STRENGTH if t=='SUN' else ub.POINT_CD_PER_W))
   col=light['color'];comp.set_editor_property('light_color',u.Color(int(255*col[0]),int(255*col[1]),int(255*col[2]),255))
   if t!='SUN':
    try:comp.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
    except Exception:pass
  except Exception as e:self.warnings.append('light %s not configured: %s'%(light['type'],type(e).__name__))
 def anim_section(self,h,asset,start,end,rate,mapped):
  u=self.u;b=self.bind[h];tr=b.find_tracks_by_exact_type(u.MovieSceneSkeletalAnimationTrack);tr=tr[0] if tr else b.add_track(u.MovieSceneSkeletalAnimationTrack)
  sec=tr.add_section();sec.set_range(start,end+1);p=sec.params;p.animation=u.load_asset(asset)
  if abs(rate-1.0)>1e-6:self.set_rate(p,rate)
 def set_rate(self,p,rate):
  """play rate of an animation section: a plain float up to UE 5.6, a MovieSceneTimeWarpVariant from 5.7; if neither works the clip keeps rate 1 and a warning says so"""
  u=self.u
  try:p.play_rate=rate;return
  except TypeError:pass
  try:
   v=u.MovieSceneTimeWarpVariant();v.set_fixed_play_rate(rate);p.play_rate=v;return
  except Exception as e:
   self.warnings.append('play rate %.2f not applied (%s); fields of MovieSceneTimeWarpVariant: %s'%(rate,type(e).__name__,[n for n in dir(u.MovieSceneTimeWarpVariant) if not n.startswith('_')][:30]))
 def camera_cut(self,name,h,start,end):
  u=self.u;tr=self.seq.find_tracks_by_exact_type(u.MovieSceneCameraCutTrack);tr=tr[0] if tr else self.seq.add_track(u.MovieSceneCameraCutTrack)
  sec=tr.add_section();sec.set_range(start,end+1);sec.set_camera_binding_id(self.seq.get_binding_id(self.bind[h]))
 def audio(self,name,path,start,vol):
  u=self.u;tr=self.seq.add_track(u.MovieSceneAudioTrack);sec=tr.add_section();sec.set_range(start,start+1000);sec.set_sound(u.load_asset(path))
 def diagnostics(self):
  """what the editor really holds for every static-mesh actor (mesh, bounds, visibility); written beside the scene file so a missing or mis-sized prop is found without looking at frames"""
  rows=[]
  for a in self.spawned:
   try:
    if hasattr(a,'get_cine_camera_component'):
     cc=a.get_cine_camera_component();rows.append(dict(label=a.get_actor_label(),focal=cc.current_focal_length,filmback=[cc.filmback.sensor_width,cc.filmback.sensor_height],aperture=cc.current_aperture,focus=str(cc.focus_settings.manual_focus_distance)));continue
    sk=getattr(a,'skeletal_mesh_component',None)
    if sk is not None and sk.skeletal_mesh is not None:
     o,e=a.get_actor_bounds(False);rows.append(dict(label=a.get_actor_label(),skeletal=sk.skeletal_mesh.get_path_name(),world_extent=[round(e.x,1),round(e.y,1),round(e.z,1)],scale=[a.get_actor_scale3d().x]));continue
    c=getattr(a,'static_mesh_component',None)
    if c is None:continue
    m=c.static_mesh;o,e=a.get_actor_bounds(False)
    rows.append(dict(label=a.get_actor_label(),mesh=m.get_path_name() if m else None,mesh_extent=[round(v,1) for v in (m.get_bounds().box_extent.x,m.get_bounds().box_extent.y,m.get_bounds().box_extent.z)] if m else None,world_extent=[round(e.x,1),round(e.y,1),round(e.z,1)],visible=bool(c.is_visible()),mobility=str(c.mobility),materials=c.get_num_materials()))
   except Exception as ex:rows.append(dict(label='?',error=str(ex)[:120]))
  return rows
 def save(self):
  self.autoplay_actor();self.u.EditorAssetLibrary.save_loaded_asset(self.seq)
  try:
   import json;folder=getattr(self,'diag_dir',None)
   if folder:open(os.path.join(folder,'%s.import.json'%self.scene),'w',encoding='utf-8').write(json.dumps(self.diagnostics(),indent=1))
  except Exception as ex:self.warnings.append('diagnostics not written: %s'%str(ex)[:100])
def load_catalog(amap):
 """the installed-asset catalogue (Environment Studio's prompt-catalog.json) used to find real meshes for placeholders that have no explicit mapping"""
 here=os.path.dirname(os.path.abspath(__file__));p=amap.get('catalog') or os.path.join(here,'assets','prompt-catalog.json')
 p=p if os.path.isabs(p) else os.path.join(here,p)
 try:return ub.load(p) if os.path.exists(p) else None
 except (ValueError,OSError):return None
def build(doc,asset_map,backend,proxy_dir='/Game/Proxy',anim_dir='/Game/Anim',tol=(.1,.05,.002),catalog=None):
 """create the sequence on the backend; returns the backend. Keys are reduced (position tolerance in cm, rotation in degrees) before they are written."""
 problems=ub.validate(doc)
 if problems:raise ValueError('export is inconsistent: %s'%problems[:5])
 backend.sequence(doc['scene'],doc['fps'],doc['frame_start'],doc['frame_end']);backend.diag_dir=doc.get('_dir');handles={};backend.ensure_characters(doc)
 for a in doc['actors']:
  asset,mapped=ub.resolve_asset(a['asset_key'],asset_map,proxy_dir,doc['scene']);k=a.get('keys');fitted=None
  if a['role']=='character' and not mapped:
   own=[backend.character_asset(c['name']) for c in doc['characters'] if c['root']==a['id']]
   if own and own[0]:asset=own[0];mapped=True
  if not mapped and catalog and a['role'] in ('prop','effect') and a.get('bounds_cm'):
   hit=ub.pick_catalog_asset(a['asset_key'],a['bounds_cm'],catalog)
   if hit:asset,fit=hit;mapped=True;fitted=fit
  h=backend.spawn(a,asset,mapped);handles[a['id']]=h
  if fitted and k and k['frames'] and ub.constant_scale(k['scale']):k=dict(k,scale=[[fitted,fitted,fitted] for _ in k['scale']])
  elif a['role'] in ('prop','effect') and a.get('parts') and k and k['frames']:
   s0=k['scale'][0];fit=backend.self_fit.get(a['id']) or (1.,1.,1.)   # the object's scale over time relative to its first frame, times the size fit of its own mesh
   k=dict(k,scale=[[(r/s if abs(s)>1e-9 else 1.)*f for r,s,f in zip(row,s0,fit)] for row in k['scale']])
  if k and k['frames']:
   vals=[l+r+s for l,r,s in zip(k['loc'],k['rot'],k['scale'])];keep=ub.reduce_keys(k['frames'],vals,tol[0])
   backend.transform_keys(h,[k['frames'][i] for i in keep],[k['loc'][i] for i in keep],[k['rot'][i] for i in keep],[k['scale'][i] for i in keep])
   if 'lens' in k:backend.lens_keys(h,[k['frames'][i] for i in keep],[k['lens'][i] for i in keep],(a.get('camera') or {}).get('sensor_width'))
  if a['role']=='light':backend.light(h,a['light'])
 for c in doc['characters']:
  for s in c['clips']:
   key=s.get('anim_file') or 'anim_%s'%s['clip']
   asset,mapped=ub.resolve_clip(s['clip'],c['name'],asset_map,anim_dir)
   own=backend.clip_asset(c['name'],key)
   if own and not mapped:asset,mapped=own,True
   loop=max(2,int(round((s.get('action_end',s['end'])-s.get('action_start',s['start'])+1)*s['scale']))) if s.get('action_end') is not None else max(2,s['end']-s['start'])
   t=s['start']
   while t<s['end']:       # a strip that repeats (Blender's repeat) becomes one section per repetition
    t1=min(s['end'],t+loop);backend.anim_section(handles[c['root']],asset,t,t1,1.0/max(1e-6,s['scale']),mapped);t=t1
 backend.environment(doc)
 for cut in doc['cuts']:backend.camera_cut(cut['name'],handles[cut['camera']],cut['start'],cut['end'])
 for au in doc['audio']:backend.audio(au['name'],au['file'],au['start'],au['volume'])
 backend.save();return backend
def run(json_path,map_path=None):
 """entry point inside the Unreal editor"""
 doc=ub.load(json_path);amap=ub.load(map_path) if map_path and os.path.exists(map_path) else {}
 return build(doc,amap,UnrealBackend(),catalog=load_catalog(amap))
if __name__=='__main__':
 doc=ub.load(sys.argv[1]);amap=ub.load(sys.argv[2]) if len(sys.argv)>2 else {};b=build(doc,amap,DryRun(),catalog=load_catalog(amap))
 c=b.counts;print('DRY RUN',json.dumps(ub.summary(doc)));print('actors %d, transform keys after reduction %d, animation sections %d, cuts %d, audio %d'%(c['actors'],c['transform_keys'],c['anim_sections'],c['cuts'],c['audio']))
 print('mapped to real assets: %d; using proxy fallback: %d'%(len(c['mapped']),len(c['unmapped'])));print('proxy keys:',sorted(set(c['unmapped']))[:30])
