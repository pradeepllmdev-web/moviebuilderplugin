"""Shared locations: built ONCE into a bank file (bank/<id>_<state>_<hash>.blend) and appended into every scene that uses them.

  python locations.py build mountain_village intact      (run through Blender by ensure(); normally you never call this by hand)

Pure parts (no Blender needed): village_terrain(x, y), VILLAGE and CITADEL constants, REGISTRY (id, states, builder), bank_path, ensure.
Inside Blender: load(id, ctx, state) appends the cached objects (or builds them in place when the bank file is missing). The bank file name contains a hash of this module, so changing a location
invalidates its cache automatically. Objects carry custom properties: 'rb' = rigid-body shape ('BOX' or 'MESH') for passive colliders, 'blk' = (column, row) for the breach blocks of the citadel.
A state describes what happened to the place: mountain_village intact | buried (snow mounds), citadel intact | breached (breach section replaced by rubble)."""
import math,random,sys,hashlib,subprocess
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
REGISTRY={'mountain_village':dict(states=('intact','buried'),build=_village,piece_default='avalanche'),'citadel':dict(states=('intact','breached'),build=_citadel,piece_default='siege')}
def bank_path(id_,state='intact'):
 h=hashlib.sha1(Path(__file__).read_bytes()).hexdigest()[:8];return BANK/('%s_%s_%s.blend'%(id_,state,h))
def ensure(id_,state='intact'):
 """Path of the bank file, building it in a separate Blender process the first time (outside Blender only)."""
 if id_ not in REGISTRY or state not in REGISTRY[id_]['states']:raise ValueError('unknown location or state: %s %s'%(id_,state))
 path=bank_path(id_,state)
 if path.exists():return path
 BANK.mkdir(exist_ok=True)
 for old in BANK.glob('%s_%s_*.blend'%(id_,state)):old.unlink()
 import quick_review
 subprocess.run([quick_review.BLENDER,'-b','--python',str(Path(__file__).resolve()),'--','build',id_,state,str(path)],capture_output=True,text=True,errors='ignore',timeout=900)
 return path if path.exists() else None
def load(id_,ctx,state='intact'):
 """Inside Blender: append the location into the current scene (from the bank file when it exists, otherwise built in place). Returns dict(path or None)."""
 import bpy
 if id_ not in REGISTRY or state not in REGISTRY[id_]['states']:raise ValueError('unknown location or state: %s %s'%(id_,state))
 path=bank_path(id_,state)
 if path.exists():
  with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=list(src.objects)
  for o in dst.objects:
   if o is not None:ctx['link'](o)
  return dict(path=str(path),cached=True)
 REGISTRY[id_]['build'](ctx,state);return dict(path=None,cached=False)
def ensure_for(piece,params=None):
 """Bank files a set piece needs (called by set_pieces.build before the scene runs)."""
 params=params or {};out=[]
 for lid,meta in REGISTRY.items():
  if meta['piece_default']==piece:
   st=params.get('location_state') if params.get('location_state') in meta['states'] else 'intact';out.append(ensure(lid,st))
 return out
def _make_ctx():
 import bpy
 scene=bpy.context.scene;mats={}
 def link(o):
  if o.name not in scene.collection.objects:scene.collection.objects.link(o)
 def mat(name,color):
  if name in mats:return mats[name]
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
  if b:b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
  mats[name]=m;return m
 def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),**kw):
  if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
  elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
  else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
  o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0]+str(color),color));return o
 return dict(link=link,mat=mat,prim=prim)
if __name__=='__main__' and 'bpy' in sys.modules or (len(sys.argv)>2 and '--' in sys.argv and sys.argv[sys.argv.index('--')+1:][:1]==['build']):
 import bpy
 a=sys.argv[sys.argv.index('--')+1:]
 if a[:1]==['build']:
  bpy.ops.wm.read_factory_settings(use_empty=True);ctx=_make_ctx();REGISTRY[a[1]]['build'](ctx,a[2]);bpy.ops.wm.save_as_mainfile(filepath=a[3]);print('LOCATION_BUILT',a[1],a[2],len(bpy.data.objects),'objects')
