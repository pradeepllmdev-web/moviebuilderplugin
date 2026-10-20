"""One command for the whole Blender -> Unreal handoff of a built movie: cached, parallel, one summary.

    python unreal_handoff.py scene <scene.blend> <scene_name> [flags]     (one scene, the unit the whole flow calls; in code: handoff_scene)
    python unreal_handoff.py <movie_folder> [--scenes 1,2] [--force] [--jobs 2] [--no-calibrate] [--recalibrate] [--check-only] [--send-anyway] [--dry-run] [--bridge URL]

For every scene the build report says passed:
  1. export  - headless Blender writes <export root>/<movie>/<scene>/<scene>.ue.json + FBX. Skipped when the .blend (hash), the exporter code and the scene's swap names are unchanged since the last export.
               Up to --jobs exports run at once and run ahead of Unreal, so the next scenes export while the current one imports.
  2. check   - unreal_check.check_scene on the export: missing meshes / characters / animation files / audio. Scenes with errors are not sent (--send-anyway sends them).
  3. import  - the scene's FBX files and apply_movie_scene through the bridge. Skipped when the export, the part of unreal_asset_map.json that concerns the scene and the importer code are unchanged and the sequence is still in the editor.
  4. exposure- measured once per scene (3 draft frames) and set in place after the single apply; the bias is remembered in handoff_state.json, so a re-import reuses it without rendering.
  5. verify  - the editor's own import diagnostics are compared with the export (a part whose mesh did not arrive is reported).
The result is one line per scene plus the grouped problems, printed in full and kept in <export root>/<movie>/handoff_summary.txt. State lives in <export root>/<movie>/handoff_state.json (delete it, or pass --force, to redo everything).
The environment swap layer (unreal_asset_map.json) is read by the exporter (swapped objects stay separate) and the importer; editing it re-imports only the scenes it concerns."""
import concurrent.futures as cf,hashlib,json,os,re,sys,time
from pathlib import Path
import ue_common as uc,unreal_check as chk,unreal_send as us
H=Path(__file__).resolve().parent
STATE_VERSION=1
EXPORT_CODE=('unreal_export.py','ue_common.py')
APPLY_CODE=('unreal_import.py','ue_common.py')
def sha_file(path,chunk=1<<20):
 h=hashlib.sha1()
 try:
  with open(path,'rb') as f:
   for b in iter(lambda:f.read(chunk),b''):h.update(b)
 except OSError:return 'missing'
 return h.hexdigest()
def sha_text(*parts):
 h=hashlib.sha1()
 for p in parts:h.update(str(p).encode('utf-8'));h.update(b'\0')
 return h.hexdigest()
def load_map(path=None):
 p=Path(path or os.environ.get('UNREAL_ASSET_MAP') or (H/'unreal_asset_map.json'))
 try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
 except (OSError,ValueError):return {}
def map_view(amap,scene):
 """the part of the asset map that can change how one scene is imported: everything global plus the 'scenes' entries that match it"""
 v={k:val for k,val in amap.items() if k!='scenes'}
 v['scenes']={pat:b for pat,b in (amap.get('scenes') or {}).items() if not pat.startswith('_') and uc._scene_matches(pat,scene)}
 return v
def export_key(blend,amap,scene,code_dir=H):
 return sha_text('export',STATE_VERSION,sha_file(blend),*[sha_file(Path(code_dir)/f) for f in EXPORT_CODE],json.dumps(uc.swap_names(amap,scene)))
def apply_key(ekey,amap,scene,code_dir=H,catalog=None):
 cat=sha_file(catalog) if catalog and os.path.exists(catalog) else ''
 return sha_text('apply',STATE_VERSION,ekey,*[sha_file(Path(code_dir)/f) for f in APPLY_CODE],json.dumps(map_view(amap,scene),sort_keys=True),cat)
def load_state(root):
 try:
  d=json.loads((Path(root)/'handoff_state.json').read_text(encoding='utf-8'))
  if d.get('version')==STATE_VERSION and isinstance(d.get('scenes'),dict):return d
 except (OSError,ValueError):pass
 return dict(version=STATE_VERSION,scenes={})
