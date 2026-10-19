"""Shared locations and props: built ONCE into a bank file (bank/<id>_<state>_<params>_<hash>.blend, the hash covers only that builder, so editing one location does not rebuild the others) and appended into every scene that uses them.

  python locations.py build mountain_village intact      (run through Blender by ensure(); normally you never call this by hand)

Pure parts (no Blender needed): village_terrain(x, y), VILLAGE and CITADEL constants, REGISTRY (id, states, builder), bank_path, ensure.
Inside Blender: load(id, ctx, state) appends the cached objects (or builds them in place when the bank file is missing). The bank file name contains a hash of this module, so changing a location
invalidates its cache automatically. Objects carry custom properties: 'rb' = rigid-body shape ('BOX' or 'MESH') for passive colliders, 'blk' = (column, row) for the breach blocks of the citadel.
A state describes what happened to the place: mountain_village intact | buried (snow mounds), citadel intact | breached (breach section replaced by rubble)."""
import math,random,sys,hashlib,subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent;BANK=H/'bank';PI=math.pi
def village_terrain(x,y):
 n=.18*(math.sin(x*.9+y*.5)+math.sin(y*1.3-x*.4))
 if x<0:return .52*(-x)+n*(1+(-x)/20.)
 if x<94:return -.04*x+n*.5
 return -3.76
VILLAGE=dict(hall=(96.,116.,12.,3.,-3.8),stalls=[(34.,3.),(44.,-4.),(54.,2.),(64.,-3.)])
CITADEL=dict(wall=(29.3,30.7,9.),block=(2.,1.,1.4))
def _village(ctx,state):
 import bpy,bmesh
 import numpy as np
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(101);terrain=village_terrain
 HALL_X0,HALL_X1,HALL_HW=96.,116.,12.;GATE_HW=3.;DOOR_Z=-3.8
 bm=bmesh.new();xs=np.arange(-72,128,2.5);ys=np.arange(-46,47,2.5);gv=[[bm.verts.new((x,y,terrain(x,y))) for y in ys] for x in xs]
 for i in range(len(xs)-1):
  for j in range(len(ys)-1):bm.faces.new((gv[i][j],gv[i+1][j],gv[i+1][j+1],gv[i][j+1]))
 me=bpy.data.meshes.new('TerrainMesh');bm.to_mesh(me);bm.free();terr=bpy.data.objects.new('Terrain',me);link(terr);me.materials.append(mat('Snowfield',(.88,.9,.94)))
 for p in me.polygons:p.use_smooth=False
 passive=[(terr,'MESH')]
 def solid(name,center,half,color):
  o=prim('cube',name,center,color,scale=half);passive.append((o,'BOX'));return o
 # shelter hall (walls, roof) with a 6 m gate opening in the west wall
 z0=DOOR_Z;H=8.
 solid('HallWallFrontL',(HALL_X0,-(GATE_HW+(HALL_HW-GATE_HW)/2),z0+H/2),(.5,(HALL_HW-GATE_HW)/2,H/2),(.5,.46,.4))
 solid('HallWallFrontR',(HALL_X0,(GATE_HW+(HALL_HW-GATE_HW)/2),z0+H/2),(.5,(HALL_HW-GATE_HW)/2,H/2),(.5,.46,.4))
 solid('HallWallBack',(HALL_X1,0,z0+H/2),(.5,HALL_HW,H/2),(.5,.46,.4))
 for s_ in (-1,1):solid('HallWallSide',((HALL_X0+HALL_X1)/2,s_*HALL_HW,z0+H/2),((HALL_X1-HALL_X0)/2,.5,H/2),(.5,.46,.4))
 solid('HallRoof',((HALL_X0+HALL_X1)/2,0,z0+H+.4),((HALL_X1-HALL_X0)/2+1,HALL_HW+1,.4),(.4,.3,.25))
 solid('GateFrame',(HALL_X0,0,z0+H-.8),(.6,GATE_HW,.8),(.4,.35,.3))
 door=solid('SlidingDoor',(HALL_X0+.7,GATE_HW+GATE_HW,z0+2.6),(.15,GATE_HW,2.6),(.35,.22,.12));door.rigid_body if False else None
 huts=[]
 for i,x in enumerate(np.arange(26,72,6.)):
  for s_ in (-1,1):
   y=s_*rnd.uniform(11,18);zt=terrain(x,y);b=prim('cube','Hut',(x,y,zt+1.4),(.55,.38,.22),scale=(2.0,2.0,1.4));r=prim('cone','HutRoof',(x,y,zt+3.4),(.5,.2,.15),scale=(2.9,2.9,1.2),vertices=4,radius1=1,depth=2,rot=(0,0,PI/4));passive.append((b,'BOX'));huts.append((x,y))
 STALLS=[(34.,3.),(44.,-4.),(54.,2.),(64.,-3.)]
 for x,y in STALLS:o=prim('cube','Stall',(x,y,terrain(x,y)+.7),(.6,.4,.2),scale=(1.1,1.1,.7));passive.append((o,'BOX'));prim('cube','StallAwning',(x,y,terrain(x,y)+1.7),(.8,.2,.2),scale=(1.3,1.3,.06))
 for i in range(160):
  x=rnd.uniform(-40,92);y=rnd.choice((-1,1))*rnd.uniform(24,44);zt=terrain(x,y);prim('cone','Pine',(x,y,zt+2.6),(.07,.26,.14),scale=(1.3,1.3,2.8),vertices=7,radius1=1,depth=2);prim('cyl','Trunk',(x,y,zt+.5),(.3,.2,.1),scale=(.15,.15,.5),vertices=5,radius=1,depth=2)
 for i in range(30):prim('cone','Peak',(rnd.uniform(-130,-70),rnd.uniform(-90,90),rnd.uniform(15,40)),(.82,.84,.9),scale=(rnd.uniform(14,30),rnd.uniform(14,30),rnd.uniform(25,50)),vertices=7,radius1=1,depth=2)
 for o,sh in passive:o['rb']=sh
 if state=='buried':
  for i in range(60):
   x=rnd.uniform(24,76);y=rnd.uniform(-20,20);r=rnd.uniform(.8,2.4);prim('sphere','SnowMound',(x,y,terrain(x,y)+r*.3),(.93,.95,1),scale=(r*1.6,r*1.2,r*.6),subdivisions=1)
