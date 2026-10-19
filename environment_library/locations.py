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
def _prop_knife(ctx,state):
 import bpy
 from mathutils import Matrix
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 kn=prim('cube','Knife',(0,0,0),(.85,.87,.9));kn.data.transform(Matrix.Diagonal((.018,.15,.005,1)));kn.scale=(1,1,1);kn.location=(0,.17,0);kn['role']='blade'
 hd=prim('cube','KnifeGrip',(0,0,0),(.25,.15,.08));hd.data.transform(Matrix.Diagonal((.022,.05,.012,1)));hd.scale=(1,1,1);hd['role']='grip'

PROPS_OF={'council':[('goblet',None),('scroll',None),('gavel',None)],'storm_ship':[('knife',None)],'siege':[('catapult',None),('winch',None),('banner',None),('ladder',dict(height=9.6))],'last_egg':[('egg_nest',None)]}
def load_prop(id_,ctx,location=(0,0,0),rot_z=0.,params=None,scale=1.):
 """Place a shared prop: returns (root empty, {role: object}). The prop is appended from the bank (or built in place) at the origin and parented to a root at the location."""
 import bpy
 before=set(bpy.data.objects.keys());load(id_,ctx,'intact',params)
 new=[o for o in bpy.data.objects if o.name not in before]
 root=bpy.data.objects.new(id_+'Root',None);ctx['link'](root);root.location=location;root.rotation_euler=(0,0,rot_z);root.scale=(scale,)*3
 for o in new:
  if o.parent is None:o.parent=root
 return root,{o['role']:o for o in new if 'role' in o.keys()}

def _dino_valley(ctx,state):
 import bpy,bmesh
 import numpy as np
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(505);TREX=Vector((78.,30.,0))
 ground=prim('cube','Ground',(70,0,-.05),(.26,.30,.12),scale=(260,160,.05))
 swamp=prim('cube','Swamp',(70,0,.02),(.12,.30,.28),scale=(28,24,.02))      # x 42..98
 for i in range(60):prim('cone','Reed',(rnd.uniform(44,96),rnd.choice((-1,1))*rnd.uniform(9,22),.6),(.3,.45,.2),scale=(.06,.06,.6),vertices=4,radius1=1,depth=2)
 def fern(x,y,s=1.,color=(.12,.42,.14)):
  for k in range(8):
   a=k*math.pi/4+rnd.uniform(-.2,.2);prim('cone','Frond',(x+math.cos(a)*.9*s,y+math.sin(a)*.9*s,.7*s),color,scale=(.18*s,1.6*s,.05*s),rot=(math.radians(55),0,a-math.pi/2),vertices=4,radius1=1,depth=2)
 def tree_fern(x,y,s=1.):
  prim('cyl','Trunk',(x,y,1.6*s),(.35,.25,.12),scale=(.18*s,.18*s,1.6*s),vertices=6,radius=1,depth=2)
  for k in range(9):
   a=k*2*math.pi/9;prim('cone','Frond',(x+math.cos(a)*1.3*s,y+math.sin(a)*1.3*s,3.4*s),(.1,.38,.12),scale=(.22*s,2.2*s,.05*s),rot=(math.radians(40),0,a-math.pi/2),vertices=4,radius1=1,depth=2)
 def pine(x,y,h):
  prim('cyl','Trunk',(x,y,h*.3),(.3,.2,.1),scale=(.3,.3,h*.3),vertices=6,radius=1,depth=2);prim('cone','Pine',(x,y,h*.7),(.07,.26,.12),scale=(h*.16,h*.16,h*.3),vertices=7,radius1=1,depth=2)
 for i in range(160):
  x=rnd.uniform(-25,215);y=rnd.choice((-1,1))*rnd.uniform(7,70)
  if abs(y)<8 and 0<x<150:continue
  if 42<x<98 and abs(y)<24:continue
  r=rnd.random()
  if r<.55:fern(x,y,rnd.uniform(.8,1.9))
  elif r<.8:tree_fern(x,y,rnd.uniform(.9,1.8))
  else:pine(x,y,rnd.uniform(14,26))
 for i in range(40):prim('sphere','Boulder',(rnd.uniform(-20,210),rnd.choice((-1,1))*rnd.uniform(6,60),.4),(.45,.43,.4),scale=(rnd.uniform(.5,1.8),rnd.uniform(.5,1.5),rnd.uniform(.4,1.))) if True else None
 # the ridge the T-Rex stands on
 prim('cone','Ridge',(TREX.x,TREX.y,1.6),(.4,.36,.3),scale=(11,9,3.2),vertices=8,radius1=1,depth=1)
 # the volcano, lava and smoke
 VOL=Vector((205.,120.,0))
 for k in range(4):
  a=rnd.uniform(3.6,5.2);pts=[(VOL.x+math.cos(a+.15*math.sin(i))*(i*14+16),VOL.y+math.sin(a+.15*math.sin(i))*(i*14+16),74-i*8.5) for i in range(8)]
  for p,q in zip(pts,pts[1:]):prim('cube','Lava',((p[0]+q[0])/2,(p[1]+q[1])/2,(p[2]+q[2])/2+.4),(1,.4,.08),scale=(math.dist(p[:2],q[:2])/2+1,2.2,.35),rot=(0,0,math.atan2(q[1]-p[1],q[0]-p[0])),emit=5.)
 lava_light=bpy.data.objects.new('LavaGlow',bpy.data.lights.new('LavaGlow','POINT'));lava_light.data.energy=400000;lava_light.data.color=(1,.45,.15);lava_light.location=(VOL.x-30,VOL.y-30,60);link(lava_light)
 for k in range(9):   # smoke plume
  o=prim('sphere','Smoke',(VOL.x,VOL.y,80+k*9),(.28,.26,.26),scale=(10+k*2,10+k*2,8+k));
DINO_VALLEY=dict(trex=(78.,30.,0.),ridge_top=3.2,volcano=(205.,120.,0.))

