"""The production rules as data, and the prompt text built from them.

    import production_rules as pr
    pr.rules_for('scenes')              the rules a scene-writing prompt must obey
    pr.prompt_for('film_spec')          the system prompt for a model that writes a film as JSON: rules + capabilities + format
    pr.capabilities()                   everything the engine can do, read from the code (species, gaits, moods, clips, locations, props)
    pr.rule_ids_in(message)             which rules a lint message belongs to

Stages: story, characters, scenes, shots, film_spec, animation, unreal. production_rules.json is the single source: change a rule there and every prompt, the lint and the checklist test follow."""
import json,re
from pathlib import Path
H=Path(__file__).resolve().parent
RULES_FILE=H/'production_rules.json'
STAGES=('story','characters','scenes','shots','film_spec','animation','unreal')
def load():
 return json.loads(RULES_FILE.read_text(encoding='utf-8'))['rules']
def rules_for(stage,severity=None):
 if stage not in STAGES:raise ValueError('unknown stage %r (known: %s)'%(stage,', '.join(STAGES)))
 return [r for r in load() if stage in r['stages'] and (severity is None or r['severity']==severity)]
def rule_ids_in(message):
 """rule ids whose guard text appears in a lint or audit message"""
 return [r['id'] for r in load() if r['guard']!='manual' and r['guard'] in message]
def capabilities():
 """the engine's vocabulary, read from the code so a prompt can never promise something the engine cannot do"""
 import cast_registry as cr,gaits,perf_plan as pp,perf_locations as pl,dialogue as dg
 src=(H/'perf_locations.py').read_text(encoding='utf-8')
 kinds=sorted(set(re.findall(r"kind=='(\w+)'",src)))
 return dict(species=sorted(cr.SPECIES),postures=list(cr.POSTURES),outfits=sorted(getattr(cr,'OUTFITS',{})),gaits=list(gaits.GAITS),moods=list(dg.MOODS),icons=list(pp.ICONS),emotes=['smile','frown','concern','sad','brows'],act_clips=list(pp.ACT_CLIPS),
  location_presets=list(pl.PRESETS),location_object_kinds=kinds,prop_kinds=sorted(pl.PROP_KINDS),times=['dawn','day','dusk','night','overcast'],music=['calm','mystery','bright','epic','warm','comic','tense'],ambience=['wind','hall','market','harbor','forest','night'])
FORMAT_DOC='''FILM JSON (return exactly one JSON object):
{"id":"short_id","title":"...","logline":"one sentence","target_minutes":3,
 "cast":[{"id":"nell","name":"Nell","species":"person","height":1.7,"width":1.0,"depth":1.0,"posture":"neutral","outfit":"mayor","colors":[[r,g,b],[r,g,b],[r,g,b]],"description":"the clock keeper in a blue coat"}],
 "scenes":[{"id":"rock","title":"The key is left behind","objective":"Nell leaves her key behind","intent":"one sentence",
   "location":{"preset":"meadow","seed":6,"objects":[{"kind":"pedestal","at":[-1,-1],"id":"stand0","height":1.0,"size":0.4}]},
   "time":"day","ambience":"wind","music":"mystery","target_seconds":30,   (optional: the length the brief asks for)
   "cast":[{"id":"nell","at":[-5,-3.5],"face":[-1,-1],"holds":"key"}],
   "props":[{"id":"key","kind":"key","at":[-5,-3.5],"z":1.0,"size":2.2}],
   "steps":[ BEAT, BEAT, [BEAT,BEAT] ]}]}
A BEAT is one of (units are metres, positions are [x,y] on the ground; a nested list means beats that happen at the same time):
 {"do":"go","who":ID,"to":[x,y],"gait":"walk|brisk|run|...","talk":[text,mood,to_id]}     walk (optionally speaking while walking)
 {"do":"say","who":ID,"text":"...","mood":MOOD,"to":ID}                  one line of dialogue
 {"do":"convo","lines":[[ID,text,mood,to_id],...]}                       several lines one after another
 {"do":"act","who":ID,"clip":CLIP}  {"do":"point","who":ID,"at":[x,y,z]|ID|PROP,"dur":1.6}  {"do":"look","who":ID,"at":ID|[x,y],"dur":1.5}
 {"do":"icon","who":ID,"kind":ICON,"dur":1.8}  {"do":"emote","who":ID,"kind":EMOTE,"dur":2}  {"do":"wait","dur":1}
 {"do":"take","who":ID,"prop":PROP}  {"do":"put","who":ID,"on":OBJECT_ID}  {"do":"give","who":ID,"to":ID}  {"do":"sit","who":ID,"on":"bench0.0","face":ID|[x,y]}  {"do":"stand","who":ID}
 {"do":"sfx","name":"bell","at":0.3,"who":ID}'''
def prompt_for(stage,with_capabilities=None):
 """the system prompt for a stage: the rules (must first), and for film_spec the capabilities and the JSON format"""
 rs=rules_for(stage);must=[r for r in rs if r['severity']=='must'];should=[r for r in rs if r['severity']=='should']
 out=['You are a film writer and director for a low-poly animated short film. Follow these production rules exactly; they come from reviewing finished films.','','MUST:']+['- [%s] %s'%(r['id'],r['text']) for r in must]
 if should:out+=['','SHOULD:']+['- [%s] %s'%(r['id'],r['text']) for r in should]
 if with_capabilities or (with_capabilities is None and stage=='film_spec'):
  cap=capabilities();out+=['','CAPABILITIES (use only these names):']+['- %s: %s'%(k,', '.join(map(str,v))) for k,v in cap.items()]+['',FORMAT_DOC]
 return '\n'.join(out)
