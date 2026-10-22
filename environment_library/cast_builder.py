"""Blender side of the cast registry: turns a resolved look (cast_registry.resolve) into a character on the lion rig.

    import scene_base as sb, cast_builder as cb
    ch=cb.build(S, look, tag)          # S.character with the tint, root scale (width, depth, height), body parts and accessories parented to the rig's bones

The geometry is data first: part_prims(look) and accessory_prims(look) return plain dicts (shape, name, location, scale, rotation, colour, bone) in the lion's idle-pose space (metres, forward is -Y, head centre about (0,-.12,1.45), top of the mane at z 1.71), no Blender needed,
so tests can check them (every prim has a known bone, sizes stay near the lion's body, the head items sit on the head). build() creates the primitives, then parents each to its bone with a parent-inverse computed from the evaluated idle pose, so it
follows the clip exactly and keeps its place. The root scale is set last (the root is an unscaled empty until then, so nothing is corrected twice)."""
import math
from cast_registry import hash_unit
PI=math.pi
HC=(0.,-.12,1.45)                 # head centre, lion idle pose
LIMB_BONES={n:'mixamorig:'+n for n in ('LeftArm','LeftForeArm','RightArm','RightForeArm','LeftUpLeg','LeftLeg','RightUpLeg','RightLeg','LeftFoot','RightFoot','LeftHand','RightHand')}
BONES={'head':'mixamorig:Head','neck':'mixamorig:Neck','spine':'mixamorig:Spine2','spine1':'mixamorig:Spine1','hips':'mixamorig:Hips','hand_r':'mixamorig:RightHand','hand_l':'mixamorig:LeftHand','tail':'Tail'}
BONES.update(LIMB_BONES)
def T(name,bone,r,t0,t1,color):
 """a tube along a limb bone from fraction t0 to t1 of its length (radius r, metres at scale 1): sleeves, trousers, boots follow the bone exactly"""
 return dict(shape='tube',name=name,loc=(0,0,0),scale=(1,1,1),rot=(0,0,0),color=tuple(color),bone=bone,emit=0.,kw={},r=r,t0=t0,t1=t1)
PALETTE=[(.75,.15,.12),(.15,.35,.7),(.2,.55,.3),(.85,.65,.15),(.5,.25,.6),(.9,.9,.85),(.55,.35,.2),(.2,.5,.55)]
GOLD=(.95,.75,.2);STEEL=(.7,.72,.78);LEATHER=(.4,.26,.14);CLOTH=(.85,.8,.7);DARK=(.1,.1,.12)
def P(shape,name,loc,scale,color,bone,rot=(0,0,0),emit=0.,kw=None):return dict(kw=dict(kw or {}),shape=shape,name=name,loc=loc if isinstance(loc,str) else tuple(loc),scale=tuple(scale),rot=tuple(rot),color=tuple(color),bone=bone,emit=emit)
# fitted garments are cut from the lion's own body mesh (so they bend exactly with the skeleton), pushed out along the normals: (vertex groups, height range in cm, offset in cm)
ARMS=('LeftArm','RightArm','LeftForeArm','RightForeArm');LEGS=('Hips','LeftUpLeg','RightUpLeg','LeftLeg','RightLeg')
FITTED={'shirt':(('Head','Spine','Spine1','Spine2','LeftShoulder','RightShoulder','Hips','LeftUpLeg','RightUpLeg')+ARMS,(56,200),1.9,88),'sleeves':(ARMS,(0,200),3.0,0),'shortsleeves':(('LeftArm','RightArm'),(0,200),3.0,0),
 'pants':(LEGS,(0,72),2.0,0),'shorts':(('Hips','LeftUpLeg','RightUpLeg'),(34,72),2.0,0),'gloves':(('LeftHand','RightHand'),(0,200),1.4,0),'boots':(('LeftFoot','RightFoot','LeftToeBase','RightToeBase','LeftLeg','RightLeg'),(0,15),1.5,0)}
def fitted(S,ch,name,kind,color,color2=None):
 """one fitted garment as a copy of the body mesh with only the wanted faces, sharing its armature and weights; zh>0 lets head-weighted vertices below that height in; FIT_OPT: open=cm (an opening down the front, a jacket or vest), front=cm (only the front panel, a bib), pattern=plaid|stripe (a second colour)"""
 import bpy,bmesh
 groups,zr,off,zh=FITTED[kind];op=FIT_OPT.get(kind,{});body=[o for o in ch['objs'] if o.name.startswith('char1')][0]
 names={g.index:g.name.split(':')[-1] for g in body.vertex_groups}
 new=body.copy();new.data=body.data.copy();new.name=name;bpy.context.scene.collection.objects.link(new)
 bm=bmesh.new();bm.from_mesh(new.data);dl=bm.verts.layers.deform.active;ok={}
 for v in bm.verts:
  d=v[dl]
  if not d:ok[v.index]=False;continue
  ok[v.index]=zr[0]<=v.co.z<=zr[1] and sum(w for g,w in ((names[i],w) for i,w in d.items()) if g in groups and (g!='Head' or v.co.z<=zh))>=.5
 def cut(f):
  if not all(ok[v.index] for v in f.verts):return True
  if 'open' in op and all(abs(v.co.x)<op['open'] and v.co.y<-16 for v in f.verts):return True
  if 'front' in op and not all(abs(v.co.x)<op['front'] and v.co.y<-16 for v in f.verts):return True
  return False
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if cut(f)],context='FACES')
 bm.verts.ensure_lookup_table();bm.normal_update()
 for v in bm.verts:v.co+=v.normal*off
 pat=op.get('pattern');cuff=op.get('cuff',0.);zmin=min((v.co.z for v in bm.verts),default=0.)
 for f in bm.faces:
  x,y,z=f.calc_center_median()
  f.material_index=2 if (cuff and z<zmin+cuff) else 1 if (pat=='plaid' and (x%11<2.4 or z%11<2.4)) or (pat=='stripe' and z%12<4.5) else 0
 bm.to_mesh(new.data);bm.free();new.data.materials.clear();new.data.materials.append(S.mat(name,color,0))
 new.data.materials.append(S.mat(name+'_b',color2 or (_trim(color) if pat=='plaid' else (.93,.92,.88)),0));new.data.materials.append(S.mat(name+'_c',_trim(color),0))
 return new