CLIFF=dict(col_a=-2.6,col_b=3.0,col_c=9.6,ledge2_z=7.0,slab_z=13.0,ledge2=(2.6,6.5),slab=(3.45,9.0),gap=(-2.0,2.4,6.4,15.2),xs=-2.35,xe=3.0)
CLIFF_STEP=.33
CLIFF_LIMBS={'RH':dict(off=0.,top=1.45,lat=.2),'LF':dict(off=.25,top=.49,lat=-.14),'LH':dict(off=.5,top=1.45,lat=-.2),'RF':dict(off=.75,top=.49,lat=.14)}   # right = +x when facing the wall
def _smooth(u):
 u=max(0.,min(1.,u));return u*u*(3-2*u)
def cliff_ywall(x,z):
 """Depth of the rock face (m) at x, z; the gap between the climbing columns is a recess 1.6 m deep."""
 n=.07*(3+math.sin(x*1.3+z*.7)+math.sin(x*.5-z*1.1+1)+math.sin(x*2.1+z*1.9))
 x0,x1,z0,z1=CLIFF['gap'];e=.5;inx=_smooth((x-x0)/e)*_smooth((x1-x)/e);inz=_smooth((z-z0)/e)*_smooth((z1-z)/e);return n+1.6*inx*inz
def cliff_hold_abs(limb,k,col):
 """World position (x, y, z) of hold k of a limb in a climbing column; deterministic jitter so the holds look natural."""
 import zlib
 L=CLIFF_LIMBS[limb];r=random.Random(zlib.crc32(('%s%d%.1f'%(limb,k,col)).encode()));z=L['off']*CLIFF_STEP+k*CLIFF_STEP+L['top']+r.uniform(-.03,.03)
 return (col+L['lat']+r.uniform(-.04,.04),-.04,z)
def _cliff_face(ctx,state):
 import bpy,bmesh
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(606)
 COL_A,COL_B,COL_C=CLIFF['col_a'],CLIFF['col_b'],CLIFF['col_c'];LEDGE2_Z,SLAB_Z=CLIFF['ledge2_z'],CLIFF['slab_z'];LEDGE2=CLIFF['ledge2'];SLAB=CLIFF['slab'];XS,XE=CLIFF['xs'],CLIFF['xe'];AX=(XS+XE)/2;STEP=CLIFF_STEP;LIMBS=CLIFF_LIMBS
 ywall=cliff_ywall
 def hold_abs(limb,k,col):return Vector(cliff_hold_abs(limb,k,col))
 bpy.ops.mesh.primitive_plane_add(size=1,location=(10,6,-.05));g=bpy.context.object;g.scale=(120,90,1);g.name='Ground';g.data.materials.append(mat('Ground',(.25,.33,.14)))
 bm=bmesh.new();NX,NZ=57,53;grid=[[bm.verts.new((-14+i*.5,ywall(-14+i*.5,j*.5),j*.5)) for j in range(NZ)] for i in range(NX)]
 for i in range(NX-1):
  for j in range(NZ-1):bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]))
 me=bpy.data.meshes.new('CliffMesh');bm.to_mesh(me);bm.free();cliff=bpy.data.objects.new('Cliff',me);link(cliff);me.materials.append(mat('Cliff',(.42,.38,.33)))
 for p in me.polygons:p.use_smooth=False
 prim('cube','CliffBack',(0,5,13),(.34,.31,.27),scale=(15,4.8,13.5))
 for i in range(30):prim('cone','CliffPeak',(rnd.uniform(-40,50),rnd.uniform(25,70),rnd.uniform(2,18)),(.36,.34,.32),scale=(rnd.uniform(8,16),rnd.uniform(8,16),rnd.uniform(14,34)),vertices=6,radius1=1,depth=2)
 ledge2=prim('cube','Ledge2',((LEDGE2[0]+LEDGE2[1])/2,-.7,LEDGE2_Z-.2),(.4,.36,.31),scale=((LEDGE2[1]-LEDGE2[0])/2,.7,.2))
 slab=prim('cube','CubLedge',((SLAB[0]+SLAB[1])/2,-.8,SLAB_Z-.2),(.4,.36,.31),scale=((SLAB[1]-SLAB[0])/2,.8,.2))
 prim('cone','Spur',(AX,-.2,13.9),(.36,.32,.28),scale=(.35,.35,.5),vertices=6,radius1=1,depth=2)
 prim('cube','Peg',(XS,-.05,8.3),(.3,.2,.1),scale=(.05,.05,.05));prim('cyl','EyeBolt',(COL_C,-.12,14.0),(.2,.2,.2),scale=(.05,.05,.05),vertices=6,radius=1,depth=1)
 for i in range(22):prim('sphere','Boulder',(rnd.uniform(-12,22),rnd.uniform(-12,-6),.3),(.4,.38,.35),scale=(rnd.uniform(.4,1.2),rnd.uniform(.4,1),rnd.uniform(.3,.7)),subdivisions=1)
 for i in range(70):
  x=rnd.uniform(-12,26);y=rnd.uniform(-34,-15);prim('cone','Pine',(x,y,2.4),(.07,.26,.12),scale=(1.1,1.1,2.4),vertices=7,radius1=1,depth=2);prim('cyl','Trunk',(x,y,.5),(.3,.2,.1),scale=(.15,.15,.5),vertices=5,radius=1,depth=2)
 allholds=[]
 for col,lo,hi in ((COL_A,0,8),(COL_B,7,13.8),(COL_C,12.5,14.6)):
  for limb in LIMBS:
   for k in range(int((lo-LIMBS[limb]['off']*STEP)/STEP)-1,int((hi-LIMBS[limb]['off']*STEP)/STEP)+3):
    p=hold_abs(limb,k,col);allholds.append(p);prim('sphere','Hold',p+Vector((0,.03,0)),(.85,.62,.3),scale=(.09,.06,.07),subdivisions=1)

