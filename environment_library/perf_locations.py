"""Small location specs for the performance engine (pure Python first, Blender only in build()).

A location is a dict:   dict(preset='forest_clearing', seed=3, objects=[...extra objects...], ground=(r,g,b), half=(24,24), water=[x0,y0,x1,y1], markers={'gate':[x,y]})
or a hand-written one with no preset. Objects are small recipes made from primitives (house, tree, pine, rock, wall, fence, table, bench, stool, chair, log, campfire, crate, barrel, lamp, pillar, arch, tent, stall, boat, well, statue,
haystack, sign, cart, anvil, shelf, bed, throne, stairs-free): dict(kind='house', at=[x,y], yaw=0 (degrees), size=1.0, color=None, id=None, to=[x,y] for walls and fences).

layout(loc) -> what the planner needs: obstacles (circles x,y,r covering every solid footprint), seats {id:(x,y,seat_height)}, surfaces {id:(x,y,top_z,radius)}, markers, bounds, floor z. prims(loc) -> primitive dicts (shape, name, loc, scale, rot, color, emit, kw)
for the Blender builder. PROP_KINDS (what can be carried or pushed) lives here too, so planner, builder and audits read one table. build(S,loc,time) creates the location in a scene_base.Scene: ground, objects, lights, sky.
Locations are deliberately low-poly and quick; the performance is the point. Everything in a location is visible for the whole scene (nothing is hidden or moved)."""
import math,random
PI=math.pi
# ---------------------------------------------------------------------------------------------------------------- props: carried or pushed
# size is the full extent (x,y,z) in metres at scale 1; carry: both hands / one hand; weight: seconds of strain shown when carried
PROP_KINDS={
 'crate':dict(size=(.5,.5,.4),carry='both',color=(.55,.38,.2)),'sack':dict(size=(.4,.35,.45),carry='both',color=(.72,.62,.42)),'basket':dict(size=(.4,.4,.3),carry='both',color=(.7,.5,.25)),'barrel_small':dict(size=(.4,.4,.5),carry='both',color=(.45,.3,.18)),
 'lantern':dict(size=(.16,.16,.26),carry='R',color=(.95,.75,.3),emit=2.5),'scroll':dict(size=(.1,.1,.3),carry='R',color=(.9,.85,.7)),'book':dict(size=(.22,.3,.06),carry='R',color=(.5,.15,.15)),'key':dict(size=(.07,.16,.02),carry='R',color=(.95,.8,.25)),
 'cup':dict(size=(.1,.1,.12),carry='R',color=(.75,.75,.8)),'jar':dict(size=(.14,.14,.2),carry='R',color=(.5,.75,.6)),'gem':dict(size=(.12,.12,.16),carry='R',color=(.4,.9,1.),emit=3.),'flag':dict(size=(.3,.04,.9),carry='R',color=(.8,.2,.2)),
 'plank':dict(size=(.9,.2,.05),carry='both',color=(.6,.45,.28)),'bundle':dict(size=(.5,.3,.3),carry='both',color=(.8,.8,.7)),'tool':dict(size=(.5,.06,.06),carry='R',color=(.5,.5,.55)),'apple':dict(size=(.09,.09,.09),carry='R',color=(.8,.15,.1)),
 'bell':dict(size=(.15,.15,.18),carry='R',color=(.95,.8,.3)),'pie':dict(size=(.42,.42,.1),carry='both',color=(.85,.55,.22)),'letter':dict(size=(.2,.14,.02),carry='R',color=(.95,.95,.9)),'egg':dict(size=(.14,.14,.2),carry='both',color=(.9,.85,.7)),'map':dict(size=(.3,.2,.02),carry='R',color=(.85,.75,.5)),
 'cart_load':dict(size=(.9,.6,.5),carry=None,color=(.6,.5,.3)),'boulder':dict(size=(.8,.8,.7),carry=None,color=(.5,.5,.5)),'door_big':dict(size=(.2,1.3,1.9),carry=None,color=(.45,.3,.18)),
}
# ---------------------------------------------------------------------------------------------------------------- object recipes
def _p(shape,name,loc,scale,color,rot=(0,0,0),emit=0.,kw=None):return dict(shape=shape,name=name,loc=tuple(loc),scale=tuple(scale),rot=tuple(rot),color=tuple(color),emit=emit,kw=dict(kw or {}))
def _shade(c,k):return tuple(max(0,min(1,x*k)) for x in c)
def recipe(kind,o):
 """local primitives for one object (origin at the floor, +x right, +y forward, units metres); returns (prims, footprint) where footprint is ('box',w,d) or ('circle',r) or None"""
 s=o.get('size',1.);c=o.get('color');n=lambda t:'%s_%s'%(o['id'],t);W=[]
 if kind=='house':
  w,d,h=5*s,4*s,3*s;c=c or (.8,.7,.55);W=[_p('cube',n('walls'),(0,0,h/2),(w/2,d/2,h/2),c),_p('cone',n('roof'),(0,0,h+.9*s),(w*.78,d*.95,.9*s),_shade(c,.55) if not o.get('roof') else o['roof'],(0,0,PI/4),kw=dict(vertices=4)),_p('cube',n('door'),(0,-d/2-.01,1.0*s),(.45*s,.03,1.0*s),(.35,.22,.12)),_p('cube',n('window'),(w/2*.55,-d/2-.01,1.8*s),(.4*s,.03,.35*s),(.7,.85,1.),emit=o.get('lit',0.))];fp=('box',w,d)
 elif kind=='tower':
  h=7*s;c=c or (.62,.6,.58);W=[_p('cyl',n('shaft'),(0,0,h/2),(1.5*s,1.5*s,h/2),c),_p('cone',n('cap'),(0,0,h+1.1*s),(1.9*s,1.9*s,1.1*s),_shade(c,.6),kw=dict(vertices=12))];fp=('circle',1.5*s)
 elif kind=='tree':
  c=c or (.2,.5,.2);h=3.2*s;W=[_p('cyl',n('trunk'),(0,0,h*.35),(.18*s,.18*s,h*.35),(.4,.28,.16)),_p('sphere',n('crown'),(0,0,h*.85),(1.3*s,1.3*s,1.1*s),c),_p('sphere',n('crown2'),(.5*s,.3*s,h*1.05),(.9*s,.9*s,.8*s),_shade(c,1.15))];fp=('circle',.4*s)
 elif kind=='pine':
  c=c or (.1,.38,.2);h=4*s;W=[_p('cyl',n('trunk'),(0,0,.4*s),(.14*s,.14*s,.4*s),(.35,.24,.14))]+[_p('cone',n('c%d'%i),(0,0,(1.0+i*1.05)*s),((1.35-i*.33)*s,(1.35-i*.33)*s,.9*s),_shade(c,1+i*.08),kw=dict(vertices=10)) for i in range(3)];fp=('circle',.35*s)
 elif kind=='rock':
  c=c or (.5,.5,.52);W=[_p('sphere',n('r'),(0,0,.45*s),(.9*s,.75*s,.6*s),c)];fp=('circle',.8*s)
 elif kind=='bush':
  c=c or (.22,.5,.25);W=[_p('sphere',n('b'),(0,0,.4*s),(.7*s,.7*s,.45*s),c)];fp=('circle',.5*s)
 elif kind=='wall':
  c=c or (.6,.58,.55);L=math.hypot(o['to'][0]-o['at'][0],o['to'][1]-o['at'][1]);h=o.get('height',1.6)*s;W=[_p('cube',n('w'),(L/2,0,h/2),(L/2,.25*s,h/2),c)];fp=('segment',L,.3*s)
 elif kind=='fence':
  c=c or (.55,.4,.25);L=math.hypot(o['to'][0]-o['at'][0],o['to'][1]-o['at'][1]);k=max(2,int(L/1.2));W=[_p('cube',n('rail'),(L/2,0,.8),(L/2,.03,.05),c),_p('cube',n('rail2'),(L/2,0,.45),(L/2,.03,.05),c)]+[_p('cube',n('p%d'%i),(L*i/k,0,.5),(.05,.05,.5),c) for i in range(k+1)];fp=('segment',L,.1)
 elif kind=='table':
  c=c or (.5,.34,.2);w,d=(o.get('w',1.8)*s,o.get('d',.9)*s);W=[_p('cube',n('top'),(0,0,.78),(w/2,d/2,.04),c)]+[_p('cube',n('l%d'%i),(sx*(w/2-.1),sy*(d/2-.1),.38),(.05,.05,.38),_shade(c,.8)) for i,(sx,sy) in enumerate(((1,1),(1,-1),(-1,1),(-1,-1)))];fp=('box',w,d)
 elif kind=='stool':
  c=c or (.5,.34,.2);W=[_p('cyl',n('seat'),(0,0,.3),(.2,.2,.03),c),_p('cyl',n('leg'),(0,0,.15),(.05,.05,.15),_shade(c,.8))];fp=('circle',.25)
 elif kind=='chair':
  c=c or (.5,.34,.2);W=[_p('cube',n('seat'),(0,0,.3),(.24,.24,.03),c),_p('cube',n('back'),(0,.24,.6),(.24,.02,.3),c)]+[_p('cube',n('l%d'%i),(sx*.2,sy*.2,.15),(.025,.025,.15),_shade(c,.8)) for i,(sx,sy) in enumerate(((1,1),(1,-1),(-1,1),(-1,-1)))];fp=('circle',.3)
 elif kind=='bench':
  c=c or (.5,.34,.2);w=o.get('w',1.8)*s;W=[_p('cube',n('seat'),(0,0,.3),(w/2,.22,.03),c),_p('cube',n('l1'),(-w/2+.15,0,.15),(.04,.18,.15),_shade(c,.8)),_p('cube',n('l2'),(w/2-.15,0,.15),(.04,.18,.15),_shade(c,.8))];fp=('box',w,.45)
 elif kind=='log':
  c=c or (.42,.3,.18);w=o.get('w',1.8)*s;W=[_p('cyl',n('l'),(0,0,.17),(.17,.17,w/2),c,(0,PI/2,0))];fp=('box',w,.35)
 elif kind=='campfire':
  W=[_p('cyl',n('stone%d'%i),(math.cos(i*PI/3)*.45,math.sin(i*PI/3)*.45,.08),(.1,.1,.08),(.45,.45,.47)) for i in range(6)]+[_p('cone',n('flame'),(0,0,.32),(.2,.2,.3),(1.,.55,.15),emit=3.,kw=dict(vertices=8)),_p('cube',n('wood'),(0,0,.1),(.28,.05,.05),(.3,.2,.12),(0,0,.6)),_p('cube',n('wood2'),(0,0,.1),(.28,.05,.05),(.3,.2,.12),(0,0,-.6))];fp=('circle',.55)
 elif kind=='crate':
  c=c or (.55,.38,.2);W=[_p('cube',n('c'),(0,0,.25*s),(.25*s,.25*s,.25*s),c)];fp=('box',.5*s,.5*s)
 elif kind=='barrel':
  c=c or (.45,.3,.18);W=[_p('cyl',n('b'),(0,0,.45*s),(.3*s,.3*s,.45*s),c),_p('cyl',n('band'),(0,0,.45*s),(.31*s,.31*s,.04),(.25,.25,.28))];fp=('circle',.32*s)
 elif kind=='lamp':
  W=[_p('cyl',n('post'),(0,0,1.4),(.05,.05,1.4),(.2,.2,.22)),_p('sphere',n('bulb'),(0,0,2.9),(.17,.17,.2),(1.,.85,.5),emit=o.get('lit',3.)),('light',n('light'),(0,0,2.9),o.get('energy',120.),(1.,.8,.5))];fp=('circle',.12)
 elif kind=='pillar':
  c=c or (.78,.76,.72);h=o.get('height',3.5)*s;W=[_p('cyl',n('p'),(0,0,h/2),(.35*s,.35*s,h/2),c,kw=dict(vertices=12)),_p('cube',n('cap'),(0,0,h+.05),(.45*s,.45*s,.06),c)];fp=('circle',.38*s)
 elif kind=='arch':
  c=c or (.7,.68,.64);W=[_p('cube',n('l'),(-1.2*s,0,1.5*s),(.3*s,.3*s,1.5*s),c),_p('cube',n('r'),(1.2*s,0,1.5*s),(.3*s,.3*s,1.5*s),c),_p('cube',n('top'),(0,0,3.2*s),(1.6*s,.3*s,.25*s),c)];fp=('pair',(-1.2*s,0,.35*s),(1.2*s,0,.35*s))
 elif kind=='tent':
  c=c or (.8,.35,.3);W=[_p('cone',n('t'),(0,0,1.0*s),(1.7*s,1.7*s,1.0*s),c,(0,0,PI/4),kw=dict(vertices=4))];fp=('circle',1.2*s)
 elif kind=='stall':
  c=c or (.75,.3,.25);W=[_p('cube',n('counter'),(0,0,.5),(1.2*s,.5*s,.5),(.5,.36,.22)),_p('cube',n('awning'),(0,.1,2.2),(1.4*s,.9*s,.05),c,(.25,0,0)),_p('cyl',n('p1'),(-1.25*s,-.5*s,1.1),(.04,.04,1.1),(.4,.3,.2)),_p('cyl',n('p2'),(1.25*s,-.5*s,1.1),(.04,.04,1.1),(.4,.3,.2))];fp=('box',2.4*s,1.0*s)
 elif kind=='boat':
  c=c or (.5,.33,.2);W=[_p('cube',n('hull'),(0,0,.35),(.9*s,2.2*s,.35),c),_p('cone',n('bow'),(0,2.35*s,.35),(.9*s,.9*s,.35),c,(PI/2,0,0),kw=dict(vertices=4)),_p('cyl',n('mast'),(0,.3,2.0),(.06,.06,1.7),(.4,.3,.2)),_p('cube',n('sail'),(0,.3,2.4),(.02,.7*s,1.0),(.95,.93,.85))];fp=('box',1.8*s,4.4*s)
 elif kind=='well':
  c=c or (.55,.54,.52);W=[_p('cyl',n('ring'),(0,0,.4),(.7,.7,.4),c,kw=dict(vertices=14)),_p('cyl',n('hole'),(0,0,.82),(.52,.52,.01),(.05,.08,.12)),_p('cube',n('p1'),(-.7,0,1.3),(.05,.05,.9),(.4,.28,.16)),_p('cube',n('p2'),(.7,0,1.3),(.05,.05,.9),(.4,.28,.16)),_p('cube',n('roof'),(0,0,2.2),(.9,.5,.05),(.5,.3,.2))];fp=('circle',.75)
 elif kind=='statue':
  c=c or (.7,.7,.72);W=[_p('cube',n('base'),(0,0,.4),(.5*s,.5*s,.4),c),_p('cyl',n('body'),(0,0,1.5*s),(.28*s,.28*s,.7*s),c),_p('sphere',n('head'),(0,0,2.45*s),(.25*s,.25*s,.28*s),c)];fp=('circle',.55*s)
 elif kind=='haystack':
  c=c or (.85,.72,.3);W=[_p('cone',n('h'),(0,0,.8*s),(1.0*s,1.0*s,.8*s),c,kw=dict(vertices=10))];fp=('circle',1.0*s)
 elif kind=='sign':
  W=[_p('cyl',n('p'),(0,0,.8),(.04,.04,.8),(.4,.3,.2)),_p('cube',n('b'),(0,0,1.45),(.45,.03,.2),c or (.7,.55,.3))];fp=('circle',.1)
 elif kind=='cart':
  c=c or (.5,.35,.2);W=[_p('cube',n('bed'),(0,0,.6),(.6,1.0,.2),c)]+[_p('cyl',n('w%d'%i),(sx*.65,0,.35),(.35,.35,.04),_shade(c,.7),(0,PI/2,0)) for i,sx in enumerate((-1,1))];fp=('box',1.4,2.0)
 elif kind=='anvil':
  W=[_p('cube',n('a'),(0,0,.55),(.35,.18,.1),(.25,.25,.28)),_p('cube',n('b'),(0,0,.3),(.2,.14,.3),(.2,.2,.22))];fp=('circle',.4)
 elif kind=='shelf':
  c=c or (.45,.3,.18);W=[_p('cube',n('s'),(0,0,1.0),(.8*s,.2,1.0),c)]+[_p('cube',n('p%d'%i),(0,-.15,.4+i*.5),(.75*s,.08,.025),_shade(c,1.3)) for i in range(4)];fp=('box',1.6*s,.4)
 elif kind=='bed':
  W=[_p('cube',n('f'),(0,0,.3),(.5,1.0,.25),c or (.45,.3,.18)),_p('cube',n('m'),(0,0,.6),(.46,.95,.08),(.85,.85,.9))];fp=('box',1.0,2.0)
 elif kind=='throne':
  c=c or (.6,.15,.18);W=[_p('cube',n('seat'),(0,0,.3),(.4,.4,.3),(.6,.5,.2)),_p('cube',n('back'),(0,.38,1.2),(.4,.05,.9),c),_p('cube',n('a1'),(-.42,0,.6),(.05,.35,.05),(.6,.5,.2)),_p('cube',n('a2'),(.42,0,.6),(.05,.35,.05),(.6,.5,.2))];fp=('box',.9,.9)
 elif kind=='platform':
  c=c or (.5,.45,.4);w,d,h=o.get('w',4)*s,o.get('d',3)*s,o.get('height',.4);W=[_p('cube',n('p'),(0,0,h/2),(w/2,d/2,h/2),c)];fp=None
 elif kind=='pedestal':
  c=c or (.7,.7,.72);h=o.get('height',.9);W=[_p('cube',n('p'),(0,0,h/2),(.3*s,.3*s,h/2),c)];fp=('box',.6*s,.6*s)
 elif kind=='cloud':
  W=[_p('sphere',n('c%d'%i),(i*.9-.9,0,0),(1.2,.9,.5),(.95,.95,.98)) for i in range(3)];fp=None
 elif kind=='path':
  c=c or (.62,.52,.38);L=math.hypot(o['to'][0]-o['at'][0],o['to'][1]-o['at'][1]);zq=.012+.004*(int(abs(o['at'][0]*7+o['at'][1]*13+o['to'][0]*3+o['to'][1]*5))%6);W=[_p('cube',n('p'),(L/2,0,zq),(L/2,o.get('width',1.2)/2,.012),c)];fp=None   # every path a different height: crossing paths never share a top face (no flicker where they meet)
 elif kind=='mountain':
  c=c or (.45,.45,.5);W=[_p('cone',n('m'),(0,0,6*s),(12*s,12*s,6*s),c,kw=dict(vertices=8)),_p('cone',n('snow'),(0,0,10.2*s),(4.5*s,4.5*s,2*s),(.95,.95,1.),kw=dict(vertices=8))];fp=('circle',12*s*.55)
 else:raise ValueError('unknown object kind %r'%kind)
 return W,fp
