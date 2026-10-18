"""Automatic story checks: what a director would flag before a previs is built (pure Python, instant).

lint(plan, direction) -> list of findings {shot, rule, severity, message}. Run by `quick_review.py previs` before building
(`--strict` stops on errors). Every rule exists because a viewer noticed the problem in a built previs:

  continuity.place_change   cut to another place with no travel or establishing shot ("bridge suddenly shown")
  continuity.actor_missing  an actor leaves a scene and returns later in the same place ("human missing")
  continuity.prop_popping   scenery used by one shot (table, steps, bench) is absent from other shots at the same place
  continuity.prop_flicker   story props that exist only in some shots of a place (paw prints appear/disappear)
  staging.facing_camera     both actors of an interaction face the camera instead of each other or the side
  staging.contact_context   a handshake/hug/laugh/cheer cut in without a shot of the actors approaching or meeting
  staging.service           sit/drink shots with no one serving the drink, or no reason for the table
  set.door_needs_wall       a door beat with no wall, room or building behind it
  set.light_needs_window    dialogue about a light/lamp/fire with no lit window or lamp in the set
  dialogue.needs_object     a line names an object (cub, cup, door, light) that is not in the set or is not looked at
  dialogue.needs_building   a line about the cafe/shop/hut with no such building in the set

Rules read the plan and the DIRECTION dict (sets, shot places and cameras, story props); they never need Blender."""
import math,re
SCENERY_BY_ACTION={'sit_down':'bench','sit':'bench','sit_talk':'bench','drink':'table','stand_up':'bench','climb_stairs':'stairs','pick_up':'table','open_door':'door'}
KEYWORDS=[   # (regex over dialogue, needs, message)
 (r'\blight|\blamp|\bfire\b|\blantern','lit_window','mentions a light but the set has no lit window or lamp'),
 (r'\bcub\b|little one','cub','mentions the cub but there is no cub prop in the shots'),
 (r'\bcaf[eé]\b|\bshop\b|open for business','building','mentions a cafe/shop but no such building is in the place'),
 (r'\bdoor\b|\bhut\b|inside|come in','door','mentions a door/room but the shot has no door and walls'),
]
def _actors(shot):return shot.get('actors') or [dict(character=shot.get('character'),position_cm=[0,0],segments=shot.get('segments',[]))]
def _place(direction,title):return tuple((direction or {}).get('shots',{}).get(title,{}).get('origin_cm',[0,0]))
def _camera_pos(direction,title,shot):
 cam=((direction or {}).get('shots',{}).get(title,{}).get('camera'))
 return cam['pos_cm'] if cam else None
