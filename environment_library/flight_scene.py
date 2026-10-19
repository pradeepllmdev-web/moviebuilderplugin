"""Blender script: 'The Flight' - Leo rides a procedural dragon through a sky canyon: a slalom between rock spires and a dive under a stone arch (about 36 s).

blender -b --disable-autoexec --python flight_scene.py -- <ship_assets_dir> <out.blend>

New in this scene: a PROCEDURAL FLYING CREATURE. The dragon is a chain of 16 body segments that follow the flight path (segment i sits where the head was i*0.9 m ago, so the tail trails and snakes by itself), banked into the
turns from the path curvature. Each wing is a forward-kinematics chain (shoulder, elbow, wrist, three finger tips) whose joint angles lag one behind the other, so the wave of the beat runs from root to tip; the wing membrane is
one mesh driven by shape keys sampled from the same chain (the bones are placed from the same blend, so skin and bones always agree). Beats come in bursts before each spire; in between the wings glide. A route planner passes
each spire on the side with the smaller lateral shift (clearance = spire radius + half wingspan + margin). Leo sits in the saddle (leo_sit) with IK hands on a handlebar. Audit: clearance of the spine and of both wing tips
to every spire, the arch and the floor over the whole flight, hands in reach and gripping, persistence, camera visibility. Clips: sit."""
import bpy,math,random,sys,os,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit,scene_params,locations
from mathutils import Vector,Euler,Matrix
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;PI=math.pi
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color,emit=0.):
 key=name+str(color)+str(emit)
 if key in _m:return _m[key]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.7
  if emit:
   for k in ('Emission Color','Emission'):
    if k in b.inputs:b.inputs[k].default_value=(*color,1);break
   if 'Emission Strength' in b.inputs:b.inputs['Emission Strength'].default_value=emit
 _m[key]=m;return m
def prim(kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=None,**kw):
 if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
 elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
 elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
 else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
 o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(mat(name.split('.')[0],color,emit))
 if parent:o.parent=parent
 return o
CTX=dict(link=link,mat=mat,prim=prim);S=locations.SKY;AX,AY,AZ0,AZ1=S['arch']
locations.load('sky_canyon',CTX,'intact')
# ---------------------------------------------------------------------------------------------------------- the route
V=14.;DSEG=.9;NSEG=16;SPAN=6.0;MARGIN=3.0
wps=[(0.,0.,22.)];prev=0.;sp=sorted(S['spires'],key=lambda s:s[0]);PASS=[]
for k,(x,y,r,h) in enumerate(sp):
 if x>AX and wps[-1][0]<AX:
  wps+=[(AX-35,0.,12.),(AX,0.,8.),(AX+40,0.,12.)];prev=0.
 d=r+SPAN+MARGIN;cands=[y+d,y-d];ok=[c for c in cands if abs(c)<=24] or cands;yp=min(ok,key=lambda c:abs(c-prev));zz=22.+3*math.sin(k*1.3);wps+=[(x-6,yp,zz),(x,yp,zz),(x+6,yp,zz)];PASS.append((x,y,r,h,yp));prev=yp
wps.append((480.,0.,24.))
P=np.array(wps)
def catmull(p0,p1,p2,p3,u):return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3)
pts=[]
for i in range(len(P)-1):
 p0=P[max(0,i-1)];p1=P[i];p2=P[i+1];p3=P[min(len(P)-1,i+2)]
 for u in np.linspace(0,1,40,endpoint=False):pts.append(catmull(p0,p1,p2,p3,u))
pts.append(P[-1]);PT=np.array(pts);seglen=np.linalg.norm(np.diff(PT,axis=0),axis=1);CUM=np.concatenate([[0],np.cumsum(seglen)]);TOTAL=CUM[-1]
def path_at(s):
 s=min(max(s,0.),TOTAL-1e-6);i=int(np.searchsorted(CUM,s,side='right')-1);u=(s-CUM[i])/max(1e-9,CUM[i+1]-CUM[i]);return Vector(PT[i]*(1-u)+PT[i+1]*u)
def tangent_at(s):
 a=path_at(s-1.0);b=path_at(s+1.0);return (b-a).normalized()