def _citadel(ctx,state):
 import bpy,bmesh
 import numpy as np
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(202)
 WY0,WY1,WH=29.3,30.7,9.;BLK=(2.,1.,1.4)
 bpy.ops.mesh.primitive_plane_add(size=1,location=(0,-30,-.05));g=bpy.context.object;g.scale=(400,260,1);g.name='Field';g.data.materials.append(mat('Field',(.36,.44,.22)))
 passive=[]
 def solid(name,center,half,color):
  o=prim('cube',name,center,color,scale=half);passive.append(o);return o
 STONE=(.58,.54,.47)
 solid('WallW',(-26,30,WH/2),(8,.7,WH/2),STONE);solid('WallE',(18.5,30,WH/2),(15.5,.7,WH/2),STONE);solid('WallMidW',(-4.5,30,WH/2),(1.5,.7,WH/2),STONE)
 for sx in (-5.5,5.5):
  for sy in (28.8,32.2):solid('GatePillar',(sx,sy,7.5),(.35,.35,7.5),(.5,.46,.4))
 solid('GateRoof',(0,30.5,14.2),(6.2,2.6,.8),(.45,.3,.22));solid('GateLintel',(0,30,6.6),(3,.7,.6),STONE)
 for x in (-34,34):
  prim('cyl','Tower',(x,30,7),(.52,.48,.42),scale=(5,5,7),vertices=12,radius=1,depth=2);prim('cone','TowerRoof',(x,30,15.5),(.5,.16,.14),scale=(5.6,5.6,2.8),vertices=12,radius1=1,depth=2)
 solid('KeepWall',(0,60,8),(14,.8,8),STONE);solid('KeepTower',(0,57,10),(4,4,10),(.5,.46,.4));prim('cone','KeepRoof',(0,57,22),(.5,.16,.14),scale=(4.6,4.6,3),vertices=8,radius1=1,depth=2)
 for s_ in (-1,1):solid('CourtWall',(s_*34,45,5),(.7,15,5),STONE)
 for i in range(14):x=rnd.uniform(-28,28);y=rnd.uniform(36,52);prim('cube','House',(x,y,1.5),(.55,.4,.25),scale=(2,2,1.5));prim('cone','HouseRoof',(x,y,3.6),(.5,.2,.15),scale=(3,3,1.2),vertices=4,radius1=1,depth=2,rot=(0,0,PI/4))
 # the breach section: 6 columns x 9 rows of blocks, x from -18 to -6
 BLOCKS=[]
 for c in range(6):
  for r in range(9):
   x=-17+c*2.;z=.5+r*1.;o=prim('cube','Block',(x,30,z),tuple(v*(.5+.02*((c+r)%2)) for v in (.58,.54,.47)) if False else ((.6,.56,.5) if (c+r)%2 else (.55,.5,.44)),scale=(BLK[0]/2-.02,BLK[2]/2-.02,BLK[1]/2-.02));BLOCKS.append((o,c,r))
 # gate: portcullis (bars) in the opening, on a rail
 port=prim('cube','PortcullisTop',(0,30,6.1),(.2,.2,.2),scale=(3,.15,.12))
 portbars=[port]
 for i,x in enumerate(np.linspace(-2.7,2.7,10)):portbars.append(prim('cube','PortBar',(x,30,3.0),(.22,.22,.22),scale=(.08,.12,3.0)))
 for z in (1.5,3.0,4.5):portbars.append(prim('cube','PortCross',(0,30,z),(.22,.22,.22),scale=(3,.1,.07)))
 for o in portbars:
  if o is not port:o.parent=port
  # parent keeps local offsets; the bars are positioned relative to the world origin so convert
 port.location=(0,30,0);port.name='Portcullis'
 for o in portbars[1:]:o.location=(o.location.x,o.location.y-30,o.location.z)
 port.scale=(1,1,1)
 g['rb']='BOX'
 for o in passive:o['rb']='BOX'
 for o,c,r in BLOCKS:o['blk']=(c,r)
 if state=='breached':
  for o,c,r in BLOCKS:bpy.data.objects.remove(o,do_unlink=True)
  for i in range(34):
   x=rnd.uniform(-18,-5);y=rnd.uniform(26.5,33.5);z=rnd.uniform(.2,1.6);prim('cube','Rubble',(x,y,z),(.58,.54,.47),scale=(rnd.uniform(.4,1.0),rnd.uniform(.4,.9),rnd.uniform(.3,.8)),rot=(rnd.uniform(0,3),rnd.uniform(0,3),rnd.uniform(0,3)))

