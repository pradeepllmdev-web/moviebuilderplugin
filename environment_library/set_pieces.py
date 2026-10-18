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
  needs=['assets/quaternius_dinosaurs_download (CC0 "Dinosaur Animated Pack - Dec 2018" by Quaternius, itch.io; ask before downloading)','scenes/dino_assets (python build_leo_assets.py)'],
  beats='lion walks to a nest, picks up an egg, is chased by raptors, leaps onto a triceratops and rides through a swamp, a T-Rex roars, the egg is returned to the apatosaurus and glows (50 s, 9 cameras, sound)',
  limits='the leap is an arc, the rider sits via the Sit clip, no biting or fighting contact'),
 'storm_ship':dict(title='The Storm Ship',script='ship_scene.py',keywords=r'\bship\b|\bsailing\b|\bpirate|sea serpent|kraken|storm at sea|\bmast\b',
  needs=['scenes/ship_assets (python build_ship_assets.py)'],
  beats='lion on a rocking ship climbs the mast, cuts a cloth sail, falls, fights a sea serpent, lightning ends it, calm (60 s, 13 cameras, sound)',
  limits='climbing is a walk cycle on a ladder, hands do not grip, serpent is chunky spheres, rain is thin'),
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
def missing(piece):
 """Human-readable list of what is not there yet (nothing is downloaded automatically)."""
 gone=[]
 if piece=='last_egg':
  if not DINO_DIR.is_dir():gone.append('dinosaur pack: '+SET_PIECES[piece]['needs'][0])
  if not (H/'scenes/dino_assets/leo_run.blend').exists():gone.append('lion clips: python build_leo_assets.py')
 elif piece=='storm_ship':
  if not (H/'scenes/ship_assets/leo_idle.blend').exists():gone.append('lion clips: python build_ship_assets.py')
 elif piece in('horse_herd','rider'):
  if not horse_blend().exists():gone.append('horse pack: '+SET_PIECES['horse_herd']['needs'][0])
  if piece=='rider' and not (H/'scenes/lion_source.blend').exists():gone.append('rider scene: build a lion shot first')
 return gone
def command(piece,out,seconds=None):
 import quick_review
 b=[quick_review.BLENDER,'-b','--disable-autoexec','--python',str(H/SET_PIECES[piece]['script']),'--']
 tail=[str(seconds)] if seconds else []
 if piece=='last_egg':return b+[str(DINO_DIR),str(H/'scenes/dino_assets'),str(out)]+tail
 if piece=='storm_ship':return b+[str(H/'scenes/ship_assets'),str(out)]+tail
 if piece=='horse_herd':return b+[str(horse_blend()),str(out),'64']+tail
 return b+[str(horse_blend()),str(H/'scenes/lion_source.blend'),str(out),str(seconds or 22),'lion']
def build(piece,out=None,seconds=None):
 """Build a set piece in Blender; returns {'ok','out','audit':[...],'missing':[...]} (audit lines come from scene_kit.audit)."""
 gone=missing(piece)
 if gone:return dict(ok=False,missing=gone,audit=[],out=None)
 out=Path(out or H/'scenes'/(piece+'.blend'));out.parent.mkdir(parents=True,exist_ok=True)
 proc=subprocess.run(command(piece,out,seconds),capture_output=True,text=True,errors='ignore',timeout=1800)
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
