"""Activity templates: one declaration per activity, shared by the planner, the builder and quick_review.

An activity names its beats (clip, base motion), whether it is seated, what the planner may be told, how to
recognise a request for it and a short test shot. Geometry that depends on the character is never listed here:
it is measured from the evaluated body (body_measures.py) and solved in the activity's module, whose
feasibility(measures) answers in milliseconds, before any Blender build, whether this body can do it."""
ACTIVITIES={
 'sit':dict(
  beats={'sit_down':dict(action='sit_down',clip='Stand_To_Sit',clip_start=2.),'sit':dict(action='sit',clip='Sit_Idle'),
   'sit_talk':dict(action='sit',clip='Mixamo_Sitting_Talking'),'stand_up':dict(action='stand_up',clip='Sit_To_Stand_M')},
  seated=['sit','sit_talk'],module=None,characters=['lion'],planner=None,
  request=r'\b(?:sits?|sitting|sat)\s+(?:down|on)\b|\btakes? a seat\b',requires='sit_down',
  test_beats=[('idle',2),('sit_down',3),('sit',3),('stand_up',3)]),
 'drink':dict(
  beats={'drink':dict(action='sit',clip='Sit_Idle')},seated=['drink'],module='drink_actions',characters=['lion'],
  planner="Drinking: action drink (3.5..8 s, no dialogue) happens seated, between sit_down and stand_up, at a low table with a cup that is placed automatically. The lion keeps the cup on the table, rests a hand beside it, leans in and dips its muzzle to the rim, then sits back. Never combine with walking, props or other actions inside the beat; a seated line before or after it goes on a sit or sit_talk beat.",
  request=r'\b(?:drinks?|drinking|sips?|sipping)\b.*\b(?:cup|mug|glass)\b|\b(?:cup|mug|glass)\b.*\b(?:drinks?|drinking|sips?|sipping)\b',requires='drink',
  min_duration=3.5,max_duration=8,
  test_beats=[('idle',2),('sit_down',3),('drink',6),('stand_up',3)]),
}
# Standing, in-place gestures played straight from the shared clip library (name = clip preference key in
# realistic_clips.CLIP_PREFERENCES). One entry each: (request regex, planner description). sad, listen, point and cry are left out:
# the lion has no clip for them (they fall back to Idle_3), so idle with look_at covers listening.
GESTURES={
 'wave':(r'\bwav(?:es|ing|e)\b','waves hello with one hand'),
 'nod':(r'\bnods?\b|\bnodding\b','nods in agreement'),
 'shrug':(r'\bshrugs?\b|\bshrugging\b','shrugs'),
 'think':(r'\bthinks?\b|\bthinking\b|\bponders?\b','stands thinking, a hand to the chin'),
 'bow':(r'\bbows?\b|\bbowing\b','takes a formal bow'),
 'celebrate':(r'\bcelebrat\w+|\bcheers?\b|\bcheering\b','cheers or celebrates'),
 'laugh':(r'\blaugh\w*','laughs'),
 'hands_on_hips':(r'\bhands on (?:his |its |their )?hips\b','stands with hands on hips'),
 'look_around':(r'\blooks? around\b|\bscans? the\b','looks around'),
 'pick_up':(r'\bpicks? up\b|\bbends? down\b','bends down to pick something up'),
 'open_door':(r'\bopens? the door\b','opens a door'),
 'push':(r'\bpush(?:es|ing)?\b','pushes forward'),
 'kick':(r'\bkicks?\b','kicks'),
 'punch':(r'\bpunch(?:es)?\b|\bjabs?\b','throws a punch'),
 'dodge':(r'\bdodg\w+','dodges'),
 'startle':(r'\bstartl\w+|\bflinch\w*|\bjumps? back\b','is startled'),
 'block':(r'\bblocks?\b','blocks with its arms'),
 'hit_react':(r'\bgets? hit\b|\bis hit\b','reacts to being hit'),
 'fall_back':(r'\bfalls? back\b|\bfalls? over\b','falls backward'),
 'get_up':(r'\bgets? up\b|\bgetting up\b','gets up from the ground'),
 'kneel':(r'\bkneel\w*','kneels'),
 'crawl':(r'\bcrawl\w*','crawls'),
 'lie_down':(r'\blies? down\b','lies down'),
 'sleep':(r'\bsleeps?\b|\basleep\b','sleeps'),
 'headache':(r'\bheadache\b','holds its head in pain'),
 'stunned':(r'\bstunned\b|\bdumbfounded\b','stands stunned'),
 'argue':(r'\barg(?:ues?|uing)\b','argues angrily'),
}
for _name,(_regex,_what) in GESTURES.items():
 ACTIVITIES[_name]=dict(beats={_name:dict(action=_name)},seated=[],module=None,characters=['lion','cat','rowan'],family='clip',planner=None,
  request=_regex,requires=_name,min_duration=2,max_duration=8,test_beats=[('idle',2),(_name,4),('idle',2)],what=_what,check_request=False)
