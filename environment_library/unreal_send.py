"""Send built scenes to a running Unreal editor through the UnrealBridge HTTP bridge (the editor plugin in unrealplugin-next, default http://127.0.0.1:8500).

    python unreal_send.py <movie_folder> [--bridge http://127.0.0.1:8500] [--dry-run] [--scenes 1,2]

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
  if not isinstance(body,dict) or body.get('status')!='ok' or 'result' not in body:raise BridgeError((body.get('error') if isinstance(body,dict) else None) or 'Invalid Unreal bridge response')
  return body['result']
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
  for f in sorted(json_path.parent.glob('*.fbx')):
   if f.name.startswith(('anim_','character_')) and not import_characters:continue
   bridge.command('import_asset',{'file':str(f),'kind':'mesh','destination':'/Game/Proxy/%s'%doc['scene'],'replace':True});imported.append(f.name)
 res=bridge.command('apply_movie_scene',{'scene_json':str(json_path),'dry_run':bool(dry_run)});res['imported']=imported;return res
def scenes_to_send(report,only=None):
 """(name, blend) for scenes that built and passed; scenes with audit issues, failures or no scene type are left out and reported"""
 ok=[];skipped=[]
 for r in report['report']:
  name='%s_%02d_%s'%('m',r['index'],r['piece'] or 'shot')
  if only and r['index'] not in only:continue
  good=r['piece'] and r.get('file') and not r.get('audit') and (r['status'].startswith('built') or r['status']=='reused')
  (ok if good else skipped).append((r['index'],r['piece'],r.get('file'),r['status'],r.get('audit')))
 return ok,skipped
def send_movie(movie_dir,bridge,only=None,dry_run=False,export=export_scene,progress=None):
 movie_dir=Path(movie_dir);report=json.loads((movie_dir/'report.json').read_text(encoding='utf-8'));ok,skipped=scenes_to_send(report,only);results=[];root=export_root()/movie_dir.name
 for index,piece,blend,status,audit in ok:
  name='%s_%02d_%s'%(movie_dir.name,index,piece)
  if progress:progress('Exporting %s'%name)
  j=export(blend,root/name,name)
  if progress:progress('Sending %s to Unreal'%name)
  results.append(dict(index=index,piece=piece,name=name,result=send_scene(bridge,j,dry_run=dry_run)))
 return dict(sent=results,skipped=[dict(index=i,piece=p,status=s,audit=a) for i,p,f,s,a in skipped])
if __name__=='__main__':
 a=sys.argv[1:];bridge_url=None;dry='--dry-run' in a;only=None
 if '--bridge' in a:i=a.index('--bridge');bridge_url=a[i+1];del a[i:i+2]
 if '--scenes' in a:i=a.index('--scenes');only={int(x) for x in a[i+1].split(',')};del a[i:i+2]
 a=[x for x in a if x!='--dry-run'];res=send_movie(a[0],Bridge(bridge_url),only,dry,progress=print);print(json.dumps(res,indent=1)[:4000])
