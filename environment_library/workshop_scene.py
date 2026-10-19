"""Blender script: 'The Workshop' - Leo assembles a clockwork music box: picks three gears from the bench, seats them on their pins, turns the crank, a bird pops out (about 30 s).

blender -b --disable-autoexec --python workshop_scene.py -- <ship_assets_dir> <out.blend>

New in this scene: FINE MANIPULATION. Both hands are IK wrist targets driven by timed hand paths (hover, descend, grasp, lift, carry, seat, release); the carried gear is placed from the wrist, so it follows the hand,
not the other way round. The gears have real teeth and rotate by the meshing law (neighbour angle = pi + pi/N - angle*N1/N2, centres one pitch radius sum apart), so the teeth never collide; the hand rides
the crank knob on a circle. Audit: every grasp/seat target is within the arm reach (no clamping), grips on gear and knob, tooth meshing at sample angles, seated gears land exactly on their pins, persistence,
camera visibility. Clip: leo_idle (build_ship_assets.py)."""
import bpy,math,random,sys,os,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit,scene_params,locations
from mathutils import Vector,Euler
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
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.5 if name.startswith('Gear') else .9
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
CTX=dict(link=link,mat=mat,prim=prim);W=locations.WORKSHOP;BZ=W['bench']['z']+.004
locations.load('workshop',CTX,'intact')
# ---------------------------------------------------------------------------------------------------------- the machine
MOD=.004;TEETH=(20,13,8);RAD=[n*MOD for n in TEETH]
PIN=[Vector((0,.10,0)),Vector((RAD[0]+RAD[1],.10,0)),Vector((RAD[0]+2*RAD[1]+RAD[2],.10,0))]
RACK=[Vector((-.30,.06,0)),Vector((.34,.05,0)),Vector((.43,.05,0))]
PLATE_TOP=BZ+.014;ZP=PLATE_TOP+.007;ZR=BZ+.007;PIN_Z=[ZP]*3;THICK=.012
def make_gear(name,n,r,color):
 root,tip=r-.005,r+.005;p=2*PI/n;pts=[]
 for k in range(n):
  for da,rr in ((-.25,root),(-.14,tip),(.14,tip),(.25,root)):a=(k+da)*p;pts.append((rr*math.cos(a),rr*math.sin(a)))
 m=bpy.data.meshes.new(name);h=THICK/2;N=len(pts)
 faces=[list(range(N-1,-1,-1)),list(range(N,2*N))]+[[i,(i+1)%N,N+(i+1)%N,N+i] for i in range(N)]
 m.from_pydata([(x,y,-h) for x,y in pts]+[(x,y,h) for x,y in pts],[],faces);m.update();m.materials.append(mat('Gear'+name,color))
 o=bpy.data.objects.new(name,m);link(o);return o