KINDS=('house','tower','tree','pine','rock','bush','wall','fence','table','stool','chair','bench','log','campfire','crate','barrel','lamp','pillar','arch','tent','stall','boat','well','statue','haystack','sign','cart','anvil','shelf','bed','throne','platform','pedestal','cloud','path','mountain')
SEAT_KINDS={'stool':[(0,0,.3)],'chair':[(0,0,.3)],'bench':'bench','log':'bench','throne':[(0,0,.3)],'bed':[(0,0,.45)]}
SURFACE_KINDS={'bench':.35,'table':.8,'crate':.5,'barrel':.9,'pedestal':None,'anvil':.65,'platform':None,'stall':1.0,'shelf':None,'well':.82,'statue':.8}
def _rot(x,y,a):c,s=math.cos(a),math.sin(a);return x*c-y*s,x*s+y*c
def normalise(loc):
 """objects with ids and defaults; the preset (if any) is expanded; returns a new dict"""
 loc=dict(loc);objs=[]
 if loc.get('preset'):
  if loc['preset'] not in PRESETS:raise ValueError('unknown location preset %r (known: %s)'%(loc['preset'],', '.join(sorted(PRESETS))))
  base=PRESETS[loc['preset']](random.Random(loc.get('seed',1)),loc);objs+=base.get('objects',[])
  for k in ('ground','half','water','markers','floor','sky','inside'):
   if k in base and k not in loc:loc[k]=base[k]
  loc['markers']=dict(base.get('markers',{}),**loc.get('markers',{}))
 if loc.get('dress',True) and loc.get('preset') in DRESS:
  kinds,n,r0,r1=DRESS[loc['preset']];objs+=_ring(random.Random(loc.get('seed',1)*7+3),kinds,n,0,0,r0,r1)    # a living edge: trees, rocks, barrels and lamps round the playing area
 objs+=loc.get('objects',[]);out=[];count={}
 for o in objs:
  o=dict(o);k=o['kind']
  if k not in KINDS:raise ValueError('unknown object kind %r'%k)
  count[k]=count.get(k,0)+1;o.setdefault('id','%s%d'%(k,count[k]));o.setdefault('at',[0,0]);o.setdefault('yaw',0.);o.setdefault('size',1.);out.append(o)
 ids=[o['id'] for o in out]
 if len(set(ids))!=len(ids):raise ValueError('duplicate object ids in the location: %s'%sorted({i for i in ids if ids.count(i)>1}))
 loc['objects']=out;loc.pop('preset',None);loc.setdefault('ground',(.35,.5,.3));loc.setdefault('half',(30,30));loc.setdefault('markers',{});loc.setdefault('floor','grass');return loc
