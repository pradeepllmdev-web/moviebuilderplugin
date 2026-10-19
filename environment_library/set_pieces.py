"""Registry of the large Blender set pieces (creature, herd, rider and ship scenes) so prompts can be routed to them and built with the lessons applied.

  python set_pieces.py match "a lion fights a sea serpent on a ship in a storm"
  python set_pieces.py build storm_ship [seconds]
  python set_pieces.py --write-docs        regenerate SET_PIECES.md (lessons come from scene_kit.LESSONS)

A set piece is not a per-shot activity plan (scene_prompt.py): it is a whole scene script. The planner text below tells the AI planner to report such requests as
unsupported 'set_piece:<id>' so the studio can route them here instead of faking them with the forest shot builder."""
import re,subprocess,sys,json
from pathlib import Path
H=Path(__file__).resolve().parent
DINO_DIR=H/'assets/quaternius_dinosaurs_download/extracted/Dinosaur Animated Pack - Dec 2018/Blends'
def horse_blend():
 found=sorted((H/'assets/quaternius_farm_animals_download').glob('**/Horse.blend'));return found[0] if found else H/'assets/quaternius_farm_animals_download/Horse.blend'
SET_PIECES={
 'last_egg':dict(title='The Last Egg',script='dino_scene.py',keywords=r'dinosaur|dino\b|raptor|t-?rex|triceratops|apatosaurus|jurassic|prehistoric|volcano.*egg|egg.*volcano',
  needs=['assets/quaternius_dinosaurs_download (CC0 "Dinosaur Animated Pack - Dec 2018" by Quaternius, itch.io; ask before downloading)','scenes/ship_assets (python build_ship_assets.py; needs climb, idle, pick, run, jump, sit)'],
  beats='lion walks to a nest, picks up an egg, is chased by raptors, leaps onto a triceratops and rides through a swamp, a T-Rex roars, the egg is returned to the apatosaurus and glows (50 s, 9 cameras, sound)',
  limits='the leap is an arc, the rider sits via the Sit clip, no biting or fighting contact'),
 'storm_ship':dict(title='The Storm Ship',script='ship_scene.py',keywords=r'\bship\b|\bsailing\b|\bpirate|sea serpent|kraken|storm at sea|\bmast\b',
  needs=['scenes/ship_assets (python build_ship_assets.py)'],
  beats='lion on a rocking ship climbs the mast, cuts a cloth sail, falls, fights a sea serpent, lightning ends it, calm (60 s, 13 cameras, sound)',
  limits='climbing is a walk cycle on a ladder, hands do not grip, serpent is chunky spheres, rain is thin'),
 'cliff_rescue':dict(title='The Cliff Rescue',script='cliff_scene.py',keywords=r'\bcliff\b|rock face|rock climb|free.?climb|rappel|abseil|rope swing|stranded cub|lost cub',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs the pick clip)'],
  beats='lion free-climbs a cliff on real hand and foot holds, swings across a gap on a rope, climbs on while rocks fall, lifts a cub onto his back and rappels down as the rope frays (62 s, 12 cameras, sound)',
  limits='rappel feet slide instead of hopping, hands do not wrap the rope, wall is low poly, rocks do not hit the climber'),
 'arena_duel':dict(title='The Arena',script='arena_scene.py',keywords=r'\barena\b|gladiator|\bduel\b|fights? (?:a |the )?(?:rival|lion)|wrestl|\bgrapple|\bfight scene|boss fight',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs block, bow, kick, jump, punch, fall, getup, hit, dodge, run, cele)'],
  beats='Leo fights a bigger rival lion in a ruined arena: charge and block, counter jab, grapple, sweep, throw over the shoulder, roar, bow (52 s, 14 cameras, sound)',
  limits='grapple is a bear-hug (arms on shoulders), feet skate in the grapple, impact points are bone-to-bone only (no soft-body)'),
 'great_escape':dict(title='The Great Escape',script='train_scene.py',keywords=r'\btrain\b|railway|\bescape\b|prison|train roof|jump(?:s|ing)? (?:between|across) (?:wagons|cars)|chased on|roof of a',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, run, jump, kick, getup, fall, look, cele)'],
  beats='Leo wakes on a speeding prison train, runs the roofs with two guards behind him, jumps the gaps, ducks a gantry, kicks a guard off, turns a brake wheel to release the coupling so the rear cars fall behind, and leaps from a bridge into a river (54 s, 14 cameras, sound)',
  limits='ducking is a lean on the run clip, the hands do not grip the rim exactly (they follow rim points), guards use one clip set, interior of the wagons is not modelled'),
 'avalanche':dict(title='The Avalanche',script='avalanche_scene.py',keywords=r'avalanche|landslide|rockslide|village flees|crowd (?:flees|runs)|evacuat|stampede of people|panic',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, look, run, climb, pick, cele)'],
  beats='an avalanche of 270 baked boulders hits a mountain village: Leo warns the 36 cloned lions, saves a lost cub, closes the sliding door of the shelter in time (48 s, 12 cameras, sound)',
  limits='the avalanche is boulders and puffs (no snow simulation), the door push is a walk clip with hands on the edge, characters do not react to near boulders'),
 'siege':dict(title='The Siege',script='siege_scene.py',keywords=r'siege|castle|citadel|fortress|catapult|battering|storm(?:s|ing)? the (?:wall|gate)|army (?:attacks|storms|marches)|medieval battle',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, look, run, climb, kick, fall, cele)'],
  beats='an army of 34 cloned lions and 240 troopers besieges a citadel: four catapults breach the wall (54 baked blocks), Leo climbs a ladder, kicks a defender off the wall, turns the winch to raise the portcullis, the army floods in and he hoists the banner (72 s, 14 cameras, sound)',
  limits='troopers are cones, the portcullis does not block the crowd physically, arrows are not aimed at actors, no cavalry'),
 'council':dict(title='The Council',script='council_scene.py',keywords=r'council|debate|negotiat|meeting|argue around|round table|decide together|discuss(?:es|ion)?|conversation at the table',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs sit)'],
  beats='six lions argue and decide around a round table: scripted lines with lip sync from syllables, eye lines to the speaker, arm gestures, a scroll passed across the table, a gavel (66 s, generated coverage, voices synthesised from the same syllable times)',
  limits='seated gestures are IK arm targets (no finger poses), voices are synthetic syllable tones, expressions come from the pipeline shape keys'),
 'heist':dict(title='The Night Heist',script='heist_scene.py',keywords=r'heist|burglar|steal(?:s|ing)? (?:the|a) (?:jewel|diamond|gem)|museum|laser|sneak(?:s|ing)? past|stealth|thief|robb(?:ery|er)',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, look, run, climb, crawl, kneel, jump)'],
  beats='Leo sneaks through a moonlit museum past two sweeping flashlight sentries and a blinking laser gate, cracks the pedestal dial, lifts the glass lid, takes the jewel, the alarm sounds and he leaps out of the window (about 50 s; the route is found by a stealth planner and audited frame by frame)',
  limits='sentries only sweep (no chase), vision is cone plus ray cast, hands use IK targets with no finger poses'),
 'workshop':dict(title='The Workshop',script='workshop_scene.py',keywords=r'workshop|tinker|clockwork|music box|gears?|invent(?:s|or|ion)|assembl(?:es|ing)|watchmaker|crank',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle)'],
  beats='Leo assembles a clockwork music box at his bench: picks three gears, seats them on their pins with IK hands, turns the crank (the gears mesh with real teeth) and a bird pops out and a bell rings (about 30 s)',
  limits='one standing pose at the bench, hands are IK targets with no finger poses, gears are fixed to three pins'),
 'rapids':dict(title='The Rapids',script='rapids_scene.py',keywords=r'rapids|raft|white ?water|river canyon|paddl(?:es|ing)|rafting|steers? (?:the|a) (?:raft|boat)|boulders?',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle)'],
  beats='Leo steers a log raft down a canyon river with a sweep oar: seven boulders, the raft rides the real animated water surface (height, pitch, roll from ray casts), a planner picks the pass side and times the oar strokes (about 36 s)',
  limits='straight canyon, waves are modifier waves (no foam simulation), one stance on the raft, hands are IK targets with no finger poses'),
 'flood':dict(title='The Flood',script='flood_scene.py',keywords=r'flood(?:s|ed|ing)?|tidal wave|tsunami|dam (?:breaks|bursts)|wall of water|torrent|deluge',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, run)'],
  beats='a wall of water sweeps down a valley: forty villagers flee to the hill (a planner speeds up anyone who would be caught), debris floats and drifts, Leo outruns the front, lifts a stranded child off a cart with IK hands and sets it on a rock on the hilltop (about 30 s)',
  limits='the flood is one water body with a constant-speed front (no splashes or spray simulation), villagers are simple figures, hands are IK targets with no finger poses'),
 'flight':dict(title='The Flight',script='flight_scene.py',keywords=r'dragon|fl(?:y|ies|ying) (?:on|over|through)|\bwings?\b|soar(?:s|ing)?|wyvern|flight|ride[sr]? a dragon',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs sit)'],
  beats='Leo rides a procedural dragon through a sky canyon: a slalom between ten rock spires and a dive under a stone arch; the body trails along the path, the wings beat in bursts before each spire (FK chain with lag, membrane by shape keys) and glide in between (about 36 s)',
  limits='the dragon has no legs, the rider is seated (no gestures), wings are a three-finger fan, hands are IK targets on a handlebar'),
 'ice':dict(title='The Ice Cave',script='ice_scene.py',keywords=r'ice cave|frozen cave|glacier|ice floes?|stalactites?|frozen lake|crosses? the ice',
  needs=['scenes/ship_assets (python build_ship_assets.py; needs idle, run, jump)'],
  beats='Leo crosses a frozen cavern by leaping between nine drifting ice floes while stalactites crash down around him: a planner finds each hop window from the sine paths of the floes, stalactites land as near misses (about 40 s)',
  limits='floes are rigid discs on sine paths, shattering is shards on ballistic arcs, hands are not used'),
 'ruins':dict(title='The Boulder Trap',script='ruins_scene.py',keywords='boulder trap|rolling boulder|giant boulder|temple trap|desert ruins|desert temple|booby.?trap|treasure temple',
  needs=['scenes/ship_assets (needs idle, startle, run, jump, crawl, cele)'],
  beats='a giant boulder is released in a desert temple corridor: its top speed is bisected so the closest approach to Leo is 2.2 m, it smashes ten statues, jams in a pit Leo jumps, and Leo slides under a closing door whose timing is solved for a 1.0 m gap (about 28 s)',limits='one corridor, the boulder rolls straight (no steering), statues topple forward only, hands are not used'),
 'jungle':dict(title='The Vine Swings',script='jungle_scene.py',keywords='jungle|vines?|swings? (?:from|across|between)|temple ravine|stone platforms|idol',
  needs=['scenes/ship_assets (needs idle, run, cele)'],
  beats='Leo crosses a jungle ravine on five real pendulum vines: each vine is at its back extreme when he is ready, he hops on, hangs by IK hands, and the release time is solved so the ballistic flight lands him at the next grab point (about 36 s)',limits='platforms are level, one vine per gap, hands are IK targets with no finger poses'),
 'reef':dict(title='The Reef',script='reef_scene.py',keywords='reef|underwater|coral|dives? (?:into|down)|shark|giant clam|pearl|school of fish',
  needs=['scenes/ship_assets (needs idle, run)'],
  beats='Leo dives through a coral reef (flutter-kick swim, pitched from the path), opens a giant clam and takes the pearl with both hands, and escapes a shark into a crevice: 100 boid fish part around him and burst away from the shark, whose head follows his path a shrinking 14 to 3.4 m behind (about 55 s)',limits='swimming reuses the run clip as the kick, one school, the shark is a segment chain with no jaw animation, hands are IK targets with no finger poses'),
 'forge':dict(title='The Volcano Forge',script='forge_scene.py',keywords='forge|blacksmith|anvil|hammer(?:s|ing)? (?:a |the )?(?:sword|blade|iron)|molten|lava river|forges? a sword',
  needs=['scenes/ship_assets (needs idle, climb)'],
  beats='Leo forges a sword in a cavern by a lava river: heats the billet in the furnace, hammers it in three rounds of blows (the head arcs to the strike point, sparks fly, the blade lengthens), a heat model that decays between stations, quenches it in the trough and raises the finished blade (about 45 s)',limits='one smith, one blade; the swing is a planar arc, hands are IK targets with no finger poses'),
 'sky':dict(title='The Sky City',script='sky_scene.py',keywords='sky city|floating (?:city|islands?|platforms?)|moving platforms?|cloud city|airship|above the clouds',
  needs=['scenes/ship_assets (needs idle, jump, cele)'],
  beats='Leo crosses a floating city by riding and leaping between moving platforms (a slider, lifts, a rotating disc he rides round on, an orbiting pad): the planner scans for each hop window in 3D, the landing point on the disc is placed on the side he arrives from, and platforms dip on landing (about 40 s)',limits='platform paths are analytic, one traveller, wind turbines and an airship are scenery on fixed paths, hands are not used'),
 'market':dict(title='The Night Market',script='market_scene.py',keywords='night market|bazaar|market chase|chases? (?:the |a )?thief|lantern market|stolen sack|crowded market',
  needs=['scenes/ship_assets (needs idle, run, startle)'],
  beats='Leo chases a thief through a crowded lantern market: a path-following pursuit whose gap closes from 10 m to 0.9 m, 60 steered bystanders part around the runners, the thief topples five crate stacks that Leo vaults, and the thief hands the sack back (about 45 s)',limits='one street, bystanders are simple figures, the thief is a second lion, hands are IK targets with no finger poses'),
 'swamp':dict(title='The Swamp',script='swamp_scene.py',keywords='swamp|bayou|mangrove|crocodiles?|alligators?|punt|poles? (?:a|the) (?:boat|punt)',
  needs=['scenes/ship_assets (needs idle)'],
  beats='Leo poles a punt through a night swamp: the pole is planted on the bed and its tip stays fixed while the boat advances by exactly the change in its lean, four crocodiles lunge as he passes (heads arc off the hull, bodies trail the head), and two are fended off by the pole (about 50 s)',limits='one channel, crocodiles lunge and miss (no bite or damage), hands are IK targets with no finger poses'),
 'duel':dict(title='The Spell Duel',script='duel_scene.py',keywords='spell duel|wizard|mage|sorcer|magic duel|casts? (?:a )?spells?|spell',
  needs=['scenes/ship_assets (needs idle, dodge, block, fall, lie, cele)'],
  beats='on a moonlit mage tower Leo and a rival trade five homing spells: spells steer with a limited turn rate, the dodge planner picks the sidestep timing that gives the smallest miss of at least 0.75 m, one spell is blocked by a shield and Leo reflects the last back at the rival (about 38 s)',limits='two fighters on a platform, spells are glowing spheres with trails, casting is an IK arm thrust (no finger poses)'),
 'horse_herd':dict(title='Horse herd',script='horse_herd.py',keywords=r'herd of horses|horse herd|galloping horses|wild horses|stampede',
  needs=['assets/quaternius_farm_animals_download (CC0 "Farm Animals Animated" by Quaternius; ask before downloading)'],
  beats='aerial herd of 70 galloping horses along a river toward mountains (16 s, 5 cameras, sound)',limits='no riders, foals are scaled copies'),
 'rider':dict(title='Rider on a galloping horse',script='rider_scene.py',keywords=r'ride[sr]? a horse|riding a horse|rider on|on horseback|horseback|mounts? (?:the|a) horse',
  needs=['assets/quaternius_farm_animals_download','a built rider scene.blend (lion_source.blend or a quick_review shot)'],
  beats='rider mounts and gallops, jumps a fence, dust at every hoof, 7 cameras incl. rider point of view (22 s)',limits='mount is a leap, legs are IK, hands do not wrap the reins'),
}
def match(prompt):
 """Set piece ids whose keywords appear in the prompt, best first."""
 scored=[(len(re.findall(v['keywords'],prompt,re.I)),k) for k,v in SET_PIECES.items()];return [k for n,k in sorted(scored,reverse=True) if n]
