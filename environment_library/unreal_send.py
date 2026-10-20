"""Send built scenes to a running Unreal editor through the UnrealBridge HTTP bridge (the editor plugin in unrealplugin-next, default http://127.0.0.1:8500).

    python unreal_send.py <movie_folder> [--bridge http://127.0.0.1:8500] [--dry-run] [--scenes 1,2]     (runs unreal_handoff: cached, parallel, one summary; see its docstring for the flags)

For every scene the build report says passed: export it (Blender, headless -> <export root>/<movie>/<scene>/<scene>.ue.json + FBX), import the environment/prop FBX through the bridge's import_asset,
then ask the bridge to apply the scene (command apply_movie_scene, which runs unreal_import inside the editor and creates a Level Sequence, never overwriting). The bridge only reads files below the export root
(MOVIEBUILDER_EXPORT_ROOT, default <this folder>/scenes/unreal_export), so exports are written there. Requirements on the Unreal side: the UnrealBridge plugin with the apply_movie_scene command and the
environment variable MOVIEBUILDER_ENV_LIB pointing at this folder. Same local-only URL rules as unrealplugin-next's UnrealClient: http, localhost or 127.0.0.1, no path or credentials."""
import json,os,subprocess,sys,time,urllib.error,urllib.request
from pathlib import Path
from urllib.parse import urlsplit
H=Path(__file__).resolve().parent
class BridgeError(RuntimeError):pass
class Bridge:
 def __init__(self,url=None,timeout=900):
  self.url=(url or os.environ.get('BRIDGE_URL') or 'http://127.0.0.1:8500').rstrip('/');u=urlsplit(self.url)
  if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or u.path or u.query or u.fragment or u.username or u.password:raise ValueError('Use a local HTTP bridge URL with no path or credentials')
  self.timeout=timeout
 def command(self,name,params=None):
  data=json.dumps({'command':name,'params':params or {}}).encode('utf-8');req=urllib.request.Request(self.url+'/',data,{'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=self.timeout) as r:body=json.loads(r.read())
  except urllib.error.HTTPError as e:
   try:msg=json.loads(e.read()).get('error')
   except Exception:msg=None
   raise BridgeError('Unreal bridge %s failed (%d): %s'%(name,e.code,(msg or '')[:1500]))
  except (urllib.error.URLError,TimeoutError,OSError,ValueError) as e:raise BridgeError('Unreal bridge %s could not complete: %s'%(name,type(e).__name__))
  if isinstance(body,dict) and body.get('status')=='pending':return {'pending':True,'message':body.get('message','')}   # the editor is still working (replies are limited to ~30 s)
  if not isinstance(body,dict) or body.get('status')!='ok' or 'result' not in body:raise BridgeError((body.get('error') if isinstance(body,dict) else None) or 'Invalid Unreal bridge response')
  return body['result']
 def get(self,path):
  with urllib.request.urlopen(self.url+path,timeout=60) as r:return json.loads(r.read())
 def drop_sequences(self,scene):
  """delete earlier Level Sequences of this scene (LS_<scene>, LS_<scene>_2, ...)"""
  try:have={a['path'].split('.')[0] for a in self.get('/assets?path=/Game/Movie')['assets']}
  except Exception:return
  for p in sorted(have):
   n=p.split('/')[-1]
   if n=='LS_'+scene or (n.startswith('LS_%s_'%scene) and n[len('LS_%s_'%scene):].isdigit()):
    try:self.command('delete_asset',{'asset_path':p})
    except BridgeError:pass
 def clear_proxy(self,scene):
  """delete the scene's imported proxy meshes and materials: a re-import over an existing asset keeps the old geometry, so a changed export would not show"""
  try:items=self.get('/assets?path=/Game/Proxy/%s'%scene)['assets']
  except Exception:return
  for a in items:
   try:self.command('delete_asset',{'asset_path':a['path']})
   except BridgeError:pass
 def wait_for_scene(self,scene,timeout=1200,quiet=8.0):
  """after a pending reply: wait until the scene's sequence exists and its actors stopped appearing"""
  t0=time.time();last=None;stable_since=None
  while time.time()-t0<timeout:
   try:
    seq=[a for a in self.get('/assets?path=/Game/Movie')['assets'] if a['path'].split('/')[-1].startswith('LS_'+scene)]
    n=sum(1 for a in self.get('/status')['actors'] if a['label'].startswith(scene+'/'))
   except Exception:time.sleep(3);continue
   key=(len(seq),n)
   if seq and n and key==last:
    stable_since=stable_since or time.time()
    if time.time()-stable_since>=quiet:return seq[-1]['path']
   else:stable_since=None
   last=key;time.sleep(3)
  raise BridgeError('the editor did not finish importing %s within %d s'%(scene,timeout))
def export_root():return Path(os.environ.get('MOVIEBUILDER_EXPORT_ROOT') or (H/'scenes'/'unreal_export')).resolve()
def export_scene(blend,out_dir,name):
 """headless Blender export of one built scene; returns the .ue.json path"""
 import quick_review
 out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
 r=subprocess.run([quick_review.BLENDER,'-b',str(blend),'--python',str(H/'unreal_export.py'),'--',str(out_dir),name],capture_output=True,text=True,errors='ignore',timeout=1800)
 j=out_dir/(name+'.ue.json')
 if not j.exists():raise BridgeError('export failed for %s: %s'%(name,r.stdout[-300:]))
 return j
def send_scene(bridge,json_path,import_assets=True,import_characters=False,dry_run=False):
 """import the scene's mesh files, then apply the scene; returns the bridge's answer"""
 json_path=Path(json_path);doc=json.loads(json_path.read_text(encoding='utf-8'));imported=[]
 if import_assets and not dry_run:
  bridge.clear_proxy(doc['scene'])
  for f in sorted(json_path.parent.glob('*.fbx')):
   if f.name.startswith(('anim_','character_')) and not import_characters:continue
   bridge.command('import_asset',{'file':str(f),'kind':'mesh','destination':'/Game/Proxy/%s'%doc['scene'],'replace':True});imported.append(f.name)
 if not dry_run:bridge.drop_sequences(doc['scene'])   # an old sequence points at actors the import removes; the editor can only delete it from outside the import
 res=bridge.command('apply_movie_scene',{'scene_json':str(json_path),'dry_run':bool(dry_run)});res['imported']=imported
 if res.get('pending') and not dry_run:res['sequence']=bridge.wait_for_scene(doc['scene']);res['pending']=False
 if not dry_run:
  try:bridge.command('save_level',{});res['level_saved']=True      # the sequence's actors live in the level: save it so they are there next time the project opens
  except BridgeError as e:res['level_saved']=False;res.setdefault('warnings',[]).append('level not saved: %s'%e)
 return res
def measure_luma(path):
 """mean brightness (0..1, sRGB) of a rendered frame"""
 from PIL import Image,ImageStat
 return ImageStat.Stat(Image.open(path).convert('L')).mean[0]/255.
def wait_render(bridge,timeout=1800,poll=2.0):
 """wait until the bridge's Movie Render Queue job is done; returns its last /render_status"""
 time.sleep(poll);t0=time.time();st={}
 while time.time()-t0<timeout:
  st=bridge.get('/render_status')
  if st.get('state')=='done':return st
  if st.get('state') in ('error','failed'):raise BridgeError('render failed: %s'%str(st)[:300])
  time.sleep(poll)
 raise BridgeError('the render did not finish within %d s'%timeout)
def set_exposure(bridge,json_path,bias):
 """change the exposure of the shot cameras of an imported scene in place: a tiny scene document with op=set_exposure goes through apply_movie_scene, which only touches the tagged cameras (nothing is rebuilt)"""
 json_path=Path(json_path);doc=json.loads(json_path.read_text(encoding='utf-8'))
 p=json_path.with_name(doc['scene']+'.exposure.ue.json');p.write_text(json.dumps(dict(scene=doc['scene'],fps=doc.get('fps',24),frame_start=1,frame_end=2,actors=[],characters=[],cuts=[],audio=[],op='set_exposure',exposure_bias=float(bias))),encoding='utf-8')
 try:return bridge.command('apply_movie_scene',{'scene_json':str(p),'dry_run':False})
 finally:
  try:p.unlink()
  except OSError:pass
def calibrate_exposure(bridge,json_path,sequence,start_bias=None,target=.32,frames=3):
 """the shot cameras' exposure bias is measured, not guessed: render a few frames of the scene as it was just applied (at start_bias), then move the bias in place to where their mean brightness meets the target. One apply, one correction;
 returns (bias, measured brightness)."""
 import tempfile,ue_common
 json_path=Path(json_path);doc=json.loads(json_path.read_text(encoding='utf-8'));fs,fe=doc['frame_start'],doc['frame_end'];cur=float(doc.get('exposure_bias') if start_bias is None and doc.get('exposure_bias') is not None else (start_bias if start_bias is not None else 2.0))
 seq=sequence.split('.')[0];vals=[]
 for i in range(frames):
  f=int(fs+(fe-fs)*(i+.5)/frames)
  with tempfile.TemporaryDirectory() as d:
   bridge.command('render_movie',{'sequence_path':seq,'preset':'draft','resolution':[480,270],'format':'png','start_frame':f,'end_frame':f+1,'output_dir':d.replace(chr(92),'/')});wait_render(bridge,300)
   got=sorted(Path(d).glob('*.png'))
   if got:vals.append(measure_luma(got[-1]))
 if not vals:return cur,None
 m=sum(vals)/len(vals);new=ue_common.exposure_step(cur,m,target)
 if new!=cur:set_exposure(bridge,json_path,new)
 return new,round(m,3)
def purge_scene(bridge,root,scene):
 """take a scene out of the editor (actors tagged moviebuilder:<scene> and its Level Sequences): a tiny document with op=purge goes through apply_movie_scene"""
 d=Path(root)/scene;d.mkdir(parents=True,exist_ok=True);p=d/(scene+'.purge.ue.json');p.write_text(json.dumps(dict(scene=scene,fps=24,frame_start=1,frame_end=2,actors=[],characters=[],cuts=[],audio=[],op='purge')),encoding='utf-8')
 try:return bridge.command('apply_movie_scene',{'scene_json':str(p),'dry_run':False})
 finally:
  try:p.unlink()
  except OSError:pass
def scenes_to_send(report,only=None):
 """(name, blend) for scenes that built and passed; scenes with audit issues, failures or no scene type are left out and reported"""
 ok=[];skipped=[]
 for r in report['report']:
  name='%s_%02d_%s'%('m',r['index'],r['piece'] or 'shot')
  if only and r['index'] not in only:continue
  good=r['piece'] and r.get('file') and not r.get('audit') and (r['status'].startswith('built') or r['status']=='reused')
  (ok if good else skipped).append((r['index'],r['piece'],r.get('file'),r['status'],r.get('audit')))
 return ok,skipped
def send_movie(movie_dir,bridge,only=None,dry_run=False,export=export_scene,progress=None,calibrate=True):
 movie_dir=Path(movie_dir);report=json.loads((movie_dir/'report.json').read_text(encoding='utf-8'));ok,skipped=scenes_to_send(report,only);results=[];root=export_root()/movie_dir.name
 for index,piece,blend,status,audit in ok:
  name='%s_%02d_%s'%(movie_dir.name,index,piece)
  if progress:progress('Exporting %s'%name)
  j=export(blend,root/name,name)
  if progress:progress('Sending %s to Unreal'%name)
  res=send_scene(bridge,j,dry_run=dry_run)
  if not dry_run and calibrate:
   if progress:progress('Calibrating exposure of %s'%name)
   res['exposure']=calibrate_exposure(bridge,j,res['sequence']) if res.get('sequence') else None
  results.append(dict(index=index,piece=piece,name=name,result=res))
 return dict(sent=results,skipped=[dict(index=i,piece=p,status=s,audit=a) for i,p,f,s,a in skipped])
if __name__=='__main__':
 import unreal_handoff;a=sys.argv[1:]
 if a and a[0]=='handoff':a=a[1:]
 sys.exit(unreal_handoff.main(a))