def _railway(ctx,state,params):
 import bpy,bmesh
 import numpy as np
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(303);ROOF=3.2;PI=math.pi
 XMAX,XV0,XV1,X_BR=params['xmax'],params['xv0'],params['xv1'],params['x_br']
 bpy.ops.mesh.primitive_plane_add(size=1,location=(XMAX/2-60,0,-.1));g=bpy.context.object;g.name='Ground';g.scale=(XMAX+300,260,1);g.data.materials.append(mat('Ground',(.34,.42,.2)))
 # valley under the bridge: the ground has a hole, floor and water below
 g.scale=(XV0+200,260,1);g.location=((XV0-200)/2,0,-.1)
 g2=prim('cube','GroundAfter',(XV1+(XMAX+300-XV1)/2,0,-.6),(.34,.42,.2),scale=((XMAX+300-XV1)/2,130,.5))
 prim('cube','ValleyFloor',((XV0+XV1)/2,0,-8.6),(.5,.42,.3),scale=((XV1-XV0)/2+2,130,.4));prim('cube','Water',((XV0+XV1)/2,0,-8.0),(.12,.3,.42),scale=((XV1-XV0)/2+2,20,.05))
 for s_ in (-1,1):prim('cube','ValleyWall',((XV0+XV1)/2,s_*130,-4),(.45,.38,.3),scale=((XV1-XV0)/2+2,.5,5))
 for xe in (XV0,XV1):prim('cube','Abutment',(xe,0,-4.2),(.45,.38,.3),scale=(.5,130,4.5))
 prim('cube','BridgeDeck',((XV0+XV1)/2,0,-.35),(.3,.3,.32),scale=((XV1-XV0)/2,2.8,.25))
 for x in np.arange(XV0+10,XV1,15.):prim('cube','Pier',(x,0,-4.4),(.4,.38,.34),scale=(.8,2.2,4.1))
 for s_ in (-1,1):
  prim('cube','BridgeRail',((XV0+XV1)/2,s_*2.7,.7),(.5,.5,.5),scale=((XV1-XV0)/2,.05,.05))
  for x in np.arange(XV0,XV1,6.):prim('cube','RailPost',(x,s_*2.7,.4),(.5,.5,.5),scale=(.05,.05,.4))
 for s_ in (-.72,.72):prim('cube','Rail',(XMAX/2-60,s_,.12),(.5,.5,.55),scale=((XMAX+300)/2,.04,.1))
 prim('cube','Ballast',(XMAX/2-60,0,.02),(.28,.25,.22),scale=((XMAX+300)/2,1.6,.06))
 for x in np.arange(-150.,XMAX,45.):
  for s_ in (-1,1):
   if XV0-3<x<XV1+3:continue
   prim('cyl','Pole',(x,s_*4.5,3.2),(.33,.24,.14),scale=(.08,.08,3.2),vertices=5,radius=1,depth=2);prim('cube','PoleArm',(x,s_*4.5,6.2),(.33,.24,.14),scale=(.04,.9,.05))
 for i in range(520):
  x=rnd.uniform(-150,XMAX);y=rnd.choice((-1,1))*rnd.uniform(9,90)
  if XV0-10<x<XV1+10:continue
  prim('cone','Tree',(x,y,2.5),(.1,.3,.12),scale=(1.4,1.4,2.6),vertices=7,radius1=1,depth=2);prim('cyl','Trunk',(x,y,.5),(.3,.2,.1),scale=(.15,.15,.5),vertices=5,radius=1,depth=2)
 for i in range(30):prim('cone','Hill',(rnd.uniform(-100,XMAX),rnd.choice((-1,1))*rnd.uniform(110,240),rnd.uniform(8,26)),(.38,.4,.3),scale=(rnd.uniform(30,70),rnd.uniform(30,60),rnd.uniform(16,50)),vertices=7,radius1=1,depth=2)
 # the gantry Leo and the guards must duck under
 for s_ in (-1,1):prim('cube','GantryPost',(X_BR,s_*2.6,(ROOF+1.4)/2),(.4,.36,.32),scale=(.35,.35,(ROOF+1.4)/2))
 prim('cube','GantryBeam',(X_BR,0,ROOF+1.25),(.38,.34,.3),scale=(.6,3.0,.25))