GEAR=[make_gear('Big',TEETH[0],RAD[0],(.78,.56,.18)),make_gear('Mid',TEETH[1],RAD[1],(.7,.7,.74)),make_gear('Small',TEETH[2],RAD[2],(.85,.35,.2))]
prim('cube','MachinePlate',(.1,.1,BZ+.007),(.22,.17,.14),scale=(.2,.14,.007))
for i in range(3):prim('cyl','GearPin',(PIN[i].x,PIN[i].y,PLATE_TOP+.01),(.8,.8,.82),scale=(.006,.006,.012),vertices=8,radius=1,depth=2)
for i in range(3):prim('cyl','GearRack',(RACK[i].x,RACK[i].y,BZ+.002),(.3,.18,.1),scale=(RAD[i]+.012,RAD[i]+.012,.003),vertices=20,radius=1,depth=2)
KR=.05;lever=prim('cube','CrankLever',(KR/2,0,.034),(.75,.75,.78),scale=(KR/2+.006,.005,.003),parent=GEAR[2]);knob=prim('cyl','CrankKnob',(KR,0,.062),(.6,.15,.12),scale=(.009,.009,.03),vertices=10,radius=1,depth=2,parent=GEAR[2])
HX,HY=.05,.40
prim('cube','BirdBox',(HX,HY,BZ+.06),(.3,.2,.12),scale=(.14,.11,.06));rim=prim('cube','BirdRim',(HX,HY,BZ+.125),(.55,.4,.2),scale=(.15,.12,.008))
BIRD=prim('sphere','Bird',(HX,HY,BZ+.02),(.2,.55,.85),scale=(.045,.03,.05),subdivisions=2);prim('cone','BirdBeak',(0,.035,.01),(1,.7,.2),scale=(.012,.016,.012),rot=(-PI/2,0,0),vertices=6,radius1=1,depth=2,parent=BIRD)
LAMP=prim('sphere','Indicator',(HX+.1,HY-.09,BZ+.14),(.15,.9,.25),scale=(.012,.012,.012),emit=0.,subdivisions=1)
# ---------------------------------------------------------------------------------------------------------- the story clock
T_START=3.0;DUR=4.0;TS=[T_START+DUR*i for i in range(3)];T_CR0=T_START+DUR*3;T_TURN0=T_CR0+1.8;T_TURN1=T_TURN0+6.0;T_POP=T_TURN1+.5;T_END=T_POP+4.0;seconds=T_END+1.5;frames=int(seconds*fps)
scene.frame_start=1;scene.frame_end=frames
TURNS=2.5
def theta3(t):
 if t<T_TURN0:return 0.
 u=min(1.,(t-T_TURN0)/(T_TURN1-T_TURN0));return TURNS*2*PI*smooth(u)
def rot_of(t):
 r3=theta3(t);r2=(PI+PI/TEETH[2]-r3)*TEETH[2]/TEETH[1];r1=(PI+PI/TEETH[1]-r2)*TEETH[1]/TEETH[0];return [r1,r2,r3]
# ---------------------------------------------------------------------------------------------------------- Leo (static at the bench) and his hands
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
 rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create();return dict(root=root,rig=rig,objs=new)
