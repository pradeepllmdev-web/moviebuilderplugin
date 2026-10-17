"""Approximate framing from scalar profile heights, not model geometry."""
import math
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def unit(v):
 length=math.sqrt(dot(v,v));return [x/length for x in v]
def in_frame(point,position,target,focal,margin=.94):
 forward=unit([b-a for a,b in zip(position,target)]);right=unit([forward[1],-forward[0],0]);up=[right[1]*forward[2]-right[2]*forward[1],right[2]*forward[0]-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0]]
 delta=[p-c for p,c in zip(point,position)];depth=dot(delta,forward)
 return depth>1 and abs(dot(delta,right)/depth)<18/focal*margin and abs(dot(delta,up)/depth)<10.125/focal*margin

def standard_full_report(routes,heights,focal=32):
 samples=head_outside=feet_outside=0
 for frame in range(0,len(next(iter(routes.values()))),12):
  cx=sum(rows[frame]['location_cm'][0] for rows in routes.values())/len(routes);cy=sum(rows[frame]['location_cm'][1] for rows in routes.values())/len(routes)
  position=[cx+520,cy+220,230];target=[cx,cy,105]
  for name,rows in routes.items():
   x,y,z=rows[frame]['location_cm'];samples+=1
   head_outside+=not in_frame([x,y,z+heights[name]*.9],position,target,focal)
   feet_outside+=not in_frame([x,y,z+5],position,target,focal)
 return dict(samples=samples,adaptive_focal_mm=focal if focal!=32 else None,head_outside_samples=head_outside,feet_outside_samples=feet_outside,scope='Standard two-character full camera, scalar profile heights; no occlusion or mesh silhouette checks')
