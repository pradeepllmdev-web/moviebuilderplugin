"""Pure geometry for the costume pieces that are not cut from the body: skirts, robes, ponchos, capes and aprons (lofts around the torso, in the body mesh's own space: centimetres, z up, the character faces -Y) and hats (surfaces of revolution on the head, in the idle-pose
space of cast_builder: metres, head centre (0,-.12,1.45)). Every function returns (verts, faces, mats): vertex tuples, face index tuples and one material index per face (0 = cloth, 1 = trim), so tests need no Blender; cast_builder skins the lofts to the skeleton and parents the hats to the head bone."""
import math
PI=math.pi
def _faces(rings,cols,closed,mats_row):
 """quads between consecutive rings (ring i holds `cols` vertices), wound so the normals point outward for rings that go around counter-clockwise seen from above and downward"""
 f=[];m=[];n=cols if closed else cols-1
 for j in range(len(rings)-1):
  for i in range(n):
   i2=(i+1)%cols;a,b,c,d=rings[j][i],rings[j][i2],rings[j+1][i2],rings[j+1][i]
   q=tuple(dict.fromkeys((d,c,b,a)))
   if len(q)>=3:f.append(q);m.append(mats_row[j])
 return f,m
def loft(z0,z1,rx,ry,cy=-14.,rows=8,seg=36,flare=0.,power=1.6,pleat=0.,folds=9,arc=None,hem=0.,sway=0.,cx=0.):
 """a skirt-like surface from height z0 (waist, top) down to z1: ellipse radii rx,ry at the top growing by `flare` (fraction, along t**power), `pleat` sine folds (fraction of the radius, growing downward), an optional trim band of height `hem` at the bottom (material 1); arc=(a0,a1) in radians
 (front is -pi/2) makes a panel instead of a closed ring; sway shifts the lower rows toward +y (a coat that hangs back). Also returns per-vertex t (0 top .. 1 bottom) in a list as the 4th item."""
 closed=arc is None;a0,a1=(0.,2*PI) if closed else arc;cols=seg if closed else seg+1;rings=[];verts=[];ts=[];mats=[]
 steps=[(z0+(z1-z0)*j/rows,j/rows,0) for j in range(rows+1)]
 if hem:steps+=[(z1,1.,1),(z1-hem,1.,1)]
 for k,(z,t,tr) in enumerate(steps):
  ring=[]
  for i in range(cols):
   th=a0+(a1-a0)*i/(seg if not closed else seg);g=1+flare*t**power+(.045*(hem and tr))
   g*=1+pleat*t*math.sin(folds*th);ring.append(len(verts));verts.append((cx+rx*g*math.cos(th),cy+ry*g*math.sin(th)+sway*t*t,z));ts.append(t)
  rings.append(ring)
 f,m=_faces(rings,cols,closed,[s[2] for s in steps[1:]])
 return verts,f,m,ts
def cape(z0=100.,z1=14.,half=20.,spread=16.,back=8.,cy=-14.,rows=10,cols=12,hem=3.):
 """a cloak hanging from the shoulders behind the body: a sheet with a gentle curve that widens and swings back toward the hem"""
 rings=[];verts=[];ts=[];steps=[(z0+(z1-z0)*j/rows,j/rows,0) for j in range(rows+1)]
 if hem:steps+=[(z1-hem,1.,1)]
 for z,t,tr in steps:
  ring=[]
  for i in range(cols):
   u=-1+2*i/(cols-1);w=half+spread*t;x=u*w;y=cy+back+3*(1-u*u)*(1-t)*-1+10*t*t+7*u*u*(.4+t);ring.append(len(verts));verts.append((x,y,z));ts.append(t)
  rings.append(ring)
 f=[];m=[]
 for j in range(len(rings)-1):
  for i in range(cols-1):f.append((rings[j][i+1],rings[j+1][i+1],rings[j+1][i],rings[j][i]));m.append(steps[j+1][2])
 return verts,f,m,ts
