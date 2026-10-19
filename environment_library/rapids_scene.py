"""Blender script: 'The Rapids' - Leo steers a log raft through a canyon river full of boulders with a long sweep oar (about 36 s).

blender -b --disable-autoexec --python rapids_scene.py -- <ship_assets_dir> <out.blend>

New in this scene: WATER and BUOYANCY. The river is a mesh with two animated Wave modifiers (shared bank); every key frame the raft is set onto the real evaluated water surface by ray casts at its four
corners (height, pitch and roll from the corner heights), so it rides the swell exactly. A route planner passes each boulder on the side that needs the smaller lateral shift (clearance = boulder radius + raft
half-length + margin) and schedules the oar strokes: a lateral shift to the left is made with strokes on the right side, timed to start with the shift. Hands are IK targets on the oar grips; the blades splash
only while they are in the water. Audit: boulder clearance over the whole route, bank clearance, hands within reach, grips, raft height against the water, persistence, camera visibility. Clip: leo_idle."""
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
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.35 if name=='Water' else .9
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
CTX=dict(link=link,mat=mat,prim=prim);R=locations.RAPIDS;BOUL=R['boulders']
locations.load('rapids',CTX,'intact')
water=bpy.data.objects['Water']
# ---------------------------------------------------------------------------------------------------------- the route planner
SPEED=4.5;T0=2.0;X0=0.;X_END=150.;CLEAR=1.5+.5;YMAX=5.6
route=[(X0,0.)];prev=0.;PASS=[]
for (x,y,r) in BOUL:
 d=r+2.0;cands=[y+d,y-d];ok=[c for c in cands if abs(c)<=YMAX] or cands;yp=min(ok,key=lambda c:abs(c-prev));route.append((x,yp));PASS.append((x,y,r,yp));prev=yp
route.append((X_END,0.))
def path_y(x):
 for (xa,ya),(xb,yb) in zip(route,route[1:]):
  if xa<=x<=xb:return ya+(yb-ya)*smooth((x-xa)/(xb-xa))
 return route[-1][1]
def path_dy(x,h=.2):return (path_y(x+h)-path_y(x-h))/(2*h)
def raft_x(t):return min(X_END+6,X0+SPEED*max(0.,t-T0))
T_END=T0+(X_END-X0)/SPEED;seconds=T_END+3.5;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
def yaw_at(t):
 x=raft_x(t);return math.atan(path_dy(x)) if x<X_END else 0.
def t_of(x):return T0+(x-X0)/SPEED
# oar strokes: a lateral shift to the left is made with strokes on the right side (s=-1), and the other way round
STROKES=[]
for (xa,ya),(xb,yb) in zip(route,route[1:]):
 dy=yb-ya
 if abs(dy)>.8:
  s=-1 if dy>0 else 1;ta=t_of(xa)+.15
  for k in range(2 if abs(dy)<4.5 else 3):STROKES.append((ta+k*1.0,s))
STROKE_DUR=.95;A_MAX=.75;B_MAX=.45;GRIP=.2;SHAFT=2.0
def stroke_state(t):
 for t0,s in STROKES:
  if t0<=t<t0+STROKE_DUR:
   u=(t-t0)/STROKE_DUR;env=math.sin(PI*u)**.8;prog=smooth(u);return (-s*A_MAX*env,-s*B_MAX*(.5-prog)*env/(env+1e-9) if env>.001 else 0.,s,env)
 return (0.,0.,0,0.)
CZ=1.25;CX=.30
def paddle_pose(t):
 a,b,s,env=stroke_state(t);R_=Euler((0,0,b),'XYZ').to_matrix()@Euler((a,0,0),'XYZ').to_matrix();return Vector((CX,0,CZ)),R_
