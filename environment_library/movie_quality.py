"""Compact production checks; no model buffers are read or returned."""
import json,wave
from pathlib import Path

def check_movie(movie,root):
 errors=[];warnings=[];shots=[]
 for item in movie['shots']:
  d=Path(root)/'scene_jobs'/item['scene_id'];native=json.loads((d/'native.json').read_text());scene=json.loads((d/'scene.json').read_text());contact=json.loads((d/'contact-check.json').read_text())
  if not contact.get('ok'):errors.append(item['title']+': route checks failed')
  camera=d/'camera-check.json'
  if camera.exists():
   framing=json.loads(camera.read_text())
   if framing['head_outside_samples'] or framing['feet_outside_samples']:warnings.append(item['title']+': approximate camera bounds flag cropping; review framing')
  events=scene.get('events',[])
  if any(e['type']=='branch_fall' for e in events):
   report=d/'wind-check.json'
   if not report.exists() or json.loads(report.read_text()).get('branches',0)!=sum(e['type']=='branch_fall' for e in events):errors.append(item['title']+': falling-branch actor is missing')
  manifest=json.loads((d/'performance/manifest.json').read_text())
  speakers={line['speaker'] for line in scene.get('lines',[])}
  for actor in manifest['characters']:
   if actor['name'] in speakers:
    jaws=[c['values'] for c in actor.get('facial_channels',[]) if c['name'] in ['jawOpen','JawOpen','Jaw_Down','V_Open']]
    if not jaws or max(max(v)-min(v) for v in jaws)<.02:errors.append(actor['name']+': speech has no changing jaw curve')
  for grip_report in d.glob('actor_*/grip-check.json'):
   if not json.loads(grip_report.read_text()).get('ok'):errors.append(item['title']+': palm attachment drift exceeds limit')
   warnings.append(item['title']+': palm-anchor test; finger contact and body penetration require visual review')
  for report in d.glob('actor_*/box-contact-check.json'):
   data=json.loads(report.read_text())
   if data['contact_samples'] and not data['ok']:errors.append(item['title']+': box wrist targets exceed contact tolerance')
   prop=d/'box-prop-check.json'
   if not prop.exists() or json.loads(prop.read_text()).get('boxes')!=1:errors.append(item['title']+': independent box prop is missing')
   warnings.append(item['title']+': keyed box contact; inspect skin, fingers and torso clearance; no rigid-body simulation')
  safety_files=list(d.glob('actor_*/motion-safety.json'))
  if not safety_files:warnings.append(item['title']+': legacy scene has no joint-discontinuity report')
  for safety_file in safety_files:
   safety=json.loads(safety_file.read_text())
   if not safety['ok']:errors.append(item['title']+': unsafe bone-control motion')
  if any(actor['name']=='Rowan' for actor in native['characters']):
   eye_report=d/'eye-material-check.json'
   if eye_report.exists():
    if not json.loads(eye_report.read_text()).get('ok'):errors.append(item['title']+': eye material alpha conversion failed')
   else:warnings.append(item['title']+': legacy scene has no eye material report')
  for actor in native['characters']:
   if not actor.get('body_tracks'):errors.append(actor['name']+': missing body tracks')
   if actor.get('facial',{}).get('missing_animated_targets'):errors.append(actor['name']+': missing animated facial targets')
  for line in scene.get('lines',[]):
   with wave.open(line['audio']) as audio:duration=audio.getnframes()/audio.getframerate()
   if line['start']+duration>scene['duration']+.05:errors.append(item['title']+': dialogue exceeds shot')
  lines=scene.get('lines',[])
  for index,line in enumerate(lines):
   for other in lines[index+1:]:
    if line['speaker']!=other['speaker'] and min(line['end'],other['end'])-max(line['start'],other['start'])>.15:warnings.append(item['title']+': dialogue overlaps between speakers; review interruption timing')
  if any(actor['name'] in ['Leo','Amber'] for actor in native['characters']):warnings.append(item['title']+': animal eyelid deformation remains unverified; no automatic blink-quality guarantee')
  if any(g['action'] in ['walk','run','circle','turn'] for actor in scene['actors'] for g in actor['segments']):warnings.append(item['title']+': locomotion needs visual review; foot/joint realism is not certified')
  shots.append({'scene_id':item['scene_id'],'body_tracks':[a['body_tracks'] for a in native['characters']],'contacts':contact.get('ok'),'dialogue_lines':len(scene.get('lines',[]))})
 warnings.append('Camera cropping, pupil contact and facial appeal still require visual review.')
 # Legacy scenes may predate route reports. Never fabricate their coverage.
 if all((Path(root)/'scene_jobs'/s['scene_id']/'routes.json').exists() and (Path(root)/'scene_jobs'/s['scene_id']/'plan.json').exists() for s in movie['shots']):
  from shot_continuity import check
  continuity=check(movie,root)
  if not continuity['ok']:warnings.append('Root position or heading changes across cuts; review continuity before rendering.')
 else:continuity={'ok':None,'scope':'Legacy scenes have no complete route reports'}
 return {'ok':not errors,'errors':errors,'warnings':warnings,'shots':shots,'root_continuity':continuity}