def save_state(root,state):
 Path(root).mkdir(parents=True,exist_ok=True);p=Path(root)/'handoff_state.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(state,indent=1),encoding='utf-8');os.replace(t,p)
def group_messages(msgs):
 """collapse messages that differ only in numbers: ['no mesh for SparkFly1','... SparkFly2'] -> [('no mesh for SparkFly#', 2, ['SparkFly1','SparkFly2'])]"""
 groups={}
 for m in msgs:
  t=re.sub(r'\d+','#',m);g=groups.setdefault(t,[0,[]]);g[0]+=1
  if len(g[1])<4:g[1].append(m)
 return [(t,n,ex) for t,(n,ex) in groups.items()]
def diag_missing(doc,diag):
 """parts of the export whose mesh is not in the editor after the import, from the importer's own diagnostics (<scene>.import.json): labels 'scene/actor/mesh' with no mesh"""
 have={r.get('label'):r for r in diag if isinstance(r,dict)};miss=[]
 for a in doc.get('actors',[]):
  if a['role'] not in ('prop','effect'):continue
  if (have.get('%s/%s'%(doc['scene'],a['name'])) or {}).get('mesh'):continue     # an environment swap puts the real mesh on the actor itself: the parts do not exist then
  for p in a.get('parts') or []:
   r=have.get('%s/%s/%s'%(doc['scene'],a['name'],p['mesh']))
   if r is None or not r.get('mesh'):miss.append('%s/%s'%(a['name'],p['mesh']))
 return miss