SHIP=dict(L=9.,HB=3.2,DZ=1.6,MAST_X=-.4,masts=[(-.4,12.,'Main'),(4.4,9.5,'Fore'),(-5.3,8.,'Mizzen')],wheel_pos=(-5.2,0,1.6))
def _galleon(ctx,state):
 import bpy,bmesh
 import numpy as np
 from mathutils import Vector
 link,mat,prim0=ctx['link'],ctx['mat'],ctx['prim']
 L,HB,DZ,MAST_X=SHIP['L'],SHIP['HB'],SHIP['DZ'],SHIP['MAST_X']
 ship=bpy.data.objects.new('Ship',None);link(ship)
 def put(o,color,name,emit=0.,parent=True):
  o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color,emit))
  if parent:o.parent=ship
  return o
 def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=True,**kw):
  o=prim0(kind,name,loc,color,scale=scale,rot=rot,emit=emit,**kw)
  if parent:o.parent=ship
  return o
 def line(a,b,r,color,name='Rope',emit=0.,parent=True):
  a,b=Vector(a),Vector(b);d=b-a;o=prim('cyl',name,(a+b)/2,color,scale=(r,r,d.length/2),vertices=5,radius=1,depth=2,emit=emit,parent=parent);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
 def hull():
  import bmesh
  bm=bmesh.new();stations=[-L+i*L*2/16 for i in range(17)];rows=[]
  for x in stations:
   u=x/L;b=HB*max(.02,(1-u**4))**.65*(1 if x<0 else 1-.25*u*u);zd=DZ+.9*max(0,u)**3+.5*max(0,-u)**2;keel=-1.5*(1-.5*max(0,u)**2)
   rows.append([bm.verts.new(v) for v in ((x,-b,zd),(x,-b*.8,zd*.35+keel*.2),(x,0,keel),(x,b*.8,zd*.35+keel*.2),(x,b,zd))])
  for r0,r1 in zip(rows,rows[1:]):
   for k in range(4):
    try:f=bm.faces.new((r0[k],r0[k+1],r1[k+1],r1[k]));f.material_index=0
    except ValueError:pass
  try:bm.faces.new(rows[0][::-1])
  except ValueError:pass
  me=bpy.data.meshes.new('HullMesh');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('Hull',me);link(o);o.parent=ship;me.materials.append(mat('Hull',(.28,.15,.07)));return o
 hull()
 deck=prim('cube','Deck',(0,0,DZ-.04),(.58,.4,.2),scale=(L*.93,HB*.8,.05))
 for i in range(-8,9):prim('cube','Plank',(i*1.0,0,DZ+.012),(.45,.3,.14),scale=(.02,HB*.78,.01))
 for s in (-1,1):   # rails
  line((-L*.9,s*HB*.9,DZ+.9),(L*.78,s*HB*.8,DZ+.9),.05,(.35,.2,.1),'Rail')
  for x in np.linspace(-L*.9,L*.75,9):line((x,s*HB*.9*(1-max(0,x/L)**2*.1),DZ),(x,s*HB*.9*(1-max(0,x/L)**2*.1),DZ+.9),.04,(.35,.2,.1),'Post')
 prim('cube','Cabin',(-7.0,0,DZ+.6),(.5,.3,.14),scale=(1.4,HB*.75,.6));prim('cube','CabinRoof',(-7.0,0,DZ+1.25),(.38,.22,.1),scale=(1.55,HB*.82,.07))
 wheel_pos=Vector((-5.2,0,DZ));prim('cyl','WheelRing',(-5.4,0,DZ+1.15),(.4,.25,.1),scale=(.5,.5,.04),rot=(0,math.pi/2,0),vertices=14,radius=1,depth=2)
 for k in range(4):a=k*math.pi/4;line((-5.4,math.cos(a)*.55,DZ+1.15+math.sin(a)*.55),(-5.4,-math.cos(a)*.55,DZ+1.15-math.sin(a)*.55),.03,(.4,.25,.1),'Spoke')
 prim('cyl','WheelPost',(-5.4,0,DZ+.55),(.3,.18,.08),scale=(.1,.1,.55),vertices=6,radius=1,depth=2)
 MASTS=[(MAST_X,12.,'Main'),(4.4,9.5,'Fore'),(-5.3,8.,'Mizzen')]
 for x,h,n in MASTS:
  prim('cyl',n+'Mast',(x,0,DZ+h/2),(.35,.22,.1),scale=(.22,.22,h/2),vertices=8,radius=1,depth=2)
  yv=DZ+h*.62;prim('cyl',n+'Yard',(x,0,yv),(.35,.22,.1),scale=(.1,.1,HB*1.1),rot=(math.pi/2,0,0),vertices=6,radius=1,depth=2)
  for s in (-1,1):line((x,0,DZ+h),(x-.5,s*HB*.85,DZ+.9),.025,(.15,.1,.07),'Shroud');line((x,0,DZ+h),(x+(2.5 if n!='Mizzen' else -1.5),0,DZ+.9),.025,(.15,.1,.07),'Stay')
 def sail(name,x,yv,w,h,flap):
  bpy.ops.mesh.primitive_grid_add(x_subdivisions=14,y_subdivisions=10,size=1,location=(x+(-.45 if x==MAST_X else .45),0,yv-h/2),rotation=(0,math.pi/2,0));o=bpy.context.object;o.scale=(h,w,1)
  put(o,(.85,.8,.68),name)
  if flap:m=o.modifiers.new('Flap','WAVE');m.height=flap;m.width=1.5;m.speed=.25;m.narrowness=3.;m.use_normal=True
  return o
 mainsail=sail('MainSail',MAST_X,DZ+12*.62,HB*1.9,6.5,0);sail('ForeSail',4.4,DZ+9.5*.62,HB*1.7,5.2,.2);sail('MizzenSail',-5.3,DZ+8*.62,HB*1.4,4.2,.15)
 TORN=prim('cube','TornSail',(MAST_X-.55,.8,DZ+12*.62-1.6),(.85,.8,.68),scale=(.02,HB*.65,1.8))   # the strip that stays on the yard after the cut
 for k in range(14):prim('cube','Rung',(.18,0,DZ+.5+k*.55),(.4,.25,.1),scale=(.04,.7,.03));
 mainsail['role']='mainsail';TORN['role']='torn'