prm=scene_params.get();LEO=load_char('Leo',prm['hero_tint'])
LEO['root'].location=(0.,-.22,0.);LEO['root'].rotation_euler=(0,0,PI)
with bpy.data.libraries.load(os.path.join(ASSETS,'leo_idle.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_idle']
ACT=dst.actions[0];st=LEO['rig'].animation_data.nla_tracks.new().strips.new('idle',1,ACT);st.action_slot=ACT.slots[0];n_=ACT.frame_range[1]-ACT.frame_range[0]+1;st.repeat=(frames+30)/n_;st.extrapolation='HOLD'
IK={};TG={};rig=LEO['rig']
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Wrist_'+limb,None);tg.empty_display_size=.04;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,.9)
 k_=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;k_.influence=0;IK[limb]=k_
scene.frame_set(1);bpy.context.view_layer.update()
SH={l:rig.matrix_world@rig.pose.bones['mixamorig:'+b+'Arm'].head for l,b in (('LH','Left'),('RH','Right'))};print('SHOULDERS',{k:tuple(round(x,2) for x in v) for k,v in SH.items()})
REACH=.44
def V(p,z):return Vector((p.x,p.y,z))
HOV=1.16;GZ=.05
NEUT={'LH':Vector((-.20,-.03,1.12)),'RH':Vector((.20,-.03,1.12))}
def gear_keys(i,limb,ts):
 R=V(RACK[i],ZR);P=V(PIN[i],ZP);top=lambda p,z:Vector((p.x,p.y,z))
 return [(ts,top(R,HOV)),(ts+.7,top(R,ZR+GZ)),(ts+1.5,top(R,HOV+.01)),(ts+1.95,top((R+P)/2,HOV+.05)),(ts+2.4,top(P,HOV+.01)),(ts+2.9,top(P,ZP+GZ)),(ts+3.3,top(P,ZP+GZ)),(ts+3.9,top(P,HOV))]
KEYS={'LH':[(0.,NEUT['LH'])],'RH':[(0.,NEUT['RH'])]};ACTIVE={'LH':[],'RH':[]}
LIMB=['LH','RH','RH'];GRAB=[]
for i in range(3):
 ks=gear_keys(i,LIMB[i],TS[i]);KEYS[LIMB[i]]+=[(t,p) for t,p in ks];ACTIVE[LIMB[i]].append((TS[i]-.5,TS[i]+3.9+.4));GRAB.append((TS[i]+.9,TS[i]+3.0))
ST=V(Vector((PIN[2].x,PIN[2].y,0)),ZP)
def knob_pos(t):
 th=theta3(t);return Vector((PIN[2].x+KR*math.cos(th),PIN[2].y+KR*math.sin(th),ZP+.034+.045+.02))
KEYS['RH']+=[(T_CR0,Vector((PIN[2].x+KR,PIN[2].y,HOV))),(T_TURN0-.1,knob_pos(0.))]
STEADY=Vector((-.16,.08,1.07))
KEYS['LH']+=[(T_CR0,Vector((-.16,.08,HOV))),(T_CR0+1.0,STEADY)]
ACTIVE['RH'].append((T_CR0-.5,T_POP+1.9));ACTIVE['LH'].append((T_CR0-.5,T_POP+1.9))
KEYS['RH'].append((T_TURN1+.1,knob_pos(T_TURN1)));KEYS['RH'].append((T_POP+1.4,Vector((.30,-.03,1.14))))
KEYS['LH'].append((T_POP+.6,STEADY));KEYS['LH'].append((T_POP+1.5,Vector((-.20,-.03,1.14))))
for l in KEYS:KEYS[l].sort(key=lambda kv:kv[0])
def eval_keys(ks,t):
 if t<=ks[0][0]:return ks[0][1]
 for (t0,p0),(t1,p1) in zip(ks,ks[1:]):
  if t0<=t<=t1:return p0.lerp(p1,smooth((t-t0)/max(1e-6,t1-t0)))
 return ks[-1][1]
def wrist(l,t):
 if l=='RH' and T_TURN0-.1<=t<=T_TURN1+.1:return knob_pos(t)
 return eval_keys(KEYS[l],t)
def influence(l,t):
 w=0.
 for a,b in ACTIVE[l]:w=max(w,smooth((t-a)/.5)*(1-smooth((t-(b-.5))/.5)))
 return w
reach_err=[]
for f in range(1,frames+1,2):
 t=(f-1)/fps
 for l in ('LH','RH'):
  p=wrist(l,t);w=influence(l,t);TG[l].location=p;TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
  d=(p-SH[l]).length
  if w>.99 and d>REACH:reach_err.append((round(d-REACH,3),l,round(t,1)))
# gears follow the wrist while held, rest on rack before and on the pin after
def gear_pos(i,t):
 a,b=GRAB[i]
 if t<a:return V(RACK[i],ZR)
 if t>b:return V(PIN[i],ZP)
 return wrist(LIMB[i],t)-Vector((0,0,GZ))
prevr=[None]*3
for f in range(1,frames+1,2):
 t=(f-1)/fps;r=rot_of(t)
 for i,g in enumerate(GEAR):g.location=gear_pos(i,t);g.rotation_euler=(0,0,r[i]);g.keyframe_insert('location',frame=f);g.keyframe_insert('rotation_euler',frame=f)
# the bird pops up on a spring, the indicator lights
def bird_z(t):
 if t<T_POP:return BZ+.02
 u=(t-T_POP)/.7;return BZ+.02+.17*(math.sin(min(u,1)*PI/2)+(.12*math.exp(-3*(u-1))*math.sin(18*(u-1)) if u>1 else 0.))
for f in range(1,frames+1,2):
 t=(f-1)/fps;BIRD.location=(HX,HY,bird_z(t));BIRD.rotation_euler=(0,0,(.4*math.sin(2*PI*1.3*(t-T_POP)) if t>T_POP else 0.));BIRD.keyframe_insert('location',frame=f);BIRD.keyframe_insert('rotation_euler',frame=f)
lm=LAMP.data.materials[0].copy();LAMP.data.materials[0]=lm;eb=lm.node_tree.nodes.get('Principled BSDF')
if eb and 'Emission Strength' in eb.inputs:
 for f in range(1,frames+1,3):
  t=(f-1)/fps;eb.inputs['Emission Strength'].default_value=10. if t>=T_POP else 0.;eb.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# gaze: the head follows the working hand
scene.frame_set(1);bpy.context.view_layer.update()
hm=(rig.matrix_world@rig.pose.bones['mixamorig:Head'].matrix).to_3x3();fwd0=Vector((0,1,0))
AXES={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
FACE_AXIS=max(AXES,key=lambda k:AXES[k].normalized().dot(fwd0));gz=bpy.data.objects.new('Gaze',None);link(gz)
k_=rig.pose.bones['mixamorig:Head'].constraints.new('DAMPED_TRACK');k_.target=gz;k_.track_axis=FACE_AXIS;k_.influence=.8
def look_at(t):
 if t<T_START-.6:return Vector((0,.25,1.1))
 if t>=T_POP-.2:return Vector((HX,HY,BZ+.2))
 best=max(('LH','RH'),key=lambda l:influence(l,t))
 return wrist(best,t)
for f in range(1,frames+1,2):
 t=(f-1)/fps;gz.location=look_at(t);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('establish',0,T_START+.4,'wide')]
for i in range(3):cuts.append(('gear %d'%(i+1),TS[i]+.4,TS[i]+DUR+.2,'bench%d'%i))
cuts+=[('the crank',T_CR0,T_TURN0+3.0,'crank'),('turning',T_TURN0+3.0,T_POP-.2,'face'),('the bird',T_POP-.2,T_POP+2.8,'bird'),('end',T_POP+2.8,seconds,'wide2')]
cams=[];CAMKEYS=[]
for k,(name,a,b,kind) in enumerate(cuts):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=100;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);cam.data.lens=40
  mid=Vector((.1,.1,1.12))
  if kind=='wide':p=Vector((-2.4+1.2*u,-2.6,1.7));q=Vector((0,.1,1.15));cam.data.lens=28
  elif kind.startswith('bench'):
   i=int(kind[-1]);g=gear_pos(i,t);p=Vector((.15+.35*(i-1),1.05,1.55-.05*u));q=Vector((g.x*.7+.03,.1,1.1));cam.data.lens=62
  elif kind=='crank':p=Vector((.9,-.55,1.3));q=Vector((PIN[2].x,.1,1.1));cam.data.lens=52
  elif kind=='face':p=Vector((.55,1.3,1.5));q=Vector((0,-.1,1.15));cam.data.lens=46
  elif kind=='bird':p=Vector((-.5,.95,BZ+.5));q=Vector((HX,HY,BZ+.15+.08*smooth(min(1,(t-T_POP)/.7))));cam.data.lens=60
  else:p=Vector((.9,2.6,1.9));q=Vector((0,0,1.2));cam.data.lens=30
  cam.location=p;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
