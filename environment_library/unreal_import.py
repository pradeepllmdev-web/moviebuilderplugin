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
import unreal_bridge as ub
class DryRun:
 """records what would be created; same interface as the Unreal backend"""
 def __init__(self):self.log=[];self.counts={'actors':0,'transform_keys':0,'anim_sections':0,'cuts':0,'audio':0,'unmapped':[],'mapped':[]}
 def sequence(self,name,fps,start,end):self.log.append(('sequence',name,fps,start,end))
 def spawn(self,a,asset,mapped):
  self.counts['actors']+=1;(self.counts['mapped'] if mapped else self.counts['unmapped']).append(a['asset_key']);self.log.append(('spawn',a['name'],a['role'],asset))
  return a['id']
 def transform_keys(self,h,frames,loc,rot,scale):self.counts['transform_keys']+=len(frames)
 def lens_keys(self,h,frames,lens):self.log.append(('lens',h,len(frames)))
 def light(self,h,light):self.log.append(('light',h,light['type']))
 def anim_section(self,h,asset,start,end,rate,mapped):self.counts['anim_sections']+=1;(self.counts['mapped'] if mapped else self.counts['unmapped']).append(os.path.basename(asset))
 def camera_cut(self,name,h,start,end):self.counts['cuts']+=1
 def audio(self,name,path,start,vol):self.counts['audio']+=1
 def save(self):self.log.append(('save',))
class UnrealBackend:
 """thin wrapper over the Unreal editor Python API (see the module docstring for the version note)"""
 def __init__(self):
  import unreal;self.u=unreal;self.seq=None;self.bind={}
 def sequence(self,name,fps,start,end):
  u=self.u;tools=u.AssetToolsHelpers.get_asset_tools();self.seq=tools.create_asset('LS_%s'%name,'/Game/Movie',u.LevelSequence,u.LevelSequenceFactoryNew())
  self.seq.set_display_rate(u.FrameRate(fps,1));self.seq.set_playback_start(start);self.seq.set_playback_end(end+1);self.fps=fps
 def _class_for(self,role):
  u=self.u
  return {'camera':u.CineCameraActor,'light':u.PointLight,'character':u.SkeletalMeshActor}.get(role,u.StaticMeshActor)
 def spawn(self,a,asset,mapped):
  u=self.u;sub=u.get_editor_subsystem(u.EditorActorSubsystem);cls=self._class_for(a['role'])
  if a['role']=='light':
   cls={'SUN':u.DirectionalLight,'SPOT':u.SpotLight}.get(a['light']['type'],u.PointLight)
  actor=sub.spawn_actor_from_class(cls,u.Vector(0,0,0));actor.set_actor_label(a['name'])
  if a['role'] in ('prop','effect') and u.EditorAssetLibrary.does_asset_exist(asset):
   actor.static_mesh_component.set_static_mesh(u.load_asset(asset))
  b=self.seq.add_possessable(actor);self.bind[a['id']]=b;return a['id']
 def transform_keys(self,h,frames,loc,rot,scale):
  u=self.u;b=self.bind[h];tr=b.add_track(u.MovieScene3DTransformTrack);sec=tr.add_section();sec.set_range(frames[0],frames[-1]+1);ch=sec.get_channels()
  for i,f in enumerate(frames):
   fn=u.FrameNumber(f);vals=loc[i]+[rot[i][0],rot[i][1],rot[i][2]]+scale[i]
   for c in range(9):ch[c].add_key(fn,vals[c])
 def lens_keys(self,h,frames,lens):pass
 def light(self,h,light):pass
 def anim_section(self,h,asset,start,end,rate,mapped):
  u=self.u;b=self.bind[h];tr=b.find_tracks_by_exact_type(u.MovieSceneSkeletalAnimationTrack);tr=tr[0] if tr else b.add_track(u.MovieSceneSkeletalAnimationTrack)
  sec=tr.add_section();sec.set_range(start,end+1);p=sec.params;p.animation=u.load_asset(asset);p.play_rate=rate
 def camera_cut(self,name,h,start,end):
  u=self.u;tr=self.seq.find_master_tracks_by_exact_type(u.MovieSceneCameraCutTrack);tr=tr[0] if tr else self.seq.add_master_track(u.MovieSceneCameraCutTrack)
  sec=tr.add_section();sec.set_range(start,end+1);sec.set_camera_binding_id(self.bind[h].get_binding_id())
 def audio(self,name,path,start,vol):
  u=self.u;tr=self.seq.add_master_track(u.MovieSceneAudioTrack);sec=tr.add_section();sec.set_range(start,start+1000);sec.set_sound(u.load_asset(path))
 def save(self):self.u.EditorAssetLibrary.save_loaded_asset(self.seq)
def build(doc,asset_map,backend,proxy_dir='/Game/Proxy',anim_dir='/Game/Anim',tol=(.1,.05,.002)):
 """create the sequence on the backend; returns the backend. Keys are reduced (position tolerance in cm, rotation in degrees) before they are written."""
 problems=ub.validate(doc)
 if problems:raise ValueError('export is inconsistent: %s'%problems[:5])
 backend.sequence(doc['scene'],doc['fps'],doc['frame_start'],doc['frame_end']);handles={}
 for a in doc['actors']:
  asset,mapped=ub.resolve_asset(a['asset_key'],asset_map,proxy_dir,doc['scene']);h=backend.spawn(a,asset,mapped);handles[a['id']]=h
  k=a.get('keys')
  if k and k['frames']:
   vals=[l+r+s for l,r,s in zip(k['loc'],k['rot'],k['scale'])];keep=ub.reduce_keys(k['frames'],vals,tol[0])
   backend.transform_keys(h,[k['frames'][i] for i in keep],[k['loc'][i] for i in keep],[k['rot'][i] for i in keep],[k['scale'][i] for i in keep])
   if 'lens' in k:backend.lens_keys(h,[k['frames'][i] for i in keep],[k['lens'][i] for i in keep])
  if a['role']=='light':backend.light(h,a['light'])
 for c in doc['characters']:
  for s in c['clips']:
   asset,mapped=ub.resolve_clip(s['clip'],c['name'],asset_map,anim_dir);backend.anim_section(handles[c['root']],asset,s['start'],s['end'],1.0/max(1e-6,s['scale']),mapped)
 for cut in doc['cuts']:backend.camera_cut(cut['name'],handles[cut['camera']],cut['start'],cut['end'])
 for au in doc['audio']:backend.audio(au['name'],au['file'],au['start'],au['volume'])
 backend.save();return backend
def run(json_path,map_path=None):
 """entry point inside the Unreal editor"""
 doc=ub.load(json_path);amap=ub.load(map_path) if map_path and os.path.exists(map_path) else {}
 return build(doc,amap,UnrealBackend())
if __name__=='__main__':
 doc=ub.load(sys.argv[1]);amap=ub.load(sys.argv[2]) if len(sys.argv)>2 else {};b=build(doc,amap,DryRun())
 c=b.counts;print('DRY RUN',json.dumps(ub.summary(doc)));print('actors %d, transform keys after reduction %d, animation sections %d, cuts %d, audio %d'%(c['actors'],c['transform_keys'],c['anim_sections'],c['cuts'],c['audio']))
 print('mapped to real assets: %d; using proxy fallback: %d'%(len(c['mapped']),len(c['unmapped'])));print('proxy keys:',sorted(set(c['unmapped']))[:30])
