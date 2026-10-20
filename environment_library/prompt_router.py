"""Decide which engine answers a prompt, so the new scenes override the old generators where they are better and the old code stays where it is still the only answer.

    import prompt_router
    r = prompt_router.route(prompt)        # {'engine': 'story'|'set_piece'|'shot'|'environment', 'pieces': [...], 'reason': str}
    r = prompt_router.run(prompt, out_dir) # builds with the new pipeline when the engine is 'story'/'set_piece'; for 'shot'/'environment' returns the decision so the caller uses its existing builder

Rules, in order:
  1. PROMPT_ENGINE=legacy  -> 'shot' (everything goes to the old path; the instant rollback).
  2. several paragraphs, or a long prompt about a film/movie/story -> 'story' (build_movie.py).
  3. the prompt selects a registered scene type (set_pieces.match) -> 'set_piece'.
  4. the prompt only describes a place (build/make a village, city, street, house...) without an actor doing something -> 'environment' (the Unreal prompt-environment builder).
  5. otherwise 'shot' (the single-shot prompt builder).
Fallback: if a new-pipeline build fails its audit or raises, run() reports it and returns engine 'shot' with fell_back=True, so a bad build never silently replaces a working old one."""
import os,re,time
from pathlib import Path
import set_pieces,story_plan
H=Path(__file__).resolve().parent
ENV_WORDS=re.compile(r'\b(build|make|create|generate|design)\b.{0,40}\b(village|town|city|street|streets|house|building|forest|landscape|environment|island|valley|map|level)\b',re.I)
ACTION_WORDS=re.compile(r'\b(walks?|runs?|jumps?|climbs?|fights?|sits?|talks?|says?|chases?|escapes?|swims?|rides?|dances?|opens?|carries|lion|leo|hero|character)\b',re.I)
def route(prompt):
 p=(prompt or '').strip()
 if os.environ.get('PROMPT_ENGINE','').lower()=='legacy':return dict(engine='shot',pieces=[],reason='PROMPT_ENGINE=legacy')
 paras=[x for x in re.split(r'\n\s*\n',p) if x.strip()];words=len(p.split());pieces=set_pieces.match(p)
 if len(paras)>=2 or (words>=60 and re.search(r'\b(film|movie|story|scenes?)\b',p,re.I)):return dict(engine='story',pieces=pieces,reason='%d paragraph(s), %d words'%(len(paras),words))
 if pieces:return dict(engine='set_piece',pieces=pieces,reason='keywords select %s'%pieces[0])
 if ENV_WORDS.search(p) and not ACTION_WORDS.search(p):return dict(engine='environment',pieces=[],reason='describes a place, no actor')
 return dict(engine='shot',pieces=[],reason='no scene type matched')
def run(prompt,out_dir=None,seconds=None):
 """build with the new pipeline when it applies"""
 r=route(prompt);out=Path(out_dir) if out_dir else H/'scenes'/('prompt_'+time.strftime('%Y%m%d_%H%M%S'))
 if r['engine']=='story':
  import build_movie
  try:
   res=build_movie.run(prompt,str(out));r['result']=res;rep=res.get('report',[])
   bad=[x for x in rep if x['piece'] and (x['audit'] or not (x['status'].startswith('built') or x['status']=='reused'))]
   r['legacy_scenes']=[x['index'] for x in rep if not x['piece']]
   if bad:r.update(engine='shot',fell_back=True,reason='scene %d (%s): %s'%(bad[0]['index'],bad[0]['piece'],(bad[0]['audit'] or [bad[0]['status']])[0]))
  except Exception as e:r.update(engine='shot',fell_back=True,reason='build failed: %s'%e)
 elif r['engine']=='set_piece':
  try:
   res=set_pieces.build(r['pieces'][0],out/'scene.blend',seconds,None);r['result']=res
   if not res.get('ok') or res.get('audit'):r.update(engine='shot',fell_back=True,reason='set piece failed or has audit issues: %s'%(res.get('missing') or res.get('audit')))
  except Exception as e:r.update(engine='shot',fell_back=True,reason='set piece raised: %s'%e)
 return r
if __name__=='__main__':
 import sys,json;print(json.dumps(route(' '.join(sys.argv[1:])),indent=1))