FAMILY=set(kit._family(LEO['root']))
for o in bpy.data.objects:
 if o.name.startswith(('Big','Mid','Small','Crank','Gear','Bird','Indicator','Wrist')):FAMILY.add(o.name)
CAND=[(0,0,.2),(0,0,.5),(0,-.5,.3),(0,.5,.3),(.4,0,.2),(-.4,0,.2)]
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
for i in range(3):
 for tt in (GRAB[i][0],GRAB[i][1]):
  for l in ('LH','RH'):pass
 e=(gear_pos(i,GRAB[i][1]-.01)-V(PIN[i],ZP)).length
 if e>.012:issues.append('AUDIT seat: gear %d is %.1f cm from its pin at release'%(i+1,e*100))
# the meshing law: no vertex of one gear's outline lies inside its neighbour's outline (checked at sampled crank angles)
def outline(n,r):
 root,tip=r-.005,r+.005;p=2*PI/n;return [(rr*math.cos((k+da)*p),rr*math.sin((k+da)*p)) for k in range(n) for da,rr in ((-.25,root),(-.14,tip),(.14,tip),(.25,root))]
def inside(pt,poly):
 x,y=pt;c=False;j=len(poly)-1
 for i in range(len(poly)):
  xi,yi=poly[i];xj,yj=poly[j]
  if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi+1e-12)+xi:c=not c
  j=i
 return c
def placed(i,rot):
 c,s_=math.cos(rot),math.sin(rot);return [(PIN[i].x+x*c-y*s_,PIN[i].y+x*s_+y*c) for x,y in outline(TEETH[i],RAD[i])]