# Observed gaps: motions people ask for that the lion has no clip for. The planner reports them in `unsupported`
# instead of substituting something else, and require_requested_controls enforces it.
UNSUPPORTED={
 'sad':(r'\b(?:looks?|feels?|stands?|sits?|is|are) sad\b|\bsulks?\b','no sad clip (falls back to idle); use a plain idle or talk beat and list it as unsupported'),
 'point':(r'\bpoints? (?:at|to|ahead|toward|towards|forward|out)\b|\bpointing\b','no pointing clip for the lion'),
 'cry':(r'\bcr(?:ies|ying)\b|\bstarts? to cry\b|\bweeps?\b','no crying clip for the lion'),
}
# Things that pass the Blender checks but have not been judged on screen; shown in capabilities, never enforced.
CAVEATS={
 'laugh':'uses the shared agree-gesture clip, so it reads like nodding',
 'phone':'phone is a plain box in the hand; no Unreal prop yet','pick_up':'cup on a crate; props are Blender-only so far','open_door':'door is a Blender proxy; no Unreal prop yet','carry_walk':'cup is a Blender proxy; no Unreal prop yet','climb_stairs':'root rises with the steps but feet are not IK-planted; no Unreal stairs yet','handshake':'two actors; Blender only, hands meet at the midpoint','hug':'two actors; hands on the partner sides, not a full wrap; Blender only',
 'fall_back':'ends low on the ground; review in Unreal','get_up':'starts low on the ground; review in Unreal','lie_down':'ends on the ground; review in Unreal',
 'sleep':'lying pose; review in Unreal','crawl':'low body; review in Unreal','kneel':'low body; review in Unreal',
 'drink':'cup stays on a low table, hand rests beside it (the lion cannot lift a cup to its muzzle)',
}
ACTIVITIES['phone']=dict(beats={'phone':dict(action='phone')},seated=[],module='phone_actions',characters=['lion','cat','rowan'],family='clip',planner=None,request=r'\bphone\b|\bphon(?:es|ing)\b|\bmakes? a call\b',requires='phone',min_duration=3,max_duration=8,test_beats=[('idle',2),('phone',5),('idle',2)],what='talks on a phone held to its ear',check_request=False)
for _name,_rx,_what,_lo,_hi,_pair in (
 ('carry_walk',r'\bcarr(?:ies|ying) (?:a |the |his |its )?(?:cup|mug|bag|basket)\b|\bwalks? (?:while )?carrying\b','walks while carrying a cup in one hand (give distance_cm like walk)',3,12,False),
 ('climb_stairs',r'\bstairs?\b|\bsteps? up\b|\bclimbs? (?:up )?(?:the )?steps?\b','climbs three steps while walking forward (give distance_cm of at least 160)',4,12,False),
 ('handshake',r'\bshak(?:es|ing) hands?\b|\bhandshake\b','shakes hands with the other actor (two actors standing close (about 50..72 cm apart for lion and Rowan; the validator reports the exact range), same beat for both)',3,8,True),
 ('hug',r'\bhugs?\b|\bhugging\b|\bembrac(?:es|ing)\b','hugs the other actor (two actors standing close (about 51..57 cm apart for lion and Rowan; the validator reports the exact range), same beat for both)',3,8,True),
):
 ACTIVITIES[_name]=dict(beats={_name:dict(action=_name)},seated=[],module='contact_actions',characters=['lion','cat','rowan'],family='clip',planner=None,
  request=_rx,requires=_name,min_duration=_lo,max_duration=_hi,test_beats=[('idle',2),(_name,5 if not _pair else 5),('idle',2)],what=_what,check_request=False,pair=_pair)
BASE_SIT=('sit_down','sit','sit_talk','stand_up')
def summary():
 """Machine-readable list for the studio capabilities endpoint, so every client (3dobjectnew, the editor) sees the same set."""
 return {'activities':{k:dict(family=_family(k),beats=list(a['beats']),seated=bool(a['seated']),min_s=a.get('min_duration'),max_s=a.get('max_duration'),caveat=CAVEATS.get(k)) for k,a in ACTIVITIES.items()},
  'unsupported':{k:why for k,(rx,why) in UNSUPPORTED.items()}}
def unsupported_requests(prompt):
 """Names of requested motions the lion cannot do, from the prompt text."""
 import re
 return [k for k,(rx,why) in UNSUPPORTED.items() if re.search(rx,prompt,re.I)]
def _family(name):return ACTIVITIES[name].get('family','seat')
def beats(family=None):
 """Every beat name -> NLA fields, across activities (optionally one family: seat or clip)."""
 return {name:spec for key,a in ACTIVITIES.items() if family in (None,_family(key)) for name,spec in a['beats'].items()}
def seated_beats():return {n for a in ACTIVITIES.values() for n in a['seated']}
def extra_actions(family=None):return [n for key,a in ACTIVITIES.items() if family in (None,_family(key)) for n in a['beats'] if n not in BASE_SIT]
def planner_text():
 gestures='; '.join(f"{k} ({a['what']})" for k,a in ACTIVITIES.items() if a.get('family')=='clip')
 missing='; '.join(f'{k} ({why.split(";")[0]})' for k,(rx,why) in UNSUPPORTED.items())
 return ' '.join(a['planner'] for a in ACTIVITIES.values() if a.get('planner'))+' The lion has no clip for: '+missing+'. Never substitute another motion for these: describe the request in unsupported and keep a plain idle/talk beat. A character who only listens uses idle with look_at partner. Standing gestures (2..8 s, in place, lion, full or medium camera, dialogue allowed): '+gestures+'. Use them instead of idle when the user asks for the gesture; do not combine with locomotion inside the beat.'
def request_checks():return [(a['request'],a['requires']) for a in ACTIVITIES.values()]
def validate_beat(beat):
 """Duration limits an activity declares for its own beats."""
 for a in ACTIVITIES.values():
  if beat['action'] in a['beats'] and a.get('min_duration') and not a['min_duration']<=beat['duration']<=a.get('max_duration',99):
   raise ValueError(f"{beat['action']} needs {a['min_duration']}..{a.get('max_duration',99)} seconds")
def feasibility(name,measures):
 """Instant verdict from cached body measurements; activities without a module have nothing to solve."""
 import importlib
 module=ACTIVITIES[name]['module']
 return importlib.import_module(module).feasibility(measures) if module else {'ok':True,'note':'no body-dependent solve'}