def planner_text():
 names=', '.join('%s (%s)'%(k,v['beats'].split(' (')[0][:70]) for k,v in SET_PIECES.items())
 return ' Whole-scene set pieces exist outside this shot builder: '+names+'. If the request is one of these (creature chase, ship at sea, horse herd, riding a horse), do not fake it with walk or run beats: list "set_piece:<id>" in unsupported and keep a plain idle beat so the studio can route it.'
ASSET_PIECES=('storm_ship','cliff_rescue','arena_duel','great_escape','avalanche','siege','council','heist','workshop','rapids','flood','flight','ice','ruins','jungle','reef','forge','sky','market','swamp','duel')   # scenes that take (ship_assets, out)
def missing(piece):
 """Human-readable list of what is not there yet (nothing is downloaded automatically)."""
 gone=[]
 if piece=='last_egg':
  if not DINO_DIR.is_dir():gone.append('dinosaur pack: '+SET_PIECES[piece]['needs'][0])
  if not (H/'scenes/ship_assets/leo_sit.blend').exists():gone.append('lion clips: python build_ship_assets.py')
 elif piece in ASSET_PIECES:
  if not (H/'scenes/ship_assets/leo_idle.blend').exists():gone.append('lion clips: python build_ship_assets.py')
 elif piece in('horse_herd','rider'):
  if not horse_blend().exists():gone.append('horse pack: '+SET_PIECES['horse_herd']['needs'][0])
  if piece=='rider' and not (H/'scenes/lion_source.blend').exists():gone.append('rider scene: build a lion shot first')
 return gone