import cast_garments as cg
TORSO=('Head','Spine','Spine1','Spine2','Hips','LeftUpLeg','RightUpLeg','LeftShoulder','RightShoulder')
FITTED.update({'tshirt':(TORSO+('LeftArm','RightArm'),(58,200),1.9,88),'jacket':(TORSO+ARMS,(46,200),2.9,88),'vest':(TORSO,(50,200),2.5,88),'tunicbody':(TORSO+('LeftArm','RightArm'),(60,200),2.2,88),
 'bodice':(TORSO,(60,200),1.9,88),'robebody':(TORSO+ARMS,(60,200),2.4,88),'plate':(TORSO,(64,200),3.0,88),'bib':(('Spine','Spine1','Spine2','Hips'),(58,100),2.2,0),
 'plaidshirt':FITTED['shirt'],'stripedshirt':FITTED['shirt'],'plaidsleeves':FITTED['sleeves'],'stripedsleeves':FITTED['sleeves']})
FIT_OPT={'jacket':dict(open=5.5),'vest':dict(open=6.),'bib':dict(front=13.),'plaidsleeves':dict(pattern='plaid',cuff=5.),'stripedsleeves':dict(pattern='stripe',cuff=5.),'sleeves':dict(cuff=5.),'shortsleeves':dict(cuff=4.),'pants':dict(cuff=4.)}
SKIN_POOL=('Hips','LeftUpLeg','RightUpLeg','LeftLeg','RightLeg','Spine','Spine1')
# kind -> pieces: ('fit', fitted kind, colour), ('skirt', cast_garments.SKIRTS key, colour), ('cape',); colours: c main, t trim, steel, white
# shells: torso skins from cast_garments.shell (name -> arguments); fit = cut from the body; skirt = cast_garments.SKIRTS
SHELLS={'waist':dict(z0=74,z1=46,off=2.3,neck=False),'shirt':dict(z0=90,z1=54,off=2.1),'tshirt':dict(z0=90,z1=56,off=2.1),'plaidshirt':dict(z0=90,z1=54,off=2.1,pattern='plaid'),'stripedshirt':dict(z0=90,z1=54,off=2.1,pattern='stripe'),'jacket':dict(z0=90,z1=44,off=3.4,gap=.3,hem=2),'vest':dict(z0=90,z1=52,off=2.9,gap=.3,hem=1.5),
 'dressshirt':dict(z0=90,z1=44,off=2.1),'tunicbody':dict(z0=90,z1=60,off=2.4),'bodice':dict(z0=90,z1=66,off=2.1),'robebody':dict(z0=90,z1=60,off=2.8),'plate':dict(z0=90,z1=62,off=3.6,hem=2),'bib':dict(z0=84,z1=60,off=2.5,arc=(-math.pi/2-.62,-math.pi/2+.62),seg=14,neck=False),
 'strapL':dict(z0=96,z1=80,off=2.7,arc=(-math.pi/2+.42,-math.pi/2+.56),seg=2,neck=False,step=2.),'strapR':dict(z0=96,z1=80,off=2.7,arc=(-math.pi/2-.56,-math.pi/2-.42),seg=2,neck=False,step=2.)}
COMPOSE={'pants':[('fit','pants','c'),('shell','waist','c')],'shorts':[('fit','shorts','c'),('shell','waist','c')],'shirt':[('shell','shirt','c'),('fit','sleeves','c')],'tshirt':[('shell','tshirt','c'),('fit','shortsleeves','c')],'plaidshirt':[('shell','plaidshirt','c'),('fit','plaidsleeves','c')],'stripedshirt':[('shell','stripedshirt','c'),('fit','stripedsleeves','c')],
 'jacket':[('shell','jacket','c'),('fit','sleeves','c')],'vest':[('shell','vest','c')],
 'tunic':[('shell','tunicbody','c'),('fit','shortsleeves','c'),('skirt','tunic','c')],'dress':[('shell','bodice','c'),('skirt','dress','c')],'robe':[('shell','robebody','c'),('fit','sleeves','c'),('skirt','robe','c')],'armor':[('shell','plate','steel'),('skirt','tassets','c')],
 'poncho':[('skirt','poncho','c')],'apron':[('shell','bib','c'),('skirt','apronskirt','c')],'overalls':[('fit','pants','c'),('shell','waist','c'),('shell','bib','c'),('shell','strapL','c'),('shell','strapR','c')],'kilt':[('skirt','kilt','c')],'cape':[('cape',)],
 'suit':[('shell','jacket','c'),('fit','sleeves','c'),('shell','dressshirt','white'),('fit','pants','c'),('shell','waist','c')]}
GARMENT_KINDS=(set(COMPOSE)|set(cg.HATS))-{'armor','cape'}
HATZ={'helmet':1.6,'hat_cap':1.55,'hat_beanie':1.5,'hat_cowboy':1.6,'hat_sou':1.62,'hat_straw':1.66}
HATSCALE={'hat_cap':1.18,'hat_beanie':1.1}
HATCOL={'hat_top':lambda c:(c,GOLD),'hat_wizard':lambda c:(c,GOLD),'hat_straw':lambda c:((.85,.72,.4),c),'hat_cowboy':lambda c:((.55,.38,.2),c),'helmet':lambda c:(STEEL,c),'crown':lambda c:(GOLD,GOLD)}
def _mesh_object(S,name,V,F,M,cols,like=None):
 """a mesh object from raw geometry with one material per colour; like = an object whose parent, modifiers and transform it copies (the body, to share the skeleton)"""
 import bpy
 me=bpy.data.meshes.new(name);me.from_pydata([tuple(v) for v in V],[],[tuple(f) for f in F]);me.update()
 for pl,mi in zip(me.polygons,M):pl.material_index=min(mi,len(cols)-1)
 try:
  for pl in me.polygons:pl.use_smooth=True
 except Exception:pass
 for j,col in enumerate(cols):me.materials.append(S.mat('%s_%d'%(name,j),col,0))
 if like is None:o=bpy.data.objects.new(name,me)
 else:o=like.copy();o.data=me;o.name=name;[o.vertex_groups.new(name=g.name) for g in like.vertex_groups]
 bpy.context.scene.collection.objects.link(o);return o
