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
# realistic_clips.CLIP_PREFERENCES). One entry each: (request regex, planner description). sad and listen are left out:
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
}
for _name,(_regex,_what) in GESTURES.items():
 ACTIVITIES[_name]=dict(beats={_name:dict(action=_name)},seated=[],module=None,characters=['lion'],family='clip',planner=None,
  request=_regex,requires=_name,min_duration=2,max_duration=8,test_beats=[('idle',2),(_name,4),('idle',2)],what=_what,check_request=False)
BASE_SIT=('sit_down','sit','sit_talk','stand_up')
def _family(name):return ACTIVITIES[name].get('family','seat')
def beats(family=None):
 """Every beat name -> NLA fields, across activities (optionally one family: seat or clip)."""
 return {name:spec for key,a in ACTIVITIES.items() if family in (None,_family(key)) for name,spec in a['beats'].items()}
def seated_beats():return {n for a in ACTIVITIES.values() for n in a['seated']}
def extra_actions(family=None):return [n for key,a in ACTIVITIES.items() if family in (None,_family(key)) for n in a['beats'] if n not in BASE_SIT]
def planner_text():
 gestures='; '.join(f'{n} ({w})' for n,(r,w) in GESTURES.items())
 return ' '.join(a['planner'] for a in ACTIVITIES.values() if a.get('planner'))+' Standing gestures (2..8 s, in place, lion, full or medium camera, dialogue allowed): '+gestures+'. Use them instead of idle when the user asks for the gesture; do not combine with locomotion inside the beat.'
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