def lathe(profile,seg=28,cx=0.,cy=-.1,zb=1.7,gap=None,rscale=None,bend=None):
 """a surface of revolution about the vertical axis through (cx,cy): profile is a list of (r,z,mat) points from the inside of the lower edge outward, up and over to the pole (r=0); material of a segment is the mat of its first point.
 gap=(a0,a1) leaves out that sector (front opening of a hood), rscale(theta) scales the radius per angle (a brim longer at the back), bend(x,y,z) moves a vertex (a floppy tip, a curled brim)."""
 rings=[];verts=[];mats=[]
 for r,z,m in profile:
  ring=[]
  for i in range(seg):
   th=2*PI*i/seg;rr=r*(rscale(th) if rscale and r>.02 else 1.);p=(cx+rr*math.cos(th),cy+rr*math.sin(th),zb+z)
   if bend:p=bend(*p)
   ring.append(len(verts));verts.append(tuple(p))
  rings.append(ring)
 f=[];m=[]
 for j in range(len(rings)-1):
  for i in range(seg):
   th=2*PI*(i+.5)/seg
   if gap and gap[0]<=((th+PI)%(2*PI))-PI<=gap[1]:continue
   i2=(i+1)%seg;q=tuple(dict.fromkeys((rings[j][i],rings[j][i2],rings[j+1][i2],rings[j+1][i])))
   if len(q)>=3:f.append(q);m.append(profile[j][2])
 return verts,f,m
def _arc(r,h,n=7,r0=0.):
 return [(r0+(r-r0)*math.cos(PI/2*k/n),h*math.sin(PI/2*k/n)) for k in range(n+1)]
def peak(cy=-.1,zb=1.7,r0=.27,r1=.42,half=1.05,seg=9,drop=.05):
 """the flat peak of a cap, a curved plate over the front"""
 verts=[];f=[];rows=[]
 for r in (r0,(r0+r1)/2,r1):
  ring=[]
  for i in range(seg):
   th=-PI/2-half+2*half*i/(seg-1);ring.append(len(verts));verts.append((r*math.cos(th),cy+r*math.sin(th),zb-drop*(r-r0)/(r1-r0)*(1+.3*math.cos(th+PI/2)*0)))
  rows.append(ring)
 for j in range(2):
  for i in range(seg-1):f.append((rows[j][i],rows[j][i+1],rows[j+1][i+1],rows[j+1][i]))
 return verts,f,[0]*len(f)
def fin(r,h,w=.02,cy=-.1,zb=1.7,n=10,a0=-.5,a1=PI+.5):
 """a thin ridge over the top of a helmet (a crest): an arc in the y-z plane of width w"""
 verts=[];f=[];top=[];bot=[]
 for k in range(n+1):
  a=a0+(a1-a0)*k/n;y=cy-r*math.cos(a);z=zb+(r+h)*math.sin(a)*.97;y0=cy-r*math.cos(a);z0=zb+r*math.sin(a)*.97
  top.append(len(verts));verts.append((-w/2,y,z));top.append(len(verts));verts.append((w/2,y,z));bot.append(len(verts));verts.append((-w/2,y0,z0));bot.append(len(verts));verts.append((w/2,y0,z0))
 for k in range(n):
  b=k*4;nb=b+4;f.append((b,b+1,nb+1,nb));f.append((b,b+2,nb+2,nb));f.append((b+1,b+3,nb+3,nb+1))
 return verts,f,[0]*len(f)
def _join(*parts):
 """merge several (verts,faces,mats) into one"""
 V=[];F=[];M=[]
 for p in parts:
  o=len(V);V+=list(p[0]);F+=[tuple(i+o for i in q) for q in p[1]];M+=list(p[2])
 return V,F,M
