"""Data-only scene plans backed by the tested lion rig; no generated code execution."""
import asyncio, copy, json, math, os, sys
from pathlib import Path
from character_profiles import PROFILES
import activities
from sit_actions import SIT_ACTIONS
H=Path(__file__).resolve().parent
ACTIONS=['idle','talk','walk','run','circle','dance','jump','hold_ball','turn','box_pickup','box_carry','box_back','box_hold','box_setdown','box_bump','sit_down','sit','sit_talk','stand_up']+activities.extra_actions()
ENVIRONMENTS=['forest','mountains']
SYSTEM='''Return only a JSON scene plan. Schema: {"version":1,"title":"...","character":"lion","environment":"forest","mood":"golden_hour","camera":"full","segments":[{"action":"walk","duration":4,"distance_cm":200,"radius_cm":100,"gap_cm":40,"dialogue":"Hello!"}],"unsupported":[],"notes":[]}.
Installed characters are lion, cat and rowan (a clothed adult human with native eyelid and eye-direction controls). Use the requested character, never silently replace it. Environments forest or mountains; moods golden_hour or morning_fog. Camera full,medium,close,reaction; full required for movement. close/reaction only for idle/talk. Actions idle,talk,walk,run,circle,dance,jump. Dialogue can accompany any action; use exact quoted user dialogue. Durations 2..12 seconds, total <=40, max8 segments. Jump is a 3 second small rock-gap jump, gap20..60cm; at most one, only idle/talk before or after. If user requests other locomotion with jump, report this combination unsupported. Walking speed20..120cm/s, running80..350cm/s. Circle is running one complete circle, radius60..180cm and duration >=4. Straight travel follows +Y, circle starts and ends at current position. Keep all travel and circle paths inside the cleared 6m radius filming area. End with idle/talk if requested. Camera follows root. For two characters add actors:[{character:lion|cat|rowan,position_cm:[-120,0],segments:[...]},{character:cat,position_cm:[120,0],segments:[...]}]. Timelines must have exactly equal duration; use idle beats for the listener. Keep paths separated by 100cm; parallel walks are safest. Use at most one of each character. No simultaneous jumps with two characters. Top-level character/segments can be omitted when actors is present. No driving, climbing, grasping, fights, new characters, real physics, water interaction, weather or detailed custom sets in this builder yet: describe each unsupported request in unsupported, never substitute an unrelated action. If every requested action unsupported, return an idle segment and explicitly list unsupported. Every segment MUST contain action and duration. Head looks are not body actions: use action idle while looking/listening; action talk while speaking. Never return action:null or a segment containing only a look. Example actor: {"character":"cat","position_cm":[120,0],"segments":[{"action":"idle","duration":2,"dialogue":"","look_yaw_deg":-25,"look_pitch_deg":3,"emotion":"alert"},{"action":"talk","duration":4,"dialogue":"Did you hear that?","look_yaw_deg":20,"look_pitch_deg":0,"emotion":"curious"}]}. For stationary two-character dialogue, use look_at:"partner" on idle/talk beats. The builder uses actor positions and eye-height profiles, sets a safe initial body orientation, then turns the head toward the partner. Do not request partner gaze while either actor moves; use manual glances instead. Optional actor facing_yaw_deg overrides initial body direction. Each action can include look_yaw_deg:-35..35 and look_pitch_deg:-8..8 for smoothly held head attention, emotion:neutral|alert|reassuring|curious. Use restrained angles, turn toward a sound then back toward the partner; do not rotate the whole body. Optional scene events:[{type:twig_snap,time:seconds}] creates a short original sound at that exact time. Do not use imported blink morphs. No code, file paths or invented asset IDs. These are stylized animation prototypes, not physics simulations.'''