def _open_sea(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 bpy.ops.mesh.primitive_grid_add(x_subdivisions=170,y_subdivisions=170,size=320,location=(0,0,0));sea=bpy.context.object;sea.name='Sea';sea.data.materials.append(mat('Sea',(.06,.2,.3)))
 for k,(h,w,sp,x0) in enumerate(((1.3,16,.55,0),(.5,6,.9,3))):
  m=sea.modifiers.new('Wave%d'%k,'WAVE');m.height=h;m.width=w;m.speed=sp;m.narrowness=1.6;m.start_position_x=-80;m.start_position_y=30+k*20;m.use_normal=True
 for p in sea.data.polygons:p.use_smooth=False

COUNCIL=dict(table_r=2.4,table_z=.62,seat_r=2.75,seat_z=.32,n=6,hall_r=10.5)
def _council_hall(ctx,state):
 import bpy
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];rnd=random.Random(707);C=COUNCIL
 prim('cyl','Floor',(0,0,-.1),(.22,.2,.19),scale=(11.5,11.5,.1),vertices=48,radius=1,depth=2)
 for k,(r,col) in enumerate(((3.2,(.3,.25,.2)),(4.8,(.18,.16,.15)),(6.4,(.3,.25,.2)),(8.0,(.2,.18,.17)))):prim('cyl','Mosaic',(0,0,.005+k*.002),col,scale=(r,r,.01),vertices=48,radius=1,depth=2)
 prim('cyl','TableTop',(0,0,C['table_z']-.06),(.32,.2,.1),scale=(C['table_r'],C['table_r'],.06),vertices=40,radius=1,depth=2)
 prim('cyl','TableRim',(0,0,C['table_z']-.14),(.22,.14,.07),scale=(C['table_r']+.05,C['table_r']+.05,.04),vertices=40,radius=1,depth=2)
 prim('cyl','TablePedestal',(0,0,C['table_z']/2-.1),(.25,.17,.1),scale=(.8,.8,C['table_z']/2),vertices=16,radius=1,depth=2)
 for i in range(C['n']):
  a=math.radians(-90+i*360/C['n']);ux,uy=math.cos(a),math.sin(a);r=C['seat_r']+.1
  c=Vector((ux*(r-.12),uy*(r-.12),0));prim('cube','ChairSeat',(c.x,c.y,C['seat_z']-.03),(.35,.22,.12),scale=(.3,.28,.03),rot=(0,0,a))
  prim('cube','ChairBack',(ux*(r+.28),uy*(r+.28),C['seat_z']+.5),(.3,.18,.1),scale=(.04,.3,.5),rot=(0,0,a))
  for s_ in (-1,1):prim('cube','ChairLeg',(ux*(r-.12)-uy*s_*.22,uy*(r-.12)+ux*s_*.22,C['seat_z']/2),(.3,.18,.1),scale=(.035,.035,C['seat_z']/2))
 R=C['hall_r']
 for k in range(14):
  a=k*2*math.pi/14;x,y=math.cos(a)*R,math.sin(a)*R
  prim('cyl','Column',(x,y,3.5),(.55,.5,.44),scale=(.55,.55,3.5),vertices=10,radius=1,depth=2);prim('cyl','Capital',(x,y,7.1),(.6,.55,.48),scale=(.75,.75,.2),vertices=10,radius=1,depth=2)
  prim('cone','Torch',(x*.93,y*.93,3.0),(1,.55,.15),scale=(.18,.18,.3),vertices=6,radius1=1,depth=2,emit=8.)
  prim('cube','Banner',(x*.95,y*.95,5.0),tuple(c*.9 for c in ((.55,.12,.1),(.1,.25,.5),(.5,.4,.1))[k%3]),scale=(.05,.45,1.1),rot=(0,0,a+math.pi/2))
  lt=bpy.data.objects.new('TorchLight',bpy.data.lights.new('TorchLight','POINT'));lt.data.energy=900;lt.data.color=(1,.62,.3);lt.location=(x*.9,y*.9,3.4);link(lt)
  if k not in (3,10):
   a2=a+math.pi/14;prim('cube','Wall',(math.cos(a2)*(R+.4),math.sin(a2)*(R+.4),3.0),(.4,.37,.32),scale=(1.5,.5,3.0),rot=(0,0,a2+math.pi/2))
 prim('cone','Roof',(0,0,9.2),(.3,.2,.14),scale=(12.5,12.5,2.2),vertices=24,radius1=1,depth=2)
 for k in range(8):
  a=k*math.pi/8;prim('cube','Beam',(0,0,7.4),(.25,.17,.1),scale=(11,.18,.2),rot=(0,0,a))
 prim('cyl','ChandelierRing',(0,0,5.6),(.4,.35,.25),scale=(1.6,1.6,.04),vertices=24,radius=1,depth=2)
 for k in range(12):
  a=k*math.pi/6;prim('sphere','Candle',(math.cos(a)*1.6,math.sin(a)*1.6,5.75),(1,.9,.5),scale=(.07,.07,.12),emit=10.,subdivisions=1)
 ch=bpy.data.objects.new('ChandelierLight',bpy.data.lights.new('ChandelierLight','POINT'));ch.data.energy=1500;ch.data.color=(1,.8,.5);ch.location=(0,0,5.2);link(ch)
