"""Top-view percentages -> validated Unreal centimeters. No engine dependency."""
import math
def number(v,lo,hi,name):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError(f'{name} must be between {lo} and {hi}')
 return float(v)
def compile_layout(layout):
 if not isinstance(layout,dict):raise ValueError('Layout must be an object')
 width=number(layout.get('width_m',120),20,300,'Layout width');depth=number(layout.get('depth_m',120),20,300,'Layout depth')
 def point(p):
  if not isinstance(p,list) or len(p)!=2:raise ValueError('Layout points must be [x%, y%]')
  x=number(p[0],0,100,'x');y=number(p[1],0,100,'y');return [round((x/100-.5)*width*100,2),round((.5-y/100)*depth*100,2)]
 out={'width_cm':width*100,'depth_cm':depth*100,'rivers':[],'paths':[],'clear':[],'forests':[],'bridges':[]}
 for kind in ('rivers','paths'):
  items=layout.get(kind,[])
  if not isinstance(items,list) or len(items)>4:raise ValueError('At most four '+kind+' are supported')
  for item in items:
   pts=item.get('points',[])
   if not 2<=len(pts)<=16:raise ValueError(kind+' require 2–16 points')
   converted=[point(p) for p in pts]
   if any(math.dist(a,b)<100 for a,b in zip(converted,converted[1:])):raise ValueError('Consecutive route points must be at least one metre apart')
   w=number(item.get('width_m',7 if kind=='rivers' else 3),2 if kind=='rivers' else 1,25 if kind=='rivers' else 10,'Route width')
   entry={'points':converted,'width':w*100}
   if kind=='paths':
    style=item.get('style','dirt')
    if style not in ('dirt','gravel','cobble','road','boardwalk'):raise ValueError('Unsupported path style')
    entry['style']=style
   out[kind].append(entry)
 for kind in ('clear','forests'):
  items=layout.get(kind,[])
  if not isinstance(items,list) or len(items)>8:raise ValueError('At most eight '+kind+' circles are supported')
  for item in items:
   center=point(item['center']);radius=number(item.get('radius_m',8 if kind=='clear' else 20),2 if kind=='clear' else 5,40 if kind=='clear' else 70,'Region radius')*100
   if kind=='clear':out['clear'].append([*center,radius])
   else:out['forests'].append({'center':center,'radius':radius,'density':number(item.get('density',.8),.2,1.5,'Forest density')})
 bridges=layout.get('bridges',[])
 if not isinstance(bridges,list) or len(bridges)>4:raise ValueError('At most four bridges are supported')
 for item in bridges:
  index=item.get('river',0)
  if type(index)!=int or not 0<=index<len(out['rivers']):raise ValueError('Each bridge must reference a layout river index')
  out['bridges'].append({'river':index,'at':point(item['at']),'style':'wood','width':number(item.get('width_m',3),1.5,8,'Bridge width')*100})
 if layout.get('camera'):
  c=layout['camera'];out['camera']={'location':[*point(c['position']),number(c.get('height_m',2.2),1,40,'Camera height')*100],'target':[*point(c['target']),number(c.get('target_height_m',1.7),0,20,'Target height')*100]}
 return out
