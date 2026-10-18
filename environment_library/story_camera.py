"""Automatic cameras for previs: for every shot pick a camera that sees the actors from a flattering side without standing in a wall,
behind a wall or inside the wrong room (pure Python, uses the scenery footprints from story_layout).

solve(shot, place_origin, offset, scenery_boxes) -> {pos_cm, target_cm, lens[, to_pos_cm, to_target_cm]}

Rules, in order of importance:
  * the camera is in the same space as the actors: inside the room when they are, outside every room when they are not
  * it is not inside a wall, table, bench or stairs, and the line of sight to the actors crosses no wall (doorways let it through)
  * it sees faces: three-quarter front of the actors' facing (walkers: ahead and to the side), side-on for two actors facing each other
  * the distance suits the shot size (full / medium / close), shrunk to fit a room
Walking shots get a dolly: the same relative position at the start and at the end of the walk, when the line of sight stays clear."""
import math
import story_layout as sl
SIZE_CM={'full':430,'medium':290,'close':210,'reaction':210}
FOCUS_Z=100.
def _inside(b,x,y,m=0.):return b['box'][0]-m<x<b['box'][2]+m and b['box'][1]-m<y<b['box'][3]+m
def _segment_clear(p,q,solids,openings):
 n=max(2,int(math.dist(p,q)/8))
 for i in range(1,n):
  x=p[0]+(q[0]-p[0])*i/n;y=p[1]+(q[1]-p[1])*i/n
  for b in solids:
   if _inside(b,x,y,3):
    if b['name'].startswith('DoorWall') and any(o['box'][0]<=x<=o['box'][2] for o in openings):continue
    return False
 return True
def _facing_vector(actors):
 fx=fy=0.
 for a in actors:
  yaw=math.radians(a.get('facing_yaw_deg',0));fx+=-math.sin(yaw);fy+=math.cos(yaw)
 n=math.hypot(fx,fy)
 return (fx/n,fy/n) if n>1e-6 else (0.,1.)
def solve(shot,origin,boxes,at=None):
 """Camera for a shot. origin: world position of the shot's local (0,0); boxes: scenery footprints of the place; at: 'start'|'end'|None (walk position)."""
 actors=shot.get('actors') or [dict(position_cm=[0,0],segments=shot['segments'])];pts=[]
 for a in actors:
  x,y=a.get('position_cm',[0,0]);walk=sum(g.get('distance_cm',0) for g in a['segments'] if g['action'] in sl.WALKS)
  pts.append((origin[0]+x,origin[1]+y+(walk*(0 if at=='start' else 1 if at=='end' else .5))))
 cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
 solids=[b for b in boxes if b['kind']=='solid' and b['name']!='Patio'];openings=[b for b in boxes if b['kind']=='opening'];rooms=[b for b in boxes if b['kind']=='room']
 room=next((r for r in rooms if _inside(r,cx,cy)),None);size=SIZE_CM.get(shot.get('camera','full'),430)
 if len(actors)==2 and not any(g['action'] in sl.ca.CONTACT for a in actors for g in a['segments']):size*=1.1
 walkers=any(g['action'] in sl.WALKS for a in actors for g in a['segments']);face=_facing_vector(actors);best=None
 for theta in range(0,360,10):
  for scale in (.25,.32,.4,.5,.6,.7,.85,1.0,1.2):
   r=size*scale;px=cx+r*math.cos(math.radians(theta));py=cy+r*math.sin(math.radians(theta))
   if room:   # stay inside the room, away from its walls
    b=room['box']
    if not (b[0]+45<px<b[2]-45 and b[1]+45<py<b[3]-45):continue
   elif any(_inside(rm,px,py,70) for rm in rooms):continue   # outside: well clear of the building
   if any(_inside(b,px,py,80) for b in solids if not _inside(b,cx,cy,45)):continue   # never hugging a wall, table or step (pieces the actors use are excepted)
   if not _segment_clear((px,py),(cx,cy),[b for b in solids if not _inside(b,cx,cy,45)],openings):continue   # pieces the actors stand at (bench, table, steps) do not block the view of them
   v=(math.cos(math.radians(theta)),math.sin(math.radians(theta)));along=v[0]*face[0]+v[1]*face[1]   # +1: camera straight ahead of the actors
   angle=math.degrees(math.acos(max(-1,min(1,along))))
   if len(actors)==2 and not any(g['action'] in sl.ca.CONTACT for a in actors for g in a['segments']):penalty=abs(angle-90)/90     # facing each other: side on
   else:penalty=abs(angle-(55 if not walkers else 60))/60                                                                         # three quarters, faces visible
   if angle>115:penalty+=2   # never from behind
   score=penalty+abs(scale-1)*.5
   if best is None or score<best[0]:best=(score,px,py,r,scale)
 if best is None:   # nothing clear: the farthest free point on the open side
  px,py=cx+size*math.cos(0),cy+size*math.sin(0);best=(9,px,py,size,1)
 _,px,py,r,scale=best;height=140 if shot.get('camera','full')!='full' else 170
 return dict(pos_cm=[px,py,height],target_cm=[cx,cy,FOCUS_Z+(10 if len(actors)==2 else 0)],lens=(22 if room else 34 if shot.get('camera')!='full' else 30))   # wider lens inside a room
def solve_shot(shot,origin,boxes):
 """Static camera, or a dolly for walking shots (same relative position at the start and the end when the view stays clear)."""
 cam=solve(shot,origin,boxes)
 walkers=any(g['action'] in sl.WALKS for a in (shot.get('actors') or [dict(segments=shot['segments'])]) for g in a['segments'])
 if not walkers:return cam
 start=solve(shot,origin,boxes,'start');end=solve(shot,origin,boxes,'end')
 return dict(start,to_pos_cm=end['pos_cm'],to_target_cm=end['target_cm'])