def _prop_goblet(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 prim('cyl','GobletCup',(0,0,.14),(.8,.7,.2),scale=(.05,.05,.07),vertices=12,radius=1,depth=2);prim('cyl','GobletStem',(0,0,.05),(.8,.7,.2),scale=(.015,.015,.05),vertices=8,radius=1,depth=2);prim('cyl','GobletBase',(0,0,.005),(.8,.7,.2),scale=(.04,.04,.008),vertices=12,radius=1,depth=2)
def _prop_scroll(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 s=prim('cyl','ScrollBody',(0,0,.04),(.9,.8,.6),scale=(.04,.04,.28),rot=(0,math.pi/2,0),vertices=12,radius=1,depth=2);s['role']='scroll'
 for sx in (-.29,.29):prim('cyl','ScrollEnd',(sx,0,.04),(.45,.3,.15),scale=(.05,.05,.015),rot=(0,math.pi/2,0),vertices=10,radius=1,depth=2).parent=s
def _prop_gavel(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim']
 prim('cyl','GavelBlock',(0,0,.03),(.35,.2,.1),scale=(.12,.12,.03),vertices=10,radius=1,depth=2)
 h=bpy.data.objects.new('GavelPivot',None);link(h);h.location=(0,0,.06);h['role']='pivot'
 prim('cyl','GavelHandle',(0,-.12,.05),(.4,.25,.12),scale=(.015,.015,.14),rot=(math.pi/2,0,0),vertices=8,radius=1,depth=2).parent=h
 head=prim('cyl','GavelHead',(0,-.26,.05),(.4,.25,.12),scale=(.04,.04,.07),rot=(0,math.pi/2,0),vertices=10,radius=1,depth=2);head.parent=h

MUSEUM=dict(x0=-18.,x1=18.,hw=8.,h=8.,pillars=[(-12.,3.),(-12.,-3.),(-6.,3.),(-6.,-3.),(0.,3.),(0.,-3.),(6.,3.),(6.,-3.),(12.,3.),(12.,-3.)],cases=[(-9.,-5.8),(-3.,5.8),(5.,-5.8),(11.,5.8)],crate=(-15.4,-1.6),pedestal=(10.,0.),window=(18.,0.,1.1),gate_x=3.5,
 gate=[(.3,'low'),(.65,'high'),(1.0,'high')],corner_lasers=[((11.,-7.5,.5),(16.5,-2.5,.5)),((11.,7.5,.5),(16.5,2.5,.5)),((13.,-7.5,1.0),(13.,-3.5,1.0))])
def _museum_hall(ctx,state):
 import bpy
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];M=MUSEUM
 prim('cube','Floor',(0,0,-.1),(.12,.12,.16),scale=(19,9,.1))
 for ix in range(-8,9):
  for iy in range(-3,3):
   if (ix+iy)%2==0:prim('cube','FloorTile',(ix*2.2+1.1,iy*2.6+1.3,.003),(.2,.2,.22),scale=(1.1,1.3,.004))
 for sy in (-1,1):prim('cube','Wall',(0,sy*(M['hw']+.5),M['h']/2),(.2,.19,.18),scale=(19,.5,M['h']/2))
 prim('cube','WallW',(M['x0']-.5,0,M['h']/2),(.2,.19,.18),scale=(.5,9,M['h']/2))
 prim('cube','WallEUp',(M['x1']+.5,0,5.5),(.2,.19,.18),scale=(.5,9,2.5));prim('cube','WallELow',(M['x1']+.5,0,.45),(.2,.19,.18),scale=(.5,9,.45))
 for sy in (-1,1):prim('cube','WallEPost',(M['x1']+.5,sy*5.2,3.0),(.2,.19,.18),scale=(.5,3.8,.6))
 prim('cube','Ceiling',(0,0,M['h']+.3),(.12,.12,.14),scale=(19,9,.3))
 for k,x in enumerate((-12,-4,4,12)):prim('cube','Skylight',(x,0,M['h']-.02),(.5,.6,.9),scale=(1.5,3.0,.02),emit=3.)
 for (x,y) in M['pillars']:
  p=prim('cyl','Pillar',(x,y,M['h']/2),(.5,.46,.4),scale=(.5,.5,M['h']/2),vertices=10,radius=1,depth=2);p['cover']=1
 for (x,y) in M['cases']:
  c=prim('cube','Case',(x,y,.5),(.4,.34,.22),scale=(.8,.5,.5));c['cover']=1;prim('cube','CaseGlass',(x,y,1.15),(.7,.85,.9),scale=(.75,.45,.15));prim('sphere','Exhibit',(x,y,1.35),(.9,.7,.2),scale=(.18,.18,.18),subdivisions=1)
 cx,cy=M['crate'];cr=prim('cube','Crate',(cx,cy,.6),(.4,.3,.15),scale=(.7,.7,.6));cr['cover']=1
 px,py=M['pedestal']
 ped=prim('cyl','Pedestal',(px,py,.5),(.45,.4,.35),scale=(.7,.7,.5),vertices=16,radius=1,depth=2);ped['cover']=1
 prim('cyl','PedestalCap',(px,py,1.03),(.5,.45,.4),scale=(.78,.78,.03),vertices=16,radius=1,depth=2)
 j=prim('sphere','Jewel',(px,py,1.2),(.3,.8,1),scale=(.11,.11,.15),emit=6.,subdivisions=2);j['role']='jewel'
 lid=prim('cube','GlassLid',(px,py,1.22),(.6,.75,.85),scale=(.35,.35,.28));lid['role']='lid'
 d=prim('cyl','Dial',(px-.72,py,.8),(.8,.7,.2),scale=(.1,.1,.03),rot=(0,math.pi/2,0),vertices=16,radius=1,depth=2);d['role']='dial'
 prim('cube','DialPlate',(px-.7,py,.8),(.25,.22,.2),scale=(.02,.18,.18))
 gx=M['gate_x']
 for z,kind in M['gate']:
  l=prim('cyl','Laser',(gx,0,z),(1,.05,.05),scale=(.012,.012,M['hw']),rot=(math.pi/2,0,0),vertices=6,radius=1,depth=2,emit=6.);l['group']='gate_'+kind;l['z']=z
  for sy in (-1,1):prim('cube','LaserEmitter',(gx,sy*(M['hw']-.1),z),(.2,.2,.2),scale=(.08,.08,.08))
 for k,(a,b) in enumerate(M['corner_lasers']):
  a=Vector(a);b=Vector(b);dv=b-a;l=prim('cyl','Laser',(a+b)/2,(1,.05,.05),scale=(.012,.012,dv.length/2),vertices=6,radius=1,depth=2,emit=6.);l.rotation_euler=dv.to_track_quat('Z','Y').to_euler();l['group']='corner';l['z']=a.z
 prim('cube','Balcony',(M['x1']+4.0,0,.9),(.3,.29,.28),scale=(4.0,4.0,.1));prim('cube','BalconyRail',(M['x1']+7.9,0,1.5),(.3,.29,.28),scale=(.08,4,.08))
 for k in range(5):prim('cube','Crate',(M['x1']+2+k*1.4,-3.2+k*.4,1.35),(.45,.35,.2),scale=(.45,.45,.4))
 mn=bpy.data.objects.new('MoonLight',bpy.data.lights.new('MoonLight','SUN'));mn.data.energy=.35;mn.data.color=(.55,.65,1);mn.rotation_euler=(math.radians(60),0,math.radians(120));link(mn)
 for x in (-12,-4,4,12):
  lt=bpy.data.objects.new('SkyGlow',bpy.data.lights.new('SkyGlow','POINT'));lt.data.energy=700;lt.data.color=(.45,.55,1);lt.location=(x,0,6.5);link(lt)

WORKSHOP=dict(x0=-4.5,x1=4.5,y0=-3.2,y1=3.8,h=3.6,bench=dict(x0=-1.7,x1=1.7,y0=0.,y1=.9,z=1.02))
def _workshop(ctx,state):
 import bpy
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];W=WORKSHOP;B=W['bench'];rnd=random.Random(55)
 prim('cube','Floor',(0,.3,-.1),(.3,.2,.13),scale=(4.8,3.6,.1))
 for ix in range(-4,5):
  for iy in range(-3,4):
   if (ix+iy)%2==0:prim('cube','FloorBoard',(ix*1.1,iy*1.0+.4,.004),(.34,.24,.16),scale=(.55,.5,.004))
 prim('cube','Wall',(0,W['y1']+.25,W['h']/2),(.4,.33,.26),scale=(4.8,.25,W['h']/2))
 prim('cube','WallW',(W['x0']-.25,.3,W['h']/2),(.38,.31,.25),scale=(.25,3.6,W['h']/2));prim('cube','WallE',(W['x1']+.25,.3,W['h']/2),(.38,.31,.25),scale=(.25,3.6,W['h']/2))
 prim('cube','Ceiling',(0,.3,W['h']+.2),(.25,.2,.16),scale=(4.8,3.6,.2))
 for sx in (-3.2,3.2):prim('cube','Beam',(sx,.3,W['h']-.15),(.2,.15,.1),scale=(.15,3.6,.15))
 bx=(B['x0']+B['x1'])/2;bw=(B['x1']-B['x0'])/2;by=(B['y0']+B['y1'])/2;bd=(B['y1']-B['y0'])/2
 prim('cube','BenchTop',(bx,by,B['z']-.04),(.45,.3,.16),scale=(bw,bd,.04))
 for sx in (-1,1):
  for sy in (-1,1):prim('cube','BenchLeg',(bx+sx*(bw-.1),by+sy*(bd-.08),(B['z']-.08)/2),(.3,.2,.12),scale=(.06,.06,(B['z']-.08)/2))
 prim('cube','BenchShelf',(bx,by,.3),(.35,.25,.13),scale=(bw-.1,bd-.1,.025))
 prim('cube','BenchMat',(bx,by,B['z']+.002),(.2,.27,.24),scale=(bw-.15,bd-.1,.003))
 # wall shelves with jars, tool board and decorative gears
 for k,z in enumerate((1.5,2.2,2.9)):
  prim('cube','Shelf',(-2.2,W['y1']-.2,z),(.38,.28,.17),scale=(1.5,.2,.04))
  for j in range(7):prim('cyl','Jar',(-3.4+j*.38+rnd.uniform(-.03,.03),W['y1']-.2,z+.12),(rnd.uniform(.3,.8),rnd.uniform(.3,.6),rnd.uniform(.2,.5)),scale=(.11,.11,.09+rnd.random()*.04),vertices=10,radius=1,depth=2)
 prim('cube','ToolBoard',(2.6,W['y1']-.02,1.9),(.3,.22,.15),scale=(1.4,.04,.9))
 for j in range(9):
  x=1.5+j*.25;h=.25+rnd.random()*.2;prim('cube','ToolHandle',(x,W['y1']-.08,1.95),(.4,.25,.12),scale=(.03,.03,h/2));prim('cube','ToolHead',(x,W['y1']-.08,1.95+h/2),(.6,.6,.62),scale=(.05,.025,.05))
 for k,(gx,gz,gr,n) in enumerate(((1.5,3.05,.38,16),(2.2,3.25,.26,12),(3.2,3.0,.44,18))):
  prim('cyl','WallGear',(gx,W['y1']-.05,gz),(.55,.4,.2),scale=(gr,gr,.04),rot=(math.pi/2,0,0),vertices=n*2,radius=1,depth=2)
 prim('cyl','ClockFace',(-3.4,W['y1']-.05,3.1),(.9,.85,.7),scale=(.42,.42,.03),rot=(math.pi/2,0,0),vertices=24,radius=1,depth=2)
 for sx in (-1,1):prim('cube','BarrelCrate',(sx*3.7,-.6,.45),(.35,.26,.14),scale=(.5,.5,.45))
 prim('cube','Window',(W['x1']-.02,1.6,2.0),(.45,.6,.95),scale=(.03,.7,.8),emit=1.5)
 la=bpy.data.objects.new('BenchLamp',bpy.data.lights.new('BenchLamp','POINT'));la.data.energy=1500;la.data.color=(1,.78,.5);la.location=(0,.45,2.5);link(la)
 prim('cone','LampShade',(0,.45,2.65),(.8,.55,.2),scale=(.28,.28,.15),vertices=16,radius1=1,depth=2)
 fl=bpy.data.objects.new('FillLight',bpy.data.lights.new('FillLight','POINT'));fl.data.energy=900;fl.data.color=(.75,.82,1);fl.location=(0,-2.2,2.8);link(fl)

RAPIDS=dict(x0=-12.,x1=170.,hw=9.,boulders=[(22.,1.8,1.5),(38.,-2.2,1.7),(55.,2.6,1.4),(70.,-1.5,1.8),(88.,2.0,1.5),(104.,-2.8,1.6),(122.,1.0,1.9)])
def _rapids(ctx,state):
 import bpy
 from mathutils import Vector
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];R=RAPIDS;rnd=random.Random(88)
 nx=int((R['x1']-R['x0'])/.6);ny=30;verts=[(R['x0']+i*(R['x1']-R['x0'])/nx,-R['hw']+j*2*R['hw']/ny,0.) for i in range(nx+1) for j in range(ny+1)]
 faces=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)]
 me=bpy.data.meshes.new('Water');me.from_pydata(verts,[],faces);me.update();me.materials.append(mat('Water',(.1,.32,.42)))
 w=bpy.data.objects.new('Water',me);link(w)
 for k,(h,wd,nr,sp,ph) in enumerate(((.16,3.2,1.5,.09,0.),(.07,1.3,1.2,.14,40.))):
  m=w.modifiers.new('Wave%d'%k,'WAVE');m.use_x=True;m.use_y=False;m.height=h;m.width=wd;m.narrowness=nr;m.speed=sp;m.time_offset=ph;m.use_normal=False
 for ix in range(int((R['x1']-R['x0'])/4)):
  x=R['x0']+ix*4+rnd.uniform(-1,1)
  for sy in (-1,1):
   h=rnd.uniform(4,9);prim('cube','Cliff',(x,sy*(R['hw']+1.8+rnd.uniform(0,.8)),h/2-.8),(.36+rnd.random()*.08,.3+rnd.random()*.06,.25),scale=(2.2+rnd.random(),1.6+rnd.random(),h/2),rot=(0,rnd.uniform(-.05,.05),rnd.uniform(-.2,.2)))
 prim('cube','Bed',(0,0,-.9),(.2,.17,.14),scale=((R['x1']-R['x0'])/2+20,R['hw']+6,.1)).location.x=(R['x0']+R['x1'])/2
 for (x,y,r) in R['boulders']:
  prim('sphere','Boulder',(x,y,r*.3),(.4,.38,.35),scale=(r,r*rnd.uniform(.85,1.1),r*.8),subdivisions=2)
  for k in range(3):a=rnd.uniform(0,6.28);prim('sphere','BoulderChip',(x+math.cos(a)*r*.9,y+math.sin(a)*r*.9,r*.1),(.36,.34,.3),scale=(r*.3,r*.3,r*.25),subdivisions=1)
  prim('cyl','FoamRing',(x,y,.03),(.92,.95,1),scale=(r+.7,r+.7,.012),vertices=24,radius=1,depth=2)
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=3.5;sn.rotation_euler=(math.radians(50),0,math.radians(30));link(sn)