def finding(shot_index,rule,severity,message):return dict(shot=shot_index,rule=rule,severity=severity,message=message)
def lint(plan,direction=None):
 shots=plan['shots'];out=[];titles=[s.get('title','') for s in shots];places=[_place(direction,t) for t in titles]
 props=(direction or {}).get('props',[]);set_kinds={tuple(s['origin_cm']):s['kind'] for s in (direction or {}).get('sets',[])}
 actions=[{g['action'] for a in _actors(s) for g in a['segments']} for s in shots]
 characters=[{a['character'] for a in _actors(s)} for s in shots]
 # continuity.place_change: moving to another place needs a walk that ends the previous shot or a wide establishing shot first
 for k in range(1,len(shots)):
  if places[k]!=places[k-1]:
   travelled=any(a in actions[k-1] for a in ('walk','carry_walk','climb_stairs','run'))
   establishing=shots[k].get('camera','full')=='full' and not (actions[k]&{'handshake','hug','sit_down','drink'})
   if not (travelled and establishing):out.append(finding(k+1,'continuity.place_change','warning',f"cut from the {set_kinds.get(places[k-1],'previous place')} to the {set_kinds.get(places[k],'next place')} without travel into it and a wide establishing shot; the viewer cannot place the new setting"))
 # continuity.actor_missing
 for k in range(1,len(shots)-1):
  for who in characters[k-1]&characters[k+1]:
   if who not in characters[k] and places[k-1]==places[k]==places[k+1]:out.append(finding(k+1,'continuity.actor_missing','warning',f'{who} is in the shots before and after but missing here (same place)'))
 # continuity.prop_popping: scenery needed by some shots of a place but not shown in the others
 by_place={}
 for k,p in enumerate(places):by_place.setdefault(p,[]).append(k)
 for place,ks in by_place.items():
  needed={}
  for k in ks:
   for a in actions[k]:
    if a in SCENERY_BY_ACTION:needed.setdefault(SCENERY_BY_ACTION[a],[]).append(k)
  for item,users in needed.items():
   others=[k for k in ks if k not in users]
   if others:out.append(finding(others[0]+1,'continuity.prop_popping','info',f"the {item} used in shot {users[0]+1} is kept in this place for every shot automatically; keep the other shots' actors away from it (use offset_cm for the shot that uses it)"))
 # continuity.prop_flicker: story props limited to some shots of a place
 for p in props:
  only=p.get('only_in')
  if only:
   idx=[titles.index(t) for t in only if t in titles]
   if idx:
    place=places[idx[0]];all_here=[k for k in by_place.get(place,[])]
    missing=[k for k in all_here if k not in idx and min(idx)<k<max(idx)] or ([k for k in all_here if k not in idx] if p.get('name') not in ('Cub','CubHead','CubEar') else [])
    if missing and p.get('name','Prop') not in [f.get('prop') for f in out]:out.append(dict(finding(missing[0]+1,'continuity.prop_flicker','warning',f"'{p.get('name','Prop')}' exists only in shots {', '.join(str(i+1) for i in idx)} of this place and vanishes in others"),prop=p.get('name','Prop')))
 # staging.facing_camera: both actors of an interaction look into the lens
 for k,s in enumerate(shots):
  a=_actors(s);cam=_camera_pos(direction,titles[k],s)
  if len(a)==2 and cam:
   toward=[]   # cosine between each actor's facing and the direction to the camera
   for actor in a:
    x,y=actor.get('position_cm',[0,0]);yaw=math.radians(actor.get('facing_yaw_deg',0));f=(-math.sin(yaw),math.cos(yaw));ox,oy=_place(direction,titles[k]);cx,cy=cam[0]-ox-x,cam[1]-oy-y;n=math.hypot(cx,cy) or 1
    toward.append((f[0]*cx+f[1]*cy)/n)
   interacting=actions[k]&{'handshake','hug','laugh','celebrate','wave','nod','talk','think'}
   if all(t>.7 for t in toward) and interacting:out.append(finding(k+1,'staging.facing_camera','warning','both actors face the camera, not each other or a shared point; turn them toward each other and put the camera at three quarters or side on'))
 # staging.contact_context
 for k,s in enumerate(shots):
  contact=actions[k]&{'handshake','hug'}
  if contact and k>0 and not (actions[k-1]&{'walk','wave','handshake','hug','celebrate','laugh','talk'}):out.append(finding(k+1,'staging.contact_context','warning',f"{'/'.join(sorted(contact))} starts with no shot of the actors approaching each other; it cuts in out of context"))
 # staging.service
 for k,s in enumerate(shots):
  if 'drink' in actions[k] and len(characters[k])==1 and any(len(c)==2 for c in characters):out.append(finding(k+1,'staging.service','info','a drink with only the drinker in frame: if someone served it, show them (and the table) in the same place before and after'))
 # set.door_needs_wall
 for k,s in enumerate(shots):
  if 'open_door' in actions[k]:
   out.append(finding(k+1,'set.door_auto_wall','info','the previs builds a wall, a room, a roof and a lit window around this door automatically (permanent for the place)'))
 # dialogue rules
 for k,s in enumerate(shots):
  for actor in _actors(s):
   for g in actor['segments']:
    text=g.get('dialogue','')
    if not text:continue
    for rx,need,message in KEYWORDS:
     if not re.search(rx,text,re.I):continue
     names={p.get('name','') for p in props};kind=set_kinds.get(places[k],'')
     if need=='cub' and not any(n.startswith('Cub') for n in names):out.append(finding(k+1,'dialogue.needs_object','error',f"'{text}' {message}"))
     elif need=='cub' and not any(x.get('look_at')=='point' or x.get('look_pitch_deg',0)<0 for x in actor['segments']):out.append(finding(k+1,'dialogue.needs_object','warning',f"'{text}': the speaker does not look at the cub (add a downward look)"))
     if need=='lit_window' and 'open_door' not in actions[k] and not any(n.startswith(('Window','Lamp','Lantern','Fire')) for n in names):out.append(finding(k+1,'set.light_needs_window','error',f"'{text}' {message}"))
     if need=='building' and kind not in ('cafe','village'):out.append(finding(k+1,'dialogue.needs_building','warning',f"'{text}' {message}"))
     if need=='door' and 'open_door' not in actions[k] and not any(n.startswith(('Wall','Hut','DoorWall')) for n in names) and 'hut' in text.lower():out.append(finding(k+1,'dialogue.needs_building','warning',f"'{text}' {message}"))
 # purpose.gesture: a gesture with neither a line nor a stated purpose is a hand or leg movement for nothing
 GESTURE_NEEDS_PURPOSE={'wave','nod','shrug','think','hands_on_hips','look_around','laugh','celebrate','bow','headache','argue'}
 for k,s in enumerate(shots):
  for actor in _actors(s):
   for g in actor['segments']:
    if g['action'] in GESTURE_NEEDS_PURPOSE and not g.get('dialogue') and not g.get('purpose'):out.append(finding(k+1,'purpose.gesture','warning',f"{actor['character']} {g['action']}s with no line and no stated purpose; give the beat dialogue, or purpose='...' if it answers something on screen, or use idle (held still)"))
 import story_layout
 out+=story_layout.layout(plan,direction)['findings']   # blocking and facing, from the planned layout
 unique=[];seen=set()
 for f in out:
  key=(f['shot'],f['rule'],f['message'])
  if key not in seen:seen.add(key);unique.append(f)
 return sorted(unique,key=lambda f:(f['shot'],f['rule']))
def report(findings):
 """One line per finding."""
 return [f"  {f['severity'].upper():7s} shot {f['shot']}: {f['rule']}: {f['message']}" for f in findings] or ['  no findings']
