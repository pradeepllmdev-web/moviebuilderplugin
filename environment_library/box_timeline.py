"""Scalar, deterministic box states shared by Blender hands and Unreal props.

The root path (straight carries, short back-steps and walking-arc turns) is computed here and is
authoritative for the shot route, so the body, the held box and every stand share one frame.
Local box coordinates are [lateral, forward, height] in the carrier's heading frame (cm)."""
import math
BOX_ACTIONS={'box_pickup','box_carry','box_back','box_hold','box_setdown','box_bump'}
HELD_ACTIONS={'box_carry','box_back','box_hold','box_setdown','box_bump'}
DEFAULT_CARRY=dict(size_cm=[36,26,24],hold_forward_cm=57,hold_height_cm=88,lift_cm=6,grip_out_cm=3,grip_back_cm=10,grip_up_cm=5,stand_top_cm=[30,22],
 body_cm=dict(back=20,front_low=32,half_width=22,low_height=72),penetration_limit_cm=2.5)
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
def rotate(lateral,forward,yaw):
 a=math.radians(yaw);return [lateral*math.cos(a)-forward*math.sin(a),lateral*math.sin(a)+forward*math.cos(a)]
def to_local(dx,dy,yaw):
 a=math.radians(yaw);return [dx*math.cos(a)+dy*math.sin(a),-dx*math.sin(a)+dy*math.cos(a)]
RAMP=.5  # s, as scene_spec.eased: accelerate from / brake to a standstill only
def travel(beat):
 """Signed path length: carries and walks forward, back-steps backward, turns along their arc."""
 if beat['action'] in ['box_carry','walk','run']:return beat.get('distance_cm',0)
 if beat['action']=='box_back':return -beat['distance_cm']
 if beat['action']=='turn':return abs(math.radians(beat['angle_deg']))*beat['radius_cm']
 return 0
def progress(segments,i,u):
 """Path share at time share u, with the builder's trapezoid speed so clip and root speeds agree.
 Consecutive moves in the same direction flow without slowing; a reversal stops in between."""
 T=segments[i]['duration'];d=travel(segments[i])
 if abs(d)<20 or T<=0:return u
 def flows(j):return 0<=j<len(segments) and abs(travel(segments[j]))>=20 and travel(segments[j])*d>0
 rs=0 if flows(i-1) else min(RAMP,T/3);re=0 if flows(i+1) else min(RAMP,T/3);t=u*T;v=1/(T-rs/2-re/2)
 if t<rs:return v*t*t/(2*rs)
 if t>T-re:return 1-v*(T-t)**2/(2*re)
 return v*(rs/2+t-rs)
def root_path(segments,fps,heading):
 """Straight carries/back-steps and walking-arc turns (geometry as turn_routes) on the builder's speed profile."""
 rows=[];x=y=0.;yaw=float(heading)
 for i,beat in enumerate(segments):
  count=round(beat['duration']*fps);start_x,start_y,start_yaw=x,y,yaw;angle=beat.get('angle_deg',0) if beat['action']=='turn' else 0;distance=travel(beat) if not angle else 0
  for frame in range(count):
   u=progress(segments,i,frame/max(1,count-1))
   if angle:
    a=math.radians(start_yaw);b=math.radians(start_yaw+angle*u);sign=1 if angle>0 else -1;r=beat['radius_cm']
    px=start_x+sign*r*(math.cos(b)-math.cos(a));py=start_y+sign*r*(math.sin(b)-math.sin(a));current=start_yaw+angle*u
   else:px=start_x-distance*u*math.sin(math.radians(start_yaw));py=start_y+distance*u*math.cos(math.radians(start_yaw));current=start_yaw
   rows.append({'frame':len(rows),'location_cm':[px,py,0.],'yaw':current})
  x,y=rows[-1]['location_cm'][:2];yaw=start_yaw+angle
 return rows
def corners(center,yaw,half_lateral,front,back):
 return [[center[0]+x,center[1]+y] for x,y in (rotate(a,b,yaw) for a,b in [(-half_lateral,-back),(half_lateral,-back),(half_lateral,front),(-half_lateral,front)])]
def gap(a,b):
 """Separating-axis gap between two convex quads (negative = overlap depth)."""
 best=None
 for shape in (a,b):
  for i in range(4):
   p,q=shape[i],shape[(i+1)%4];nx,ny=q[1]-p[1],p[0]-q[0];length=math.hypot(nx,ny);nx/=length;ny/=length
   pa=[x*nx+y*ny for x,y in a];pb=[x*nx+y*ny for x,y in b];g=max(min(pb)-max(pa),min(pa)-max(pb))
   best=g if best is None else max(best,g)
 return best
def stand_clearance(rows,stands,position,c):
 """Smallest plan-view gap between the carrier's lower body and any stand top (negative = walking through it)."""
 body=c['body_cm'];worst={'minimum_gap_cm':999.,'frame':None}
 for row in rows:
  shape=corners([position[0]+row['root_cm'][0],position[1]+row['root_cm'][1]],row['yaw'],body['half_width'],body['front_low'],body['back'])
  for stand in stands:
   if stand['location_cm'][2]>body['low_height']:continue
   half=stand['top_cm'][1]/2;g=gap(shape,corners(stand['location_cm'][:2],stand['yaw'],stand['top_cm'][0]/2,half,half))
   if g<worst['minimum_gap_cm']:worst={'minimum_gap_cm':g,'frame':row['frame']}
 worst['scope']='Plan-view lower-body footprint against stand tops; not mesh collision'
 return worst
