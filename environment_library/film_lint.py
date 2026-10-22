"""Check a film (a dict, or a films/*.py or *.json file) without Blender and say what is wrong, in words a model or a person can act on.

    python film_lint.py films/village_clock_key.py [--json]
    report=film_lint.lint(film)         dict(ok, errors, notes, rules, seconds, scenes)

errors: spec errors and plan audits (collisions, reach, seated eye lines ...): the film cannot be built until these are fixed.
notes: story and pacing notes (dead stretches, walks to nowhere, props that vanish, repeated lines ...): the film builds but is weaker.
rules: {rule id: [messages]}, so a repair prompt can quote the rule that was broken (production_rules.json)."""
import copy,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
BEATS=('go','turn','say','convo','act','point','look','icon','emote','wait','take','put','give','push','sit','stand','sfx','cam')
def normalise(film):
 """a film dict from a model: convo beats expanded into say beats, scene defaults, beat names checked (ValueError names the first problem)"""
 film=copy.deepcopy(film)
 for k in ('id','title','cast','scenes'):
  if k not in film:raise ValueError('the film has no %r'%k)
 if not film['cast'] or not film['scenes']:raise ValueError('the film needs a cast and scenes')
 for sc in film['scenes']:
  for k in ('id','location','cast','steps'):
   if k not in sc:raise ValueError('scene %r has no %r'%(sc.get('id','?'),k))
  sc.setdefault('title',sc['id']);sc.setdefault('intent',sc.get('objective',''));sc.setdefault('props',[]);sc.setdefault('time','day');sc.setdefault('ambience','wind');sc.setdefault('music','calm');sc.setdefault('fog',0.);sc.setdefault('extras',None);sc.setdefault('fx',None)
  def fix_one(b,sid):
   if not isinstance(b,dict) or 'do' not in b:raise ValueError('scene %s: a step is not a beat with a "do"'%sid)
   if b['do'] not in BEATS:raise ValueError('scene %s: unknown beat %r (known: %s)'%(sid,b['do'],', '.join(BEATS)))
   return b
  flat=[]
  for b in sc['steps']:
   if isinstance(b,list):flat.append([fix_one(y,sc['id']) for y in b]);continue
   b=fix_one(b,sc['id'])
   if b['do']=='convo':
    for l in b['lines']:
     d=dict(do='say',who=l[0],text=l[1])
     if len(l)>2 and l[2]:d['mood']=l[2]
     if len(l)>3 and l[3]:d['to']=l[3]
     flat.append(d)
   else:flat.append(b)
  sc['steps']=flat
 film['_normalised']=True
 return film
def load_any(path):
 import perf_movie as pm
 p=Path(path)
 return json.loads(p.read_text(encoding='utf-8')) if p.suffix=='.json' else pm.load_film(p)
def lint(film):
 import perf_movie as pm,perf_plan as pp,perf_storyboard as sb,production_rules as pr
 film=normalise(film) if not film.get('_normalised') else film
 errors=[];notes=[];reg=None
 try:reg=pm.registry_of(film)
 except Exception as e:return dict(ok=False,errors=['cast: %s'%e],notes=[],rules={},seconds=0.,scenes=0)
 rows=pm.plan_check(film,reg);plans=[]
 for sp,r in zip(film['scenes'],rows):
  if r['error']:errors.append('scene %s: %s'%(sp['id'],r['error']));plans.append(None);continue
  errors+=['scene %s: %s'%(sp['id'],a) for a in r['audit']]
  try:plans.append(pp.compile(sp,reg))
  except pp.SpecError as e:plans.append(None);errors.append('scene %s: %s'%(sp['id'],e))
 try:problems=reg.distinct_report()
 except Exception:problems=[]
 notes+=['the cast: %s and %s look alike (score %.2f): make them more different'%p for p in problems]
 if any(plans):
  md=sb.review_md(film,plans)
  if '## Notes' in md:notes+=[l[2:] for l in md.split('## Notes',1)[1].splitlines() if l.startswith('* ') and 'nothing flagged' not in l]
 rules={}
 for m in errors+notes:
  for rid in pr.rule_ids_in(m):rules.setdefault(rid,[]).append(m)
 return dict(ok=not errors,errors=errors,notes=notes,rules=rules,seconds=sum(r['seconds'] for r in rows),scenes=len(rows))
if __name__=='__main__':
 a=sys.argv[1:]
 if not a:print(__doc__);sys.exit(1)
 rep=lint(load_any(a[0]))
 if '--json' in a:print(json.dumps(rep,indent=1))
 else:
  print('%s: %d scenes, %.0f s'%('OK' if rep['ok'] else 'ERRORS',rep['scenes'],rep['seconds']))
  for e in rep['errors']:print('ERROR',e)
  for n in rep['notes']:print('note ',n)
