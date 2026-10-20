"""Prompt -> story file (one paragraph per scene) that build_movie.py turns into a film.

    import story_writer
    text, notes = story_writer.write_story('a lion hero crosses ice, fire and sky to stop a rival mage', minutes=8)

Two paths, same output:
  * with a model (llm.py): the model chooses and orders scenes from the set-piece catalogue and writes one sentence per scene; every sentence is checked to select its intended scene type
    (set_pieces.match) and repaired once if not, so the planner never silently builds the wrong scene;
  * without a model (offline, or the model failed): deterministic. Scene types the prompt names (by their own keywords) come first, then a dramatic default arc fills the film up to the
    requested length, using the template sentences below (each guaranteed, by test, to select its own scene type).
The result is plain text you can edit by hand before building."""
import json,re
import set_pieces,story_plan,llm
SENT={
 'council':'At night the lion council sits around the round table and debates who will take the quest, and Leo volunteers.',
 'workshop':'In his workshop Leo tinkers with clockwork gears and turns the crank of a music box that points the way.',
 'great_escape':'A prison train thunders across the plains while Leo escapes over the roofs and leaps from the bridge into the river.',
 'rapids':'Downstream Leo paddles a raft through the rapids between the boulders of the canyon river.',
 'horse_herd':'At noon a herd of wild horses gallops along the river toward the mountains.',
 'rider':'Leo rides a horse galloping across the plains and jumps the fence.',
 'cliff_rescue':'At the foot of the mountains Leo climbs a sheer cliff to rescue a lost cub and swings across the gap on a rope.',
 'avalanche':'At dusk an avalanche thunders down the snowy mountain and Leo outruns it with the cub.',
 'flood':'A wall of water floods the valley below and Leo rescues a child and carries it to the hill.',
 'flight':'At sunset Leo rides a dragon through the canyon between the rock spires and under the stone arch.',
 'storm_ship':'In a storm Leo fights a sea serpent on the mast of a sailing ship.',
 'last_egg':'At night a stolen dinosaur egg lies in a prehistoric valley beside a glowing volcano and Leo carries it back to its mother.',
 'heist':'At midnight Leo sneaks into the museum past the laser gate and the sentries and steals the jewel before the alarm sounds.',
 'siege':'At dawn an army besieges the citadel with catapults and Leo opens the gate.',
 'arena_duel':'At noon in the gladiator arena Leo faces the rival lion in a duel before the roaring crowd.',
 'observatory':'At night in the old observatory Leo turns the mirror wheels until a moonbeam strikes the crystal and the dome opens.',
 'market':'A thief snatches the star map and Leo chases him through the crowded night market, vaulting the crates he topples.',
 'swamp':'Leo poles a punt through the mangrove swamp while crocodiles lunge from the dark water.',
 'jungle':'Deep in the jungle Leo swings from vine to vine across a ravine toward the ancient temple.',
 'ruins':'Inside the desert temple a giant boulder is released and Leo outruns it, jumps the pit and slides under the closing door.',
 'ice':'In the ice cave Leo leaps between drifting ice floes while stalactites crash around him.',
 'forge':'At the volcano forge Leo hammers a glowing sword on the anvil beside the lava river and quenches it.',
 'reef':'Leo dives into the coral reef, opens a giant clam for the pearl and escapes a shark.',
 'bridge':'Leo sprints across the rotten rope bridge as the planks fall away behind him.',
 'sky':'Leo crosses the floating city, riding the moving platforms above the clouds.',
 'colossus':'A stone giant lifts its arm and Leo rides the palm, walks to the shoulder and pulls the glowing core from its chest.',
 'duel':'On the moonlit tower the rival mage and Leo trade spells in a magic duel, and Leo\'s shield turns the last spell back.'}
# a dramatic default order: set-up, journey, trials, the big set piece, the confrontation
ARC=['council','observatory','workshop','market','great_escape','rapids','swamp','jungle','ruins','ice','forge','reef','horse_herd','rider','cliff_rescue','avalanche','flood','bridge','sky','flight','storm_ship','last_egg','heist','siege','colossus','arena_duel','duel']
def seconds_of(piece):return story_plan.DEFAULT_SECONDS.get(piece,40)
def _pieces_in_prompt(prompt):
 hits=[p for p in set_pieces.match(prompt) if p in SENT]
 return hits
def deterministic(prompt,minutes):
 """scene ids chosen offline: the ones the prompt names, then the default arc until the length is reached"""
 chosen=_pieces_in_prompt(prompt);total=sum(seconds_of(p) for p in chosen);target=minutes*60.
 for p in ARC:
  if total>=target:break
  if p in chosen or p not in SENT:continue
  chosen.append(p);total+=seconds_of(p)
 # keep the arc order for the unnamed fill, the named ones first
 named=_pieces_in_prompt(prompt);rest=[p for p in ARC if p in chosen and p not in named];return named+rest
def _catalogue():
 return [dict(id=k,title=v['title'],what=v['beats'][:160],seconds=seconds_of(k)) for k,v in set_pieces.SET_PIECES.items() if k in SENT]
SYSTEM=('You write the scene list for a short animated film starring a lion hero called Leo. Choose scenes ONLY from the catalogue (use each at most once, in dramatic order) and write ONE plain sentence per scene '
 'that describes what happens and uses the scene\'s own vocabulary so it can be recognised. Return JSON: {"title": str, "scenes": [{"id": catalogue id, "sentence": str}]}.')
def _validate_factory(minutes):
 ids={c['id'] for c in _catalogue()}
 def validate(raw):
  sc=raw['scenes'];out=[];seen=set()
  if not isinstance(sc,list) or not sc:raise ValueError('scenes must be a non-empty list')
  for s in sc:
   i=s['id'];t=str(s['sentence']).strip()
   if i not in ids:raise ValueError('unknown scene id %r'%i)
   if i in seen:raise ValueError('scene %s used twice'%i)
   m=set_pieces.match(t)
   if not m or m[0]!=i:raise ValueError('the sentence for %s selects %s instead; use the scene\'s own words'%(i,m[:1]))
   seen.add(i);out.append((i,t))
  return dict(title=str(raw.get('title','')),scenes=out)
 return validate
def write_story(prompt,minutes=8,use_model=True,theme_time=None):
 """returns (story_text, notes). notes say which path was used and what the length came to."""
 notes=[];scenes=None
 if use_model and llm.available():
  user='Film idea: %s\nTarget length: about %d minutes (scene lengths in the catalogue, seconds).\nCatalogue: %s'%(prompt,minutes,json.dumps(_catalogue()))
  got=llm.plan_json(SYSTEM,user,validate=_validate_factory(minutes))
  if got:scenes=got['scenes'];notes.append('model-written scene list (%s)'%(got.get('title') or 'untitled'))
  else:notes.append('model unavailable or rejected; used the offline writer')
 if scenes is None:
  ids=deterministic(prompt,minutes);scenes=[(i,SENT[i]) for i in ids];notes.append('offline writer: %d scenes'%len(scenes)) if not notes else None
 text='\n\n'.join(t for i,t in scenes)+'\n';total=sum(seconds_of(i) for i,t in scenes);notes.append('about %.1f minutes at default scene lengths'%(total/60.))
 return text,notes
if __name__=='__main__':
 import sys
 prompt=' '.join(sys.argv[2:]) or 'a lion hero journey';mins=int(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1].isdigit() else 8
 t,n=write_story(prompt,mins);print(t);print('\n'.join('# '+x for x in n))
