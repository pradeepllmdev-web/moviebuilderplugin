"""Conservative route checks; these are not a physics simulation."""
import math

def validate_routes(routes):
 if not routes:raise ValueError('No character routes')
 lengths={len(rows) for rows in routes.values()}
 if len(lengths)!=1 or 0 in lengths:raise ValueError('Character routes must share a nonempty timeline')
 maximum_step=0;maximum_heading_step=0
 for rows in routes.values():
  previous=None;previous_yaw=None
  for row in rows:
   pos=row['location_cm']
   if len(pos)!=3 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in pos):raise ValueError('Route has invalid coordinates')
   if math.hypot(*pos[:2])>700:raise ValueError('Route leaves the cleared seven metre filming area')
   if previous:
    step=math.dist(pos,previous);maximum_step=max(maximum_step,step)
    if step>30:raise ValueError('Route changes by more than 30 cm in a frame; review movement or grounding')
   yaw=row.get('yaw',0)
   if isinstance(yaw,bool) or not isinstance(yaw,(int,float)) or not math.isfinite(yaw):raise ValueError('Route has invalid heading')
   if previous_yaw is not None:
    delta=abs((yaw-previous_yaw+180)%360-180);maximum_heading_step=max(maximum_heading_step,delta)
    if delta>8:raise ValueError('Route heading snaps by more than eight degrees per frame')
   previous_yaw=yaw
   previous=pos
 minimum=None
 if len(routes)>1:
  first,second=list(routes.values());minimum=min(math.dist(a['location_cm'][:2],b['location_cm'][:2]) for a,b in zip(first,second))
  if minimum<90:raise ValueError('Character routes approach within 90 cm; separate placements or paths')
 return {'ok':True,'minimum_actor_separation_cm':minimum,'maximum_root_step_cm':maximum_step,'maximum_heading_step_deg':maximum_heading_step,'physics':'conservative route separation and grounding; no rigid-body contacts'}
