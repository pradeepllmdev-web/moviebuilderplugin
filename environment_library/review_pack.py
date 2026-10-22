"""One page to review a whole film in minutes, without watching a render.

    python review_pack.py films/<film>.py scenes/<folder> [--width 480] [--force]

For every scene of a built film (scene_NN_id.blend in the folder, written by perf_movie.py) it renders one still of every camera cut (Workbench, seconds per scene) and writes <folder>/review_pack.html: the film's story notes first (the table-read review and story check), then for each scene its goal, a grid of stills each labelled with time, shot and the PURPOSE of the shot, the spoken lines with their moods, and the audit results. Stills are reused until the scene's .blend changes.
Pure helper: html_page(title, notes, sections) is tested without Blender."""
import html,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
CSS="body{font-family:system-ui,sans-serif;margin:0;background:#16171b;color:#e8e8ea}main{max-width:1280px;margin:0 auto;padding:16px}h1{font-size:22px}h2{font-size:18px;margin:28px 0 4px;border-top:1px solid #333;padding-top:14px}.goal{color:#a9b3c9;margin:0 0 8px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px}.shot{background:#202228;border-radius:6px;overflow:hidden}.shot img{width:100%;display:block}.cap{padding:4px 8px;font-size:12px}.cap b{color:#ffd37a}.lines li{margin:2px 0}.mood{color:#8fb7ff;font-size:12px}.bad{color:#ff8d8d}.ok{color:#8fe3a0}ul{margin:6px 0 6px 18px;padding:0}"
def purpose_at(rows,t):
 """(purpose, detail) of the storyboard row that covers time t"""
 for r in rows:
  if r['t0']<=t<r['t1']+1e-6:return r['purpose'],r['detail']
 return '',''
def html_page(title,notes,sections):
 """sections: list of dict(id, title, goal, shots=[dict(img, time, cut, purpose, detail)], lines=[dict(t0, speaker, to, mood, text)], audit=[str])"""
 e=html.escape;o=['<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s review pack</title><style>%s</style></head><body><main><h1>%s: review pack</h1>'%(e(title),CSS,e(title))]
 o.append('<h2>Story notes</h2><ul>'+''.join('<li>%s</li>'%e(n) for n in notes)+'</ul>' if notes else '<p class="ok">No story notes.</p>')
 for s in sections:
  o.append('<h2>%s</h2><p class="goal">%s</p><div class="grid">'%(e(s['title']),e(s.get('goal',''))))
  for sh in s['shots']:o.append('<div class="shot"><img loading="lazy" src="%s" alt=""><div class="cap"><b>%.1f s</b> %s<br>%s: %s</div></div>'%(e(sh['img']),sh['time'],e(sh['cut']),e(sh['purpose']),e(sh['detail'])))
  o.append('</div><ul class="lines">'+''.join('<li><b>%s</b> to %s <span class="mood">(%s, %.0f s)</span>: %s</li>'%(e(L['speaker']),e(str(L['to'])),e(L['mood']),L['t0'],e(L['text'])) for L in s['lines'])+'</ul>')
  o.append(('<ul class="bad">'+''.join('<li>%s</li>'%e(a) for a in s['audit'])+'</ul>') if s['audit'] else '<p class="ok">Audit clean.</p>')
 o.append('</main></body></html>');return '\n'.join(o)
def build(film_path,out,width=480,force=False):
 import perf_movie as pm,perf_plan as pp,perf_storyboard as sb
 out=Path(out).resolve();film=pm.load_film(film_path);reg=pm.registry_of(film);pm.plan_check(film,reg);plans=[]
 for sp in film['scenes']:
  try:plans.append(pp.compile(sp,reg))
  except pp.SpecError:plans.append(None)
 notes=[];rv=sb.review_md(film,plans)
 if '## Notes' in rv:notes=[l[2:] for l in rv.split('## Notes',1)[1].splitlines() if l.startswith('* ') and 'nothing flagged' not in l]
 sections=[];rdir=out/'review';rdir.mkdir(exist_ok=True)
 for i,(sp,P) in enumerate(zip(film['scenes'],plans),1):
  blend=out/('scene_%02d_%s.blend'%(i,sp['id']))
  if P is None or not blend.exists():continue
  d=rdir/('scene_%02d'%i);fj=d/'frames.json'
  if force or not fj.exists() or fj.stat().st_mtime<blend.stat().st_mtime:
   d.mkdir(exist_ok=True);r=subprocess.run([BLENDER,'-b',str(blend),'--python',str(H/'contact_frames.py'),'--',str(d),'80',str(width)],capture_output=True,text=True,errors='ignore')
   if not fj.exists():print('scene %d: stills failed: %s'%(i,(r.stdout+r.stderr)[-300:]));continue
  meta=json.loads(fj.read_text());rows=sb.scene_rows(P);pj=Path(str(blend)+'.plan.json');audit=[a for a in (json.loads(pj.read_text()).get('audit',[]) if pj.exists() else []) if not a.startswith('AUDIT 0')]
  shots=[]
  for m in meta:
   pu,de=purpose_at(rows,m['time']);shots.append(dict(img='review/scene_%02d/f_%02d_%d.png'%(i,m['index'],m['frame']),time=m['time'],cut=m['cut'],purpose=pu,detail=de))
  sections.append(dict(id=sp['id'],title='%d. %s'%(i,sp.get('title',sp['id'])),goal=sp.get('objective') or sp.get('intent',''),shots=shots,lines=[dict(t0=L['t0'],speaker=L['speaker'],to=L['to'],mood=L['mood'],text=L['text']) for L in P.lines],audit=audit))
 page=out/'review_pack.html';page.write_text(html_page(film.get('title',film.get('id','film')),notes,sections),encoding='utf-8');return page
if __name__=='__main__':
 a=sys.argv[1:];pos=[x for x in a if not x.startswith('--')]
 if len(pos)<2:print(__doc__);sys.exit(1)
 w=int(a[a.index('--width')+1]) if '--width' in a else 480
 if '--width' in a:pos=[x for x in pos if x!=str(w)]
 print('wrote',build(pos[0],pos[1],w,'--force' in a))
