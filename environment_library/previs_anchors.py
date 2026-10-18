"""Named anchors: a story says WHERE with words ("door_front", "bridge_start") and the resolver turns them into coordinates, facings and
spacings, so nobody guesses numbers (the usual source of actors in walls, hugging through each other, or cameras behind them).

In a story plan an actor may carry
    at='door_front'                  a named anchor of the shot's place
    at=('inside_center','left')      one slot of a pair standing at an anchor ('left' / 'right'; spacing comes from the kind of beat)
    face='partner' | 'door' | 'travel' | <degrees>     (default: walkers 'travel', contact side by side, talkers 'partner')
and DIRECTION names its places:
    sets=[dict(name='cafe', kind='village', origin_cm=[0,0])]
    shots={'1 Closed cafe': dict(place='cafe', framing='full')}      (framing: full | medium | close, optional)

resolve(plan, direction) returns a plan and direction in the plain coordinate format used everywhere else, with cameras left to the
automatic camera QA. Anchors per kind below are in cm, local to the place origin; they come from the measured door hut, bridge, stairs
and seat geometry in story_layout (door 63 cm right of and 56 cm ahead of the opener, river y 190..450, stairs from y +40)."""
import copy,math
import contact_actions as ca
ANCHORS={
 'forest':{'clearing':((0,0),0),'trail_start':((0,-150),0),'trail_end':((0,250),0),'camp':((0,60),0)},
 'river':{'south_bank':((0,-150),0),'bridge_start':((0,100),0),'bridge_middle':((0,300),0),'bridge_end':((0,430),0),'north_bank':((0,520),0)},
 'village':{'street':((0,-290),0),'street_near':((0,-150),0),'door_front':((21,-60),0),'entrance':((0,-60),0),'doorway':((0,-80),0),'room_entry':((0,150),0),'inside_center':((0,300),0),'inside_back':((0,470),0),
  'inside_near':((0,170),0),'seat_inside':((-150,300),0),'patio':((190,-10),0)},   # inside anchors sit in the clear acting zone of the 760 x 640 cm room
 'mountains':{'path_start':((0,-250),0),'stairs_bottom':((0,-100),0),'stairs_top':((0,140),0),'summit':((0,60),0)},
}
TALK_SPACING_CM=150.
def _kind(direction,place):
 for s in (direction or {}).get('sets',[]):
  if s.get('name')==place or tuple(s['origin_cm'])==tuple(place if isinstance(place,(list,tuple)) else ()):return s['kind']
 return None
def _origin(direction,place):
 for s in (direction or {}).get('sets',[]):
  if s.get('name')==place:return list(s['origin_cm'])
 return None
def _anchor(kind,name):
 try:return ANCHORS[kind][name]
 except KeyError:raise ValueError(f"unknown anchor '{name}' for a {kind} place; choose from {', '.join(ANCHORS.get(kind,{}))}")
def resolve(plan,direction):
 """Expand anchors into coordinates. Plans without anchors come back unchanged."""
 if not any('at' in a for s in plan['shots'] for a in s.get('actors',[])):return plan,direction
 plan=copy.deepcopy(plan);direction=copy.deepcopy(direction or {});shots=direction.setdefault('shots',{})
 direction.setdefault('auto_camera',True)   # anchored stories get automatic cameras
 for shot in plan['shots']:
  title=shot.get('title','');d=shots.setdefault(title,{});place=d.get('place')
  if place is None:raise ValueError(f"shot '{title}' needs DIRECTION shots['{title}']['place'] (a set name) to resolve its anchors")
  origin=_origin(direction,place);kind=_kind(direction,place)
  if origin is None:raise ValueError(f"unknown place '{place}' in shot '{title}'")
  d['origin_cm']=origin
  if d.get('framing'):d['framing']=d['framing']
  actors=shot.get('actors',[]);pair=len(actors)==2
  contact=any(g['action'] in ca.CONTACT for a in actors for g in a['segments'])
  for i,a in enumerate(actors):
   at=a.pop('at',None)
   if at is None:continue
   name,slot=(at if isinstance(at,(tuple,list)) else (at,None));(x,y),yaw=_anchor(kind,name)
   if pair and slot is not None:
    if contact:
     action=next(g['action'] for g in a['segments'] if g['action'] in ca.CONTACT);low,high=ca.window(action,actors[0]['character'],actors[1]['character']);gap=high-4 if action=='handshake' else (low+high)/2   # angled handshakes need the wide end of the window (clearance between the heads)
    else:gap=TALK_SPACING_CM
    x+=(-gap/2 if slot=='left' else gap/2)
   a['position_cm']=[x,y]
   walks=any(g['action'] in ('walk','run','carry_walk','climb_stairs') for g in a['segments']);face=a.pop('face',None)
   if face is None:face='travel' if walks else ('side' if contact else 'partner' if pair else 'travel')
   handshake=pair and any(g['action']=='handshake' for g in a['segments'])
   if handshake and face=='side':a['facing_yaw_deg']=yaw+(-ca.HANDSHAKE_TURN_DEG if slot=='left' else ca.HANDSHAKE_TURN_DEG)   # greeting: turned toward each other
   elif isinstance(face,str) and face.startswith('toward:'):
    tx,ty=_anchor(kind,face.split(':',1)[1])[0];a['facing_yaw_deg']=round(ca.facing([x,y],[tx,ty]),1)   # e.g. a seated actor faces the middle of the room
   elif face in ('travel','door','side'):a['facing_yaw_deg']=yaw
   elif face=='partner' and pair:
    other=actors[1-i];ox,oy=(other.get('position_cm') or [x,y])
    a['_face_partner']=True
   elif isinstance(face,(int,float)):a['facing_yaw_deg']=face
  if pair:   # talkers face each other once both positions are known
   for i,a in enumerate(actors):
    if a.pop('_face_partner',False):
     other=actors[1-i];a['facing_yaw_deg']=round(ca.facing(a['position_cm'],other['position_cm']),1)
 return plan,direction