def footprint_circles(o,fp):
 """circles (x,y,r) covering the footprint of an object placed at o['at'] with yaw"""
 if fp is None:return []
 x0,y0=o['at'];a=math.radians(o['yaw']);out=[]
 if fp[0]=='circle':return [(x0,y0,fp[1])]
 if fp[0]=='pair':
  for (lx,ly,r) in fp[1:]:dx,dy=_rot(lx,ly,a);out.append((x0+dx,y0+dy,r))
  return out
 if fp[0]=='segment':
  L,t=fp[1],fp[2];ex,ey=o['to'];n=max(1,int(math.ceil(L/max(.3,t*1.6))));return [(x0+(ex-x0)*i/n,y0+(ey-y0)*i/n,max(.25,t*.9)) for i in range(n+1)]
 w,d=fp[1],fp[2];long_,short=max(w,d),min(w,d);r=max(.12,short/2*.95);n=max(1,int(math.ceil(long_/(r*1.2))))
 for i in range(n+1):
  u=-long_/2+r+(long_-2*r)*(i/n) if long_>2*r else 0.
  lx,ly=(u,0) if w>=d else (0,u);dx,dy=_rot(lx,ly,a);out.append((x0+dx,y0+dy,r))
 return out
def layout(loc):
 loc=normalise(loc);obst=[];seats={};surf={};per={}
 for o in loc['objects']:
  W,fp=recipe(o['kind'],o);cs=footprint_circles(o,fp);per[o['id']]=cs
  if o['kind'] not in ('path','cloud','platform'):obst+=cs
  a=math.radians(o['yaw']);k=o['kind'];s=o.get('size',1.)
  if k in SEAT_KINDS:
   spec=SEAT_KINDS[k]
   if spec=='bench':
    w=o.get('w',1.8)*s;n=max(1,int(w/.7));spec=[(-w/2+w*(i+.5)/n,0,.3) for i in range(n)]
   for i,(lx,ly,z) in enumerate(spec):
    dx,dy=_rot(lx,ly,a);seats['%s.%d'%(o['id'],i)]=(o['at'][0]+dx,o['at'][1]+dy,z*s if k!='bed' else z)
  if k in SURFACE_KINDS:
   top=SURFACE_KINDS[k]
   if k=='pedestal':top=o.get('height',.9)
   if k=='platform':top=o.get('height',.4)
   if top:r=max(.3,(fp[1]/2) if fp and fp[0]=='box' else (fp[1] if fp else .3));surf[o['id']]=(o['at'][0],o['at'][1],top,r)
 walls=[c for o in loc['objects'] if o['kind']=='wall' for c in per[o['id']]]
 return dict(walls=walls,inside=loc.get('inside'),obstacles=obst,seats=seats,surfaces=surf,markers={k:tuple(v) for k,v in loc['markers'].items()},half=tuple(loc['half']),objects=loc['objects'],loc=loc,per_object=per)