FLOOD=dict(x0=-70.,x1=110.,hw=30.,lev=2.4,hill_x=40.,hill_len=30.,hill_h=6.,
 houses=[(6,9,3.2),(14,-10,3.4),(20,10.5,3.0),(28,-9,3.3),(34,9,3.1),(-8,-9,3.2),(-12,10,3.4),(40,-11,3.0),(10,-4.5,2.2),(31,7.4,2.2)],
 trees=[(52,-14),(58,-17),(64,-13),(70,16),(76,-18),(80,14),(56,17),(66,-19),(-30,15),(-35,-16),(-20,-17),(-14,18)])
def flood_ground(x,y,F=None):
 F=F or FLOOD;u=min(1.,max(0.,(x-F['hill_x'])/F['hill_len']));s=u*u*(3-2*u);return F['hill_h']*s+max(0.,abs(y)-16.)*.5
def _flood_valley(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];F=FLOOD;rnd=random.Random(21)
 nx=int((F['x1']-F['x0'])/2);ny=int(2*F['hw']/2);verts=[(F['x0']+i*2.,-F['hw']+j*2.,flood_ground(F['x0']+i*2.,-F['hw']+j*2.)) for i in range(nx+1) for j in range(ny+1)]
 faces=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1) for i in range(nx) for j in range(ny)]
 me=bpy.data.meshes.new('Ground');me.from_pydata(verts,[],faces);me.update();me.materials.append(mat('Ground',(.32,.38,.2)));g=bpy.data.objects.new('Ground',me);link(g)
 for (x,y,s) in F['houses']:
  h=2.2+rnd.random()*.6;prim('cube','House',(x,y,h/2),(.55+rnd.random()*.15,.42,.3),scale=(s/2,s/2*.85,h/2))
  prim('cone','Roof',(x,y,h+.7),(.5,.2,.15),scale=(s*.72,s*.65,.7),vertices=4,radius1=1,depth=2,rot=(0,0,math.pi/4))
 for (x,y) in F['trees']:
  h=3.+rnd.random()*2.;z=flood_ground(x,y);prim('cyl','Trunk',(x,y,z+h*.2),(.3,.2,.1),scale=(.18,.18,h*.2),vertices=6,radius=1,depth=2);prim('cone','Crown',(x,y,z+h*.7),(.12,.34,.14),scale=(1.1,1.1,h*.4),vertices=8,radius1=1,depth=2)
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=2.2;sn.data.color=(.85,.88,1);sn.rotation_euler=(math.radians(55),0,math.radians(-35));link(sn)