def command(piece,out,seconds=None):
 import quick_review
 b=[quick_review.BLENDER,'-b','--disable-autoexec','--python',str(H/SET_PIECES[piece]['script']),'--']
 tail=[str(seconds)] if seconds else []
 if piece=='last_egg':return b+[str(DINO_DIR),str(H/'scenes/ship_assets'),str(out)]+tail
 if piece in ASSET_PIECES:return b+[str(H/'scenes/ship_assets'),str(out)]+tail
 if piece=='horse_herd':return b+[str(horse_blend()),str(out),'64']+tail
 return b+[str(horse_blend()),str(H/'scenes/lion_source.blend'),str(out),str(seconds or 22),'lion']
PARAM_PIECES=('last_egg','arena_duel','great_escape','avalanche','siege')   # scenes that read SCENE_PARAMS (time_of_day, hero_tint); the storm scenes keep their own sky
def build(piece,out=None,seconds=None,params=None):
 """Build a set piece in Blender; returns {'ok','out','audit':[...],'missing':[...]} (audit lines come from scene_kit.audit)."""
 gone=missing(piece)
 if gone:return dict(ok=False,missing=gone,audit=[],out=None)
 out=Path(out or H/'scenes'/(piece+'.blend'));out.parent.mkdir(parents=True,exist_ok=True)
 try:
  import locations;locations.ensure_for(piece,dict(params or {},seconds=seconds or 54.))   # shared locations are built once into bank/ and appended by the scene
 except Exception as ex:
  print('locations bank skipped:',ex)
 import os
 env=dict(os.environ);env['SCENE_PARAMS']=json.dumps(params or {})
 proc=subprocess.run(command(piece,out,seconds),capture_output=True,text=True,errors='ignore',timeout=1800,env=env)
 audit=[l.strip() for l in proc.stdout.splitlines() if l.startswith('AUDIT ') and 'issues' not in l]
 return dict(ok=proc.returncode==0 and out.exists(),out=str(out),audit=audit,missing=[],log=proc.stdout[-600:] if proc.returncode else '')