SYSTEM+=' Shared stationary attention can use look_at:point and look_target_cm:[x,y,z] in scene centimetres, with the same point on both actors. Targets must be in front within a bounded head turn; moving body turns remain unsupported. Optional events type wind_gust with time and duration 0.3..6 adds keyed drifting leaves and original gust audio; it does not simulate full weather or guarantee tree deformation. hold_ball is an isolated stationary lion palm-anchor audition, optionally with dialogue. No pickup, release, walking with props, or finger-grip guarantee; other characters are unsupported for this action.'
SYSTEM+=' A nearby falling branch can use events:[{type:"branch_fall",time:1,duration:1,position_cm:[0,180],length_cm:90}]. This is a keyed wooden branch and timed impact sound, not collision physics. Use a stationary full/medium observation shot, keep its landing site at least 100cm plus half its length from every character, and use a separate shot for escape movement. Body turns and dodging contact remain unsupported. For safe escape use a short walk or run followed by idle, within the cleared area. Preserve listener idle beats and brief dialogue.'
SYSTEM+=' Optional lookdev:soft_portrait adds broad, restrained fill lights that follow the cast. This changes generated scene lighting only; it does not change character geometry, fur or rig capability.'
SYSTEM+=' Box workflow exception: lion supports box_pickup (a 36x26x24cm box from a 70cm stand in front, not the ground), box_back (a short back-step, distance_cm 20..60 at 10..40cm/s), turn (walking arc while holding), box_carry with distance_cm and walking speed20..120cm/s, box_hold, box_setdown onto another 70cm stand, and box_bump (a small keyed contact/recoil, not simulated physics). The pickup stand is directly ahead, so after box_pickup use box_back about 40cm and a walking turn (60..100cm radius) before box_carry; the builder rejects paths that walk through a stand. Use full camera for pickup/back/turn/carry/setdown/bump. Always pick up before carrying, holding or putting down; keep the box across cuts. Only box actions, turn and idle/talk can share this audition. Do not combine running, jumps or other props. Fingers/skin contact still require review.'
SYSTEM+=' Seat workflow exception: lion (alone in the shot) can sit on a bench that is placed under it automatically: sit_down (stand to seated, 2.5..5 s), sit (seated idle, dialogue allowed), sit_talk (seated, gesturing while speaking), stand_up (seated to standing, 2.5..5 s). Order: sit_down, then sit/sit_talk beats, then stand_up; while seated only sit/sit_talk; idle/talk only while standing. Seated state carries across cuts, so a later shot may open with sit or sit_talk and end with stand_up. Do not combine walking, turn, box, jump or props with sitting in the same shot. Full camera for sit_down/stand_up; medium is fine for seated beats.'
SYSTEM+=' Seated dialogue: any line the lion should say while sitting (including after sitting down, such as a remark to the viewer) belongs on a sit or sit_talk beat BEFORE stand_up, with enough seated time for it (about 1 s per 2.5 words). Never put it on idle/talk after stand_up, because the lion is already on its feet then. Give stand_up its own beat without dialogue, and finish any seated line before it. Plan the order sit_down, sit/sit_talk with the line, stand_up, then standing dialogue.'
SYSTEM+=' '+activities.planner_text()
SYSTEM+=' Supported exception to the earlier body-turn restriction: action turn is a small WALKING ARC, not a planted pivot. Supply angle_deg:-120..120 (absolute >=30), radius_cm:60..100, duration:2..6. Use only lion for this audition; full camera. Arc speed must be 20..120cm/s. In a shot containing turn use only walk/run/idle/talk/turn. Heading carries into subsequent walk and subsequent movie shots. Positive heading turns left from +Y; negative turns right toward +X. Use stationary partner gaze in a separate dialogue shot after the turn. Rowan locomotion remains uncalibrated. Do not promise foot-perfect pivoting or physical contact.'