_ENV={}
TORSO_GROUPS=('Spine','Spine1','Spine2','Hips','LeftUpLeg','RightUpLeg','LeftShoulder','RightShoulder')
def _envelope(body,seg=40,dz=2.5):
 """per height slab of the torso: centre y and, for seg angles, how far the body reaches (support function of its vertices); smoothed across rows and angles, so a shell around it is clean where the body mesh is lumpy with fur"""
 key=body.as_pointer()
 if key not in _ENV:
  names={g.index:g.name.split(':')[-1] for g in body.vertex_groups};slabs={}
  for v in body.data.vertices:
   if v.groups and (names[max(v.groups,key=lambda g:g.weight).group] in TORSO_GROUPS or (v.co.z>=84 and names[max(v.groups,key=lambda g:g.weight).group] in ('LeftArm','RightArm'))):slabs.setdefault(int(round(v.co.z/dz)),[]).append((v.co.x,v.co.y))
  zs=sorted(k for k,p in slabs.items() if len(p)>=12);raw={}
  for k in zs:
   pts=slabs[k];cy=(max(p[1] for p in pts)+min(p[1] for p in pts))/2
   raw[k]=(cy,[max(x*math.cos(2*math.pi*b/seg)+(y-cy)*math.sin(2*math.pi*b/seg) for x,y in pts) for b in range(seg)])
  sm={}
  for n,k in enumerate(zs):
   nb=[raw[zs[min(len(zs)-1,max(0,n+d))]] for d in(-1,0,1)];cy=sum(a[0] for a in nb)/3;rad=[sum(a[1][b] for a in nb)/3 for b in range(seg)]
   sm[k*dz]=(cy,[(rad[b-1]+2*rad[b]+rad[(b+1)%seg])/4 for b in range(seg)])
  _ENV[key]=sm
 return _ENV[key]
def _env_fn(body):
 sm=_envelope(body);ks=sorted(sm)
 def f(z):
  z=min(max(z,ks[0]),ks[-1]);i=max(j for j in range(len(ks)) if ks[j]<=z);j=min(i+1,len(ks)-1);t=0. if j==i else (z-ks[i])/(ks[j]-ks[i]);a,b=sm[ks[i]],sm[ks[j]]
  return a[0]*(1-t)+b[0]*t,[p*(1-t)+q*t for p,q in zip(a[1],b[1])]
 return f
_POOL={}
def _skin(body,o,ts,anchor,pool,ramp=1.2,k=4):
 """weights of a loft: inverse-distance blend of the nearest body vertices (only those of the pool groups), faded in from the anchor group at the top (t=0) so a skirt hangs from the waist and follows the legs lower down"""
 from mathutils import kdtree
 key=(body.as_pointer(),pool)
 if key not in _POOL:
  names={g.index:g.name.split(':')[-1] for g in body.vertex_groups};pts=[];ws=[]
  for v in body.data.vertices:
   if not v.groups or names[max(v.groups,key=lambda g:g.weight).group] not in pool:continue
   pts.append(v.co.copy());ws.append({names[g.group]:g.weight for g in v.groups if g.weight>.01})
  kd=kdtree.KDTree(len(pts))
  for i,p in enumerate(pts):kd.insert(p,i)
  kd.balance();_POOL[key]=(kd,ws)
 kd,ws=_POOL[key];real={g.name.split(':')[-1]:g.name for g in o.vertex_groups}
 for i,v in enumerate(o.data.vertices):
  acc={}
  for _,j,d in kd.find_n(v.co,k):
   for g,w in ws[j].items():acc[g]=acc.get(g,0.)+w/(d+.5)
  tot=sum(acc.values()) or 1.;acc={g:w/tot for g,w in acc.items()};a=min(.72,ts[i]*ramp) if anchor else 1.
  if anchor:
   acc={g:w*a for g,w in acc.items()};acc[anchor]=acc.get(anchor,0.)+1-a
  for g,w in sorted(acc.items(),key=lambda x:-x[1])[:4]:
   if g in real and w>.01:o.vertex_groups[real[g]].add([i],w,'REPLACE')
