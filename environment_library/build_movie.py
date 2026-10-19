"""Build a whole movie from a story, one scene after another, then assemble it.

  python build_movie.py story.txt out_folder [--hero-tint r,g,b] [--force]

For every scene of story_plan.plan: set_pieces.build (skipped when the scene file already exists for the same piece, parameters and length, so a rerun rebuilds only what changed or failed),
audit lines are collected, then assemble_movie.py joins the good scenes into <out_folder>/movie.blend and a report (report.json and report.md) says what passed, what needs attention and why.
Scenes with no set piece are listed as 'shots' (build them with the shot-by-shot movie planner) and are left out of the master. Scenes are built strictly one after another."""
import json,sys,subprocess,hashlib,time
from pathlib import Path
import story_plan,set_pieces
H=Path(__file__).resolve().parent
def key(s):return hashlib.sha1(json.dumps([s['piece'],s['params'],s['seconds']]).encode()).hexdigest()[:10]
def run(story_text,out,hero_tint=None,force=False,build=None):
 """build: optional replacement for set_pieces.build (used by tests)."""
 build=build or set_pieces.build
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);plan=story_plan.plan(story_text,hero_tint);report=[];files=[]
 for s in plan['scenes']:
  rec=dict(index=s['index'],title=s['title'],piece=s['piece'],params=s['params'],seconds=s['seconds'],status='',audit=[],file=None)
  if s['builder']!='set_piece':
   rec['status']='needs the shot-by-shot planner';report.append(rec);continue
  f=out/('scene_%02d_%s.blend'%(s['index'],s['piece']));meta=f.with_suffix('.json')
  if not force and f.exists() and meta.exists() and json.loads(meta.read_text()).get('key')==key(s):
   rec.update(status='reused',file=str(f),audit=json.loads(meta.read_text()).get('audit',[]));report.append(rec);files.append(dict(file=str(f),title=s['title'],card_seconds=2.0));continue
  t=time.time();r=build(s['piece'],out=f,seconds=s['seconds'],params=s['params'])
  if r['missing']:
   rec['status']='missing: '+'; '.join(r['missing']);report.append(rec);continue
  if not r['ok']:
   rec['status']='build failed';rec['audit']=[r.get('log','')[-200:]];report.append(rec);continue
  meta.write_text(json.dumps(dict(key=key(s),audit=r['audit'])));rec.update(status='built in %.0fs'%(time.time()-t),file=str(f),audit=r['audit']);report.append(rec);files.append(dict(file=str(f),title=s['title'],card_seconds=2.0))
 master=None
 if files:
  (out/'plan.json').write_text(json.dumps(dict(scenes=files)))
  try:
   import quick_review
   subprocess.run([quick_review.BLENDER,'-b','--python',str(H/'assemble_movie.py'),'--',str(out/'plan.json'),str(out/'movie.blend')],capture_output=True,text=True,errors='ignore')
   master=str(out/'movie.blend') if (out/'movie.blend').exists() else None
  except Exception:master=None
 result=dict(plan=plan,report=report,master=master);(out/'report.json').write_text(json.dumps(result,indent=1))
 lines=['# Movie build report','','Planned: %d s in %d scenes'%(plan['total_seconds'],len(plan['scenes'])),'']
 for r in report:lines.append('* scene %d "%s" (%s): %s%s'%(r['index'],r['title'][:40],r['piece'] or 'shots',r['status'],''.join('\n  * '+a for a in r['audit'])))
 lines+=['']+['* WARNING: '+w for w in plan['warnings']]+['','Master: '+str(master)]
 (out/'report.md').write_text('\n'.join(lines),encoding='utf-8');return result
if __name__=='__main__':
 a=sys.argv[1:];tint=None
 if '--hero-tint' in a:
  i=a.index('--hero-tint');tint=[float(x) for x in a[i+1].split(',')];del a[i:i+2]
 force='--force' in a;a=[x for x in a if x!='--force']
 run(open(a[0],encoding='utf-8').read(),a[1],tint,force);print(open(Path(a[1])/'report.md',encoding='utf-8').read())