def validate(raw):
 p=copy.deepcopy(raw)
 if not isinstance(p,dict):raise ValueError('Plan must be an object')
 p.setdefault('notes',[]);p.setdefault('unsupported',[])
 if p.get('lookdev','default') not in ['default','soft_portrait']:raise ValueError('Unknown appearance preset')
 # A planner may place a valid installed set ID in the preset field.
 # Preserve the exact saved level; never turn an unknown name into a preset.
 if not p.get('environment_id') and isinstance(p.get('environment'),str) and p['environment'] not in ENVIRONMENTS:
  try:resolve_environment(p['environment'])
  except ValueError:pass
  else:p['environment_id']=p['environment'];p['environment']='forest'
 if 'events' not in p and 'scene_events' in p:p['events']=p['scene_events']
 if p.get('actors'):
  if not isinstance(p['actors'],list) or not 1<=len(p['actors'])<=2:raise ValueError('Use one or two installed characters')
  seen=set();durations=[]
  for i,a in enumerate(p['actors']):
   if a.get('character') in seen:raise ValueError('Use each character at most once')
   seen.add(a.get('character'))
   single={k:v for k,v in p.items() if k!='actors'};single.update(character=a.get('character'),segments=a.get('segments'),position_cm=a.get('position_cm',[-120 if i==0 else 120,0]),_member=True)
   checked=validate(single);a['segments']=checked['segments'];durations.append(sum(g['duration'] for g in a['segments']))
   pos=a.setdefault('position_cm',[-120 if i==0 else 120,0])
   if not isinstance(pos,list) or len(pos)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>600 for v in pos):raise ValueError('Actor placement must be within 6 metres; complete route is checked against the cleared area')
   if 'facing_yaw_deg' in a and (isinstance(a['facing_yaw_deg'],bool) or not isinstance(a['facing_yaw_deg'],(int,float)) or not math.isfinite(a['facing_yaw_deg']) or abs(a['facing_yaw_deg'])>180):raise ValueError('Invalid body facing angle')
   if len(p['actors'])>1 and any(g['action']=='jump' for g in a['segments']):raise ValueError('Review rock jumps with one actor first')
  if max(durations)-min(durations)>.001:raise ValueError('Actor timelines must have equal duration; add idle/listen beats')
  from scene_gaze import conversation_context
  for a in p['actors']:conversation_context(p,a)
  import contact_actions
  heights={k:v['height_cm'] for k,v in PROFILES.items()}
  for i in range(len(p['actors'])):contact_actions.pair_inputs(p['actors'],i,heights)
  p['character']=p['actors'][0]['character'];p['segments']=p['actors'][0]['segments']
  if any(g['action'] in ['walk','run','circle','jump','turn','box_pickup','box_carry','box_setdown','box_bump'] for a in p['actors'] for g in a['segments']):p['camera']='full'
  return p
 if p.get('version')!=1 or p.get('character') not in PROFILES:raise ValueError('Choose an installed character profile')
 if p.get('environment_id'):
  resolve_environment(p['environment_id'])
 if p.get('environment') not in ENVIRONMENTS or p.get('mood') not in ['golden_hour','morning_fog']:raise ValueError('Unsupported environment or lighting')
 if p.get('focus','both') not in list(PROFILES)+['both']:raise ValueError('Invalid camera focus')
 if p.get('camera') not in ['full','medium','close','reaction']:raise ValueError('Choose full or medium camera')
 if not isinstance(p.get('title'),str) or len(p['title'])>160:raise ValueError('Invalid title')
 for key in ['unsupported','notes']:
  if not isinstance(p.get(key),list) or len(p[key])>20 or any(not isinstance(x,str) or len(x)>500 for x in p[key]):raise ValueError('Invalid '+key)
 segs=p.get('segments')
 if not isinstance(segs,list) or not 1<=len(segs)<=8:raise ValueError('Use 1..8 actions')
 total=0;distance=0
 def number(v,lo,hi):
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Action parameter outside supported range')
  return float(v)
 for g in segs:
  if g.get('action') not in ACTIONS:raise ValueError('Unsupported action: '+str(g.get('action')))
  g['duration']=number(g.get('duration'),2,12);total+=g['duration']
  if not isinstance(g.get('dialogue',''),str) or len(g.get('dialogue',''))>220:raise ValueError('Dialogue must be <=220 characters per action')
  g.setdefault('dialogue','')
  for key,lo,hi in [('look_yaw_deg',-35,35),('look_pitch_deg',-8,8)]:g[key]=number(g.get(key,0),lo,hi)
  if g.get('emotion','neutral') not in ['neutral','alert','reassuring','curious']:raise ValueError('Unsupported expression')
  g.setdefault('emotion','neutral')
  if g.get('look_at','manual') not in ['manual','forward','partner','point']:raise ValueError('Invalid gaze target')
  if g.get('look_at')=='point':
   target=g.get('look_target_cm')
   if not isinstance(target,list) or len(target)!=3:raise ValueError('Point gaze needs look_target_cm [x,y,z]')
   for coordinate in target:number(coordinate,-50000,50000)

  if g['action'] in ['walk','run','box_carry','carry_walk','climb_stairs']:
   g['distance_cm']=number(g.get('distance_cm',g['duration']*(60 if g['action'] in ['walk','box_carry','carry_walk','climb_stairs'] else 160)),0,1200)
   speed=g['distance_cm']/g['duration'];lo,hi=(20,120) if g['action'] in ['walk','box_carry','carry_walk','climb_stairs'] else (80,350)
   if not lo<=speed<=hi:raise ValueError('Locomotion speed outside supported range')
   distance+=g['distance_cm']
  if g['action']=='box_back':
   g['distance_cm']=number(g.get('distance_cm',40),20,60)
   if not 10<=g['distance_cm']/g['duration']<=40:raise ValueError('Box back-step needs 10..40 cm/s')
   distance+=g['distance_cm']
  if g['action']=='circle':
   g['radius_cm']=number(g.get('radius_cm',100),60,180)
   if g['duration']<4:raise ValueError('Circle needs at least 4 seconds')
  if g['action']=='turn':
   angle=number(g.get('angle_deg'),-120,120);radius=number(g.setdefault('radius_cm',80),60,100)
   if abs(angle)<30 or g['duration']>6 or not 20<=abs(math.radians(angle))*radius/g['duration']<=120:raise ValueError('Walking turn needs 30..120 degrees, 2..6 seconds and speed 20..120 cm/s')
   if p['character']!='lion':raise ValueError('Walking turns currently require the calibrated lion')
   distance+=abs(math.radians(angle))*radius
  if g['action']=='jump':
   g['gap_cm']=number(g.get('gap_cm',40),20,60);g['duration']=3;distance+=70+g['gap_cm']
  if g['action'] in ['walk','run','circle','jump','turn','box_pickup','box_carry','box_back','box_setdown','box_bump','carry_walk','climb_stairs']:p['camera']='full'
 boxed=any(g['action'].startswith('box_') for g in segs)
 if any(g['action']=='turn' for g in segs) and not boxed and any(g['action'] not in ['walk','run','idle','talk','turn'] for g in segs):raise ValueError('Keep walking turns separate from circle/jump/dance/prop auditions')
 if boxed:
  if p['character']!='lion' or any(g['action'] not in ['idle','talk','turn','box_pickup','box_carry','box_back','box_hold','box_setdown','box_bump'] for g in segs):raise ValueError('Box workflow currently needs the lion and separate box/turn/idle/talk actions only')
  # Validate the shared path now: the carrier must never walk through a stand.
  from box_timeline import build as box_path
  from character_profiles import profile as character_profile
  first=next(g['action'] for g in segs if g['action'].startswith('box_'))
  box_path(segs,[0,0],None if first=='box_pickup' else {'id':'TrailCrate','phase':'held','location_cm':[0,0,0]},24,p.get('facing_yaw_deg',0),character_profile('lion')['box'])
 if any(g['action'] in SIT_ACTIONS for g in segs):
  if p['character']!='lion' or any(g['action'] not in ['idle','talk']+sorted(SIT_ACTIONS) for g in segs):raise ValueError('Seat workflow currently needs the lion with idle/talk and sit actions only')
  from sit_actions import validate as validate_sitting
  validate_sitting(segs)
  for g in segs:
   activities.validate_beat(g)
   if g['action'] in ['sit_down','stand_up'] and g['duration']<2.5:raise ValueError(g['action']+' needs at least 2.5 seconds')
   if g['action'] in ['sit_down','stand_up']:p['camera']='full'
 import contact_actions
 if any(g['action'] in contact_actions.CONTACT for g in segs) and not p.pop('_member',False):raise ValueError('Handshake and hug need two actors with the same beat at the same time, 25..72 cm apart')
 p.pop('_member',None)
 jumps=[i for i,g in enumerate(segs) if g['action']=='jump']
 if any(g.get('look_at')=='point' for g in segs) and any(g['action'] not in ['idle','talk','hold_ball'] for g in segs):raise ValueError('Point gaze currently supports stationary beats only; use manual glances while moving')
 if any(g['action']=='hold_ball' for g in segs) and (p['character']!='lion' or any(g['action']!='hold_ball' for g in segs)):raise ValueError('hold_ball is an isolated stationary lion test; dialogue is allowed, other actions and characters need separate calibration')
 if len(jumps)>1 or (jumps and any(g['action'] not in ['idle','talk'] for g in segs[:jumps[0]]+segs[jumps[0]+1:])):raise ValueError('Rock-gap jump currently needs its own scene with only idle/talk before or after; build locomotion separately')
 extent=distance+max([2*g.get('radius_cm',0) for g in segs if g['action']=='circle'] or [0])
 if sum(g['duration'] for g in segs)>40 or extent>600:raise ValueError('Keep scene <=40 seconds and route inside the cleared 6 metre filming area')
 events=p.setdefault('events',[])
 if not isinstance(events,list) or len(events)>8:raise ValueError('Use at most eight sound events')
 for event in events:
  if event.get('type') not in ['twig_snap','wind_gust','branch_fall']:raise ValueError('Unsupported sound event')
  if event['type']=='wind_gust':number(event.setdefault('duration',2),.3,6)
  if event['type']=='branch_fall':
   duration=number(event.setdefault('duration',1),.4,2)
   pos=event.setdefault('position_cm',[0,180]);length=number(event.setdefault('length_cm',90),40,140)
   if not isinstance(pos,list) or len(pos)!=2:raise ValueError('Branch landing position requires [x,y]')
   for coordinate in pos:number(coordinate,-400,400)
   if event.get('time',0)+duration>total:raise ValueError('Branch fall must finish inside its shot')
   if any(g['action'] not in ['idle','talk'] for g in segs):raise ValueError('Review falling branches in stationary shots before escape movement')
   for actor in p.get('actors') or [{'position_cm':p.get('position_cm',[0,0])}]:
    if math.dist(pos,actor.get('position_cm',[0,0]))<100+length/2:raise ValueError('Branch landing site is too close to a character')
  number(event.get('time'),0,sum(g['duration'] for g in segs)-.1)
 return p