def head_s(t):return V*t+DSEG*(NSEG)+3.
T_END=(TOTAL-8.-head_s(0.))/V;seconds=T_END+1.0;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
def roll_at(s):
 a=tangent_at(s-4);b=tangent_at(s+4);psi=lambda v:math.atan2(v.y,v.x);dpsi=((psi(b)-psi(a)+PI)%(2*PI)-PI)/8.;return -max(-.7,min(.7,math.atan(V*V*dpsi/9.81)*.9))
def frame_at(s,roll=None):
 T=tangent_at(s);up0=Vector((0,0,1));L=up0.cross(T).normalized();U=T.cross(L);r=roll_at(s) if roll is None else roll
 L2=math.cos(r)*L+math.sin(r)*U;U2=math.cos(r)*U-math.sin(r)*L;return Matrix(((T.x,L2.x,U2.x),(T.y,L2.y,U2.y),(T.z,L2.z,U2.z)))
def mat4(p,R):m=R.to_4x4();m.translation=p;return m
# flap bursts before each spire and around the arch dive
bursts=[]
for (x,y,r,h,yp) in PASS:
 xs=x-38;ts=(xs-head_s(0)+DSEG*0)/V;bursts.append((max(0.,(x-38-(NSEG*DSEG+3))/V),(x-12-(NSEG*DSEG+3))/V))
bursts.append(((AX-30-(NSEG*DSEG+3))/V,(AX+30-(NSEG*DSEG+3))/V-3.0))
def env(t):
 e=0.
 for a,b in bursts:e=max(e,smooth((t-a)/.5)*(1-smooth((t-(b-.5))/.5)))
 return e
PH=[0.];dt=1/fps
for fi in range(1,frames+2):PH.append(PH[-1]+2*PI*1.15*env((fi-1)/fps)*dt)
def phase(t):return PH[min(len(PH)-1,int(t*fps))]
# ---------------------------------------------------------------------------------------------------------- wing forward kinematics
L1,L2=1.7,1.6;LF=(2.0,2.2,1.8);KS=(.15,.6,1.05);WS=(0.,.55,.45)
def fk(theta1,theta2,theta3,side):
 S0=Vector((WS[0],side*WS[1],WS[2]));J1=S0+L1*Vector((-.12,side*math.cos(theta1),math.sin(theta1)));J2=J1+L2*Vector((-.25,side*math.cos(theta2),math.sin(theta2)))
 T=[J2+LF[k]*Vector((-KS[k],side*math.cos(theta3),math.sin(theta3))).normalized() for k in range(3)]
 B1=Vector((-1.1,side*.5,.3));B2=Vector((-2.4,side*.45,.15));return [S0,J1,J2,T[0],T[1],T[2],B1,B2]
GL=.12;KPH=[2*PI*k/8 for k in range(8)]
def flap_pose(ph,side):A=.75;return fk(GL+A*math.sin(ph),GL+A*.95*math.sin(ph-.5),GL+A*1.1*math.sin(ph-1.0),side)
GLIDE={s:fk(GL,GL+.02,GL+.04,s) for s in (-1,1)};KEYP={s:[flap_pose(p,s) for p in KPH] for s in (-1,1)}
def key_weights(ph):
 u=(ph%(2*PI))/(2*PI)*8;i=int(u)%8;w=u-int(u);ww=[0.]*8;ww[i]=1-w;ww[(i+1)%8]=w;return ww
def wing_pts(ph,e,side):
 ww=key_weights(ph);out_=[]
 for j in range(8):
  p=GLIDE[side][j].copy()
  for k in range(8):p+=e*ww[k]*(KEYP[side][k][j]-GLIDE[side][j])
  out_.append(p)
 return out_
# ---------------------------------------------------------------------------------------------------------- the dragon
GREEN=(.18,.42,.25);DARK=(.1,.2,.14);RAD=[.55,.45,.5,.65,.8,.85,.8,.7,.6,.5,.42,.34,.27,.2,.15,.1]
SEG=[]
for i in range(NSEG):
 e=bpy.data.objects.new('DragonSeg%d'%i,None);link(e);SEG.append(e);prim('sphere','DragonBody%d'%i,(0,0,0),GREEN if i%2 else (.22,.5,.3),scale=(RAD[i]*1.3,RAD[i],RAD[i]),subdivisions=2,parent=e)
