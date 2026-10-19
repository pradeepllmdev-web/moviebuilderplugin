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