def require_requested_controls(plan,prompt):
 import re
 shots=plan.get('shots',[plan])
 # Explicit named presets are deterministic controls, not optional AI suggestions.
 for name in activities.unsupported_requests(prompt):
  if not plan.get('unsupported') and not any(s.get('unsupported') for s in shots):raise ValueError('Requested '+name+' has no clip for the lion; describe it in unsupported and keep a plain idle or talk beat.')
 if re.search(r'\bsoft_portrait\b|\bsoft portrait lighting\b',prompt,re.I):
  for shot in shots:shot['lookdev']='soft_portrait'
 if re.search(r'look(?:s|ing)?\s+(?:at|toward|towards)\s+each other|face\s+each other|\beye contact\b',prompt,re.I):
  actors=[a for s in shots for a in s.get('actors',[])]
  if not actors or any(not any(g.get('look_at')=='partner' for g in a['segments']) for a in actors):raise ValueError('Requested partner-facing attention is missing. Use look_at partner on stationary idle/talk beats for both actors.')
 segments=[g for s in shots for a in (s.get('actors') or [{'segments':s.get('segments',[])}]) for g in a['segments']]
 for pattern,action in [(r'\bpick(?:s|ing)? up\b.*\bbox\b','box_pickup'),(r'\bcarry(?:ing)?\b.*\bbox\b','box_carry'),(r'\bput(?:s|ting)?\b.*\bbox\b.*\bdown\b|\bset(?:s|ting)?\b.*\bbox\b.*\bdown\b','box_setdown'),(r'\b(?:sits?|sitting|sat)\s+(?:down|on)\b|\btakes? a seat\b','sit_down'),(r'\bstand(?:s|ing)?\s+(?:back\s+)?up\b|\bgets?\s+(?:back\s+)?up\b','stand_up')]+[c for c in activities.request_checks() if c[1]!='sit_down']:
  if re.search(pattern,prompt,re.I) and not any(g['action']==action for g in segments) and not plan.get('unsupported'):raise ValueError('Requested '+action+' is missing; use the calibrated '+('seat' if action in ['sit_down','stand_up','drink'] else 'gesture' if action in activities.GESTURES else 'box')+' workflow or report unsupported handling explicitly.')
 if re.search(r'\bstepping turn\b|\bwalking turn\b|\bbody turn\b|\bturn around\b',prompt,re.I):
  if not any(g['action']=='turn' for g in segments) and not plan.get('unsupported'):raise ValueError('Requested body turn is missing. Use a bounded lion walking-arc turn, or explicitly report the unsupported pivot.')
 if re.search(r'\btwig\b.*\bsnaps?\b|\bsnaps?\b.*\btwig\b',prompt,re.I|re.S):
  if not any(e.get('type')=='twig_snap' for s in shots for e in s.get('events',[])):raise ValueError('Requested twig snap is missing. Add a scene events entry with type twig_snap and the requested time within that shot.')
 if re.search(r'\bwind gust\b|\bsudden gust\b|\bgust of wind\b',prompt,re.I):
  if not any(e.get('type')=='wind_gust' for shot in shots for e in shot.get('events',[])):raise ValueError('Requested wind gust is missing; add a wind_gust event with local time and duration.')
 if re.search(r'\bfalling branch\b|\bbranch falls\b',prompt,re.I):
  if not any(e.get('type')=='branch_fall' for shot in shots for e in shot.get('events',[])):raise ValueError('Requested falling branch is missing; add a safe stationary branch_fall cue or explicitly mark it unsupported.')
 if re.search(r'\bturns?\b.*\bhead\b|\blooks? back\b|\bhead attention\b',prompt,re.I|re.S):
  if not any(g.get('look_at') in ['partner','point'] or abs(g.get('look_yaw_deg',0))>2 or abs(g.get('look_pitch_deg',0))>2 for g in segments):raise ValueError('Requested head attention is missing. Give the reacting actor nonzero look_yaw_deg and look_pitch_deg on the appropriate beats, within the supported bounds.')
 return plan

