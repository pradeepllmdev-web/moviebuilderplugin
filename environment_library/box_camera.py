"""Heading-relative cameras for box shots, chosen so the box never hides the carrier's head. Pure geometry."""
import math
VIEWS={'full':dict(forward=120,lateral=400,height=185,target_forward=30,target_height=90),
 'medium':dict(forward=260,lateral=190,height=160,target_forward=20,target_height=112)}
def axes(yaw):
 a=math.radians(yaw);return (math.cos(a),math.sin(a)),(-math.sin(a),math.cos(a))
def view(root,yaw,kind,side):
 v=VIEWS['full' if kind=='full' else 'medium'];lateral,forward=axes(yaw);x,y,z=root
 position=[x+forward[0]*v['forward']+lateral[0]*v['lateral']*side,y+forward[1]*v['forward']+lateral[1]*v['lateral']*side,z+v['height']]
 target=[x+forward[0]*v['target_forward'],y+forward[1]*v['target_forward'],z+v['target_height']]
 return position,target
def blocks(start,end,center,yaw,size):
 """Slab test: does the segment start->end pass through the yawed box?"""
 a=math.radians(yaw);c,s=math.cos(a),math.sin(a)
 def local(p):dx,dy,dz=p[0]-center[0],p[1]-center[1],p[2]-center[2];return [dx*c+dy*s,-dx*s+dy*c,dz]
 p,q=local(start),local(end);lo,hi=0.,1.
 for axis in range(3):
  half=size[axis]/2;d=q[axis]-p[axis]
  if abs(d)<1e-9:
   if abs(p[axis])>half:return False
   continue
  t1,t2=(-half-p[axis])/d,(half-p[axis])/d
  lo,hi=max(lo,min(t1,t2)),min(hi,max(t1,t2))
  if lo>hi:return False
 return True
def choose(route,box,kind,eye_height,eye_forward=40,step=6):
 """Pick the camera side with the fewest frames where the box covers the eyes; report the count."""
 best=None
 for side in (1,-1):
  covered=0;samples=0
  for frame in range(0,len(route),step):
   root=route[frame]['location_cm'];position,_=view(root,route[frame]['yaw'],kind,side);row=box['rows'][min(frame,len(box['rows'])-1)]
   center=[row['location_cm'][0],row['location_cm'][1],row['location_cm'][2]+root[2]];eye=[root[0],root[1],root[2]+eye_height]
   # Eyes sit near the head bone; aim at the face in front of it.
   lateral,forward=axes(route[frame]['yaw']);eye=[eye[0]+forward[0]*eye_forward,eye[1]+forward[1]*eye_forward,eye[2]]
   samples+=1;covered+=blocks(position,eye,center,row['box_yaw'],box['size_cm'])
  if best is None or covered<best['covered_samples']:best={'side':side,'covered_samples':covered,'samples':samples}
 best['scope']='Camera-to-face ray against the box volume; not a full silhouette check'
 return best