def prims(loc):
 """primitive dicts for every object, in world space (yaw and position applied), plus ('light', ...) tuples"""
 loc=normalise(loc);out=[]
 for o in loc['objects']:
  W,fp=recipe(o['kind'],o);a=math.radians(o['yaw'])
  if o['kind'] in ('wall','fence','path'):a=math.atan2(o['to'][1]-o['at'][1],o['to'][0]-o['at'][0])
  for p in W:
   if isinstance(p,tuple):
    lx,ly,lz=p[2];dx,dy=_rot(lx,ly,a);out.append(('light',p[1],(o['at'][0]+dx,o['at'][1]+dy,lz),p[3],p[4]));continue
   lx,ly,lz=p['loc'];dx,dy=_rot(lx,ly,a);q=dict(p);q['loc']=(o['at'][0]+dx,o['at'][1]+dy,lz+o.get('z',0.));r=list(p['rot']);r[2]+=a;q['rot']=tuple(r);out.append(q)
 return out
def floor_z(loc,x,y):return 0.
DRESS={'village_square':(['tree','bush','rock','haystack','barrel','crate','tree'],18,20,28),'market':(['barrel','crate','bush','tree','haystack'],14,19,26),'harbor':(['crate','barrel','rock','bush','crate'],10,20,27),'meadow':(['tree','bush','rock','log','tree','pine'],14,17,29),'hilltop':(['rock','bush','pine','tree'],8,14,24),'forest_clearing':(['tree','pine','bush','rock'],12,18,28)}
def blocked(lay,x,y,margin=0.):return any(math.hypot(x-cx,y-cy)<r+margin for cx,cy,r in lay['obstacles'])
# ---------------------------------------------------------------------------------------------------------------- presets (generators of small object lists)
def _scatter(rnd,kinds,n,xr,yr,avoid=(),gap=2.5,**kw):
 out=[];tries=0
 while len(out)<n and tries<n*30:
  tries+=1;x,y=rnd.uniform(*xr),rnd.uniform(*yr)
  if any(math.hypot(x-ax,y-ay)<ar for ax,ay,ar in avoid) or any(math.hypot(x-o['at'][0],y-o['at'][1])<gap for o in out):continue
  out.append(dict(kind=rnd.choice(kinds),at=[round(x,2),round(y,2)],yaw=rnd.uniform(0,360),size=round(rnd.uniform(.8,1.3),2),**kw))
 return out
