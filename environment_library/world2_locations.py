"""Second world of shared locations (ice cave, desert ruins, jungle temple, reef, forge, sky city, market, swamp, mage tower, rope bridge, observatory, colossus).
Registered into locations.REGISTRY (see the end of locations.py); each builder is a pure function of (ctx, state) like the first generation."""
import math,random
class _R(dict):pass
REGISTRY={}
def reg(id_,build,consts=None,piece='world2',states=('intact',)):
 d=dict(states=states,build=build,piece_default=piece)
 if consts is not None:d['consts']=(lambda c=consts:c)
 REGISTRY[id_]=d
# ------------------------------------------------------------------------------------------------ 1 ice cave
ICE=dict(x0=-14.,x1=96.,hw=15.,ceil=17.,floes=[(8.5+6.2*k,[1.5,-2.0,2.2,-1.2,2.4,-2.2,1.0,-1.8,1.6][k],2.0+.25*(k%3),2.6+.3*(k%2),.32+.04*(k%4),k*1.1) for k in range(9)],start_edge=5.,end_edge=62.)
def _ice_cave(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];I=ICE;rnd=random.Random(5);cx=(I['x0']+I['x1'])/2;L=(I['x1']-I['x0'])/2
 prim('cube','IceWater',(cx,0,-.4),(.03,.07,.12),scale=(L,I['hw'],.02))
 prim('cube','IceShelfStart',((I['x0']+I['start_edge'])/2,0,-.5),(.62,.8,.9),scale=((I['start_edge']-I['x0'])/2,I['hw'],.5))
 prim('cube','IceShelfEnd',((I['end_edge']+I['x1'])/2,0,-.5),(.62,.8,.9),scale=((I['x1']-I['end_edge'])/2,I['hw'],.5))
 for sy in (-1,1):prim('cube','IceWall',(cx,sy*(I['hw']+3),I['ceil']/2),(.5,.72,.85),scale=(L,3,I['ceil']/2))
 prim('cube','IceWallEnd',(I['x1']+3,0,I['ceil']/2),(.5,.72,.85),scale=(3,I['hw'],I['ceil']/2));prim('cube','IceWallStart',(I['x0']-3,0,I['ceil']/2),(.5,.72,.85),scale=(3,I['hw'],I['ceil']/2))
 prim('cube','IceCeiling',(cx,0,I['ceil']+1.5),(.45,.65,.8),scale=(L,I['hw']+6,1.5))
 for k in range(90):
  x=rnd.uniform(I['x0'],I['x1']);y=rnd.uniform(-I['hw'],I['hw']);h=rnd.uniform(1.5,5.5);r=rnd.uniform(.3,1.0)
  prim('cone','Stalactite',(x,y,I['ceil']-h/2),(.7,.85,.95),scale=(r,r,h/2),rot=(math.pi,0,0),vertices=7,radius1=1,depth=2)
 for k in range(30):
  x=rnd.uniform(I['x0'],I['x1']);sy=rnd.choice((-1,1));h=rnd.uniform(2,6);prim('cone','Crystal',(x,sy*(I['hw']-.5),h/2),(.4,.85,1.),scale=(.6,.6,h/2),vertices=6,radius1=1,depth=2,emit=2.5)
 for x in range(-10,110,20):
  lt=bpy.data.objects.new('CaveLight',bpy.data.lights.new('CaveLight','POINT'));lt.data.energy=6000;lt.data.color=(.55,.75,1);lt.location=(x,0,12);link(lt)
 sn=bpy.data.objects.new('CaveFill',bpy.data.lights.new('CaveFill','SUN'));sn.data.energy=.6;sn.data.color=(.6,.75,1);sn.rotation_euler=(math.radians(35),0,math.radians(80));link(sn)