def generate(prompt):
 if not isinstance(prompt,str) or not 5<=len(prompt.strip())<=4000:raise ValueError('Prompt must contain 5..4000 characters')
 sys.path.insert(0,str(H.parent.parent/'3dobjectnew/server'))
 import scene_ai
 scene_ai.load_env_file()
 async def call():
  raw=await scene_ai._call_openai_json(SYSTEM+'\nSaved environment IDs: '+json.dumps(environment_options())+'\nOptional environment_id must exactly match a supplied ID; omit to use procedural preset.',prompt,os.environ.get('OPENAI_API_KEY',''),None)
  import uuid
  reports=H/'planner_reports';reports.mkdir(exist_ok=True);(reports/(uuid.uuid4().hex+'.json')).write_text(json.dumps(raw))
  try:
   from scene_director import complete_controls
   return await complete_controls(validate(raw),prompt,scene_ai,validate,require_requested_controls)
  except (ValueError,KeyError,TypeError) as e:
   return require_requested_controls(validate(await scene_ai._call_openai_json(SYSTEM,prompt+'\nRepair plan: '+json.dumps(raw)+'\nError: '+str(e),os.environ.get('OPENAI_API_KEY',''),None)),prompt)
 return asyncio.run(call())


def environment_options():
 result=[]
 for f in (H/'demos').glob('*/build-result.json'):
  try:
   r=json.loads(f.read_text());result.append({'id':f.parent.name,'category':r.get('biome','set')})
  except (ValueError,OSError):continue
 return result[-40:]

def resolve_environment(key):
 import re
 if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,100}',key):raise ValueError('Invalid environment ID')
 p=H/'demos'/key/'build-result.json'
 if not p.is_file():raise ValueError('Choose an existing environment ID from the catalogue')
 level=json.loads(p.read_text())['level']
 if not isinstance(level,str) or not level.startswith('/Game/EnvironmentDemos/'):raise ValueError('Invalid saved environment path')
 return level