SKY=dict(x0=-60.,x1=520.,hw=34.,spires=[(45.,5.,2.8,60.),(80.,-6.,3.2,70.),(115.,4.,2.5,55.),(150.,-5.,3.0,65.),(185.,6.,3.4,72.),(220.,-4.,2.6,58.),(340.,5.,3.1,66.),(372.,-6.,2.9,62.),(404.,3.,3.3,70.),(436.,-5.,2.7,60.)],arch=(270.,11.,15.,19.))
def _sky_canyon(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];S=SKY;rnd=random.Random(64);cx=(S['x0']+S['x1'])/2;L=(S['x1']-S['x0'])/2
 prim('cube','Floor',(cx,0,-.5),(.36,.3,.22),scale=(L,S['hw'],.5))
 prim('cube','River',(cx,0,.02),(.12,.3,.4),scale=(L,6,.02))
 for sy in (-1,1):
  for k in range(int(2*L/12)):
   x=S['x0']+k*12+rnd.uniform(-2,2);h=70+rnd.uniform(0,40);prim('cube','Cliff',(x,sy*(S['hw']+4+rnd.uniform(0,3)),h/2),(.42+rnd.random()*.1,.34,.26),scale=(6+rnd.random()*2,4+rnd.random()*3,h/2),rot=(0,0,rnd.uniform(-.15,.15)))
 for (x,y,r,h) in S['spires']:
  prim('cone','Spire',(x,y,h/2),(.46,.38,.3),scale=(r,r,h/2),vertices=10,radius1=1,depth=2);prim('cyl','SpireTop',(x,y,h+.6),(.5,.42,.33),scale=(r*.35,r*.35,1.2),vertices=8,radius=1,depth=2)
 ax,ay,z0,z1=S['arch']
 for sy in (-1,1):prim('cube','ArchPillar',(ax,sy*ay,z1/2),(.44,.36,.28),scale=(2.2,2.0,z1/2))
 prim('cube','ArchBeam',(ax,0,(z0+z1)/2+1),(.46,.38,.3),scale=(2.4,ay+2.0,(z1-z0)/2+1))
 for k in range(26):
  x=S['x0']+rnd.uniform(0,2*L);y=rnd.uniform(-30,30);z=rnd.uniform(48,90);s=rnd.uniform(8,16);prim('sphere','Cloud',(x,y,z),(.95,.95,.98),scale=(s,s*.6,s*.28),subdivisions=2)
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=4.;sn.data.color=(1,.93,.8);sn.rotation_euler=(math.radians(50),0,math.radians(70));link(sn)