reg('ice_cave',_ice_cave,ICE,'ice')
# ------------------------------------------------------------------------------------------------ 2 desert ruins (boulder corridor)
DESERT=dict(x0=-24.,x1=140.,hw=5.,wall_h=9.,pit=(89.0,92.6,4.),door_x=118.,statues=[(22.,1),(22.,-1),(36.,1),(36.,-1),(50.,1),(50.,-1),(64.,1),(64.,-1),(76.,1),(76.,-1)])
def _desert_ruins(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];D=DESERT;rnd=random.Random(17);px0,px1,pd=D['pit']
 prim('cube','Floor',((D['x0']+px0)/2,0,-.5),(.62,.5,.3),scale=((px0-D['x0'])/2,D['hw'],.5));prim('cube','Floor',((px1+D['x1'])/2,0,-.5),(.62,.5,.3),scale=((D['x1']-px1)/2,D['hw'],.5))
 prim('cube','PitBottom',((px0+px1)/2,0,-pd-.5),(.12,.1,.08),scale=((px1-px0)/2,D['hw'],.5))
 for sy in (-1,1):
  prim('cube','PitWall',((px0+px1)/2,sy*D['hw'],-pd/2),(.5,.4,.28),scale=((px1-px0)/2,.1,pd/2))
  prim('cube','Wall',((D['x0']+D['x1'])/2,sy*(D['hw']+1.2),D['wall_h']/2),(.7,.55,.35),scale=((D['x1']-D['x0'])/2,1.2,D['wall_h']/2))
  for k in range(26):
   x=D['x0']+3+k*6.2;prim('cube','WallPanel',(x,sy*(D['hw']-.05),3.2),(.85,.7,.35),scale=(2.2,.05,1.3),emit=.4);prim('cube','WallCap',(x+1.5,sy*(D['hw']+.3),D['wall_h']+.3),(.62,.5,.3),scale=(1.2,.8,.4))
  for x in range(-20,136,14):
   prim('cone','TorchFire',(x,sy*(D['hw']-.4),2.2),(1,.55,.15),scale=(.16,.16,.3),vertices=6,radius1=1,depth=2,emit=7.)
   lt=bpy.data.objects.new('TorchLight',bpy.data.lights.new('TorchLight','POINT'));lt.data.energy=450;lt.data.color=(1,.6,.28);lt.location=(x,sy*(D['hw']-1.0),2.6);link(lt)
 prim('cube','Sand',((D['x0']+D['x1'])/2,0,-.9),(.78,.64,.38),scale=((D['x1']-D['x0'])/2+30,40,.1))
 for k in range(14):
  x=rnd.uniform(D['x0'],D['x1']);y=rnd.choice((-1,1))*rnd.uniform(14,30);prim('sphere','Dune',(x,y,-3),(.82,.68,.4),scale=(rnd.uniform(10,20),rnd.uniform(6,10),rnd.uniform(4,7)),subdivisions=2)
 prim('cube','DoorFrame',(D['door_x'],0,D['wall_h']-1.2),(.62,.5,.3),scale=(1.6,D['hw']+.6,1.2));prim('cube','DoorPostL',(D['door_x'],-D['hw']-.4,4.5),(.62,.5,.3),scale=(1.6,.8,4.5));prim('cube','DoorPostR',(D['door_x'],D['hw']+.4,4.5),(.62,.5,.3),scale=(1.6,.8,4.5))
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=3.;sn.data.color=(1,.85,.65);sn.rotation_euler=(math.radians(55),0,math.radians(-60));link(sn)
reg('desert_ruins',_desert_ruins,DESERT,'ruins')
# ------------------------------------------------------------------------------------------------ 3 jungle temple (vine swings)
def _jungle_consts():
 px=[0.,14.,28.,42.,56.,70.];pz=[0.,0.,0.,0.,0.,0.];LB=12.;TH=math.radians(24.6);DROP=.8
 anchors=[((px[k]+px[k+1])/2,pz[k]+.7+DROP+LB*math.cos(TH)) for k in range(len(px)-1)]
 return dict(px=px,pz=pz,pr=3.0,LB=LB,TH=TH,DROP=DROP,anchors=anchors,temple_x=84.,hw=22.)
JUNGLE=_jungle_consts()
def _jungle_temple(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];J=JUNGLE;rnd=random.Random(33)
 for k,(x,z) in enumerate(zip(J['px'],J['pz'])):
  prim('cyl','Platform',(x,0,z/2-3),(.5,.5,.42),scale=(J['pr'],J['pr'],z/2+3.),vertices=14,radius=1,depth=2);prim('cyl','PlatformMoss',(x,0,z+.02),(.2,.45,.2),scale=(J['pr']*.8,J['pr']*.8,.03),vertices=14,radius=1,depth=2)
 for k,(ax,az) in enumerate(J['anchors']):
  prim('cyl','Branch',(ax,1.6,az+.5),(.3,.2,.12),scale=(.55,.55,1.8),rot=(math.pi/2,0,0),vertices=8,radius=1,depth=2);prim('cyl','BranchTrunk',(ax,3.3,(az+.5)/2),(.3,.2,.12),scale=(1.1,1.1,(az+.5)/2),vertices=8,radius=1,depth=2)
 prim('cube','RavineFloor',(40,0,-9),(.12,.2,.14),scale=(70,J['hw']+10,.5));prim('cube','Mist',(40,0,-4),(.7,.8,.8),scale=(70,J['hw']+10,.05),emit=.15)
 for sy in (-1,1):
  for k in range(34):
   x=rnd.uniform(-16,100);y=sy*rnd.uniform(J['hw'],J['hw']+12);h=rnd.uniform(14,26);prim('cyl','Tree',(x,y,h/2-6),(.28,.2,.12),scale=(rnd.uniform(.7,1.4),)*2+(h/2,),vertices=7,radius=1,depth=2)
   prim('sphere','Canopy',(x,y,h-6),(.1,.35,.14),scale=(rnd.uniform(4,7),rnd.uniform(4,7),rnd.uniform(2.5,4)),subdivisions=2)
   for v in range(2):prim('cyl','Vine',(x+rnd.uniform(-2,2),y-sy*rnd.uniform(1,3),h-6-4),(.15,.4,.15),scale=(.06,.06,rnd.uniform(3,5)),vertices=5,radius=1,depth=2)
 tx=J['temple_x']
 for i in range(5):prim('cube','TempleStep',(tx+i*1.1,0,.2+i*.5),(.48,.46,.4),scale=(3.4-i*.3,6.5-i*.6,.25))
 prim('cube','TempleBack',(tx+8.5,0,5),(.46,.44,.38),scale=(.8,8,5));prim('cube','TempleRoof',(tx+6,0,10.5),(.42,.4,.34),scale=(3.8,8.5,.5))
 for sy in (-1,1):prim('cyl','TempleColumn',(tx+4.5,sy*6,5),(.5,.48,.42),scale=(.9,.9,5),vertices=10,radius=1,depth=2)
 prim('cyl','IdolBase',(tx+7,0,3.0),(.55,.5,.4),scale=(1.4,1.4,1.0),vertices=12,radius=1,depth=2);prim('sphere','IdolBody',(tx+7,0,4.8),(.6,.55,.42),scale=(1.3,1.1,1.6),subdivisions=2)
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=3.;sn.data.color=(1,.95,.75);sn.rotation_euler=(math.radians(50),0,math.radians(120));link(sn)
 fl=bpy.data.objects.new('GreenFill',bpy.data.lights.new('GreenFill','POINT'));fl.data.energy=8000;fl.data.color=(.6,1,.7);fl.location=(40,0,14);link(fl)