head=SEG[0];prim('cone','Snout',(.75,0,-.12),(.2,.46,.28),scale=(.32,.3,.5),rot=(0,PI/2,0),vertices=8,radius1=1,depth=2,parent=head)
for sy in (-1,1):
 prim('sphere','DragonEye',(.3,sy*.33,.22),(1,.8,.1),scale=(.09,.09,.09),emit=4.,subdivisions=1,parent=head);prim('cone','Horn',(-.35,sy*.3,.45),(.8,.75,.6),scale=(.09,.09,.45),rot=(-.5,sy*-.3,0),vertices=6,radius1=1,depth=2,parent=head)
for i in range(2,11):prim('cone','Spike',(0,0,RAD[i]+.1),DARK,scale=(.14,.1,.28),vertices=5,radius1=1,depth=2,parent=SEG[i])
TORSO=bpy.data.objects.new('Torso',None);link(TORSO);SADDLE=bpy.data.objects.new('Saddle',None);link(SADDLE)
WM={};BONES={1:[],-1:[]};MEMB={}
for side in (-1,1):
 me=bpy.data.meshes.new('Wing%d'%side);pts0=GLIDE[side];me.from_pydata([tuple(p) for p in pts0],[],[(0,1,6),(1,2,3,6),(6,3,4,7),(7,4,5)]);me.update();me.materials.append(mat('WingMembrane',(.5,.12,.1)))
 ob=bpy.data.objects.new('Wing%d'%side,me);link(ob);ob.parent=TORSO;MEMB[side]=ob;ob.shape_key_add(name='Basis')
 for k in range(8):
  sk=ob.shape_key_add(name='p%d'%k)
  for j,p in enumerate(KEYP[side][k]):sk.data[j].co=p
 for (a,b) in ((0,1),(1,2),(2,3),(2,4),(2,5)):BONES[side].append((a,b,prim('cyl','WingBone',(0,0,0),(.3,.22,.16),scale=(.05,.05,1),vertices=6,radius=1,depth=2,parent=TORSO)))
# ---------------------------------------------------------------------------------------------------------- Leo in the saddle
def load_char(tag,tint=None):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
 new=[]
 for o in dst.objects:
  if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
  link(o);new.append(o)
 root=bpy.data.objects.new(tag+'Root',None);link(root)
 for o in new:
  if o.parent is None:o.parent=root
  if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
  if tint and o.type=='MESH':
   for i,slot in enumerate(o.material_slots):
    if slot.material:
     m=slot.material.copy();c=slot.material.diffuse_color;m.diffuse_color=(c[0]*tint[0],c[1]*tint[1],c[2]*tint[2],1);o.material_slots[i].material=m
 rg=next(o for o in new if o.type=='ARMATURE');rg.animation_data_clear();rg.animation_data_create();return dict(root=root,rig=rg,objs=new)
