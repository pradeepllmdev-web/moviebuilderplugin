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