def _fmt_s(x):return '-' if x is None else ('%.0fs'%x if x<100 else '%dm%02ds'%(x//60,x%60))
def format_summary(movie,rows,wall=None):
 """compact summary: a header, one line per scene, then the issues grouped (nothing is cut off)"""
 n=len(rows);c=lambda f:sum(1 for r in rows if f(r))
 head='Handoff %s: %d scene(s) | export %d ran, %d cached | unreal %d applied, %d cached | %d blocked, %d failed%s'%(movie,n,c(lambda r:r['export']=='ran'),c(lambda r:r['export']=='cached'),c(lambda r:r['unreal']=='applied'),c(lambda r:r['unreal']=='cached'),c(lambda r:r['unreal']=='blocked'),c(lambda r:r.get('error')),(' | %s'%_fmt_s(wall)) if wall is not None else '')
 lines=[head]
 for r in rows:
  ex=r['export'] if r['export']!='ran' else 'ran '+_fmt_s(r.get('export_s'));un=r['unreal'] if r['unreal']!='applied' else 'applied '+_fmt_s(r.get('unreal_s'))
  e=r.get('exposure');ev='%+.2f'%e if isinstance(e,(int,float)) else '-'
  errs=sum(1 for i in r.get('issues',[]) if i['level']=='error')+len(r.get('missing',[]));warns=sum(1 for i in r.get('issues',[]) if i['level']=='warn')+len(r.get('warnings',[]))
  lines.append(' %02d %-14s export %-9s unreal %-12s exp %-6s %s'%(r['index'],(r['piece'] or '')[:14],ex,un,ev,('FAILED: '+str(r['error'])[:120]) if r.get('error') else ('%d error, %d warn'%(errs,warns) if errs or warns else 'ok')))
 probs=[]
 for r in rows:
  tag='%02d %s'%(r['index'],r['piece'])
  for i in r.get('issues',[]):probs.append(('ERROR' if i['level']=='error' else 'warn',tag,i['msg']))
  if r.get('missing'):probs.append(('ERROR',tag,'mesh missing in Unreal after import: '+', '.join(r['missing'][:8])+(' (+%d more)'%(len(r['missing'])-8) if len(r['missing'])>8 else '')))
  for t,k,ex in group_messages(r.get('warnings',[])):probs.append(('warn',tag,'%s%s'%(ex[0] if k==1 else t,'' if k==1 else ' (x%d, e.g. %s)'%(k,'; '.join(ex[:2])))))
  if r.get('error'):probs.append(('ERROR',tag,str(r['error'])[:300]))
 if probs:
  lines.append('Problems:')
  lines+=[' %-5s %s: %s'%p for p in probs]
 return '\n'.join(lines)
def _doc_with_exposure(json_path,bias):
 """write the remembered exposure bias into the export document so the importer builds the cameras with it"""
 d=json.loads(Path(json_path).read_text(encoding='utf-8'))
 if d.get('exposure_bias')!=bias:d['exposure_bias']=bias;Path(json_path).write_text(json.dumps(d),encoding='utf-8')
def unreal_state(bridge):
 """({sequence names}, {scene names with actors in the level}) as the editor has them now"""
 try:seqs={a['path'].split('/')[-1] for a in bridge.get('/assets?path=/Game/Movie')['assets']}
 except Exception:seqs=set()
 try:act={a['label'].split('/')[0] for a in bridge.get('/status')['actors'] if '/' in a['label']}
 except Exception:act=set()
 return seqs,act
def handoff(movie_dir,bridge,only=None,dry_run=False,force=False,jobs=2,calibrate=True,recalibrate=False,check_only=False,send_anyway=False,export=us.export_scene,progress=None,amap=None,root=None,scenes=None):
 """run the handoff; returns dict(rows, sent, skipped, summary). export(blend,out_dir,name) -> .ue.json path is injectable for tests."""
 t_start=time.time();movie_dir=Path(movie_dir)
 if scenes is not None:ok=[(s.get('index',1),s.get('piece'),s['blend'],'built',[]) for s in scenes];skipped=[];names={id(o):s['name'] for o,s in zip(ok,scenes)}     # scenes=[{blend,name[,index,piece]}]: no report.json needed
 else:report=json.loads((movie_dir/'report.json').read_text(encoding='utf-8'));ok,skipped=us.scenes_to_send(report,only);names={}
 root=Path(root) if root else us.export_root()/movie_dir.name;root.mkdir(parents=True,exist_ok=True);state=load_state(root);amap=amap if amap is not None else load_map()
 say=progress or (lambda s:None);catalog=H/'assets'/'prompt-catalog.json'
 seqs,live=(set(),set()) if (check_only) else unreal_state(bridge)
 plan=[]
 for index,piece,blend,status,audit in ok:
  name=names.get(id(ok[len(plan)])) or uc.scene_name(movie_dir.name,index,piece);ekey=export_key(blend,amap,name);j=root/name/(name+'.ue.json');ent=state['scenes'].get(name,{})
  plan.append(dict(index=index,piece=piece,name=name,blend=blend,ekey=ekey,json=j,need_export=force or ent.get('export_key')!=ekey or not j.exists()))
 def run_export(p):
  t=time.time();say('Exporting %s'%p['name']);export(p['blend'],root/p['name'],p['name']);return time.time()-t
 rows=[];pool=cf.ThreadPoolExecutor(max_workers=max(1,jobs));futs={p['name']:pool.submit(run_export,p) for p in plan if p['need_export']}
 try:
  for p in plan:
   name=p['name'];r=dict(index=p['index'],piece=p['piece'],name=name,export='cached',unreal='-',issues=[],warnings=[],missing=[]);rows.append(r);ent=state['scenes'].setdefault(name,{})
   try:
    if name in futs:
     r['export_s']=futs[name].result();r['export']='ran';ent.update(export_key=p['ekey'],blend_sha=sha_file(p['blend']));ent.pop('apply_key',None);save_state(root,state)
    doc=json.loads(p['json'].read_text(encoding='utf-8'));r['issues']=chk.check_scene(doc,p['json'].parent)
    if check_only:r['unreal']='not sent';continue
    if chk.blocking(r['issues']) and not send_anyway:r['unreal']='blocked';continue
    akey=apply_key(p['ekey'],amap,name,catalog=catalog);look=uc.look_overrides(amap,name);pinned=look.get('exposure');lkey=sha_text('look',sha_file(H/'unreal_import.py'),sha_file(H/'ue_common.py'),json.dumps(look,sort_keys=True));bias=float(pinned) if pinned is not None else (ent.get('exposure') if ent.get('exposure_for')==lkey else None)     # a measured bias belongs to the lighting it was measured under
    if not force and not dry_run and ent.get('apply_key')==akey and name in live and any(x.startswith('LS_'+name) for x in seqs):
     r['unreal']='cached';r['sequence']=ent.get('sequence');r['exposure']=ent.get('exposure');continue
    t=time.time();say('Sending %s to Unreal'%name)
    if bias is not None:_doc_with_exposure(p['json'],bias)
    res=us.send_scene(bridge,p['json'],dry_run=dry_run);r['warnings']=list(res.get('warnings') or [])
    if dry_run:r['unreal']='dry run';continue
    r['sequence']=res.get('sequence');r['unreal']='applied'
    if calibrate and r['sequence'] and pinned is None and (bias is None or recalibrate):
     say('Calibrating exposure of %s'%name);bias,measured=us.calibrate_exposure(bridge,p['json'],r['sequence'],start_bias=bias,target=float(look.get('exposure_target',.32)));ent['measured']=measured
     if bias is not None:
      try:bridge.command('save_level',{})
      except us.BridgeError:pass
    r['exposure']=bias;r['unreal_s']=time.time()-t
    try:diag=json.loads((p['json'].parent/(name+'.import.json')).read_text(encoding='utf-8'));r['missing']=diag_missing(doc,diag)
    except (OSError,ValueError):pass
    ent.update(apply_key=akey,sequence=r['sequence'],exposure=bias,exposure_for=lkey,applied_at=int(time.time()),clean=not(r['missing'] or chk.blocking(r['issues'])));save_state(root,state)
   except Exception as e:     # one scene failing never stops the others
    r['error']='%s: %s'%(type(e).__name__,e) if not isinstance(e,us.BridgeError) else str(e)
    if r['unreal']=='-':r['unreal']='failed'
 finally:pool.shutdown(wait=True)
 summary=format_summary(movie_dir.name,rows,time.time()-t_start)
 try:(root/'handoff_summary.txt').write_text(summary+'\n',encoding='utf-8')
 except OSError:pass
 sent=[dict(index=r['index'],piece=r['piece'],name=r['name'],result=dict(sequence=r.get('sequence'),exposure=r.get('exposure'),warnings=r['warnings'])) for r in rows if r['unreal'] in ('applied','cached','dry run')]
 return dict(rows=rows,sent=sent,skipped=[dict(index=i,piece=p,status=s,audit=a) for i,p,f,s,a in skipped],summary=summary)
def handoff_scene(blend,name,bridge,movie='single',**kw):
 """the unit of the whole flow: one built Blender scene -> exported, checked, imported, exposed, playing in Unreal (all the cache rules of handoff apply). Returns the scene's row (export/unreal status, sequence, exposure, issues, warnings, missing) plus the summary text."""
 res=handoff(movie,bridge,scenes=[dict(blend=str(blend),name=name)],**kw);row=res['rows'][0];row['summary']=res['summary'];return row
def movie_scenes(movie,seqs,live):
 """scene names of a movie as the editor holds them: from actor labels 'scene/...' and Level Sequence names LS_<scene>[_<n>]"""
 import re
 out={l for l in live if re.fullmatch(re.escape(movie)+r'_\d+_\w+',l)}
 for q in seqs:
  m=re.fullmatch(r'LS_('+re.escape(movie)+r'_\d+_[A-Za-z]\w*?)(?:_\d+)?',q)
  if m:out.add(m.group(1))
 return sorted(out)
def clean_movie(movie,bridge,progress=None,root=None):
 """remove every scene of a movie from the editor (actors and sequences named <movie>_NN_...) and forget the handoff state; returns the scene names removed. Characters and imported assets stay."""
 seqs,live=unreal_state(bridge);names=movie_scenes(movie,seqs,live)
 root=Path(root) if root else us.export_root()/movie
 for n in names:
  if progress:progress('Removing %s'%n)
  us.purge_scene(bridge,root,n)
 try:bridge.command('save_level',{})
 except us.BridgeError:pass
 try:(root/'handoff_state.json').unlink()
 except OSError:pass
 return names
def save_map(amap,path=None):
 p=Path(path or os.environ.get('UNREAL_ASSET_MAP') or (H/'unreal_asset_map.json'));t=p.with_suffix('.tmp');t.write_text(json.dumps(amap,indent=1),encoding='utf-8');os.replace(t,p)
def swap_main(a):
 """python unreal_handoff.py swap <name> <asset> [--scene swamp] [--scale 1.2] [--no-fit]  |  swap --env <scene> <asset>  |  swap --remove <name> [--scene swamp]  |  swap --list"""
 amap=load_map();scene=None
 if '--scene' in a:i=a.index('--scene');scene=a[i+1];del a[i:i+2]
 scale=None
 if '--scale' in a:i=a.index('--scale');scale=float(a[i+1]);del a[i:i+2]
 fit=False if '--no-fit' in a else None;a=[x for x in a if x!='--no-fit']
 paths=[x for x in (a[2:3] if a[:1]==['--env'] else a[1:2] if len(a)==2 else []) if x]
 for x in paths:
  if not x.startswith('/') or ':' in x or chr(92) in x:print('%r is not an Unreal asset path (like /Game/Props/SM_Rock). Git Bash rewrites a leading / into a Windows path: set MSYS_NO_PATHCONV=1 or use PowerShell.'%x);return 2
 if a[:1]==['--list']:print(json.dumps({k:v for k,v in amap.items() if k in ('assets','props','scenes')},indent=1));return 0
 if a[:1]==['--env'] and len(a)==3:uc.set_environment(amap,a[1],a[2],scale=scale)
 elif a[:1]==['--remove'] and len(a)==2:uc.set_swap(amap,a[1],None,scene)
 elif len(a)==2:uc.set_swap(amap,a[0],a[1],scene,scale=scale,fit=fit)
 else:print(swap_main.__doc__);return 2
 save_map(amap);print('asset map updated (%s); the scenes it concerns are re-imported on the next handoff'%(scene or (a[1] if a[:1]==['--env'] else 'global')));return 0
def main(argv):
 a=list(argv)
 if a[:1]==['swap']:return swap_main(a[1:])
 if a[:1]==['clean'] and len(a)>=2:     # python unreal_handoff.py clean <movie_name> [--bridge URL]
  url=a[a.index('--bridge')+1] if '--bridge' in a else None;gone=clean_movie(a[1],us.Bridge(url),progress=print);print('removed %d scene(s): %s'%(len(gone),', '.join(gone)));return 0
 if a[:1]==['scene'] and len(a)>=3:     # python unreal_handoff.py scene <scene.blend> <scene_name> [flags]
  rest=a[3:];blend,name=a[1],a[2];a=rest;mode='scene'
 else:mode='movie'
 opt=lambda f:f in a
 def val(f,cast=str,default=None):
  if f in a:i=a.index(f);v=cast(a[i+1]);del a[i:i+2];return v
  return default
 bridge_url=val('--bridge');only=val('--scenes',lambda x:{int(y) for y in x.split(',')});jobs=val('--jobs',int,2)
 flags={f:opt(f) for f in ('--force','--dry-run','--no-calibrate','--recalibrate','--check-only','--send-anyway')};a=[x for x in a if x not in flags]
 if mode=='scene':a=['single']
 if not a:print(__doc__);return 2
 bridge=us.Bridge(bridge_url) if not flags['--check-only'] else None
 res=handoff(a[0],bridge,only,dry_run=flags['--dry-run'],force=flags['--force'],jobs=jobs,calibrate=not flags['--no-calibrate'],recalibrate=flags['--recalibrate'],check_only=flags['--check-only'],send_anyway=flags['--send-anyway'],scenes=[dict(blend=blend,name=name)] if mode=='scene' else None,progress=lambda s:print(s,flush=True))
 print(res['summary']);bad=[r for r in res['rows'] if r.get('error') or r['unreal']=='blocked']
 for s in res['skipped']:print('SKIPPED',s)
 return 1 if bad else 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
