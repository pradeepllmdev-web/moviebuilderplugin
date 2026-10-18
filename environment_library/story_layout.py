"""Pre-build layout planning for a story, in the order a director works (pure Python, instant):

  1. environment and props   footprints of the scenery each shot needs (hut around a door, bench and table, stairs, patio, river)
  2. paths                   where every actor stands and walks in every shot (walks go +Y, as the builder moves actors)
  3. blocking                actors must not stand in scenery, walk through walls or water, or crowd each other
  4. facing                  walkers face their direction of travel, talkers face their partner, contact beats are side by side

layout(plan, direction) -> {'scenery': {place: [box]}, 'paths': [...], 'findings': [...]}. story_lint.lint() includes these findings
(rule families 'blocking.*' and 'facing.*'), so `quick_review.py previs` prints them before building and --strict stops on errors.

Numbers come from the lion's measured build (door centre 63 cm to the right of the standing spot and 56 cm ahead; seat and table from
the drink layout; stairs from contact_actions.STEP); other characters use the same until they are measured. All boxes are
(x0, y0, x1, y1) in world cm with the place origin and the shot offset already added."""
import math
import contact_actions as ca
DOOR_RIGHT_CM=63.;DOOR_AHEAD_CM=56.;DOOR_WIDTH_CM=102.;ROOM_HALF_WIDTH_CM=280.;ROOM_DEPTH_CM=440.;WALL_CM=15.
SEAT_BACK_CM=25.;TABLE_NEAR_CM=22.;TABLE_FAR_CM=92.;TABLE_HALF_WIDTH_CM=40.;BENCH_HALF_DEPTH_CM=20.
RIVER_Y=(190.,450.);BRIDGE_HALF_WIDTH_CM=110.
ACTOR_RADIUS_CM=35.;ACTOR_GAP_CM=70.
WALKS=('walk','run','carry_walk','climb_stairs')
def box(x0,y0,x1,y1,name,kind='solid'):return dict(box=(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)),name=name,kind=kind)
def _origin(direction,title):
 d=(direction or {}).get('shots',{}).get(title,{});o=d.get('origin_cm',[0,0]);f=d.get('offset_cm',[0,0]);return tuple(o),(o[0]+f[0],o[1]+f[1])
def _actors(shot):return shot.get('actors') or [dict(character=shot.get('character'),position_cm=[0,0],segments=shot['segments'])]
def segment_paths(shot):
 """(start, end, action) of each beat of each actor, local to the shot (walks advance +Y; sitting eases back 25 cm)."""
 out=[]
 for a in _actors(shot):
  x,y=a.get('position_cm',[0,0]);t=0.
  for g in a['segments']:
   dy=g.get('distance_cm',0) if g['action'] in WALKS else (-SEAT_BACK_CM if g['action']=='sit_down' else SEAT_BACK_CM if g['action']=='stand_up' else 0)
   out.append(dict(actor=a['character'],start=(x,y),end=(x,y+dy),action=g['action'],t0=t,t1=t+g['duration']));y+=dy;t+=g['duration']
 return out
def scenery(plan,direction):
 """Footprints per place, from the beats that need scenery."""
 sc={}
 for shot in plan['shots']:
  title=shot.get('title','');place,origin=_origin(direction,title);boxes=sc.setdefault(place,[])
  for a in _actors(shot):
   x,y=origin[0]+a.get('position_cm',[0,0])[0],origin[1]+a.get('position_cm',[0,0])[1];acts=[g['action'] for g in a['segments']]
   if 'open_door' in acts:   # a hut around the door the actor opens
    cx,py=x+DOOR_RIGHT_CM,y+DOOR_AHEAD_CM;half=DOOR_WIDTH_CM/2;r=ROOM_HALF_WIDTH_CM
    boxes+=[box(cx-r,py-WALL_CM/2,cx-half,py+WALL_CM/2,'DoorWallL'),box(cx+half,py-WALL_CM/2,cx+r,py+WALL_CM/2,'DoorWallR'),
     box(cx-r,py+ROOM_DEPTH_CM-WALL_CM/2,cx+r,py+ROOM_DEPTH_CM+WALL_CM/2,'HutBack'),box(cx-r-WALL_CM/2,py,cx-r+WALL_CM/2,py+ROOM_DEPTH_CM,'HutSideA'),
     box(cx+r-WALL_CM/2,py,cx+r+WALL_CM/2,py+ROOM_DEPTH_CM,'HutSideB'),box(cx-half,py-WALL_CM/2,cx+half,py+WALL_CM/2,'Doorway','opening'),box(cx-r,py,cx+r,py+ROOM_DEPTH_CM,'Room','room')]
    if (direction or {}).get('shots',{}).get(title,{}).get('door_style')=='cafe':
     for sx in (-1,1):boxes.append(box(cx+sx*190-55,py+150-55,cx+sx*190+55,py+150+55,'Patio'))
   if 'sit_down' in acts or 'drink' in acts:   # bench under the seat, table in front
    sy=y-SEAT_BACK_CM;boxes+=[box(x-35,sy-BENCH_HALF_DEPTH_CM+12,x+35,sy+BENCH_HALF_DEPTH_CM+12,'Bench'),box(x-TABLE_HALF_WIDTH_CM,y+TABLE_NEAR_CM-SEAT_BACK_CM,x+TABLE_HALF_WIDTH_CM,y+TABLE_FAR_CM-SEAT_BACK_CM,'DrinkTable')]
   if 'climb_stairs' in acts:
    st=ca.STEP;boxes.append(box(x-100,y+st['first_cm'],x+100,y+st['first_cm']+st['count']*st['tread_cm']+6,'Stairs'))
   if 'pick_up' in acts:boxes.append(box(x-30,y+10,x+10,y+60,'SideTable'))
 return sc