prm=scene_params.get();LEO=load_char('Leo',prm['hero_tint']);rig=LEO['rig']
LEO['root'].parent=SADDLE;LEO['root'].location=(0,0,RAD[3]-.32+.0);LEO['root'].rotation_euler=(0,0,PI/2)
with bpy.data.libraries.load(os.path.join(ASSETS,'leo_sit.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_sit']
SIT=dst.actions[0];st=rig.animation_data.nla_tracks.new().strips.new('sit',1,SIT);st.action_slot=SIT.slots[0];st.action_frame_start=91;st.action_frame_end=145;st.repeat=(frames+120)/55.;st.extrapolation='HOLD'
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Wrist_'+limb,None);tg.empty_display_size=.04;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,.9)
 k_=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;k_.influence=1.;IK[limb]=k_
# pose the chain once so the saddle frame exists at frame 1, then read the shoulders in saddle space and mount the handlebar there
def set_frames(t):
 hs=head_s(t);M={}
 for i in range(NSEG):
  s=hs-i*DSEG;M[i]=mat4(path_at(s),frame_at(s))
 return M
M0=set_frames(0.);SADDLE.matrix_world=M0[3];TORSO.matrix_world=M0[4];scene.frame_set(1);bpy.context.view_layer.update()
SADDLE.matrix_world=M0[3];bpy.context.view_layer.update()
SHL={l:SADDLE.matrix_world.inverted()@(rig.matrix_world@rig.pose.bones['mixamorig:'+b+'Arm'].head) for l,b in (('LH','Left'),('RH','Right'))};print('SHOULDERS(saddle)',{k:tuple(round(x,2) for x in v) for k,v in SHL.items()})
GRIPL={l:SHL[l]+Vector((.26,-.06*(1 if l=='LH' else -1),-.20)) for l in SHL}
bar=prim('cyl','Handlebar',((GRIPL['LH'].x+GRIPL['RH'].x)/2,0,(GRIPL['LH'].z+GRIPL['RH'].z)/2),(.5,.4,.3),scale=(.035,.035,abs(GRIPL['LH'].y-GRIPL['RH'].y)/2+.12),rot=(PI/2,0,0),vertices=8,radius=1,depth=2,parent=SADDLE)
for l in GRIPL:prim('cyl','HandlebarPost',(GRIPL[l].x,GRIPL[l].y,(GRIPL[l].z+RAD[3]-.1)/2),(.5,.4,.3),scale=(.03,.03,(GRIPL[l].z-RAD[3]+.1)/2),vertices=6,radius=1,depth=2,parent=SADDLE)
# ---------------------------------------------------------------------------------------------------------- keys
prevR={};clear=[];worst_tip=[1e9,0];min_spine=[1e9,0]
def euler_of(M,key):
 e=M.to_3x3().to_euler('XYZ',prevR[key]) if key in prevR else M.to_3x3().to_euler('XYZ');prevR[key]=e.copy();return e
def clearance(pw,t):
 """distance of a world point to the nearest obstacle surface (spires as cylinders, arch pillars and beam as boxes, floor)."""
 d=pw.z-0.
 for (x,y,r,h,yp) in PASS:
  if pw.z<h+2:
   dd=math.hypot(pw.x-x,pw.y-y)-r
   if dd<d:d=dd;LASTO[0]='spire@%d'%x
 for sy in (-1,1):
  ex=max(abs(pw.x-AX)-2.2,0);ey=max(abs(pw.y-sy*AY)-2.0,0);ez=max(pw.z-AZ1,0);d=min(d,math.sqrt(ex*ex+ey*ey+ez*ez))
 ex=max(abs(pw.x-AX)-2.4,0);ey=max(abs(pw.y)-(AY+2.0),0);ez=max(abs(pw.z-((AZ0+AZ1)/2+1))-((AZ1-AZ0)/2+1),0);d=min(d,math.sqrt(ex*ex+ey*ey+ez*ez));return d
ROLLS=[];LASTO=['floor']
for f in range(1,frames+1,2):
 t=(f-1)/fps;Ms=set_frames(t);e=env(t);ph=phase(t)
 for i,sg in enumerate(SEG):
  sg.location=Ms[i].translation;sg.rotation_euler=euler_of(Ms[i],('s',i));sg.keyframe_insert('location',frame=f);sg.keyframe_insert('rotation_euler',frame=f)
  if i<3 or i in (6,10,15):
   c=clearance(Ms[i].translation,t)-RAD[i]
   if c<min_spine[0]:min_spine=[c,t]
 for o_,M_ in ((TORSO,Ms[4]),(SADDLE,Ms[3])):o_.location=M_.translation;o_.rotation_euler=euler_of(M_,o_.name);o_.keyframe_insert('location',frame=f);o_.keyframe_insert('rotation_euler',frame=f)
 for side in (-1,1):
  wp=wing_pts(ph,e,side);ob=MEMB[side];ww=key_weights(ph)
  for k in range(8):sk=ob.data.shape_keys.key_blocks['p%d'%k];sk.value=e*ww[k];sk.keyframe_insert('value',frame=f)
  for a,b,cy in BONES[side]:
   A,B=wp[a],wp[b];cy.location=(A+B)/2;cy.scale=(.05,.05,(B-A).length/2);cy.rotation_euler=(B-A).to_track_quat('Z','Y').to_euler();cy.keyframe_insert('location',frame=f);cy.keyframe_insert('scale',frame=f);cy.keyframe_insert('rotation_euler',frame=f)
  for j in (5,4,3):
   tw=Ms[4]@wp[j];c=clearance(tw,t)
   if c<worst_tip[0]:worst_tip=[c,t];pass
 ROLLS.append(roll_at(head_s(t)-3*DSEG))
 for l in ('LH','RH'):TG[l].location=Ms[3]@GRIPL[l];TG[l].keyframe_insert('location',frame=f)
# gaze: ahead along the path
scene.frame_set(1);bpy.context.view_layer.update()
hm=(rig.matrix_world@rig.pose.bones['mixamorig:Head'].matrix).to_3x3();fwd0=tangent_at(head_s(0)-3*DSEG)
AXES={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
FACE_AXIS=max(AXES,key=lambda k:AXES[k].normalized().dot(fwd0));gz=bpy.data.objects.new('Gaze',None);link(gz)
k_=rig.pose.bones['mixamorig:Head'].constraints.new('DAMPED_TRACK');k_.target=gz;k_.track_axis=FACE_AXIS;k_.influence=.8
for f in range(1,frames+1,2):
 t=(f-1)/fps;gz.location=path_at(head_s(t)+18)+Vector((0,0,.5));gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
def dframe(t):s=head_s(t)-3*DSEG;R=frame_at(s);return path_at(s),R
pass_t=[((x-(NSEG*DSEG+3)-3*DSEG)/V,k) for k,(x,y,r,h,yp) in enumerate(PASS)];t_arch=(AX-(NSEG*DSEG+3)-3*DSEG)/V
cuts=[('establish',0,3.0,'under')];last=3.0;alt=0;evs=sorted([(tp-2.6,tp+1.2,'pass%d'%k) for tp,k in pass_t]+[(t_arch-2.5,t_arch+2.5,'arch')])
for a,b,kind in evs:
 if a-last>1.0:
  n=max(1,int((a-last)//4.0));seg=(a-last)/n
  for j in range(n):cuts.append(('flight %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','side','leo','wing')[alt%4]));alt+=1
 if b-max(a,last)<.8:continue
 cuts.append((kind,max(a,last),b,kind));last=b
if seconds-last>.8:cuts.append(('landing view',last,seconds,'follow'))
else:cuts[-1]=(cuts[-1][0],cuts[-1][1],seconds,cuts[-1][3])
cams=[];CAMKEYS=[]
for k,(name,a,b,kind) in enumerate(cuts):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=2000;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);p,R=dframe(t);fw=R.col[0];lf=R.col[1];up=R.col[2];cam.data.lens=32;q=p+Vector((0,0,.6))
  if kind=='under':P=p+fw*15+lf*5+up*2;q=p;cam.data.lens=28
  elif kind=='follow':P=p-fw*11+up*4.5+lf*1.5;cam.data.lens=30
  elif kind=='side':P=p+lf*13+up*1.5+fw*(4-8*u);cam.data.lens=34
  elif kind=='leo':P=p+fw*4.2+up*1.8+lf*1.3;q=p+up*1.6;cam.data.lens=45
  elif kind=='wing':P=p-lf*2.5-up*6.5-fw*3;q=p+lf*-2.5;cam.data.lens=28
  elif kind=='arch':P=Vector((AX+26,7.,6.));q=p;cam.data.lens=30
  else:
   x_b,y_b,r_b,h_b,yp=PASS[int(kind[4:])];sg_=1 if yp>0 else -1;P=Vector((x_b-8,max(-27,min(27,yp+sg_*10)),p.z+2));q=p;cam.data.lens=36
  cam.location=P;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
FAMILY=set(kit._family(LEO['root']))|set(kit._family(TORSO))|set(kit._family(SADDLE))
for sg in SEG:FAMILY|=set(kit._family(sg))
for o in bpy.data.objects:
 if o.name.startswith(('Wing','Wrist','Dragon','Snout','Horn','Spike','Handlebar')):FAMILY.add(o.name)
CAND=[(0,0,3.),(0,0,-3.),(0,6.,0),(0,-6.,0),(8.,0,0),(-8.,0,0)]
offs={}
for k,cam,aim,f in CAMKEYS:
 settle(f);d_=bpy.context.evaluated_depsgraph_get();p=Vector(cam.location);q=Vector(aim.location);np_,idx=kit.clear_view(scene,d_,p,q,FAMILY,CAND);offs[(k,f)]=np_-p
for k in set(a for a,b in offs):
 fs=sorted(f for a,f in offs if a==k)
 for j,f in enumerate(fs):
  win=[offs[(k,g)] for g in fs[max(0,j-3):j+4]];offs[(k,f)]=Vector((sum(v.x for v in win)/len(win),sum(v.y for v in win)/len(win),max(v.z for v in win)))
for k,cam,aim,f in CAMKEYS:
 o=offs[(k,f)]
 if o.length>1e-6:cam.location=Vector(cam.location)+o;cam.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- audit
issues=kit.persistence_audit(scene)+kit.camera_checks(scene,[LEO['root']])
if min_spine[0]<1.5:issues.append('AUDIT clearance: the body passes %.2f m from an obstacle at %.1f s (need 1.5)'%(min_spine[0],min_spine[1]))
if worst_tip[0]<1.5:issues.append('AUDIT clearance: a wing tip passes %.2f m from an obstacle at %.1f s (need 1.5)'%(worst_tip[0],worst_tip[1]))
reach_err=[];worst={}
for f in range(F(0),frames+1,12):
 settle(f)
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.46:reach_err.append((round(d-.44,3),l,round((f-1)/fps,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,(f-1)/fps)
if reach_err:issues.append('AUDIT reach: wrist target beyond arm reach %s (%d samples)'%(reach_err[:3],len(reach_err)))
for l,(g,t) in worst.items():
 if g>.07:issues.append('AUDIT grip: %s misses the handlebar by %.0f cm at %.1f s'%(l,g*100,t))
print('FLIGHT path %.0f m at %.0f m/s, bursts %d, max bank %.2f rad, min clearance body %.1f m wing tips %.1f m, GRIP %s'%(TOTAL,V,len(bursts),max(abs(r) for r in ROLLS),min_spine[0],worst_tip[0],{k:round(v[0]*100,1) for k,v in worst.items()}))
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);adir=os.path.join(os.path.dirname(out),'audio_flight');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(14)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w_:w_.setnchannels(1);w_.setsampwidth(2);w_.setframerate(SR);w_.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
def at(arr,t,x,g=1.):
 i=int(t*SR)
 if 0<=i<len(arr):
  n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
tt=np.arange(N_)/SR;wind=lp(nr.standard_normal(N_),10)*(.5+.3*np.sin(2*PI*.2*tt))
beats=np.zeros(N_+SR);k=np.arange(int(.4*SR))/SR;thump=np.sin(2*PI*55*k)*np.exp(-k*9)+lp(nr.standard_normal(len(k)),12)*np.exp(-k*14)*.5
for i in range(1,len(PH)):
 if int(PH[i]/(2*PI))>int(PH[i-1]/(2*PI)):at(beats,i/fps,thump,.9)
roar=np.zeros(N_+SR*3);rk=np.arange(int(2.2*SR))/SR;at(roar,t_arch-1.5,(lp(nr.standard_normal(len(rk)),6)*np.sin(2*PI*(90+30*np.sin(2*PI*5*rk))*rk))*np.sin(PI*rk/2.2)**2,.8)
who=np.zeros(N_+SR*3);k2=np.arange(int(1.0*SR))/SR;wh=lp(nr.standard_normal(len(k2)),25)*np.sin(PI*k2/1.0)**2
for tp,kk in pass_t:at(who,tp-.4,wh,.8)
mus=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 for f0 in ((196,246.9,293.7),(174.6,220,261.6),(164.8,196,246.9),(146.8,185,220))[ci%4]:
  kk=np.arange(int(4.2*SR))/SR;at(mus,ci*4.,np.sin(2*PI*f0*kk)*np.minimum(kk/.3,1)*np.exp(-kk*.6)*.18)
mus=mus[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('wind.wav',wind,.5),wav('wingbeats.wav',beats[:N_],.7),wav('roar.wav',roar[:N_],.7),wav('rocks.wav',who[:N_],.5),wav('music.wav',mus,.35)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('wind','wing beats','roar','rock passes','music')),start=1):strips.new_sound(n,p,ch,1)
scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.5,.65,.9)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('FLIGHT_DONE',frames,'frames')