reg('jungle_temple',_jungle_temple,JUNGLE,'jungle')
# ------------------------------------------------------------------------------------------------ 4 reef (underwater)
def _reef_consts():
 r=random.Random(77);rocks=[(r.uniform(12,150),r.choice((-1,1))*r.uniform(5,16),-12+r.uniform(0,2),r.uniform(2.2,4.2)) for _ in range(16)]
 return dict(x0=-10.,x1=170.,hw=40.,floor=-12.,rocks=rocks,clam=(78.,0.,-12.),crevice=(152.,-3.,-12.),surface=0.)
REEF=_reef_consts()
def _reef(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];R=REEF;rnd=random.Random(78);cx=(R['x0']+R['x1'])/2;L=(R['x1']-R['x0'])/2
 prim('cube','Seabed',(cx,0,R['floor']-.5),(.72,.68,.5),scale=(L+20,R['hw'],.5));prim('cube','DustSurfaceGlow',(cx,0,2),(.5,.8,1.),scale=(L+20,R['hw'],.05),emit=.5)
 for (x,y,z,r) in R['rocks']:prim('sphere','Rock',(x,y,z),(.38,.4,.42),scale=(r,r*rnd.uniform(.8,1.1),r*rnd.uniform(.8,1.3)),subdivisions=2)
 cols=[(.9,.3,.4),(.95,.55,.2),(.7,.25,.8),(.3,.8,.6),(.95,.85,.3)]
 for k in range(260):
  x=rnd.uniform(R['x0'],R['x1']);y=rnd.uniform(-R['hw']*.7,R['hw']*.7);c=rnd.choice(cols);h=rnd.uniform(.8,3.2)
  if rnd.random()<.55:prim('cone','Coral',(x,y,R['floor']+h/2),c,scale=(rnd.uniform(.3,.9),)*2+(h/2,),vertices=7,radius1=1,depth=2)
  else:prim('sphere','CoralBrain',(x,y,R['floor']+h*.3),c,scale=(h*.6,h*.6,h*.4),subdivisions=1)
 for k in range(70):
  x=rnd.uniform(R['x0'],R['x1']);y=rnd.uniform(-R['hw']*.7,R['hw']*.7);h=rnd.uniform(4,9);prim('cyl','Kelp',(x,y,R['floor']+h/2),(.12,.45,.2),scale=(.12,.12,h/2),vertices=5,radius=1,depth=2)
 cx_,cy_,cz_=R['crevice']
 for sy in (-1,1):prim('sphere','CreviceRock',(cx_+3,cy_+sy*2.3,cz_+1.8),(.3,.32,.36),scale=(4.5,1.8,3.8),subdivisions=2)
 prim('sphere','CreviceRoof',(cx_+3,cy_,cz_+4.8),(.3,.32,.36),scale=(5,3,1.5),subdivisions=2)
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('Sun','SUN'));sn.data.energy=3.5;sn.data.color=(.55,.8,1);sn.rotation_euler=(math.radians(25),0,math.radians(70));link(sn)
 for x in range(0,170,30):
  lt=bpy.data.objects.new('ReefLight',bpy.data.lights.new('ReefLight','POINT'));lt.data.energy=5000;lt.data.color=(.5,.8,1);lt.location=(x,0,-3);link(lt)
reg('reef',_reef,REEF,'reef')