USES={'Bench':{'sit_down','sit','sit_talk','stand_up','drink'},'DrinkTable':{'sit_down','sit','sit_talk','stand_up','drink'},'Stairs':{'climb_stairs'},'SideTable':{'pick_up'}}
def layout(plan,direction=None):
 """Run the four stages; returns scenery, paths and findings."""
 shots=plan['shots'];sc=scenery(plan,direction);findings=[];paths=[]
 def add(k,rule,severity,message):findings.append(dict(shot=k+1,rule=rule,severity=severity,message=message))
 kinds={tuple(s['origin_cm']):s['kind'] for s in (direction or {}).get('sets',[])}
 for k,shot in enumerate(shots):
  title=shot.get('title','');place,origin=_origin(direction,title);segs=segment_paths(shot)
  boxes=sc.get(place,[]);solids=[b for b in boxes if b['kind']=='solid'];openings=[b for b in boxes if b['kind']=='opening']
  for s in segs:
   a0=(s['start'][0]+origin[0],s['start'][1]+origin[1]);a1=(s['end'][0]+origin[0],s['end'][1]+origin[1]);paths.append(dict(shot=k+1,actor=s['actor'],action=s['action'],start=a0,end=a1))
   steps=max(2,int(math.dist(a0,a1)/10)+1);hit=None
   for i in range(steps):   # 3. blocking against solid scenery (an actor may touch the pieces its own action uses)
    px=a0[0]+(a1[0]-a0[0])*i/(steps-1);py=a0[1]+(a1[1]-a0[1])*i/(steps-1)
    for b in solids:
     x0,y0,x1,y1=b['box']
     if b['name']=='Patio' or s['action'] in USES.get(b['name'],()):continue
     if b['name'].startswith('DoorWall') and any(o['box'][0]+20<=px<=o['box'][2]-20 for o in openings):continue
     if x0-ACTOR_RADIUS_CM<px<x1+ACTOR_RADIUS_CM and y0-ACTOR_RADIUS_CM<py<y1+ACTOR_RADIUS_CM:hit=(b['name'],px,py);break
    if hit:break
   if hit:add(k,'blocking.scenery','error',f"{s['actor']} ({s['action']}) is in the {hit[0]} at ({hit[1]:.0f},{hit[2]:.0f}); move the actor or give the shot an offset_cm")
   if kinds.get(place)=='river':
    for i in range(steps):
     px=a0[0]+(a1[0]-a0[0])*i/(steps-1)-place[0];py=a0[1]+(a1[1]-a0[1])*i/(steps-1)-place[1]
     if RIVER_Y[0]<py<RIVER_Y[1] and abs(px)>BRIDGE_HALF_WIDTH_CM-30:add(k,'blocking.water','error',f"{s['actor']} is in the river at ({px:.0f},{py:.0f}); keep to the bridge (x within +-80) or stay on the bank");break
   if s['action'] in WALKS:   # 4. a walker faces the direction of travel (the builder walks +Y)
    actor=next(a for a in _actors(shot) if a['character']==s['actor']);yaw=actor.get('facing_yaw_deg',0)
    if abs(yaw)>20:add(k,'facing.walker','warning',f"{s['actor']} walks +Y but faces {yaw:.0f} degrees; walkers face their direction of travel (facing_yaw_deg 0)")
  actors=_actors(shot)
  if len(actors)==2:
   contact=any(g['action'] in ca.CONTACT for a in actors for g in a['segments']);p0,p1=actors[0].get('position_cm',[0,0]),actors[1].get('position_cm',[0,0])
   ends=[[s for s in segs if s['actor']==a['character']] for a in actors]
   for which in (0,-1):
    d=math.dist(ends[0][which]['start' if which==0 else 'end'],ends[1][which]['start' if which==0 else 'end'])
    if not contact and d<ACTOR_GAP_CM:add(k,'blocking.actors','warning',f"{actors[0]['character']} and {actors[1]['character']} are only {d:.0f} cm apart without a contact beat (bodies are about 70 cm wide)");break
   for i,actor in enumerate(actors):
    other=actors[1-i];x,y=actor.get('position_cm',[0,0]);ox,oy=other.get('position_cm',[0,0]);yaw=actor.get('facing_yaw_deg',0)
    if contact:
     if abs(yaw-other.get('facing_yaw_deg',0))>1:add(k,'facing.contact','warning','contact beats are side by side: both actors should face the same way')
    elif not any(g['action'] in WALKS for g in actor['segments']):
     want=ca.facing([x,y],[ox,oy]);err=abs((yaw-want+180)%360-180)
     if err>75 and any(g.get('dialogue') or g['action'] in ('wave','laugh','celebrate','nod') for g in actor['segments']):add(k,'facing.partner','warning',f"{actor['character']} faces {yaw:.0f} degrees but the partner is at {want:.0f}; turn toward them (facing_yaw_deg {want:.0f})")
 return dict(scenery=sc,paths=paths,findings=findings)