def worker(job,lock,prompt=None,piece=None,seconds=None):
 """Studio job: with a prompt, find matching set pieces and what they still need; with a piece id, build it in Blender and report the audit."""
 if prompt is not None:
  ids=match(prompt);job.update(status='ready',stage='Matched set pieces',matches=[dict(id=k,title=SET_PIECES[k]['title'],story=SET_PIECES[k]['beats'],limits=SET_PIECES[k]['limits'],missing=missing(k)) for k in ids]);return
 if piece not in SET_PIECES:raise ValueError('Unknown set piece')
 if seconds is not None and not 4<=float(seconds)<=120:raise ValueError('seconds must be 4..120')
 if not lock.acquire(blocking=False):job.update(status='failed',error='Another build is running. Wait for it to finish.');return
 try:
  job['stage']='Building '+SET_PIECES[piece]['title']+' in Blender';r=build(piece,seconds=seconds)
  if r['missing']:job.update(status='failed',error='Missing: '+'; '.join(r['missing']),report=r);return
  if not r['ok']:job.update(status='failed',error='Blender build failed: '+r.get('log','')[-300:],report=r);return
  job.update(status='complete',stage='Built; open the .blend in Blender (press Space to play)',report=r)
 finally:lock.release()
def docs():
 import scene_kit
 lines=['# Set pieces (generated by `python set_pieces.py --write-docs`; do not edit by hand)','',
  'Whole-scene Blender scripts for creature, herd, rider and ship scenes. The dinosaur and ship scripts end with `scene_kit.audit` (skin/skeleton size, action slots, floor contact, subjects in frame) and print `AUDIT ...` lines; an empty audit means clean. Preview with stills or `previs.open_viewer`, never mp4.','']
 for k,v in SET_PIECES.items():
  lines+=['## %s (`%s`)'%(v['title'],k),'','* script: `%s`'%v['script'],'* story: %s'%v['beats'],'* needs: '+'; '.join(v['needs']),'* known limits: %s'%v['limits'],'* prompt keywords: `%s`'%v['keywords'],'']
 lines+=['## Lessons (symptom, cause, rule)','','| id | symptom | cause | rule |','|---|---|---|---|']
 for l in scene_kit.LESSONS:lines.append('| %s | %s | %s | %s |'%(l['id'],l['symptom'],l['cause'],l['rule']))
 return '\n'.join(lines)+'\n'
if __name__=='__main__':
 a=sys.argv[1:]
 if a[:1]==['match']:print(match(' '.join(a[1:])))
 elif a[:1]==['build']:print(json.dumps(build(a[1],seconds=a[2] if len(a)>2 else None),indent=1))
 elif a[:1]==['--write-docs']:(H/'SET_PIECES.md').write_text(docs(),encoding='utf-8');print('wrote SET_PIECES.md')
 else:print(__doc__)
