"""Bounded walking arcs. Pure scalar geometry; no model buffers."""
import math

def route(segments,fps=24,heading=0):
 rows=[];x=y=0.;yaw=float(heading)
 for beat in segments:
  count=round(beat['duration']*fps);start_x,start_y,start_yaw=x,y,yaw
  angle=beat.get('angle_deg',0) if beat['action']=='turn' else 0
  distance=beat.get('distance_cm',0) if beat['action'] in ['walk','run'] else 0
  for frame in range(count):
   u=frame/max(1,count-1)
   # Smooth angular acceleration while retaining a walking gait through the arc.
   if angle:
    u=u*u*(3-2*u);a=math.radians(start_yaw);b=math.radians(start_yaw+angle*u);sign=1 if angle>0 else -1;r=beat['radius_cm']
    px=start_x+sign*r*(math.cos(b)-math.cos(a));py=start_y+sign*r*(math.sin(b)-math.sin(a));current=start_yaw+angle*u
   else:
    # Ease a straight route at the start/stop, with exact shared endpoints.
    u=u*u*(3-2*u);px=start_x-distance*u*math.sin(math.radians(start_yaw));py=start_y+distance*u*math.cos(math.radians(start_yaw));current=start_yaw
   rows.append({'frame':len(rows),'location_cm':[px,py,0.],'yaw':current})
  x,y=rows[-1]['location_cm'][:2];yaw=start_yaw+angle
 return rows