REGISTRY={'mountain_village':dict(consts=lambda:VILLAGE,states=('intact','buried'),build=_village,piece_default='avalanche'),'citadel':dict(consts=lambda:CITADEL,states=('intact','breached'),build=_citadel,piece_default='siege'),
 'arena_ruins':dict(states=('intact',),build=_arena_ruins,piece_default='arena_duel'),
 'railway_plains':dict(states=('intact',),build=_railway,piece_default='great_escape',params=True),
 'catapult':dict(states=('intact',),build=_prop_catapult,piece_default=None),
 'winch':dict(states=('intact',),build=_prop_winch,piece_default=None),
 'knife':dict(states=('intact',),build=_prop_knife,piece_default=None),
 'banner':dict(states=('intact',),build=_prop_banner,piece_default=None),
 'ladder':dict(states=('intact',),build=_prop_ladder,piece_default=None,params=True),
 'egg_nest':dict(states=('intact',),build=_prop_egg_nest,piece_default=None),
 'dino_valley':dict(consts=lambda:DINO_VALLEY,states=('intact',),build=_dino_valley,piece_default='last_egg'),
 'cliff_face':dict(consts=lambda:(CLIFF,CLIFF_LIMBS,CLIFF_STEP),states=('intact',),build=_cliff_face,piece_default='cliff_rescue'),
 'galleon':dict(consts=lambda:SHIP,states=('intact',),build=_galleon,piece_default='storm_ship'),
 'open_sea':dict(states=('intact',),build=_open_sea,piece_default='storm_ship'),
 'council_hall':dict(consts=lambda:COUNCIL,states=('intact',),build=_council_hall,piece_default='council'),
 'goblet':dict(states=('intact',),build=_prop_goblet,piece_default=None),
 'scroll':dict(states=('intact',),build=_prop_scroll,piece_default=None),
 'gavel':dict(states=('intact',),build=_prop_gavel,piece_default=None),
 'museum_hall':dict(consts=lambda:MUSEUM,states=('intact',),build=_museum_hall,piece_default='heist'),
 'workshop':dict(consts=lambda:WORKSHOP,states=('intact',),build=_workshop,piece_default='workshop'),
 'rapids':dict(consts=lambda:RAPIDS,states=('intact',),build=_rapids,piece_default='rapids'),
 'flood_valley':dict(consts=lambda:FLOOD,states=('intact',),build=_flood_valley,piece_default='flood'),
 'sky_canyon':dict(consts=lambda:SKY,states=('intact',),build=_sky_canyon,piece_default='flight'),
 'train_consist':dict(states=('intact',),build=_train_consist,piece_default='great_escape',params=True)}
def bank_path(id_,state='intact',params=None):
 import inspect
 h=hashlib.sha1((inspect.getsource(REGISTRY[id_]['build'])+inspect.getsource(_make_ctx)+repr(REGISTRY[id_].get('consts',lambda:None)())).encode()).hexdigest()[:8];ph=hashlib.sha1(json.dumps(params,sort_keys=True,default=list).encode()).hexdigest()[:6] if params else '-'
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
def prune():
 """Delete bank files whose builder changed since they were built (their hash is no longer current). Returns the deleted names."""
 gone=[]
 if not BANK.exists():return gone
 for f in BANK.glob('*.blend'):
  parts=f.stem.rsplit('_',3)
  if len(parts)<4:continue
  id_,state,ph,h=parts
  if id_ in REGISTRY and bank_path(id_,state,None).stem.rsplit('_',1)[-1]!=h:f.unlink();gone.append(f.name)
 return gone

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
import sys as _sys,os as _os
_sys.path.insert(0,_os.path.dirname(_os.path.abspath(__file__)))
try:
 import world2_locations as _w2
 REGISTRY.update(_w2.REGISTRY)
except ImportError:
 pass
if __name__=='__main__' and 'bpy' in sys.modules or (len(sys.argv)>2 and '--' in sys.argv and sys.argv[sys.argv.index('--')+1:][:1]==['build']):
 import bpy
 a=sys.argv[sys.argv.index('--')+1:]
 if a[:1]==['build']:
  bpy.ops.wm.read_factory_settings(use_empty=True);ctx=_make_ctx();(REGISTRY[a[1]]['build'](ctx,a[2],json.loads(a[4])) if REGISTRY[a[1]].get('params') else REGISTRY[a[1]]['build'](ctx,a[2]));bpy.ops.wm.save_as_mainfile(filepath=a[3]);print('LOCATION_BUILT',a[1],a[2],len(bpy.data.objects),'objects')