def _ring(rnd,kinds,n,cx,cy,r0,r1,**kw):
 out=[]
 for i in range(n):
  a=2*PI*i/n+rnd.uniform(-.2,.2);r=rnd.uniform(r0,r1);out.append(dict(dict(kind=rnd.choice(kinds),at=[round(cx+math.cos(a)*r,2),round(cy+math.sin(a)*r,2)],yaw=rnd.uniform(0,360),size=round(rnd.uniform(.9,1.4),2)),**kw))
 return out
def forest_clearing(rnd,p):
 o=_ring(rnd,['pine','tree','pine','bush','rock'],22,0,0,12,20)+_scatter(rnd,['bush','rock'],5,(-9,9),(-9,9),avoid=[(0,0,4)],gap=4)
 return dict(objects=o,ground=(.25,.42,.22),half=(30,30),markers=dict(center=(0,0),edge=(10,0),far=(-12,6)))
def campfire_night(rnd,p):
 b=forest_clearing(rnd,p);b['objects']+=[dict(kind='campfire',at=[0,0],id='fire'),dict(kind='log',at=[-2.2,0.2],yaw=90,id='log_w'),dict(kind='log',at=[2.2,0.2],yaw=90,id='log_e'),dict(kind='log',at=[0,-2.3],yaw=0,id='log_s')];b['markers'].update(fire=(0,0));return b