def _train_consist(ctx,state,params):
 import bpy,bmesh
 import numpy as np
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];ROOF=params['roof'];WHEEL=__import__('mathutils').Vector(params['wheel']);PI=math.pi
 front=bpy.data.objects.new('FrontCars',None);link(front);rear=bpy.data.objects.new('RearCars',None);link(rear)
 COL=[(.55,.18,.14),(.2,.32,.5),(.5,.42,.16),(.25,.45,.28),(.55,.3,.14),(.4,.2,.45)]
 wheels=[]
 def wagon(k,par):
  cx=-(6.5+12.4*k);c=COL[k];prim('cube','Wagon%d'%k,(cx,0,1.9),c,scale=(5.5,1.3,1.3),parent=par);prim('cube','Roof%d'%k,(cx,0,ROOF-.04),(.3,.28,.26),scale=(5.5,1.4,.05),parent=par)
  for dx in (-3.5,3.5):
   for s_ in (-.72,.72):wheels.append(prim('cyl','Wheel',(cx+dx,s_,.45),(.12,.12,.12),scale=(.45,.45,.1),rot=(PI/2,0,0),vertices=10,radius=1,depth=2,parent=par))
  prim('cube','Coupler',(cx+6.2,0,.9),(.1,.1,.1),scale=(.7,.12,.12),parent=par)
  for dx in np.linspace(-4.5,4.5,6):prim('cube','Board',(cx+dx,1.31,1.9),tuple(v*.6 for v in c),scale=(.04,.01,1.25),parent=par)
 for k in range(3):wagon(k,front)
 for k in range(3,6):wagon(k,rear)
 prim('cube','LocoBody',(4.7,0,1.9),(.12,.12,.14),scale=(4.3,1.3,1.1),parent=front);prim('cube','LocoRoof',(4.7,0,ROOF-.04),(.2,.2,.2),scale=(4.3,1.4,.05),parent=front);prim('cube','Cab',(1.8,0,3.6),(.2,.18,.16),scale=(1.4,1.35,.55),parent=front)
 prim('cyl','Chimney',(8.6,0,3.9),(.1,.1,.1),scale=(.3,.3,.7),vertices=8,radius=1,depth=2,parent=front)
 for x in (1.5,4.0,6.5,8.0):
  for s_ in (-.72,.72):wheels.append(prim('cyl','Wheel',(x,s_,.55),(.14,.14,.14),scale=(.55,.55,.1),rot=(PI/2,0,0),vertices=10,radius=1,depth=2,parent=front))
 prim('cyl','BrakeWheel',WHEEL,(.15,.15,.15),scale=(.33,.33,.03),vertices=14,radius=1,depth=2);bw=bpy.context.object;prim('cyl','BrakePost',(WHEEL.x,0,ROOF+.35),(.15,.15,.15),scale=(.05,.05,.4),vertices=6,radius=1,depth=2)
 for k_,o in enumerate((bw,bpy.context.object)):pass
 bw.parent=front
 for w in wheels:w['wheel']=1
 bw['brakewheel']=1
