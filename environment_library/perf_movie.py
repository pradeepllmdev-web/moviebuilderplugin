"""Build a whole film from performance-scene specs, one scene after another, then report.

  python perf_movie.py films/clockwork_festival.py out_folder                 plan check, build every scene (own Blender process each, strictly sequential), contact sheet per scene, master, report
  python perf_movie.py films/ember_road.py out_folder --plan-only             compile and audit every scene without Blender (seconds), print the timing table
  python perf_movie.py films/ember_road.py out_folder --scenes 3,4 --force    rebuild only some scenes
  python perf_movie.py films/ember_road.py out_folder --no-sheets --no-master

A film module defines FILM=dict(id, title, cast=[character records for cast_registry], scenes=[spec dicts from perf_dsl.scene]). Steps: (1) the cast registry is validated and written to <out>/cast.json (with the story records other tools read:
cast_story.json), (2) every scene is compiled by perf_plan and audited WITHOUT Blender (a spec error or plan audit stops the build of that scene and is reported), (3) each scene is built by perf_scene.py in its own Blender process, one after another,
reused when its spec, cast and the engine sources are unchanged (key in <scene>.meta.json), (4) a labelled contact sheet of stills (Workbench, no video) per scene is written to <out>/sheets, (5) assemble_movie.py joins the good scenes into <out>/movie.blend,
(6) report.md/report.json list per scene: length, audit lines, measured numbers (eye lines, foot slip, hand reach, framing), build time, plus the film total against its target length."""
import hashlib,importlib.util,json,subprocess,sys,time,os
from pathlib import Path
H=Path(__file__).resolve().parent
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
ASSETS=H/'scenes'/'ship_assets'
ENGINE_FILES=('perf_scene.py','perf_plan.py','perf_camera.py','perf_locations.py','perf_audio.py','cast_builder.py','cast_registry.py','gaits.py','dialogue.py','scene_base.py')
def load_film(path):
 spec=importlib.util.spec_from_file_location('film_'+Path(path).stem,str(path));m=importlib.util.module_from_spec(spec);sys.path.insert(0,str(H));spec.loader.exec_module(m);return m.FILM
def engine_hash():
 h=hashlib.sha1()
 for f in ENGINE_FILES:h.update((H/f).read_bytes())
 for g in sorted((ASSETS).glob('leo_*.blend')) if False else []:h.update(g.read_bytes())
 return h.hexdigest()[:12]
def registry_of(film):
 import cast_registry as cr
 return cr.Registry(film['cast'])
def scene_key(spec,reg_json,eh):return hashlib.sha1((json.dumps(spec,sort_keys=True)+reg_json+eh).encode()).hexdigest()[:12]
def plan_check(film,reg=None):
 """compile every scene without Blender: [(index, id, seconds, lines, audit list or [error])]"""
 import perf_plan as pp
 reg=reg or registry_of(film);rows=[]
 for i,sp in enumerate(film['scenes'],1):
  try:
   P=pp.compile(sp,reg);rows.append(dict(index=i,id=sp['id'],title=sp.get('title',''),seconds=round(P.seconds,1),lines=len(P.lines),cast=len(P.actors),audit=P.audit(),error=None))
  except pp.SpecError as e:rows.append(dict(index=i,id=sp['id'],title=sp.get('title',''),seconds=0,lines=0,cast=0,audit=[],error=str(e)))
 return rows
def total_seconds(rows):return sum(r['seconds'] for r in rows)
def build_scene(spec,out,index,cast_json,force=False,sheets=12,eh=None):
 """build one scene file; returns the report record"""
 eh=eh or engine_hash();name='scene_%02d_%s'%(index,spec['id']);blend=out/(name+'.blend');sj=out/(name+'.spec.json');meta=out/(name+'.meta.json')
 reg_json=Path(cast_json).read_text(encoding='utf-8');key=scene_key(spec,reg_json,eh)
 if not force and blend.exists() and meta.exists():
  m=json.loads(meta.read_text())
  if m.get('key')==key:m['status']='reused';return m
 sj.write_text(json.dumps(spec,indent=1),encoding='utf-8');t=time.time()
 for old in (Path(str(blend)+'.plan.json'),):
  if old.exists():old.unlink()
 r=subprocess.run([BLENDER,'-b','--disable-autoexec','--python',str(H/'perf_scene.py'),'--',str(ASSETS),str(blend),str(sj),str(cast_json)],capture_output=True,text=True,errors='ignore')
 pj=Path(str(blend)+'.plan.json');rec=dict(index=index,id=spec['id'],title=spec.get('title',''),key=key,file=str(blend))
 if not pj.exists() or not blend.exists():
  rec.update(status='build failed',audit=['BUILD FAILED: '+(r.stdout[-700:]+r.stderr[-500:]).strip().replace('\n',' | ')[-900:]],seconds=0,stats={});meta.write_text(json.dumps(rec));return rec
 info=json.loads(pj.read_text());rec.update(status='built in %.0fs'%(time.time()-t),audit=info['audit'],seconds=round(info['seconds'],1),stats=info['stats'],lines=len(info['lines']),cuts=len(info['cuts']),cast=info['cast'])
 meta.write_text(json.dumps(rec));return rec