def village_square(rnd,p):
 o=[dict(kind='house',at=[-11,8],yaw=0,id='house_a',color=(.85,.72,.5)),dict(kind='house',at=[9,10],yaw=10,id='house_b',color=(.7,.6,.5)),dict(kind='house',at=[-13,-6],yaw=90,id='house_c',color=(.78,.6,.45)),dict(kind='house',at=[13,-5],yaw=-80,id='house_d',color=(.6,.65,.7)),
  dict(kind='well',at=[0,0],id='well'),dict(kind='bench',at=[-4,-3.5],id='bench_a'),dict(kind='bench',at=[4,-3.5],id='bench_b'),dict(kind='lamp',at=[-6,3],id='lamp_a'),dict(kind='lamp',at=[6,3],id='lamp_b'),dict(kind='tree',at=[-16,14]),dict(kind='tree',at=[17,12]),dict(kind='crate',at=[-9.5,4],id='crate_a'),dict(kind='barrel',at=[-9,4.6]),
  dict(kind='path',at=[-18,0],to=[18,0],width=2.4),dict(kind='path',at=[0,-18],to=[0,14],width=2.0)]
 return dict(objects=o,ground=(.4,.55,.3),half=(30,24),markers=dict(center=(0,0),well=(0,0),north=(0,9),south=(0,-10),east=(11,0),west=(-11,0)))
def market(rnd,p):
 o=[dict(kind='stall',at=[-8+5.5*i,5],yaw=0,id='stall%d'%i,color=c) for i,c in enumerate(((.75,.3,.25),(.25,.5,.7),(.8,.65,.2),(.3,.6,.35)))]+[dict(kind='crate',at=[-9,3.5]),dict(kind='barrel',at=[3,3.2]),dict(kind='cart',at=[-4,-5],yaw=20,id='cart'),dict(kind='lamp',at=[-5,0]),dict(kind='lamp',at=[5,0]),
  dict(kind='house',at=[-12,14],id='shop_a',color=(.8,.7,.6)),dict(kind='house',at=[8,15],id='shop_b',color=(.65,.55,.45)),dict(kind='bench',at=[8,-4],id='bench_a'),dict(kind='crate',at=[1,3.2],size=.8)]
 return dict(objects=o,ground=(.5,.46,.38),half=(26,22),markers=dict(center=(0,-1),stalls=(0,3),far=(0,-12)))
def hall(rnd,p):
 o=[dict(kind='wall',at=[-12,-9],to=[12,-9],id='wall_s',height=4),dict(kind='wall',at=[-12,9],to=[12,9],id='wall_n',height=4),dict(kind='wall',at=[-12,-9],to=[-12,9],id='wall_w',height=4),dict(kind='wall',at=[12,-9],to=[12,9],id='wall_e',height=4)]
 o+=[dict(kind='pillar',at=[x,y],id='pil%d%d'%(i,j)) for i,x in enumerate((-7,7)) for j,y in enumerate((-5,5))]+[dict(kind='table',at=[0,0],id='table',w=6,d=1.4)]+[dict(kind='chair',at=[x,y],yaw=90 if y>0 else -90,id='chair_%d_%d'%(i,j)) for i,x in enumerate((-2,0,2)) for j,y in enumerate((-1.3,1.3))]
 o+=[dict(kind='throne',at=[0,7.2],yaw=180,id='throne'),dict(kind='lamp',at=[-11,0],id='lamp_w',energy=60,lit=2),dict(kind='lamp',at=[11,0],id='lamp_e',energy=60,lit=2)]
 return dict(objects=o,ground=(.45,.4,.36),half=(14,11),floor='stone',inside=[-11.3,-8.3,11.3,8.3],markers=dict(center=(0,0),door=(0,-8),throne=(0,6),west=(-9,0),east=(9,0)))
def room(rnd,p):
 o=[dict(kind='wall',at=[-5,-4],to=[5,-4],id='wall_s',height=3,color=(.7,.62,.5)),dict(kind='wall',at=[-5,4],to=[5,4],id='wall_n',height=3,color=(.7,.62,.5)),dict(kind='wall',at=[-5,-4],to=[-5,4],id='wall_w',height=3,color=(.7,.62,.5)),dict(kind='wall',at=[5,-4],to=[5,4],id='wall_e',height=3,color=(.7,.62,.5)),
  dict(kind='table',at=[1,0],id='table',w=2.2,d=1.0),dict(kind='stool',at=[-.5,1.1],id='stool_a'),dict(kind='stool',at=[2.5,1.1],id='stool_b'),dict(kind='shelf',at=[-3,3.6],id='shelf'),dict(kind='bed',at=[3.8,2.6],id='bed'),dict(kind='lamp',at=[-4.3,-3.3],energy=40,lit=2,id='lamp')]
 return dict(objects=o,ground=(.5,.4,.3),half=(7,6),floor='wood',inside=[-4.4,-3.4,4.4,3.4],markers=dict(center=(0,0),door=(0,-3.5),table=(1,-1.0),window=(-3.5,0)))
def ruins(rnd,p):
 o=[dict(kind='pillar',at=[x,y],id='pil%d'%i,height=rnd.uniform(1.5,4)) for i,(x,y) in enumerate(((-6,-5),(-6,2),(5,-6),(6,3),(0,8),(-2,-9)))]+[dict(kind='wall',at=[-9,6],to=[-3,9],height=2,id='wall_a'),dict(kind='wall',at=[4,9],to=[10,5],height=1.4,id='wall_b'),dict(kind='arch',at=[0,-10],id='arch'),dict(kind='statue',at=[0,0],id='statue'),dict(kind='rock',at=[-8,-2]),dict(kind='rock',at=[8,-1])]
 return dict(objects=o+_scatter(rnd,['bush','rock'],8,(-14,14),(-14,14),avoid=[(0,0,3)],gap=3),ground=(.45,.5,.38),half=(24,24),markers=dict(center=(0,-3),statue=(0,0),arch=(0,-8)))