def _arena_ruins(ctx,state):
 import bpy,bmesh
 import numpy as np
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(404);PI=math.pi
 bpy.ops.mesh.primitive_circle_add(vertices=48,radius=14,fill_type='NGON',location=(0,0,0));sand=bpy.context.object;sand.name='Sand';sand.data.materials.append(mat('Sand',(.72,.6,.38)))
 bpy.ops.mesh.primitive_plane_add(size=300,location=(0,0,-.1));ou=bpy.context.object;ou.name='Ground';ou.data.materials.append(mat('Ground',(.3,.28,.22)))
 for ring,(r0,h,col) in enumerate(((14.5,1.2,(.55,.5,.42)),(17.5,2.4,(.5,.45,.38)),(20.5,3.6,(.46,.42,.35)))):
  for i in range(60):
   a=i*2*PI/60
   if ring==0 and abs(math.sin(a))<.12:continue
   if rnd.random()<.08:continue
   prim('cube','Tier',(math.cos(a)*(r0+1.2),math.sin(a)*(r0+1.2),h/2),col,scale=(1.4,1.7,h/2*rnd.uniform(.8,1.0)),rot=(0,0,a))
 sections=[bpy.data.objects.new('Sec%d'%i,None) for i in range(12)]
 for s in sections:link(s)
 for ring,(r0,h) in enumerate(((16.0,1.2),(19.0,2.4),(22.0,3.6))):
  for i in range(48):
   a=i*2*PI/48+rnd.uniform(-.02,.02);sec=sections[int(a/(2*PI)*12)%12]
   if abs(math.sin(a))<.1 and abs(math.cos(a))>.9 and ring==0:continue
   col=(rnd.uniform(.3,.9),rnd.uniform(.2,.7),rnd.uniform(.2,.6));x,y=math.cos(a)*(r0+rnd.uniform(-.3,.3)),math.sin(a)*(r0+rnd.uniform(-.3,.3))
   b=prim('cone','Fan',(x,y,h+.55),col,scale=(.28,.28,.55),vertices=6,radius1=1,depth=2);hd=prim('sphere','FanHead',(x,y,h+1.2),(.85,.7,.55),scale=(.2,.2,.2),subdivisions=1);b.parent=sec;hd.parent=sec
 for a in np.linspace(0,2*PI,12,endpoint=False):
  x,y=math.cos(a)*14.4,math.sin(a)*14.4;h=rnd.uniform(6,9);prim('cyl','Pillar',(x,y,h/2),(.58,.54,.46),scale=(.6,.6,h/2),vertices=8,radius=1,depth=2);prim('cone','Torch',(x,y,h+.4),(1,.55,.15),scale=(.25,.25,.4),vertices=6,radius1=1,depth=2,emit=8.)
 for a in (0,PI):prim('cube','GateL',(math.cos(a)*14.5,0,3),(.5,.46,.4),scale=(1,.4,3),rot=(0,0,0));
