"""From a story (text, or the story package of 3dobjectnew) to a film the engine can build: a model writes it as JSON under the production rules, the lint checks it, and what is wrong goes back to the model until it is fixed.

    import film_from_story as ffs
    film,report=ffs.generate(story)            story: text or dict(title, logline, characters=[...], scenes=[...]); None when no model is available

Stages (each call is cached and has a repair round, see llm.plan_json):
  1. outline  - the cast and one line per scene (goal, place, time), under the story and character rules;
  2. scenes   - one call per scene with the scene rules, the capabilities and the film so far; the answer is compiled with the planner and rejected, with the exact errors, if it has a spec error, an audit line, or breaks a MUST pacing rule (walks, dead time, no goal);
  3. film     - the finished film is linted as a whole (props that vanish, repeated lines, the closing beat); notes that remain are returned in the report for a person to review.
Nothing here needs Blender. The film dict is the same one films/*.py define: save it with write_film() as films/generated/<id>.json; perf_movie.py builds .json films exactly like .py ones."""
import json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import llm,production_rules as pr,film_lint as fl
MUST_SCENE_RULES=('T01','T02','T05','S01')
OUTLINE_FORMAT='''Reply with one JSON object: {"id":"short_id","title":"...","logline":"one sentence","target_minutes":3,
 "cast":[{"id":"nell","name":"Nell","species":"person","height":1.7,"width":1.0,"depth":1.0,"posture":"neutral","outfit":"mayor","colors":[[0.2,0.35,0.6],[0.25,0.22,0.3],[0.2,0.12,0.08]],"description":"..."}],
 "scenes":[{"id":"rock","title":"...","objective":"the one goal","location":"meadow","time":"day","who":["nell"],"summary":"what happens, in two sentences, with the setup or payoff it carries"}]}'''
def _story_text(story):
 return story if isinstance(story,str) else json.dumps(story,indent=1)
def outline_validate(raw):
 if not isinstance(raw,dict):raise ValueError('the outline must be a JSON object')
 for k in ('id','title','cast','scenes'):
  if k not in raw:raise ValueError('the outline has no %r'%k)
 if not 2<=len(raw['cast'])<=8:raise ValueError('use 2 to 8 characters')
 if not 3<=len(raw['scenes'])<=10:raise ValueError('use 3 to 10 scenes')
 ids={c['id'] for c in raw['cast']}
 for s in raw['scenes']:
  for k in ('id','title','objective','location','who','summary'):
   if k not in s:raise ValueError('scene %r has no %r'%(s.get('id','?'),k))
  bad=[w for w in s['who'] if w not in ids]
  if bad:raise ValueError('scene %s names characters that are not in the cast: %s'%(s['id'],bad))
 return raw
def scene_validator(outline,previous):
 """a validator for one scene's JSON: it must compile and obey the MUST pacing rules; the error text is what the model sees"""
 def validate(raw):
  if not isinstance(raw,dict):raise ValueError('the scene must be a JSON object')
  film=dict(id=outline['id'],title=outline['title'],cast=outline['cast'],scenes=[dict(s) for s in previous]+[raw])
  film=fl.normalise(film);rep=fl.lint(film);sid=raw.get('id','?')
  mine=[e for e in rep['errors'] if e.startswith('scene %s:'%sid)]
  if mine:raise ValueError('; '.join(mine[:6]))
  hard=[(r,m) for r,ms in rep['rules'].items() if r in MUST_SCENE_RULES for m in ms if m.startswith(sid+':')]
  if hard:raise ValueError('rule %s broken: %s'%(hard[0][0],'; '.join(m for r,m in hard[:4])))
  return film['scenes'][-1]
 return validate
def generate(story,provider=None,use_cache=None):
 """(film, lint report), or None when no model is available or an answer could not be repaired"""
 system=pr.prompt_for('story')+'\n\n'+pr.prompt_for('characters',with_capabilities=False).split('MUST:',1)[1]
 outline=llm.plan_json(system+'\n\n'+OUTLINE_FORMAT,'STORY:\n'+_story_text(story),validate=outline_validate,provider=provider,use_cache=use_cache)
 if outline is None:return None
 scenes=[];sysprompt=pr.prompt_for('film_spec')
 for so in outline['scenes']:
  prompt='FILM SO FAR: %s\nCAST: %s\nSCENES ALREADY WRITTEN: %s\nWRITE THIS SCENE (return only its JSON object, with a "steps" list): %s'%(outline['title'],json.dumps(outline['cast']),json.dumps([dict(id=s['id'],end_positions=[(c['id'],c['at']) for c in s['cast']],holds=[c['id'] for c in s['cast'] if c.get('holds')]) for s in scenes]),json.dumps(so))
  sc=llm.plan_json(sysprompt,prompt,validate=scene_validator(outline,scenes),provider=provider,use_cache=use_cache,retries=2)
  if sc is None:return None
  sc.setdefault('objective',so['objective']);scenes.append(sc)
 film=fl.normalise(dict(id=outline['id'],title=outline['title'],logline=outline.get('logline',''),target_minutes=outline.get('target_minutes',3),cast=outline['cast'],scenes=scenes))
 return film,fl.lint(film)
def write_film(film,folder=None):
 """save the film as films/generated/<id>.json (perf_movie.py builds it like a .py film)"""
 d=Path(folder) if folder else H/'films'/'generated';d.mkdir(parents=True,exist_ok=True);p=d/(film['id']+'.json')
 f=dict(film);f.pop('_normalised',None);f.pop('_continuity',None);p.write_text(json.dumps(f,indent=1),encoding='utf-8');return p
if __name__=='__main__':
 a=sys.argv[1:]
 if not a:print(__doc__);sys.exit(1)
 text=Path(a[0]).read_text(encoding='utf-8') if Path(a[0]).exists() else a[0]
 got=generate(text)
 if got is None:print('no model available or an answer could not be repaired (set LLM_PROVIDER / ANTHROPIC_API_KEY)');sys.exit(2)
 film,rep=got;print('wrote',write_film(film));print('errors',rep['errors']);print('notes',*rep['notes'],sep='\n  ')