def harbor(rnd,p):
 o=[dict(kind='boat',at=[6,-12],yaw=80,id='boat'),dict(kind='boat',at=[-8,-13],yaw=100,id='boat2',color=(.4,.28,.2)),dict(kind='platform',at=[0,-4],w=30,d=6,height=.05,id='quay',color=(.55,.5,.45)),dict(kind='crate',at=[-5,-2],id='crate_a'),dict(kind='crate',at=[-4.4,-2],id='crate_b',size=.9),dict(kind='barrel',at=[3,-2]),dict(kind='barrel',at=[3.7,-2.3]),
  dict(kind='house',at=[-10,8],id='house_a'),dict(kind='house',at=[8,9],id='house_b',color=(.6,.7,.8)),dict(kind='lamp',at=[-2,-1]),dict(kind='lamp',at=[5,-1]),dict(kind='bench',at=[0,1],id='bench'),dict(kind='sign',at=[-6,1],id='sign')]
 return dict(objects=o,ground=(.5,.46,.4),half=(30,26),water=[-40,-40,40,-6],markers=dict(center=(0,0),quay=(0,-3),boat=(6,-7)))
def hilltop(rnd,p):
 return dict(objects=[dict(kind='tree',at=[-5,3],id='tree'),dict(kind='rock',at=[4,-2]),dict(kind='rock',at=[-2,-6],size=.7),dict(kind='bush',at=[6,5]),dict(kind='sign',at=[1,6],id='sign')]+[dict(kind='mountain',at=[x,40],size=s,id='mtn%d'%i) for i,(x,s) in enumerate(((-40,2.2),(0,3),(45,2.5)))],ground=(.4,.55,.3),half=(28,28),markers=dict(center=(0,0),edge=(10,12),view=(0,10)))
def courtyard(rnd,p):
 o=[dict(kind='wall',at=[-14,-10],to=[14,-10],id='wall_s',height=3.5),dict(kind='wall',at=[-14,10],to=[14,10],id='wall_n',height=3.5),dict(kind='wall',at=[-14,-10],to=[-14,10],id='wall_w',height=3.5),dict(kind='wall',at=[14,-10],to=[14,10],id='wall_e',height=3.5),dict(kind='tower',at=[-14,-10],id='tower_a'),dict(kind='tower',at=[14,10],id='tower_b'),
  dict(kind='well',at=[0,0],id='well'),dict(kind='bench',at=[-6,-4],id='bench_a'),dict(kind='statue',at=[8,4],id='statue'),dict(kind='haystack',at=[-10,6]),dict(kind='crate',at=[10,-7]),dict(kind='lamp',at=[-4,5]),dict(kind='lamp',at=[5,-5])]
 return dict(objects=o,ground=(.5,.48,.42),half=(16,12),floor='stone',inside=[-13.3,-9.3,13.3,9.3],markers=dict(center=(0,0),gate=(0,-9),well=(0,0)))
def workshop(rnd,p):
 b=room(rnd,p);b['objects']+=[dict(kind='anvil',at=[-3,-1],id='anvil'),dict(kind='crate',at=[3.6,-2.6],id='crate_w'),dict(kind='barrel',at=[-4.2,-2.8])];return b
def cave(rnd,p):
 o=_ring(rnd,['rock','rock','rock'],26,0,0,9,12,size=2.2)+[dict(kind='rock',at=[-4,3]),dict(kind='rock',at=[5,-3]),dict(kind='pedestal',at=[0,6],id='altar',height=1.0),dict(kind='campfire',at=[-5,-4],id='fire')]
 return dict(objects=o,ground=(.28,.25,.24),half=(14,14),floor='stone',inside=[-7.4,-7.4,7.4,7.4],markers=dict(center=(0,0),altar=(0,5),mouth=(0,-10)))
def meadow(rnd,p):
 return dict(objects=_scatter(rnd,['tree','bush','rock'],14,(-24,24),(-24,24),avoid=[(0,0,6)],gap=5)+[dict(kind='haystack',at=[8,5]),dict(kind='fence',at=[-12,-8],to=[12,-8],id='fence'),dict(kind='log',at=[-3,2],yaw=20,id='log')],ground=(.42,.6,.3),half=(30,26),markers=dict(center=(0,0),east=(9,0),west=(-9,0),far=(0,14)))
PRESETS=dict(forest_clearing=forest_clearing,campfire_night=campfire_night,village_square=village_square,market=market,hall=hall,room=room,ruins=ruins,harbor=harbor,hilltop=hilltop,courtyard=courtyard,workshop=workshop,cave=cave,meadow=meadow)
# ---------------------------------------------------------------------------------------------------------------- Blender
def _ground_texture(ob,base):
 """soft patches of lighter and darker ground and a fine grain (procedural, visible in the lit view and in renders)"""
 import bpy
 m=ob.active_material
 if m is None or not m.use_nodes:return
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 if bs is None:return
 tc=nt.nodes.new('ShaderNodeTexCoord');n1=nt.nodes.new('ShaderNodeTexNoise');n2=nt.nodes.new('ShaderNodeTexNoise');mx=nt.nodes.new('ShaderNodeMix');cr=nt.nodes.new('ShaderNodeValToRGB');bm=nt.nodes.new('ShaderNodeBump')
 n1.inputs['Scale'].default_value=.18;n1.inputs['Detail'].default_value=3.;n2.inputs['Scale'].default_value=6.;n2.inputs['Detail'].default_value=6.
 sat=lambda c,k:tuple(max(0.,min(1.,m_+(x-m_)*k)) for x in c for m_ in [sum(c)/3]);bs.inputs['Base Color'].default_value=(*sat(base,1.4),1);cr.color_ramp.elements[0].color=(*[c*.7 for c in sat(base,1.4)],1);cr.color_ramp.elements[1].color=(*[min(1.,c*1.2) for c in sat(base,1.4)],1)
 mx.data_type='RGBA';mx.blend_type='MULTIPLY';mx.inputs[0].default_value=.35;bm.inputs['Strength'].default_value=.25
 nt.links.new(tc.outputs['Object'],n1.inputs['Vector']);nt.links.new(tc.outputs['Object'],n2.inputs['Vector']);nt.links.new(n1.outputs['Fac'],cr.inputs[0]);nt.links.new(cr.outputs[0],mx.inputs[6]);nt.links.new(n2.outputs['Color'],mx.inputs[7]);nt.links.new(mx.outputs[2],bs.inputs['Base Color']);nt.links.new(n2.outputs['Fac'],bm.inputs['Height']);nt.links.new(bm.outputs[0],bs.inputs['Normal'])