def railway_params(seconds=54.):
 """Pure Python: the numbers the railway location needs (end of the line, bridge span, gantry position) from the train timing of train_scene.py."""
 import scene_kit as kit
 fps=24;frames=int(seconds*fps);XF=[0.]
 for i in range(frames):XF.append(XF[-1]+20.*kit.smooth(i/fps/4.)/fps)
 def X(t):
  i=min(frames-1e-6,max(0.,t*fps));lo=int(i);f=i-lo;return XF[lo]*(1-f)+XF[lo+1]*f
 leg1=kit.run_path(6.6,-69.6,-33.4,[(-63.,-61.6),(-50.6,-49.2),(-38.2,-36.8)],4.2)
 return dict(xmax=X(seconds)+120.,xv0=X(37.5)+9.,xv1=X(37.5)+9.+95.,x_br=X(12.2)+kit.path_x(leg1,12.2))

# ---------------------------------------------------------------------------------------------------------- props: built once at the origin, placed by load_prop (a parent empty carries the location)
def _prop_catapult(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 prim('cube','CatBase',(0,0,.6),(.4,.28,.15),scale=(1.6,1.0,.6))
 arm=bpy.data.objects.new('CatArm',None);link(arm);arm.location=(0,0,1.8);arm['role']='arm'
 beam=prim('cube','CatBeam',(0,0,0),(.45,.3,.15),scale=(.12,3.0,.12),parent=arm);beam.location=(0,-1.2,0)
 for s_ in (-1,1):
  prim('cube','CatFrame',(s_*1.3,0,1.4),(.4,.28,.15),scale=(.12,.12,1.4));prim('cyl','CatWheel',(s_*1.5,0,.45),(.2,.15,.1),scale=(.45,.45,.1),rot=(0,PI/2,0),vertices=8,radius=1,depth=2)
def _prop_winch(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 w=prim('cyl','WinchWheel',(0,0,0),(.18,.16,.12),scale=(.33,.33,.03),vertices=14,radius=1,depth=2);w['role']='wheel'
 prim('cyl','WinchPost',(0,0,-.4),(.18,.16,.12),scale=(.05,.05,.5),vertices=6,radius=1,depth=2);prim('cube','WinchHouse',(.65,.2,1.6),(.4,.3,.22),scale=(2.2,1.6,.2))
def _prop_banner(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 prim('cyl','FlagPole',(0,0,0),(.5,.5,.5),scale=(.07,.07,4),vertices=6,radius=1,depth=2)
 f=prim('cube','Flag',(-1.0,0,-2.4),(.8,.12,.12),scale=(1.0,.03,.55));wv=f.modifiers.new('Flap','WAVE');wv.height=.15;wv.width=1.6;wv.speed=.3;wv.use_normal=True;f['role']='flag'
def _prop_ladder(ctx,state,params):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];h=params.get('height',9.6)
 for s_ in (-1,1):prim('cube','LadderRail',(s_*.42,0,h/2),(.45,.3,.15),scale=(.05,.05,h/2))
 for k in range(int(h/.33)):prim('cube','LadderRung',(0,0,.3+k*.33),(.5,.35,.18),scale=(.42,.035,.035))
def _prop_egg_nest(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 e=prim('sphere','Egg',(0,0,.58),(.92,.9,.72),scale=(.13,.13,.19),subdivisions=2);e['role']='egg'
 prim('sphere','NestRock',(0,0,.27),(.45,.42,.38),scale=(.45,.45,.27))
 for k in range(10):
  a=k*2*math.pi/10;prim('sphere','NestStick',(math.cos(a)*.26,math.sin(a)*.26,.52),(.4,.28,.12),scale=(.1,.1,.06))
 for k in range(2):prim('sphere','OtherEgg',((-.18 if k else .2),(.12 if k else -.14),.51),(.8,.78,.62),scale=(.1,.1,.14))
PROPS_OF={'siege':[('catapult',None),('winch',None),('banner',None),('ladder',dict(height=9.6))],'last_egg':[('egg_nest',None)]}
def load_prop(id_,ctx,location=(0,0,0),rot_z=0.,params=None,scale=1.):
 """Place a shared prop: returns (root empty, {role: object}). The prop is appended from the bank (or built in place) at the origin and parented to a root at the location."""
 import bpy
 before=set(bpy.data.objects.keys());load(id_,ctx,'intact',params)
 new=[o for o in bpy.data.objects if o.name not in before]
 root=bpy.data.objects.new(id_+'Root',None);ctx['link'](root);root.location=location;root.rotation_euler=(0,0,rot_z);root.scale=(scale,)*3
 for o in new:
  if o.parent is None:o.parent=root
 return root,{o['role']:o for o in new if 'role' in o.keys()}

REGISTRY={'mountain_village':dict(states=('intact','buried'),build=_village,piece_default='avalanche'),'citadel':dict(states=('intact','breached'),build=_citadel,piece_default='siege'),
 'arena_ruins':dict(states=('intact',),build=_arena_ruins,piece_default='arena_duel'),
 'railway_plains':dict(states=('intact',),build=_railway,piece_default='great_escape',params=True),
 'catapult':dict(states=('intact',),build=_prop_catapult,piece_default=None),
 'winch':dict(states=('intact',),build=_prop_winch,piece_default=None),
 'banner':dict(states=('intact',),build=_prop_banner,piece_default=None),
 'ladder':dict(states=('intact',),build=_prop_ladder,piece_default=None,params=True),
 'egg_nest':dict(states=('intact',),build=_prop_egg_nest,piece_default=None),
 'train_consist':dict(states=('intact',),build=_train_consist,piece_default='great_escape',params=True)}
def bank_path(id_,state='intact',params=None):
 import inspect
 h=hashlib.sha1((inspect.getsource(REGISTRY[id_]['build'])+inspect.getsource(_make_ctx)).encode()).hexdigest()[:8];ph=hashlib.sha1(json.dumps(params,sort_keys=True,default=list).encode()).hexdigest()[:6] if params else '-'
 return BANK/('%s_%s_%s_%s.blend'%(id_,state,ph,h))
def ensure(id_,state='intact',params=None):
 """Path of the bank file, building it in a separate Blender process the first time (outside Blender only)."""
 if id_ not in REGISTRY or state not in REGISTRY[id_]['states']:raise ValueError('unknown location or state: %s %s'%(id_,state))
 path=bank_path(id_,state,params)
 if path.exists():return path
 BANK.mkdir(exist_ok=True)
 for old in BANK.glob('%s_%s_%s_*.blend'%(id_,state,path.name.split('_')[-2])):old.unlink()
 import quick_review
 subprocess.run([quick_review.BLENDER,'-b','--python',str(Path(__file__).resolve()),'--','build',id_,state,str(path),json.dumps(params or {})],capture_output=True,text=True,errors='ignore',timeout=900)
 return path if path.exists() else None
def load(id_,ctx,state='intact',params=None):
 """Inside Blender: append the location into the current scene (from the bank file when it exists, otherwise built in place). Returns dict(path or None)."""
 import bpy
 if id_ not in REGISTRY or state not in REGISTRY[id_]['states']:raise ValueError('unknown location or state: %s %s'%(id_,state))
 path=bank_path(id_,state,params)
 if path.exists():
  with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=list(src.objects)
  for o in dst.objects:
   if o is not None:ctx['link'](o)
  return dict(path=str(path),cached=True)
 own=_make_ctx()   # no bank file: build in place with the module's own helpers so the result is identical
 (REGISTRY[id_]['build'](own,state,params or {}) if REGISTRY[id_].get('params') else REGISTRY[id_]['build'](own,state));return dict(path=None,cached=False)
def _loc_params(lid,params):
 if lid=='railway_plains':return railway_params(params.get('seconds',54.))
 if lid=='train_consist':return dict(roof=3.2,wheel=[-32.6,0,3.95])
 return None
def ensure_for(piece,params=None):
 """Bank files a set piece needs (called by set_pieces.build before the scene runs)."""
 params=params or {};out=[]
 for lid,meta in REGISTRY.items():
  if meta['piece_default']==piece:
   st=params.get('location_state') if params.get('location_state') in meta['states'] else 'intact';out.append(ensure(lid,st,_loc_params(lid,params)))
 for pid,pp in PROPS_OF.get(piece,[]):out.append(ensure(pid,'intact',pp))
 return out
def _make_ctx():
 import bpy
 scene=bpy.context.scene;mats={}
 def link(o):
  if o.name not in scene.collection.objects:scene.collection.objects.link(o)
 def mat(name,color,emit=0.):
  if name in mats:return mats[name]
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
  if b:
   b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
   if emit:
    for key in ('Emission Color','Emission'):
     if key in b.inputs:b.inputs[key].default_value=(*color,1);break
    if 'Emission Strength' in b.inputs:b.inputs['Emission Strength'].default_value=emit
  mats[name]=m;return m
 def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=None,**kw):
  if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
  elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
  else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
  o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color)+str(emit),color,emit))
  if parent:o.parent=parent
  return o
 return dict(link=link,mat=mat,prim=prim)
if __name__=='__main__' and 'bpy' in sys.modules or (len(sys.argv)>2 and '--' in sys.argv and sys.argv[sys.argv.index('--')+1:][:1]==['build']):
 import bpy
 a=sys.argv[sys.argv.index('--')+1:]
 if a[:1]==['build']:
  bpy.ops.wm.read_factory_settings(use_empty=True);ctx=_make_ctx();(REGISTRY[a[1]]['build'](ctx,a[2],json.loads(a[4])) if REGISTRY[a[1]].get('params') else REGISTRY[a[1]]['build'](ctx,a[2]));bpy.ops.wm.save_as_mainfile(filepath=a[3]);print('LOCATION_BUILT',a[1],a[2],len(bpy.data.objects),'objects')