BUTTONED={'shirt':(86,60),'plaidshirt':(86,60),'stripedshirt':(86,60),'shirt_under':(86,50)}
def _buttons(S,body,name,z0,z1,off,color):
 """a row of small buttons down the front of a closed shirt, skinned to the torso like the shell it sits on"""
 import cast_garments as cg
 f=_env_fn(body);parts=[]
 for j in range(int((z0-z1)//8)+1):
  z=z0-8*j;cy,rad=f(z);m=len(rad);r=rad[(m*3)//4]+off+.5   # angle -pi/2 is index 3m/4
  parts.append(cg.lathe([(0.,-1.1,0),(.8,-.8,0),(1.1,0.,0),(.8,.8,0),(0.,1.1,0)],seg=8,cx=0.,cy=cy-r,zb=z))
 V,F,M=cg._join(*parts);o=_mesh_object(S,name,V,F,M,[color],like=body);_skin(body,o,[0.]*len(o.data.vertices),None,TORSO_GROUPS);return o
# limb garments: tubes fitted around the arm or leg of the body mesh (cleaner than cutting its faces): groups per side, part of the limb length, trim cuff, extra radius in cm
LIMBS={'sleeves':dict(g=('Arm','ForeArm'),frac=(0.,1.),cuff=True,off=1.9),'shortsleeves':dict(g=('Arm','ForeArm'),frac=(0.,.45),cuff=True,off=1.9),'plaidsleeves':dict(g=('Arm','ForeArm'),frac=(0.,1.),cuff=True,off=1.9,pattern='plaid'),'stripedsleeves':dict(g=('Arm','ForeArm'),frac=(0.,1.),cuff=True,off=1.9,pattern='stripe'),
 'pants':dict(g=('UpLeg','Leg'),frac=(0.,.93),cuff=True,off=1.7),'shorts':dict(g=('UpLeg','Leg'),frac=(0.,.42),cuff=True,off=1.7)}
_LIMBCACHE={}
def _limb_rings(body,groups,frac,off,n=14):
 """rings (centre, u, v, radius) along the vertices of the given groups: the limb axis is the principal direction of those vertices, pointing down; each ring is centred on its slab and as wide as the slab's 85th-percentile distance from the centre plus `off`, smoothed"""
 import numpy as np
 names={g.index:g.name.split(':')[-1] for g in body.vertex_groups};pts=[]
 for v in body.data.vertices:
  if v.groups and names[max(v.groups,key=lambda g:g.weight).group] in groups:pts.append(tuple(v.co))
 P=np.array(pts);c0=P.mean(0);_,_,vt=np.linalg.svd(P-c0,full_matrices=False);ax=vt[0]
 if ax[2]>0:ax=-ax
 u=np.cross(ax,(1.,0.,0.));u=u/np.linalg.norm(u) if np.linalg.norm(u)>.1 else np.cross(ax,(0.,1.,0.));u=u/np.linalg.norm(u);v=np.cross(ax,u)
 t=(P-c0)@ax;t0,t1=t.min(),t.max();rings=[]
 for k in range(n+1):
  tt=t0+(t1-t0)*(frac[0]+(frac[1]-frac[0])*k/n);sel=np.abs(t-tt)<(t1-t0)/(n*1.5)
  if sel.sum()<6:sel=np.argsort(np.abs(t-tt))[:12]
  Q=P[sel];c=Q.mean(0);d=np.linalg.norm((Q-c)-np.outer((Q-c)@ax,ax),axis=1);rings.append([c,np.percentile(d,85)])
 rr=[r[1] for r in rings];sm=[(rr[max(0,i-1)]+2*rr[i]+rr[min(len(rr)-1,i+1)])/4 for i in range(len(rr))]
 return [(tuple(r[0]),tuple(u),tuple(v),sm[i]+off) for i,r in enumerate(rings)]
def _limb_object(S,body,name,kind,color):
 import cast_garments as cg
 sp=LIMBS[kind];parts=[];pool=[]
 for side in ('Left','Right'):
  gr=tuple(side+x for x in sp['g']);pool+=list(gr);parts.append(cg.tube(_limb_rings(body,gr,sp['frac'],sp['off']),16,sp['cuff'],sp.get('pattern')))
 V,F,M=cg._join(*parts);pat=sp.get('pattern')
 o=_mesh_object(S,name,V,F,M,[color,_trim(color) if sp['cuff'] and not pat else ((.93,.92,.88) if pat=='stripe' else _trim(color))],like=body);_skin(body,o,[0.]*len(o.data.vertices),None,tuple(pool),k=3);return o
def _cloth_colors(spec,c):return {'c':c,'t':_trim(c),'steel':STEEL,'white':(.93,.92,.88),'leather':LEATHER}[spec]
def garment(S,ch,look,acc,i):
 """every Blender object of one accessory that is not a primitive: hats (rigid on the head bone), fitted pieces and skinned lofts (deformed by the skeleton), as a list"""
 import bpy
 k=acc['kind'];c=color_of(acc,look['id'],i);base='Acc_%s_%s'%(look['id'],k);rig=ch['rig'];body=[o for o in ch['objs'] if o.name.startswith('char1')][0];out=[]
 if k in cg.HATS:
  V,F,M=cg.hat(k,zb=HATZ.get(k,1.7));sc=HATSCALE.get(k,1.);V=[(x*sc,-.1+(y+.1)*sc,z) for x,y,z in V];main,trim=HATCOL.get(k,lambda c:(c,_trim(c)))(c);o=_mesh_object(S,base,V,F,M,[main,trim]);_to_bone(rig,o,'head');return [o]
 for j,pc in enumerate(COMPOSE.get(k,[('fit',k,'c')] if k in FITTED else [])):
  col=_cloth_colors(pc[2],c) if len(pc)>2 else c;nm='%s_%d'%(base,j)
  if pc[0]=='fit':out.append(_limb_object(S,body,nm,pc[1],col) if pc[1] in LIMBS else fitted(S,ch,nm,pc[1],col))
  elif pc[0]=='shell':
   opt=dict(SHELLS[pc[1]]);V,F,M=cg.shell(_env_fn(body),**opt);o=_mesh_object(S,nm,V,F,M,[col,_trim(col) if opt.get('pattern')=='plaid' else (.93,.92,.88) if opt.get('pattern') else (GOLD if pc[2]=='steel' else _trim(col))],like=body);_skin(body,o,[0.]*len(o.data.vertices),None,TORSO_GROUPS);out.append(o)
   if pc[1] in BUTTONED:out.append(_buttons(S,body,nm+'_btn',BUTTONED[pc[1]][0],BUTTONED[pc[1]][1],opt['off'],(.12,.1,.08) if sum(col)>1.8 else (.93,.9,.8)))
  elif pc[0]=='skirt':
   V,F,M,ts=cg.skirt(pc[1]);o=_mesh_object(S,nm,V,F,M,[col,_trim(col) if pc[2]!='steel' else GOLD],like=body);_skin(body,o,ts,'Hips',SKIN_POOL);out.append(o)
  elif pc[0]=='cape':
   V,F,M,ts=cg.cape();o=_mesh_object(S,nm,V,F,M,[c,_trim(c)],like=body);_skin(body,o,ts,'Spine2',SKIN_POOL,ramp=.9);out.append(o)
 return out
def _to_bone(rig,o,bone):
 """parent o to a bone of the rig keeping its world place"""
 import bpy
 from mathutils import Matrix
 bpy.context.view_layer.update();Wm=o.matrix_world.copy();pb=rig.pose.bones[BONES[bone]];o.parent=rig;o.parent_type='BONE';o.parent_bone=pb.name;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Wm;bpy.context.view_layer.update()
 Pm=o.matrix_world@Wm.inverted();o.matrix_parent_inverse=Pm.inverted();o.matrix_basis=Wm
def _trim(c):return tuple(min(1.,x*.55+.35) for x in c)
def color_of(acc,rid,i=0):
 return tuple(acc['color']) if acc.get('color') else PALETTE[int(hash_unit(rid,'acc%d'%i)*len(PALETTE))%len(PALETTE)]
def part_prims(look):
 """body parts (ears, horns, ruff, tusks, tail tuft, beak) as primitive dicts"""
 out=[];x0,y0,z0=HC
 for p in look['parts']:
  k=p['kind'];s=p.get('size',1.);c=p.get('color') or (.8,.8,.8);sh=p.get('shape','')
  for sg in (-1,1):
   n=lambda t:'Part_%s_%s%s'%(look['id'],t,'L' if sg>0 else 'R')
   if k=='ears':
    if sh=='round':out.append(P('sphere',n('ear'),(sg*.22,y0+.04,1.66),(.1*s,.055*s,.1*s),c,'head'))
    elif sh=='point':out.append(P('cone',n('ear'),(sg*.2,y0+.04,1.78+.04*s),(.085*s,.045*s,.15*s),c,'head',(0,sg*.2,0)))
    elif sh=='long':out.append(P('cyl',n('ear'),(sg*.12,y0+.06,1.98),(.055*s,.025*s,.28*s),c,'head',(.1,sg*.12,0)))
    elif sh=='side':out.append(P('sphere',n('ear'),(sg*.38,y0+.0,1.5),(.15*s,.05*s,.08*s),c,'head',(0,sg*.3,0)))
    elif sh=='tuft':out.append(P('cone',n('ear'),(sg*.17,y0+.0,1.76),(.05*s,.04*s,.16*s),c,'head',(0,sg*.5,0)))
    elif sh=='disc':out.append(P('cyl',n('ear'),(sg*.3,y0+.02,1.64),(.17*s,.17*s,.015),c,'head',(PI/2,0,0)))
   elif k=='horns':
    out.append(P('cyl',n('horn'),(sg*.26,y0+.0,1.76),(.045*s,.045*s,.13*s),c,'head',(0,sg*.8,0)));out.append(P('cone',n('horntip'),(sg*.4,y0+.0,1.9),(.04*s,.04*s,.12*s),c,'head',(0,sg*.25,0)))
   elif k=='tusks':out.append(P('cone',n('tusk'),(sg*.13,y0-.44,1.26),(.035*s,.035*s,.12*s),c,'head',(.2,sg*-.2,0)))
  if k=='ruff':
   for i in range(10):
    a=2*PI*i/10;out.append(P('sphere','Part_%s_ruff%d'%(look['id'],i),(math.cos(a)*.3*s,y0+.04+math.sin(a)*.26*s,1.3),(.13*s,.13*s,.12*s),c,'neck'))
  elif k=='beak':out.append(P('cone','Part_%s_beak'%look['id'],(0,-.6-.04*s,1.36),(.07*s,.07*s,.14*s),c,'head',(-PI/2,0,0)))
  elif k=='tuft':out.append(P('sphere','Part_%s_tailtuft'%look['id'],'TAIL_TIP',(.11*s,.11*s,.11*s),c,'tail'))
 return out
def accessory_prims(look,hand_r=(-.36,-.1,.66),hand_l=(.36,-.1,.66)):
 """accessories as primitive dicts; hand positions come from the evaluated idle pose"""
 out=[];rid=look['id']
 for i,acc in enumerate(look['accessories']):
  k=acc['kind'];c=color_of(acc,rid,i);n=lambda t:'Acc_%s_%s_%s'%(rid,k,t);x0,y0,z0=HC
  if k in GARMENT_KINDS:pass
  elif k=='armor':out+=[P('sphere',n('padL'),(.3,-.12,1.0),(.11,.1,.07),STEEL,'spine',(0,.0,-.5)),P('sphere',n('padR'),(-.3,-.12,1.0),(.11,.1,.07),STEEL,'spine',(0,.0,.5))]
  elif k=='tie':out+=[P('cube',n('tie'),(0,-.352,.95),(.032,.01,.14),c,'spine1'),P('cube',n('knot'),(0,-.352,1.1),(.04,.012,.03),c,'spine1')]
  elif k=='cape':out.append(P('cyl',n('clasp'),(0,-.13,1.2),(.07,.07,.02),GOLD,'spine',(PI/2,0,0)))
  elif k=='glasses':
   for sg in (-1,1):out.append(P('cyl',n('lens%d'%sg),(sg*.11,-.46,1.47),(.06,.06,.01),(.7,.85,.95),'head',(PI/2,0,0)))
   out.append(P('cube',n('bridge'),(0,-.46,1.48),(.04,.01,.01),DARK,'head'))
  elif k=='eyepatch':out+=[P('cyl',n('patch'),(.11,-.465,1.47),(.085,.085,.012),DARK,'head',(PI/2,0,0)),P('cube',n('cord'),(.2,-.43,1.52),(.15,.008,.008),DARK,'head',(0,0,.5))]
  elif k=='flower':
   out.append(P('sphere',n('heart'),(.27,y0-.05,1.62),(.04,.04,.04),(.95,.85,.2),'head'))
   for j in range(5):a=2*PI*j/5;out.append(P('sphere',n('petal%d'%j),(.27+math.cos(a)*.06,y0-.07,1.62+math.sin(a)*.06),(.045,.025,.045),c,'head'))
  elif k=='scarf':out+=[P('cyl',n('wrap'),(0,y0+.06,1.17),(.25,.22,.06),c,'neck'),P('cube',n('end'),(.15,-.21,1.0),(.085,.025,.26),c,'spine'),P('cube',n('end2'),(.27,.0,1.12),(.03,.1,.05),c,'neck')]
  elif k=='bowtie':out+=[P('cone',n('a'),(.07,-.27,1.14),(.06,.06,.08),c,'neck',(0,PI/2,0)),P('cone',n('b'),(-.07,-.27,1.14),(.06,.06,.08),c,'neck',(0,-PI/2,0)),P('sphere',n('knot'),(0,-.27,1.14),(.035,.035,.035),c,'neck')]
  elif k=='backpack':out+=[P('cube',n('pack'),(0,.27,.98),(.2,.1,.22),LEATHER,'spine'),P('cyl',n('roll'),(0,.27,1.24),(.08,.08,.22),c,'spine',(0,PI/2,0))]
  elif k=='medals':
   for j in range(3):out.append(P('sphere',n('m%d'%j),(.16-j*.1,-.205,1.02),(.035,.015,.035),GOLD if j%2==0 else STEEL,'spine1'))
   out.append(P('cube',n('bar'),(.06,-.2,1.075),(.15,.01,.015),c,'spine1'))
  elif k=='armor':out+=[P('cyl',n('chest'),(0,-.01,1.0),(.38,.29,.22),STEEL,'spine'),P('sphere',n('padL'),(.3,-.12,1.0),(.11,.1,.07),STEEL,'spine',(0,.0,-.5)),P('sphere',n('padR'),(-.3,-.12,1.0),(.11,.1,.07),STEEL,'spine'),P('cyl',n('skirt'),(0,-.01,.72),(.39,.3,.09),c,'hips')]
  elif k in FITTED:pass
  elif k=='belt':out+=[P('cyl',n('band'),(0,-.02,.8),(.36,.28,.035),LEATHER,'hips'),P('cube',n('buckle'),(0,-.285,.8),(.04,.012,.035),GOLD,'hips')]
  elif k=='satchel':out+=[P('cube',n('bag'),(.37,.0,.72),(.07,.17,.15),LEATHER,'hips'),P('cube',n('strap'),(.0,-.19,1.0),(.025,.015,.3),LEATHER,'spine1',(0,-.75,.0))]
  elif k=='sword':out+=[P('cube',n('blade'),(.34,.12,.5),(.018,.012,.4),STEEL,'hips',(-.3,0,0)),P('cube',n('guard'),(.34,.06,.78),(.07,.014,.014),GOLD,'hips'),P('cyl',n('grip'),(.34,.05,.86),(.015,.015,.07),LEATHER,'hips')]
  elif k=='staff':out+=[P('cyl',n('shaft'),(hand_r[0],hand_r[1],.98),(.028,.028,1.04),LEATHER,'hand_r'),P('sphere',n('orb'),(hand_r[0],hand_r[1],2.0),(.07,.07,.07),c,'hand_r',emit=.8)]
  elif k=='cane':out+=[P('cyl',n('shaft'),(hand_r[0],hand_r[1],.4),(.02,.02,.4),LEATHER,'hand_r'),P('sphere',n('knob'),(hand_r[0],hand_r[1],.82),(.04,.04,.04),GOLD,'hand_r')]
  elif k=='lantern':out+=[P('cube',n('frame'),(hand_l[0],hand_l[1],hand_l[2]-.12),(.08,.08,.1),DARK,'hand_l'),P('sphere',n('flame'),(hand_l[0],hand_l[1],hand_l[2]-.12),(.065,.065,.065),(1.,.8,.35),'hand_l',emit=3.)]
  elif k=='banner':out+=[P('cyl',n('pole'),(hand_r[0],hand_r[1],1.05),(.02,.02,1.05),LEATHER,'hand_r'),P('cube',n('cloth'),(hand_r[0],hand_r[1]-.22,1.85),(.01,.22,.16),c,'hand_r')]
 return out
_TINTED={}
def tint_textures(ch,tint,size=1024):
 """the fur texture multiplied by the tint, so the character shows a tinted TEXTURE in every viewport mode and render (the viewport colour alone only helps flat shading); cached per source image and tint"""
 import bpy
 import numpy as np
 for o in ch['objs']:
  if o.type!='MESH':continue
  for slot in o.material_slots:
   m=slot.material
   if not m or not m.use_nodes:continue
   base=next((l.from_node for l in m.node_tree.links if l.to_socket.name=='Base Color' and l.from_node.type=='TEX_IMAGE'),None)
   if base is None or base.image is None:continue
   key=(base.image.name,tuple(round(v,3) for v in tint))
   if key not in _TINTED:
    img=base.image.copy();img.name='%s_tint%d'%(base.image.name,len(_TINTED))
    if img.size[0]>size:img.scale(size,size)
    n=len(img.pixels);a=np.empty(n,np.float32);img.pixels.foreach_get(a);a=a.reshape(-1,4);mx=max(tint)+1e-6;f=[min(1.6,1.3*v/mx) for v in tint];a[:,0]*=f[0];a[:,1]*=f[1];a[:,2]*=f[2]  ;np.clip(a,0,1,out=a);img.pixels.foreach_set(a.reshape(-1));img.update();img.pack();_TINTED[key]=img
   base.image=_TINTED[key]
import os
_A=os.path.join(os.path.dirname(os.path.abspath(__file__)),'assets')
_FARM=os.path.join(_A,'quaternius_farm_animals_download','extracted','Blends');_DINO=os.path.join(_A,'quaternius_dinosaurs_download','extracted','Dinosaur Animated Pack - Dec 2018','Blends')
CREATURE_FILES={n:(os.path.join(_FARM,n+'.blend'),'') for n in ('Pig','Cow','Horse','Llama','Pug','Sheep','Zebra')}
CREATURE_FILES.update({n:(os.path.join(_DINO,n+'.blend'),n+'_') for n in ('Trex','Triceratops','Velociraptor')})
def build_creature(S,look,tag):
 """a low-poly animal (own skeleton, own Idle/Walk/Run/Jump/Death actions) as a character dict: root (scaled to the look's height, facing like the lion rig), rig, objs, cact (short action name -> action), NLA tracks"""
 import bpy
 from mathutils import Vector
 path,prefix=CREATURE_FILES[look['creature']]
 with bpy.data.libraries.load(path,link=False) as (src,dst):dst.objects=list(src.objects);dst.actions=list(src.actions)
 root=bpy.data.objects.new(tag+'Root',None);S.link(root);objs=[]
 for o in dst.objects:
  if o is None or o.type in('CAMERA','LIGHT'):continue
  S.link(o);objs.append(o)
 for o in objs:
  if o.parent is None:o.parent=root
 bpy.context.view_layer.update()
 rig=next(o for o in objs if o.type=='ARMATURE');body=max((o for o in objs if o.type=='MESH'),key=lambda o:len(o.data.vertices))
 zs=[(body.matrix_world@Vector(c)).z for c in body.bound_box];h0=max(zs)-min(zs);k=look['height']/max(1e-6,h0);root.scale=(k,k,k)
 tint=look.get('tint',(1.,1.,1.))
 for o in objs:
  if o.type=='MESH':       # one level of subdivision and smooth shading: the low-poly body keeps its shape but loses the faceted edges
   sm=o.modifiers.new('Soft','SUBSURF');sm.levels=1;sm.render_levels=1
   for pl_ in o.data.polygons:pl_.use_smooth=True
 for o in objs:
  if o.type!='MESH':continue
  for slot in o.material_slots:
   m=slot.material
   if m is None:continue
   m=m.copy();slot.material=m;m.diffuse_color=(m.diffuse_color[0]*tint[0],m.diffuse_color[1]*tint[1],m.diffuse_color[2]*tint[2],1.)
   if m.use_nodes:
    b=m.node_tree.nodes.get('Principled BSDF')
    if b:c=b.inputs['Base Color'].default_value;b.inputs['Base Color'].default_value=(c[0]*tint[0],c[1]*tint[1],c[2]*tint[2],1.)
 import re
 cact={re.sub(r'\.\d+$','',a.name)[len(prefix):].lower():a for a in dst.actions if a is not None and re.sub(r'\.\d+$','',a.name).lower().startswith(prefix.lower())}    # a second animal of the same model gets actions named Idle.001 ...
 rig.animation_data_create();rig.animation_data.action=None
 return dict(rig=rig,root=root,objs=objs+[root],tracks=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()],n=0,creature=True,cact=cact,look=look,dress=[])
HUM_LIB=os.path.join(_A,'humanoid','ual_humanoid.blend')
def build_human2(S,look,tag):
 """a person on the Universal Animation Library rig: the mannequin (colours by region), a simple cartoon face on the head bone (eyes, brows, mouth that the speech and the feelings animate), hair and hats, scaled to the look's height; cact holds all ~90 actions"""
 import bpy,re,math
 from mathutils import Vector,Matrix
 with bpy.data.libraries.load(HUM_LIB,link=False) as (src,dst):dst.objects=list(src.objects);dst.actions=list(src.actions)
 root=bpy.data.objects.new(tag+'Root',None);S.link(root);objs=[]
 for o in dst.objects:
  if o is None:continue
  S.link(o);objs.append(o)
 rig=next(o for o in objs if o.type=='ARMATURE');mesh=next(o for o in objs if o.type=='MESH');rig.parent=root
 k=look['height']/1.8287;wx=look['scale'][0]/look['scale'][2];wy=look['scale'][1]/look['scale'][2];root.scale=(k*wx,k*wy,k);bpy.context.view_layer.update()
 d=look['dress'];cols=(d['skin'],d['shirt'],d['pants'],d['shoes'])
 for i,slot in enumerate(mesh.material_slots):
  m=slot.material.copy();slot.material=m;m.diffuse_color=(*cols[i],1.)
  if m.use_nodes:
   b=m.node_tree.nodes.get('Principled BSDF')
   if b:b.inputs['Base Color'].default_value=(*cols[i],1.)
 cact={re.sub(r'\.\d+$','',a.name):a for a in dst.actions if a is not None}
 rig.animation_data_create();rig.animation_data.action=None
 head=rig.pose.bones['Head'];hw=rig.matrix_world
 def bone_parent(o):
  o.parent=rig;o.parent_type='BONE';o.parent_bone='Head';o.matrix_parent_inverse=Matrix.Identity(4)
 def part(name,shape,loc,scale,color,mat_emit=0.):
  o=S.prim(shape,name,tuple(k*v for v in loc),color,scale=tuple(k*v for v in scale),emit=mat_emit);objs.append(o);bpy.context.view_layer.update();Wm=o.matrix_world.copy();bone_parent(o);o.matrix_basis=Wm;bpy.context.view_layer.update()
  Pm=o.matrix_world@Wm.inverted();o.matrix_parent_inverse=Pm.inverted();o.matrix_basis=Wm;return o
 face={};hc=(0.,-.005,1.70);fy=-.108
 for sg,nm in ((1,'L'),(-1,'R')):
  face['eye'+nm]=part('%s_eye%s'%(tag,nm),'sphere',(sg*.034,fy,1.714),(.017,.012,.019),(1.,1.,1.))
  face['pupil'+nm]=part('%s_pupil%s'%(tag,nm),'sphere',(sg*.034,fy-.008,1.714),(.009,.006,.011),(.04,.04,.06))
  face['brow'+nm]=part('%s_brow%s'%(tag,nm),'cube',(sg*.034,fy-.003,1.748),(.021,.004,.004),d['hair'])
 face['mouth']=part('%s_mouth'%tag,'sphere',(0.,-.121,1.622),(.023,.006,.004),(.4,.1,.12))
 part('%s_nose'%tag,'sphere',(0.,-.112,1.668),(.011,.016,.021),d['skin']);part('%s_earL'%tag,'sphere',(.088,.004,1.69),(.01,.017,.028),d['skin']);part('%s_earR'%tag,'sphere',(-.088,.004,1.69),(.01,.017,.028),d['skin'])
 hs=int(hash_unit(look['id'],'hairstyle')*5)%5;hr=d['hair']
 if hs==4:hair=part('%s_hair'%tag,'sphere',(0.,.03,1.77),(.085,.085,.06),hr)      # thin and receding
 else:hair=part('%s_hair'%tag,'sphere',(0.,.012,1.756),(.104,.106,.09),hr)
 face['hair']=hair
 if hs==1:part('%s_hairfront'%tag,'sphere',(0.,-.055,1.822),(.052,.04,.03),hr)             # a quiff
 elif hs==2:part('%s_bun'%tag,'sphere',(0.,.07,1.83),(.04,.04,.04),hr)                      # a bun
 elif hs==3:part('%s_hairback'%tag,'sphere',(0.,.07,1.68),(.085,.05,.11),hr);part('%s_hairside'%tag,'sphere',(0.,.05,1.74),(.105,.07,.08),hr)     # long
 for i,acc in enumerate(look['accessories']):
  kd=acc['kind']
  if kd in cg.HATS:
   V,F,M=cg.hat(kd,zb=0.,cy=0.);kh=.42;V=[(x*kh,y*kh+.005,z*kh+1.752) for x,y,z in V];main,trim=HATCOL.get(kd,lambda c:(c,_trim(c)))(color_of(acc,look['id'],i));o=_mesh_object(S,'%s_%s'%(tag,kd),[(k*x,k*y,k*z) for x,y,z in V],F,M,[main,trim]);objs.append(o);bpy.context.view_layer.update();Wm=o.matrix_world.copy();bone_parent(o);o.matrix_basis=Wm;bpy.context.view_layer.update();Pm=o.matrix_world@Wm.inverted();o.matrix_parent_inverse=Pm.inverted();o.matrix_basis=Wm
 return dict(rig=rig,root=root,objs=objs+[root],tracks=[],n=0,human2=True,cact=cact,face=face,look=look,k=k,dress=[],tag=tag,bn=dict(head='Head',LH_fore='lowerarm_l',RH_fore='lowerarm_r',LH_up='upperarm_l',RH_up='upperarm_r',lfoot='foot_l',rfoot='foot_r',lhand='hand_l',rhand='hand_r'))
def build(S,look,tag=None):
 """the character: lion rig, tint, scaled root, parts and accessories. Returns the S.character dict plus ch['look'], ch['dress'] (the dressing objects)."""
 import bpy
 from mathutils import Matrix,Vector
 tag=tag or look['id']
 if look.get('creature'):return build_creature(S,look,tag)
 if look.get('humanoid'):return build_human2(S,look,tag)
 ch=S.character(tag,look['tint']);rig=ch['rig'];root=ch['root'];ch['look']=look
 if tuple(look['tint'])!=(1.,1.,1.):tint_textures(ch,look['tint'])
 act=S.clip('idle');rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];S.scene.frame_set(1);bpy.context.view_layer.update()
 W=lambda b:rig.matrix_world@rig.pose.bones[b].head;hr,hl=W('mixamorig:RightHand'),W('mixamorig:LeftHand');tail=rig.matrix_world@rig.pose.bones['Tail'].tail
 prims=part_prims(look)+accessory_prims(look,tuple(hr),tuple(hl));dress=[]
 for p in prims:
  loc=p['loc'];loc=tuple(tail) if loc=='TAIL_TIP' else loc
  if p['shape']=='tube':
   pbt=rig.pose.bones[BONES[p['bone']]];hd=rig.matrix_world@pbt.head;tl=rig.matrix_world@pbt.tail;v=tl-hd;Ln=v.length;d=v.normalized();c0=hd+v*((p['t0']+p['t1'])/2);half=Ln*(p['t1']-p['t0'])/2
   eul=Vector((0,0,1)).rotation_difference(d).to_euler();o=S.prim('cyl',p['name'],tuple(c0),p['color'],scale=(p['r'],p['r'],half),rot=tuple(eul),vertices=14);bpy.context.view_layer.update();Wm=o.matrix_world.copy()
  else:
   o=S.prim(p['shape'],p['name'],loc,p['color'],scale=p['scale'],rot=p['rot'],emit=p['emit'],**p['kw']);bpy.context.view_layer.update();Wm=o.matrix_world.copy()
  pb=rig.pose.bones[BONES[p['bone']]];o.parent=rig;o.parent_type='BONE';o.parent_bone=pb.name;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Wm;bpy.context.view_layer.update()
  Pm=o.matrix_world@Wm.inverted();o.matrix_parent_inverse=Pm.inverted();o.matrix_basis=Wm;dress.append(o)
 for i,acc in enumerate(look['accessories']):
  if acc['kind'] in FITTED or acc['kind'] in COMPOSE or acc['kind'] in cg.HATS:dress+=garment(S,ch,look,acc,i)
 rig.animation_data.action=None;rig.animation_data_clear();rig.animation_data_create();ch['tracks']=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()];ch['n']=0
 for o in dress:ch['objs'].append(o)
 ch['dress']=dress;root.scale=tuple(look['scale']);return ch
