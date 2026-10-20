"""One place for every language-model call in the movie flow.

    import llm
    plan = llm.plan_json(system_text, user_text, validate=my_validator)   # dict, or None when no model is available

Why: the planners should not care which provider answers, and nothing may break when there is no key or no network. So:
  * providers are pluggable: 'scene_ai' (the existing OpenAI helper in the sibling 3dobjectnew server, so keys, model choice and request logging stay where they are), 'anthropic' (ANTHROPIC_API_KEY), or any
    function registered with register_provider(name, fn); LLM_PROVIDER picks one ('auto' = the first that has a key, in that order; 'none' disables models);
  * answers are cached on disk by (provider, system, prompt) so repeating a run costs nothing and is reproducible (LLM_CACHE=0 turns it off);
  * the caller's validate(raw) must return the checked object or raise ValueError/KeyError/TypeError; on failure the model gets one repair round with the error text, then the call returns None;
  * None always means 'use the deterministic fallback', never 'crash'."""
import asyncio,hashlib,json,os,sys,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;CACHE=H/'analysis_cache';SIBLING=H.parent.parent/'3dobjectnew'/'server'
class LLMUnavailable(Exception):pass
def _scene_ai(system,prompt):
 if str(SIBLING) not in sys.path:sys.path.insert(0,str(SIBLING))
 try:import scene_ai
 except ImportError as e:raise LLMUnavailable('scene_ai not importable: %s'%e)
 scene_ai.load_env_file();key=os.environ.get('OPENAI_API_KEY','')
 if not key:raise LLMUnavailable('no OPENAI_API_KEY')
 return asyncio.run(scene_ai._call_openai_json(system,prompt,key,None))
def _anthropic(system,prompt):
 key=os.environ.get('ANTHROPIC_API_KEY','')
 if not key:raise LLMUnavailable('no ANTHROPIC_API_KEY')
 body=json.dumps(dict(model=os.environ.get('ANTHROPIC_MODEL','claude-sonnet-5-5'),max_tokens=4096,system=system+'\nReply with one JSON object only.',messages=[dict(role='user',content=prompt)])).encode()
 req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as r:text=''.join(b.get('text','') for b in json.load(r).get('content',[]))
 a,b=text.find('{'),text.rfind('}')
 if a<0 or b<a:raise ValueError('no JSON object in the reply')
 return json.loads(text[a:b+1])
PROVIDERS={'scene_ai':_scene_ai,'anthropic':_anthropic}
def register_provider(name,fn):PROVIDERS[name]=fn
def _choose(provider=None):
 want=(provider or os.environ.get('LLM_PROVIDER','auto')).lower()
 if want=='none':return []
 if want!='auto':return [want] if want in PROVIDERS else []
 return [n for n in ('scene_ai','anthropic') if n in PROVIDERS]+[n for n in PROVIDERS if n not in ('scene_ai','anthropic')]
def _cache_path(name,system,prompt):return CACHE/('llm_%s.json'%hashlib.sha256((name+'\n'+system+'\n'+prompt).encode()).hexdigest()[:24])
def plan_json(system,prompt,validate=None,provider=None,use_cache=None,retries=1):
 """ask a model for a JSON object; returns the validated object or None (no provider, no key, bad answer after the repair round)."""
 use_cache=(os.environ.get('LLM_CACHE','1')!='0') if use_cache is None else use_cache;last=None
 for name in _choose(provider):
  cp=_cache_path(name,system,prompt)
  if use_cache and cp.exists():
   try:
    raw=json.loads(cp.read_text(encoding='utf-8'));return validate(raw) if validate else raw
   except (ValueError,KeyError,TypeError):cp.unlink()
  ask=prompt;err=None
  for attempt in range(retries+1):
   try:raw=PROVIDERS[name](system,ask)
   except LLMUnavailable as e:last=e;break
   except Exception as e:last=e;break
   try:
    out=validate(raw) if validate else raw
    if use_cache:
     CACHE.mkdir(exist_ok=True);cp.write_text(json.dumps(raw),encoding='utf-8')
    return out
   except (ValueError,KeyError,TypeError) as e:
    err=e;ask=prompt+'\nYour previous answer was rejected: %s\nPrevious answer: %s\nReply again with a corrected JSON object.'%(e,json.dumps(raw)[:3000])
 return None
def available(provider=None):
 """True when some provider looks usable (a key is present); does not call the network"""
 for n in _choose(provider):
  if n=='scene_ai':
   try:
    if str(SIBLING) not in sys.path:sys.path.insert(0,str(SIBLING))
    import scene_ai;scene_ai.load_env_file()
    if os.environ.get('OPENAI_API_KEY'):return True
   except Exception:pass
  elif n=='anthropic' and os.environ.get('ANTHROPIC_API_KEY'):return True
  elif n not in ('scene_ai','anthropic'):return True
 return False