# ---------------------------------------------------------------------------------------------------------- the raft
raft=bpy.data.objects.new('Raft',None);link(raft)
for i in range(7):prim('cyl','RaftLog',(0,-1.0+i*.333,0),(.45,.3,.16),scale=(.17,.17,1.45),rot=(0,PI/2,0),vertices=10,radius=1,depth=2,parent=raft)
for x in (-.9,.9):prim('cyl','RaftBeam',(x,0,.2),(.4,.26,.14),scale=(.07,.07,1.15),rot=(PI/2,0,0),vertices=8,radius=1,depth=2,parent=raft)
prim('cube','RaftDeck',(0,0,.17),(.5,.34,.18),scale=(1.0,.8,.02),parent=raft);prim('cube','RaftPost',(CX-.05,-1.0,.5),(.4,.26,.14),scale=(.05,.05,.35),parent=raft);prim('cube','RaftPost',(CX-.05,1.0,.5),(.4,.26,.14),scale=(.05,.05,.35),parent=raft)
pad=bpy.data.objects.new('Oar',None);link(pad);pad.parent=raft
prim('cyl','OarShaft',(0,0,0),(.55,.4,.2),scale=(.03,.03,SHAFT),rot=(PI/2,0,0),vertices=8,radius=1,depth=2,parent=pad)
for sy in (-1,1):prim('cube','OarBlade',(0,sy*(SHAFT-.2),0),(.5,.36,.18),scale=(.16,.3,.025),parent=pad)
SPL=[prim('sphere','Splash%d'%i,(0,0,0),(.95,.97,1),scale=(.001,.001,.001),subdivisions=1) for i in range(2)]
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
LEO['root'].parent=raft;LEO['root'].location=(0,0,.2);LEO['root'].rotation_euler=(0,0,PI/2)
with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_idle']
ACT=dst.actions[0];st=rig.animation_data.nla_tracks.new().strips.new('idle',1,ACT);st.action_slot=ACT.slots[0];n_=ACT.frame_range[1]-ACT.frame_range[0]+1;st.repeat=(frames+30)/n_;st.extrapolation='HOLD'
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Wrist_'+limb,None);tg.empty_display_size=.04;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,.9)
 k_=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;k_.influence=0;IK[limb]=k_
scene.frame_set(1);bpy.context.view_layer.update()
SHL={l:raft.matrix_world.inverted()@(rig.matrix_world@rig.pose.bones['mixamorig:'+b+'Arm'].head) for l,b in (('LH','Left'),('RH','Right'))};print('SHOULDERS(raft local)',{k:tuple(round(x,2) for x in v) for k,v in SHL.items()})
# ---------------------------------------------------------------------------------------------------------- per-frame: the raft rides the water, the oar and hands follow
def water_h(p):
 dg=bpy.context.evaluated_depsgraph_get();ok,loc,n,i,ob,mw=scene.ray_cast(dg,Vector((p.x,p.y,4.)),Vector((0,0,-1)),distance=8.)
 return loc.z if ok and ob.name=='Water' else 0.
RX,RY=1.4,1.1;REACH=.44;HOLD=1.0
def influence(t):return smooth((t-(T0-1.2))/.6)*(1-smooth((t-(T_END+1.0))/.8))
DEEP=[];reach_err=[];rafts={};blade_hits=[];wdev=[]
for f in range(1,frames+1,2):
 t=(f-1)/fps;scene.frame_set(f);x=raft_x(t);y=path_y(x);yaw=yaw_at(t);c,s_=math.cos(yaw),math.sin(yaw)
 H={}
 for sx in (-1,1):
  for sy in (-1,1):H[(sx,sy)]=water_h(Vector((x+c*sx*RX-s_*sy*RY,y+s_*sx*RX+c*sy*RY,0)))
 z=sum(H.values())/4;pitch=((H[(1,-1)]+H[(1,1)])-(H[(-1,-1)]+H[(-1,1)]))/2/(2*RX);roll=((H[(-1,1)]+H[(1,1)])-(H[(-1,-1)]+H[(1,-1)]))/2/(2*RY)
 raft.location=(x,y,z-.02);raft.rotation_euler=(roll,-pitch,yaw);raft.keyframe_insert('location',frame=f);raft.keyframe_insert('rotation_euler',frame=f)
 M=Matrix.Translation(raft.location)@Euler(raft.rotation_euler,'XYZ').to_matrix().to_4x4();rafts[f]=M
 C,Rm=paddle_pose(t);pad.location=C;pad.rotation_euler=Rm.to_euler();pad.keyframe_insert('location',frame=f);pad.keyframe_insert('rotation_euler',frame=f)
 w=influence(t);axis=Rm@Vector((0,1,0))
 for l,sg in (('LH',1),('RH',-1)):
  pl=C+axis*GRIP*sg;TG[l].location=M@pl;TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
  d=(pl-SHL[l]).length
  if w>.99 and d>REACH:reach_err.append((round(d-REACH,3),l,round(t,1)))
 # splash where a blade is in the water
 a_,b_,s,env=stroke_state(t)
 for i,sy in enumerate((-1,1)):
  bl=M@(C+axis*(SHAFT-.2)*sy);bottom=bl.z-.1;wz=water_h(bl);deep=(wz-bottom) if s==sy and env>.3 else -1
  if s==sy and env>.9:DEEP.append(round(wz-bottom,2))
  sc=.0008+.22*smooth(min(1,max(0,deep+.1)/.12)) if deep>-.1 else .0008
  SPL[i].location=(bl.x,bl.y,wz+.03);SPL[i].scale=(sc,sc,sc*.7);SPL[i].keyframe_insert('location',frame=f);SPL[i].keyframe_insert('scale',frame=f)
  if deep>0:blade_hits.append(t)
 wdev.append(abs(raft.location.z-(z-.02)))