bad=0
for th in np.linspace(0,12,49):
 r3=th;r2=(PI+PI/TEETH[2]-r3)*TEETH[2]/TEETH[1];r1=(PI+PI/TEETH[1]-r2)*TEETH[1]/TEETH[0];P=[placed(0,r1),placed(1,r2),placed(2,r3)]
 for a,b in ((0,1),(1,2)):
  if any(inside(pt,P[b]) for pt in P[a]) or any(inside(pt,P[a]) for pt in P[b]):bad+=1
if bad:issues.append('AUDIT mesh: teeth collide at %d of 49 sampled angles'%bad)
worst={}
for f in range(F(T_START),F(T_POP+1.5),4):
 settle(f);t=(f-1)/fps
 for l,b in (('LH','LeftForeArm'),('RH','RightForeArm')):
  if influence(l,t)<.99:continue
  d=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if d>worst.get(l,(0,0))[0]:worst[l]=(d,t)
for l,(d,t) in worst.items():
 if d>.06:issues.append('AUDIT grip: %s misses its target by %.0f cm at %.1f s'%(l,d*100,t))
print('GRIP',{k:(round(v[0]*100,1),round(v[1],1)) for k,v in worst.items()},'REACH over',len(reach_err))
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);adir=os.path.join(os.path.dirname(out),'audio_workshop');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(5)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
def at(arr,t,x,g=1.):
 i=int(t*SR)
 if 0<=i<len(arr):
  n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
k=np.arange(int(.05*SR))/SR;tick=np.sin(2*PI*1800*k)*np.exp(-k*90);thunk=lp(nr.standard_normal(len(k)),20)*np.exp(-k*60)
ticks=np.zeros(N_+SR)
for t in np.arange(0,seconds,1.0):at(ticks,t,tick,.25)
clicks=np.zeros(N_+SR)
for i in range(3):at(clicks,GRAB[i][0],thunk,.8);at(clicks,GRAB[i][1],thunk*1.2,1.)
ang=0.
for f in range(F(T_TURN0),F(T_TURN1)):
 t=(f-1)/fps;d=theta3(t+1/fps)-theta3(t);ang+=d/(2*PI)*TEETH[2]
 while ang>=1.:ang-=1.;at(clicks,t,tick*1.4,.5)
bell=np.zeros(N_+SR*3);bk=np.arange(int(2.0*SR))/SR;at(bell,T_POP+.5,(np.sin(2*PI*1568*bk)+.5*np.sin(2*PI*2093*bk))*np.exp(-bk*2.5),.5)
note=lambda f,d,v=1.:(lambda k:(np.sin(2*PI*f*k)+.3*np.sin(4*PI*f*k))*np.minimum(k/.01,1)*np.exp(-k*5/d)*v)(np.arange(int(d*SR))/SR)
box=np.zeros(N_+SR*3)
for j,fr in enumerate((784,988,1175,1319,1175,988,784,659,784,988,1175,988,784)):at(box,T_POP+1.2+j*.28,note(fr,.5,.4))
room=lp(nr.standard_normal(N_),120)*.04;mus=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 for f0 in ((130.8,164.8,196),(110,138.6,164.8),(87.3,110,130.8),(98,123.5,146.8))[ci%4]:at(mus,ci*4.,np.sin(2*PI*f0*np.arange(int(4.2*SR))/SR)*np.minimum(np.arange(int(4.2*SR))/SR/.3,1)*np.exp(-np.arange(int(4.2*SR))/SR*.8)*.15)
tt=np.arange(N_)/SR;mus=mus[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('room.wav',room+ticks[:N_],.4),wav('clicks.wav',clicks[:N_],.6),wav('bell.wav',bell[:N_],.6),wav('musicbox.wav',box[:N_],.5),wav('music.wav',mus,.3)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('room and clock','gear clicks','bell','music box','music')),start=1):strips.new_sound(n,p,ch,1)
scene.world=bpy.data.worlds.new('Dusk');scene.world.color=(.03,.025,.02)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('WORKSHOP_DONE',frames,'frames')