def build(S,loc,time='day'):
 """create the location in the scene_base.Scene S: ground (and water), objects, lights, sun for the time of day; returns the normalised location"""
 import bpy
 import scene_params
 loc=normalise(loc);hx,hy=loc['half'];gr=S.prim('cube','Ground',(0,0,-.5),loc['ground'],scale=(hx+20,hy+20,.5));_ground_texture(gr,loc['ground'])
 if loc.get('water'):
  x0,y0,x1,y1=loc['water'];S.prim('cube','Water',((x0+x1)/2,(y0+y1)/2,-.12),(.2,.4,.6),scale=((x1-x0)/2,(y1-y0)/2,.1))
 for p in prims(loc):
  if isinstance(p,tuple):
   ld=bpy.data.lights.new(p[1],'POINT');ld.energy=p[3] if time in ('night','dusk','dawn') else p[3]*.2;ld.color=p[4];ld.shadow_soft_size=.3;lo=bpy.data.objects.new(p[1],ld);lo.location=p[2];S.link(lo);continue
  o=S.prim(p['shape'],p['name'],p['loc'],p['color'],scale=p['scale'],rot=p['rot'],emit=p['emit'] if (p['emit']<2.9 or time in ('night','dusk','dawn') or True) else 0.,**p['kw'])
 pr=scene_params.preset(time if time in scene_params.TIME_OF_DAY else 'day')
 lk=LOOK.get(time,LOOK['day']);az=math.radians(-40+20*(int(loc.get('seed',1))%5));el=math.radians(lk['el'])
 def sun(name,col,energy,elev,azim,ang):
  o=bpy.data.objects.new(name,bpy.data.lights.new(name,'SUN'));o.data.energy=energy;o.data.color=col;o.data.angle=ang;o.rotation_euler=(math.pi/2-elev,0,azim);S.link(o);return o
 sun('Sun',lk['key'],lk['ke'],el,az,math.radians(3))            # the key: low and coloured, long soft shadows
 sun('FillLight',lk['fill'],lk['fe'],math.radians(50),az+math.pi*.85,math.radians(30))    # a cool fill from the shadow side
 sun('RimLight',lk['rim'],lk['re'],math.radians(14),az+math.pi,math.radians(5))           # a low back light that edges every character
 S.world_color=pr['world']
 return loc
LOOK={'day':dict(key=(1.,.86,.64),ke=3.6,el=30,fill=(.5,.62,1.),fe=.4,rim=(1.,.78,.55),re=1.0),
 'dawn':dict(key=(1.,.7,.5),ke=2.6,el=14,fill=(.6,.55,.9),fe=.5,rim=(1.,.6,.5),re=1.4),
 'dusk':dict(key=(1.,.5,.28),ke=2.4,el=9,fill=(.45,.4,.85),fe=.5,rim=(1.,.45,.6),re=1.6),
 'night':dict(key=(.5,.6,1.),ke=.9,el=38,fill=(.2,.3,.7),fe=.3,rim=(.5,.65,1.),re=1.0),
 'overcast':dict(key=(.9,.93,1.),ke=1.5,el=55,fill=(.7,.75,.9),fe=.8,rim=(.9,.9,1.),re=.3)}
SKY={'dawn':((1.,.72,.5),(.3,.4,.8)),'day':((.8,.9,1.),(.2,.48,.95)),'dusk':((1.,.58,.32),(.25,.18,.55)),'night':((.12,.14,.3),(.01,.015,.06)),'overcast':((.7,.72,.78),(.42,.46,.55))}
def sky(sc,time,fog=0.):
 """a gradient sky (horizon to zenith) as the world, lit by the same colours; fog pulls the whole sky toward a flat grey"""
 import bpy
 hz,zn=SKY.get(time,SKY['day']);g=(.55,.58,.62)
 fog*=.55    # fog tints the sky but never washes it out
 hz=tuple(h*(1-fog)+g[i]*fog*(.6 if time=='night' else 1.) for i,h in enumerate(hz));zn=tuple(z*(1-fog)+g[i]*fog*(.6 if time=='night' else 1.) for i,z in enumerate(zn))
 w=bpy.data.worlds.new('Sky');w.use_nodes=True;nt=w.node_tree;nt.nodes.clear()
 tc=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');mp=nt.nodes.new('ShaderNodeMapRange');cr=nt.nodes.new('ShaderNodeValToRGB');bg=nt.nodes.new('ShaderNodeBackground');out=nt.nodes.new('ShaderNodeOutputWorld')
 mp.inputs['From Min'].default_value=-.05;mp.inputs['From Max'].default_value=.9;cr.color_ramp.elements[0].color=(*hz,1);cr.color_ramp.elements[1].color=(*zn,1);bg.inputs['Strength'].default_value=.45    # the sky lights softly; the sun and spot do the modelling
 nt.links.new(tc.outputs['Generated'],sep.inputs[0]);nt.links.new(sep.outputs['Z'],mp.inputs['Value']);nt.links.new(mp.outputs[0],cr.inputs[0]);nt.links.new(cr.outputs[0],bg.inputs['Color']);nt.links.new(bg.outputs[0],out.inputs['Surface'])
 w.color=hz;sc.world=w
 try:
  vs=sc.view_settings;vs.view_transform='AgX';vs.look='AgX - Punchy';vs.exposure={'day':-.2,'dawn':0.,'dusk':.05,'night':.5,'overcast':0.}.get(time,0.)    # a graded, punchy image
 except Exception:pass
