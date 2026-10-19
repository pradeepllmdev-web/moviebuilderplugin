"""Story text -> scene list (pure Python, deterministic; an AI planner can refine the result).

  python story_plan.py story.txt          prints the plan

Scenes are separated by blank lines or lines such as 'Scene 3: ...'. Each scene is matched to a set piece (set_pieces.match), gets a time of day from its words, a length and parameters.
Scenes with no set piece are marked builder='shots' (the shot-by-shot movie planner in movie_prompt.py builds those). The plan also lists continuity warnings."""
import re,sys,json,hashlib
import set_pieces,scene_params,locations
LOCATION_OF={m['piece_default']:k for k,m in locations.REGISTRY.items()}
DAMAGES={'avalanche':'buried','siege':'breached'}          # what a scene does to its location for the scenes that follow
SUPPORTS_STATE={'avalanche':True,'siege':False}            # whether the scene script can show a damaged location
TOD_WORDS=[('night',r'\bnight|midnight|moonlit|stars\b'),('dusk',r'\bdusk|sunset|evening|twilight'),('dawn',r'\bdawn|sunrise|early morning|first light'),('overcast',r'\bstorm|overcast|rain|fog|gloomy'),('day',r'\bnoon|midday|afternoon|bright day|daylight|\bmorning\b')]
DEFAULT_SECONDS={'last_egg':50,'storm_ship':60,'cliff_rescue':62,'arena_duel':52,'great_escape':54,'avalanche':48,'siege':72,'council':66,'heist':50,'workshop':30,'rapids':36,'flood':30,'horse_herd':16,'rider':22}
def split_scenes(text):
 parts=[p.strip() for p in re.split(r'\n\s*\n|^\s*scene\s*\d+\s*[:.\-]\s*',text.strip(),flags=re.I|re.M) if p and p.strip()]
 return parts or [text.strip()]
def time_of_day(text):
 for name,pat in TOD_WORDS:
  if re.search(pat,text,re.I):return name
 return None
def plan(text,hero_tint=None):
 """Scene list with builder, piece, params, estimated seconds and continuity warnings."""
 scenes=[];warn=[];state_by_loc={}
 for i,t in enumerate(split_scenes(text),start=1):
  ids=set_pieces.match(t);piece=ids[0] if ids else None;tod=time_of_day(t)
  params={}
  if tod and piece in set_pieces.PARAM_PIECES:params['time_of_day']=tod
  if hero_tint and piece in set_pieces.PARAM_PIECES:params['hero_tint']=list(hero_tint)
  loc=LOCATION_OF.get(piece)
  if loc and loc in state_by_loc:
   if SUPPORTS_STATE.get(piece):params['location_state']=state_by_loc[loc]
   else:warn.append('scene %d revisits %s after it was %s, but this set piece can only show it intact'%(i,loc,state_by_loc[loc]))
  if loc and piece in DAMAGES and loc not in state_by_loc:state_by_loc[loc]=DAMAGES[piece]
  secs=DEFAULT_SECONDS.get(piece) if piece else max(8,min(90,int(len(t.split())/2.5)))
  title=(re.sub(r'\s+',' ',t)[:48]).strip(' .,;:')
  scenes.append(dict(index=i,title=title,text=t,builder='set_piece' if piece else 'shots',piece=piece,location=loc,params=params,seconds=secs,missing=set_pieces.missing(piece) if piece else [],time_of_day=tod))
 for a,b in zip(scenes,scenes[1:]):
  if a['time_of_day'] and b['time_of_day'] and {a['time_of_day'],b['time_of_day']}=={'night','day'}:warn.append('scenes %d and %d jump between night and day without a transition (add a dusk or dawn scene or a title card)'%(a['index'],b['index']))
  if a['piece'] and a['piece']==b['piece']:warn.append('scenes %d and %d use the same set piece (%s); consider merging them'%(a['index'],b['index'],a['piece']))
 for s in scenes:
  if s['builder']=='shots':warn.append('scene %d has no set piece; the shot-by-shot planner (movie_prompt.py) has to build it'%s['index'])
  for m in s['missing']:warn.append('scene %d needs: %s'%(s['index'],m))
 total=sum(s['seconds'] for s in scenes)
 return dict(scenes=scenes,total_seconds=total,estimated_build_minutes=round(sum(2 if s['builder']=='set_piece' else 1 for s in scenes)*1.0,1),warnings=warn,hash=hashlib.sha1(json.dumps([(s['piece'],s['params'],s['seconds']) for s in scenes]).encode()).hexdigest()[:10])
if __name__=='__main__':
 txt=open(sys.argv[1],encoding='utf-8').read() if len(sys.argv)>1 else sys.stdin.read()
 print(json.dumps(plan(txt),indent=1))