HATS={}
def hat(kind,zb=1.7,cy=-.1):
 """geometry of a head piece (verts, faces, mats) or None; mats 0 = main colour, 1 = band or trim colour"""
 L=lambda prof,**k:lathe(prof,cy=cy,zb=zb,**k)
 if kind=='hat_top':return L([(.17,0,0),(.29,0,0),(.30,.012,0),(.29,.026,0),(.18,.026,0),(.18,.026,1),(.18,.075,1),(.18,.075,0),(.168,.30,0),(.16,.312,0),(0,.312,0)])
 if kind=='hat_wizard':
  return L([(.2,0,0),(.27,-.02,0),(.34,-.07,0),(.35,-.065,0),(.27,-.01,0),(.2,.03,0),(.2,.03,1),(.19,.075,1),(.19,.075,0),(.13,.2,0),(.08,.36,0),(.04,.46,0),(0,.5,0)],seg=32,bend=lambda x,y,z:(x,y+1.8*max(0.,z-zb-.2)**2,z))
 if kind=='hat_cap':
  d=[(.285*math.cos(PI/2*k/8),.2*math.sin(PI/2*k/8)+(0 if k else 0),0) for k in range(9)];d[0]=(.285,0,0)
  return _join(L([(.28,-.03,1),(.285,0,1)]+d[1:]),peak(cy,zb+.0))
 if kind=='hat_flatcap':
  return _join(L([(.27,-.02,1),(.29,.0,1),(.31,.04,0),(.29,.1,0),(.2,.12,0),(0,.115,0)]),peak(cy,zb+.01,.29,.40,.9,drop=.03))
 if kind=='hat_straw':return L([(.19,0,0),(.30,-.012,0),(.41,-.06,0),(.42,-.056,0),(.30,.0,0),(.2,.025,0),(.2,.025,1),(.2,.06,1),(.2,.06,0),(.19,.12,0),(.16,.15,0),(0,.155,0)],seg=32)
 if kind=='hat_cowboy':
  def bend(x,y,z):
   r=math.hypot(x,y-cy);k=max(0.,r-.2);return (x,y,z+(1.4*k*k*(x*x)/(r*r+1e-6)-.8*k*k*((y-cy)**2)/(r*r+1e-6)) if r>.2 else z)
  return L([(.2,0,0),(.31,.0,0),(.44,.0,0),(.445,.012,0),(.31,.02,0),(.205,.02,1),(.205,.06,1),(.2,.06,0),(.185,.15,0),(.16,.19,0),(.09,.175,0),(0,.16,0)],seg=36,bend=bend)
 if kind=='hat_sou':
  return L([(.285,-.01,0),(.40,-.04,0),(.43,-.07,0),(.44,-.065,0),(.40,-.03,0),(.29,.005,0),(.285,.005,0),(.28,.1,0),(.22,.2,0),(0,.23,0)],seg=32,rscale=lambda th:1+.28*max(0.,math.sin(th))-.12*max(0.,-math.sin(th)))
 if kind=='hat_beanie':
  return _join(L([(.285,-.03,1),(.30,-.03,1),(.30,.04,1),(.29,.04,0),(.28,.12,0),(.2,.21,0),(.09,.26,0),(0,.28,0)]),lathe([(0.,.27,1)]+[(.06*math.sin(PI*k/6),.27+.06-.06*math.cos(PI*k/6),1) for k in range(1,7)],seg=10,cy=cy,zb=zb))
 if kind=='hat_beret':return L([(.19,-.01,1),(.2,.02,1),(.27,.03,0),(.33,.06,0),(.32,.1,0),(.2,.13,0),(0,.13,0)],seg=32,bend=lambda x,y,z:(x,y,z+.03*(x/.33)))
 if kind=='hat_chef':return L([(.27,0,1),(.285,.0,1),(.285,.07,1),(.28,.07,0),(.3,.16,0),(.32,.26,0),(.27,.34,0),(.15,.37,0),(0,.37,0)],seg=28)
 if kind=='hat_hood':return L([(.33,-.1,0),(.35,0,0),(.33,.14,0),(.25,.28,0),(.15,.36,0),(.05,.38,0),(0,.375,0)],seg=32,gap=(-PI/2-.62,-PI/2+.62),bend=lambda x,y,z:(x,y+.55*max(0.,z-zb-.05)**1.6,z-.2*max(0.,y-cy)))
 if kind=='hat_bonnet':return L([(.3,-.04,1),(.315,0,1),(.32,.1,0),(.27,.22,0),(.14,.3,0),(0,.31,0)],seg=32,gap=(-PI/2-.55,-PI/2+.55))
 if kind=='helmet':
  d=[(.335*math.cos(PI/2*k/9),.3*math.sin(PI/2*k/9)+.03,0) for k in range(10)]
  return _join(L([(.34,-.03,1),(.345,0,1)]+[(.34,.03,1)]+d[1:],seg=32),fin(.31,.045,.035,cy,zb))
 if kind=='crown':
  base=L([(.185,0,0),(.2,0,0),(.205,.07,0),(.19,.07,0)],seg=24);V,F,M=base;V=list(V)
  for j in range(5):
   a=2*PI*j/5;cxp=math.cos(a)*.195;cyp=cy+math.sin(a)*.195;o=len(V)
   for dx,dy in ((-.04,0),(.04,0)):V.append((cxp-math.sin(a)*dx,cyp+math.cos(a)*dx,zb+.07))
   V.append((cxp,cyp,zb+.17));F.append((o,o+1,o+2));M.append(0)
  return V,F,M
 return None