def build(segments,position=(0,0),initial=None,fps=24,heading=0,carry=None,scene_stands=None):
 c=dict(DEFAULT_CARRY,**(carry or {}));w,d,h=c['size_cm'];F=c['hold_forward_cm'];H=c['hold_height_cm'];lift=c['lift_cm']
 state=dict(initial) if initial else {'id':'TrailCrate','phase':'none'};stands=[dict(s) for s in state.get('stands',[])];obstacles=[dict(o) for o in state.get('obstacles',[])]
 path=root_path(segments,fps,heading);rows=[];frame=0;phase=state['phase'];travel=0.;box=state.get('location_cm');box_yaw=state.get('yaw',heading)
 if box is None:
  # A new box rests on its pickup stand where the carrier will be when the pickup starts.
  start=0
  for beat in segments:
   if beat['action']=='box_pickup':break
   start+=round(beat['duration']*fps)
  root=path[min(start,len(path)-1)];offset=rotate(0,F,root['yaw']);box=[position[0]+root['location_cm'][0]+offset[0],position[1]+root['location_cm'][1]+offset[1],H-lift];box_yaw=root['yaw']
 for beat in segments:
  action=beat['action'];count=round(beat['duration']*fps)
  if action in HELD_ACTIONS and phase!='held':raise ValueError(action+' needs a held box; pick it up first')
  if action=='box_pickup' and phase!='none':raise ValueError('Use a new audition for a second pickup')
  for index in range(count):
   u=index/max(1,count-1);row=path[frame];root=[row['location_cm'][0],row['location_cm'][1],0];yaw=row['yaw'];weight=1 if phase=='held' else 0;contact=False;reaction=0;local=None
   if frame:
    step=math.dist(path[frame-1]['location_cm'][:2],root[:2])
    if action in ['box_carry','walk','run']:travel+=step
    elif action=='box_back':travel-=step
   if action=='box_pickup':
    v=smooth((u-.3)/.7);local=[0,F,H-lift+lift*v];weight=smooth(u/.3);contact=u>=.3
   elif action=='box_setdown':
    v=smooth(u/.75);local=[0,F,H-lift*v];weight=1-smooth((u-.75)/.25);contact=u<=.75
   elif phase=='held':
    bump=math.sin(math.pi*u)**2 if action=='box_bump' else 0;local=[0,F+2*bump,H];contact=True;reaction=bump
   if local is not None:
    offset=rotate(local[0],local[1],yaw);box=[position[0]+root[0]+offset[0],position[1]+root[1]+offset[1],local[2]];box_yaw=yaw
   else:
    # A resting box is world-fixed; keep its carrier-relative coordinates for clearance checks.
    lateral,forward=to_local(box[0]-position[0]-root[0],box[1]-position[1]-root[1],yaw);local=[lateral,forward,box[2]]
   rows.append({'frame':frame,'root_cm':root,'yaw':yaw,'travel_cm':travel,'location_cm':list(box),'box_yaw':box_yaw,'local_cm':local,'hand_weight':weight,'contact':contact,'held':weight>0,'action':action,'reaction':reaction})
   frame+=1
  if action in ['box_pickup','box_setdown']:
   under=rows[-count] if action=='box_pickup' else rows[-1]
   stands.append({'location_cm':[under['location_cm'][0],under['location_cm'][1],H-lift-h/2],'yaw':under['box_yaw'],'top_cm':list(c['stand_top_cm'])})
  if action=='box_pickup':phase='held'
  if action=='box_setdown':phase='placed'
  if action=='box_bump':
   last=rows[-1];offset=rotate(0,F+d/2+6,last['yaw']);obstacles.append({'location_cm':[position[0]+last['root_cm'][0]+offset[0],position[1]+last['root_cm'][1]+offset[1],H],'yaw':last['yaw']})
 # Stands used later in the movie are already standing in earlier shots.
 placed=stands+[dict(s) for s in scene_stands or [] if not any(math.dist(s['location_cm'][:2],t['location_cm'][:2])<1 for t in stands)]
 clearance=stand_clearance(rows,placed,position,c)
 if clearance['minimum_gap_cm']<0:raise ValueError('The carrier walks through a box stand at frame '+str(clearance['frame'])+'; step back and turn after the pickup')
 state.update(phase=phase,location_cm=list(box),yaw=box_yaw,stands=stands,obstacles=obstacles)
 return {'rows':rows,'end_state':state,'stands':placed,'obstacles':obstacles,'size_cm':[w,d,h],'carry':c,'stand_clearance':clearance}
def movie_stands(shots,carry=None,fps=24):
 """Simulate a whole movie's box path once so every stand exists from the first shot."""
 state=None;position=[0,0];heading=0
 for segments in shots:
  if state is None and not any(g['action'].startswith('box_') for g in segments):
   path=root_path(segments,fps,heading);position=[position[0]+path[-1]['location_cm'][0],position[1]+path[-1]['location_cm'][1]];heading=path[-1]['yaw'];continue
  result=build(segments,position,state,fps,heading,carry);state=result['end_state'];last=result['rows'][-1]
  position=[position[0]+last['root_cm'][0],position[1]+last['root_cm'][1]];heading=last['yaw']
 return (state or {}).get('stands',[])