LEO_Z=.2
# gaze
scene.frame_set(1);bpy.context.view_layer.update()
hm=(rig.matrix_world@rig.pose.bones['mixamorig:Head'].matrix).to_3x3();fwd0=(raft.matrix_world.to_3x3()@Vector((1,0,0)))
AXES={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
FACE_AXIS=max(AXES,key=lambda k:AXES[k].normalized().dot(fwd0.normalized()));gz=bpy.data.objects.new('Gaze',None);link(gz)
k_=rig.pose.bones['mixamorig:Head'].constraints.new('DAMPED_TRACK');k_.target=gz;k_.track_axis=FACE_AXIS;k_.influence=.8
for f in range(1,frames+1,2):
 t=(f-1)/fps;x=raft_x(t);ax=min(x+9,X_END+5);gz.location=(ax,path_y(min(ax,X_END)),1.2);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
def raft_pos(t):x=raft_x(t);return Vector((x,path_y(x),0.))
def fwd(t):y=yaw_at(t);return Vector((math.cos(y),math.sin(y),0))
pass_t=[(t_of(x),k) for k,(x,y,r,yp) in enumerate(PASS)]
cuts=[('establish',0,T0+1.5,'wide')];last=T0+1.5;alt=0
for tp,k in pass_t:
 a=tp-2.2;b=tp+1.2
 if a-last>1.0:
  n=max(1,int((a-last)//4.5)+(1 if (a-last)%4.5>1.5 else 0));seg=(a-last)/n
  for j in range(n):cuts.append(('river %d'%len(cuts),last+j*seg,last+(j+1)*seg,('follow','front','oar')[alt%3]));alt+=1
 cuts.append(('boulder %d'%(k+1),max(a,last),b,'pass%d'%k));last=b
cuts.append(('drift',last,seconds,'wide'))
cams=[];CAMKEYS=[]
for k,(name,a,b,kind) in enumerate(cuts):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=300;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);rp=raft_pos(t);fw=fwd(t);lf=Vector((-fw.y,fw.x,0));cam.data.lens=32;q=rp+Vector((0,0,1.0))
  if kind=='wide':p=rp+Vector((-3,-7.5,4.2))+fw*(2+6*u);cam.data.lens=24
  elif kind=='follow':p=rp-fw*7.5+Vector((0,0,3.0))+lf*1.2
  elif kind=='front':p=rp+fw*6.5+lf*1.6+Vector((0,0,1.1));cam.data.lens=28
  elif kind=='oar':p=rp+fw*1.6-lf*2.6+Vector((0,0,1.7));q=rp+Vector((0,0,1.1));cam.data.lens=40
  else:
   x_b,y_b,r_b,yp=PASS[int(kind[4:])];side=-1 if y_b>0 else 1;p=Vector((x_b-8+6*u,side*7.8,2.0));q=rp+Vector((0,0,.8));cam.data.lens=34
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
FAMILY=set(kit._family(LEO['root']))|set(kit._family(raft))|set(kit._family(pad))
for o in bpy.data.objects:
 if o.name.startswith(('Splash','Wrist','Raft','Oar')):FAMILY.add(o.name)
CAND=[(0,0,1.),(0,0,2.5),(0,2.,1.),(0,-2.,1.),(2.,0,1.),(-2.,0,1.)]
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
if reach_err:issues.append('AUDIT reach: wrist target beyond arm reach %s'%reach_err[:4])
mind=1e9;minb=1e9;tmin=0
for t in np.arange(T0,T_END,.05):
 x=raft_x(t);y=path_y(x);yw=yaw_at(t);c,s_=math.cos(yw),math.sin(yw)
 for (bx,by,br,yp) in PASS:
  dx,dy=bx-x,by-y;lx=c*dx+s_*dy;ly=-s_*dx+c*dy;ex=max(abs(lx)-1.45,0);ey=max(abs(ly)-1.15,0);d=math.hypot(ex,ey)-br
  if d<mind:mind=d;tmin=t
 minb=min(minb,R['hw']-abs(y)-1.5)
if mind<.3:issues.append('AUDIT boulder: raft passes %.2f m from a boulder at %.1f s (need 0.3)'%(mind,tmin))
if minb<.5:issues.append('AUDIT bank: raft comes within %.2f m of the canyon wall'%minb)
worst={}
for f in range(F(T0),F(T_END),6):
 settle(f);t=(f-1)/fps
 for l,b in (('LH','LeftForeArm'),('RH','RightForeArm')):
  d=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if d>worst.get(l,(0,0))[0]:worst[l]=(d,t)
for l,(d,t) in worst.items():
 if d>.06:issues.append('AUDIT grip: %s misses the oar by %.0f cm at %.1f s'%(l,d*100,t))
print('ROUTE',[(round(x),round(y,1)) for x,y in route],'STROKES',len(STROKES),'blade-in-water keys',len(blade_hits),'max dip',max(DEEP) if DEEP else None,'min dip',min(DEEP) if DEEP else None,'min boulder clearance %.2f m, bank %.2f m'%(mind,minb),'GRIP',{k:round(v[0]*100,1) for k,v in worst.items()},'REACH over',len(reach_err))
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);adir=os.path.join(os.path.dirname(out),'audio_rapids');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(9)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w_:w_.setnchannels(1);w_.setsampwidth(2);w_.setframerate(SR);w_.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
def at(arr,t,x,g=1.):
 i=int(t*SR)
 if 0<=i<len(arr):
  n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
tt=np.arange(N_)/SR;rush=lp(nr.standard_normal(N_),6)*(.5+.5*np.sin(2*PI*.13*tt))*(.6+.4*np.minimum(tt/T0,1))
sp=np.zeros(N_+SR*2);k=np.arange(int(.5*SR))/SR;splash=lp(nr.standard_normal(len(k)),4)*np.exp(-k*9)
for t0,s in STROKES:at(sp,t0+.2,splash,1.)
who=np.zeros(N_+SR*3);k2=np.arange(int(1.2*SR))/SR;whoosh=lp(nr.standard_normal(len(k2)),30)*np.sin(PI*k2/1.2)**2
for tp,kk in pass_t:at(who,tp-.5,whoosh,.8)
mus=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 for f0 in ((146.8,185,220),(130.8,164.8,196),(110,138.6,164.8),(123.5,155.6,185))[ci%4]:
  kk=np.arange(int(4.2*SR))/SR;at(mus,ci*4.,np.sin(2*PI*f0*kk)*np.minimum(kk/.3,1)*np.exp(-kk*.7)*.15)
mus=mus[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('river.wav',rush,.5),wav('splash.wav',sp[:N_],.6),wav('rocks.wav',who[:N_],.5),wav('music.wav',mus,.3)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('river','oar splash','rocks','music')),start=1):strips.new_sound(n,p,ch,1)
scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.45,.6,.8)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('RAPIDS_DONE',frames,'frames')