def sheet(rec,out,n=12):
 import contact_sheet as cs
 d=out/'sheets';d.mkdir(exist_ok=True);p=d/('scene_%02d_%s.png'%(rec['index'],rec['id']))
 try:cs.render(rec['file'],str(p),n,3,480);rec['sheet']=str(p)
 except Exception as e:rec['sheet_error']=str(e)[:200]
 return rec
def run(film_path,out,scenes=None,force=False,plan_only=False,sheets=12,master=True,target_minutes=15.):
 film=load_film(film_path);out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);reg=registry_of(film)
 problems=reg.distinct_report();rows=plan_check(film,reg);cast_json=out/'cast.json';reg.save(str(cast_json));(out/'cast_story.json').write_text(json.dumps(reg.export_story_records(),indent=1),encoding='utf-8')
 lines=['# %s: build report'%film.get('title',film.get('id','film')),'','Cast: %d characters%s'%(len(film['cast']),''.join('\n* WARNING: %s and %s look alike (score %.2f)'%p for p in problems)),'','## Plan check (no Blender)','']
 for r in rows:lines.append('* scene %02d %s: %.1f s, %d characters, %d lines%s%s'%(r['index'],r['id'],r['seconds'],r['cast'],r['lines'],('\n  * SPEC ERROR: '+r['error']) if r['error'] else '',''.join('\n  * '+a for a in r['audit'])))
 tot=total_seconds(rows);lines+=['','Planned length: %.1f s = %.1f minutes (target %.0f)'%(tot,tot/60,target_minutes),'']
 if plan_only:
  (out/'plan_report.md').write_text('\n'.join(lines),encoding='utf-8');print('\n'.join(lines));return dict(rows=rows,total=tot)
 recs=[];eh=engine_hash();want=set(scenes) if scenes else None;files=[]
 for i,sp in enumerate(film['scenes'],1):
  if want and i not in want:
   meta=out/('scene_%02d_%s.meta.json'%(i,sp['id']))
   if meta.exists():r=json.loads(meta.read_text());r['status']='kept';recs.append(r);files.append(dict(file=r['file'],title=sp.get('title',''),card_seconds=0))
   continue
  if rows[i-1]['error']:recs.append(dict(index=i,id=sp['id'],title=sp.get('title',''),status='spec error',audit=['SPEC ERROR: '+rows[i-1]['error']],seconds=0,stats={}));continue
  rec=build_scene(sp,out,i,cast_json,force,sheets,eh);print('scene %02d %s: %s, %s s, %d audit lines'%(i,sp['id'],rec['status'],rec.get('seconds'),len(rec.get('audit',[]))),flush=True)
  if sheets and rec['status']!='build failed' and (rec['status']!='reused' or not (out/'sheets'/('scene_%02d_%s.png'%(i,sp['id']))).exists()):sheet(rec,out,sheets)
  elif sheets and rec['status']=='reused':rec['sheet']=str(out/'sheets'/('scene_%02d_%s.png'%(i,sp['id'])))
  recs.append(rec)
  if rec['status']!='build failed':files.append(dict(file=rec['file'],title=sp.get('title',''),card_seconds=0))
 masterf=None
 if master and files:
  (out/'plan.json').write_text(json.dumps(dict(scenes=files)))
  subprocess.run([BLENDER,'-b','--python',str(H/'assemble_movie.py'),'--',str(out/'plan.json'),str(out/'movie.blend')],capture_output=True,text=True,errors='ignore')
  masterf=str(out/'movie.blend') if (out/'movie.blend').exists() else None
 lines+=['## Build','']
 bad=0
 for r in recs:
  a=[x for x in r.get('audit',[]) if not x.startswith('AUDIT 0')];bad+=len(a)
  st=r.get('stats',{});lines.append('* scene %02d %s "%s": %s, %.1f s, %s lines, %s cuts; foot slip %.2f, reach %.2f, eye %.0f/%.0f, framing misses %s/%s%s'%(r['index'],r['id'],r.get('title',''),r['status'],r.get('seconds',0),r.get('lines','-'),r.get('cuts','-'),st.get('foot_slip',0),st.get('reach',0),st.get('eye_speaker',0),st.get('eye_listener',0),st.get('framing_misses','-'),st.get('framing_checked','-'),''.join('\n  * '+x for x in a)))
 total=sum(r.get('seconds',0) for r in recs);lines+=['','Built length: %.1f s = %.1f minutes; audit lines: %d; master: %s'%(total,total/60,bad,masterf)]
 (out/'report.md').write_text('\n'.join(lines),encoding='utf-8');(out/'report.json').write_text(json.dumps(dict(film=film.get('id'),records=recs,master=masterf,total_seconds=total,audit_lines=bad),indent=1))
 print('\n'.join(lines[-6:]));return dict(records=recs,total=total,audit_lines=bad)
if __name__=='__main__':
 a=sys.argv[1:]
 if len(a)<2:print(__doc__);sys.exit(1)
 sc=None
 if '--scenes' in a:i=a.index('--scenes');sc=[int(x) for x in a[i+1].split(',')];del a[i:i+2]
 flags=set(x for x in a if x.startswith('--'));pos=[x for x in a if not x.startswith('--')]
 run(pos[0],pos[1],sc,'--force' in flags,'--plan-only' in flags,0 if '--no-sheets' in flags else 12,'--no-master' not in flags)