for k in ('hat_top','hat_wizard','hat_cap','hat_flatcap','hat_straw','hat_cowboy','hat_sou','hat_beanie','hat_beret','hat_chef','hat_hood','hat_bonnet','helmet','crown'):HATS[k]=True
#                 z0   z1   rx  ry  extras
SKIRTS={'tunic':dict(z0=78,z1=44,rx=21,ry=18,rows=5,flare=.18,pleat=.02,hem=3),
 'dress':dict(z0=78,z1=14,rx=20.5,ry=17.5,rows=10,flare=.62,pleat=.05,folds=10,hem=4),
 'robe':dict(z0=78,z1=4,rx=21,ry=18,rows=12,flare=.5,pleat=.05,folds=8,hem=5),
 'tassets':dict(z0=76,z1=40,rx=21,ry=18,rows=4,flare=.22,pleat=.0,hem=2),
 'apronskirt':dict(z0=82,z1=26,rx=22,ry=20,rows=8,flare=.12,arc=(-PI/2-.75,-PI/2+.75),seg=18,hem=3),
 'poncho':dict(z0=96,z1=48,rx=26,ry=22,rows=8,flare=.85,pleat=.03,folds=7,hem=3,cy=-12.),
 'kilt':dict(z0=76,z1=36,rx=21,ry=18,rows=6,flare=.2,pleat=.07,folds=14,hem=0)}
def skirt(kind,**over):
 d=dict(SKIRTS[kind]);d.update(over);return loft(**d)
def shell(env,z0,z1,off=2.,seg=40,step=3.,gap=None,arc=None,hem=0.,neck=True,pattern=None,collar=96.):
 """a clean garment skin around the torso from the body's envelope: env(z) -> (cy, radii) where radii[b] is the reach of the body at angle 2*pi*b/len(radii) (x=cos, y=sin, front -pi/2) around (0,cy) at height z; the shell stands `off` cm outside it from height z0 (top, normally the shoulders)
 down to z1 (hem). neck closes the top toward the collar (rings shrink from z0 up to `collar`); gap=half-width in radians of an opening down the front (jacket, vest); arc=(a0,a1) makes a front panel (bib); hem adds a trim band; pattern plaid|stripe sets the second material"""
 zs=[];sc=[]
 if neck:zs+=[collar,(collar+z0)/2+1];sc+=[.5,.8]
 n=max(1,int(round((z0-z1)/step)));zs+=[z0+(z1-z0)*j/n for j in range(n+1)];sc+=[1.]*(n+1)
 tr=[0]*len(zs)
 if hem:zs+=[z1,z1-hem];sc+=[1.,1.];tr+=[1,1]
 closed=arc is None;a0,a1=(0.,2*PI) if closed else arc;cols=seg if closed else seg+1;rings=[];verts=[]
 for z,s in zip(zs,sc):
  cy,rad=env(z);m=len(rad);ring=[]
  for i in range(cols):
   th=a0+(a1-a0)*i/seg;u=(th%(2*PI))/(2*PI)*m;i0=int(u)%m;f=u-int(u);r=(rad[i0]*(1-f)+rad[(i0+1)%m]*f+off)*s
   ring.append(len(verts));verts.append((r*math.cos(th),cy+r*math.sin(th),z))
  rings.append(ring)
 for j in range(len(rings)):
  pass
 mats=[t for t in tr[1:]]
 f=[];mm=[]
 for j in range(len(rings)-1):
  for i in range(cols if closed else cols-1):
   th=a0+(a1-a0)*(i+.5)/seg
   if gap and abs(((th+PI/2+PI)%(2*PI))-PI)<gap and zs[j]<collar-1:continue
   i2=(i+1)%cols;q=(rings[j+1][i],rings[j+1][i2],rings[j][i2],rings[j][i])
   x,y,z=[sum(verts[k][c] for k in q)/4 for c in range(3)]
   mi=mats[j] or (1 if (pattern=='plaid' and (x%11<2.4 or z%11<2.4)) or (pattern=='stripe' and z%12<4.5) else 0)
   f.append(q);mm.append(mi)
 return verts,f,mm
