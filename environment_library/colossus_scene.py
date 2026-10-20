"""Blender script: 'The Colossus' - a stone giant lifts one arm; Leo hops onto its palm, rides it up, walks along the arm to the shoulder, climbs the stairs on the chest and pulls out the glowing core; the giant powers down and sinks back into the earth (about 55 s).

blender -b --disable-autoexec --python colossus_scene.py -- <ship_assets_dir> <out.blend>

Technique: LIVING IN A MOVING BODY'S FRAME. Leo's position is stored in the giant's local frame and converted every frame by the giant's root matrix (slow yaw sway, then the sink), so he stays on the surfaces that carry him
whatever the giant does. The palm is kept level by the wrist (its top is S.z - arm*cos(phi) + 1.5, which equals the arm's top surface when the arm is horizontal), so the ride up is continuous with the walk along the arm.
Hop-on timing is taken from the palm (stationary at the start of the lift), the stair path is a straight ramp from the arm to the chest platform, and the core, once pulled, follows his hands (IK) and chest. Audit:
the palm is level and equals the arm top at the top of the lift, the arm is horizontal during the walk, hands reach the core, Leo stays on the platform while the giant sinks and steps off within 0.8 m of the ground,
persistence, camera visibility. Clips: idle, jump, climb, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('colossus');PI=math.pi;smooth=kit.smooth;CO=w2.COLOSSUS;rnd=random.Random(12)
S.load_env('colossus_valley')
SX,SZ,ARM=CO['sx'],CO['sz'],CO['arm'];STOOL=Vector(CO['stool'])
# ---------------------------------------------------------------------------------------------------------- the timeline
T_STOOL=3.0;HOP=.7;T_R0=T_STOOL+HOP;RISE=9.0;T_TOP=T_R0+RISE;R_END=5.0;V_ARM=2.4;T_W1=T_TOP+(ARM-R_END)/V_ARM
SA=Vector((8.2,-5.7,25.5));SB=Vector((-5.0,-5.7,33.0));LST=(SB-SA).length;V_ST=2.0;T_ST=T_W1+LST/V_ST;T_TURN=T_ST+.9;T_GRIP=T_TURN+.4;T_P0=T_TURN+1.2;T_P1=T_P0+1.6
T_S0=T_P1+1.5;SINK=10.0;T_S1=T_S0+SINK;D_END=32.5;T_OFF=T_S1+.5;WALKOFF=4.0;T_END=T_OFF+WALKOFF+3.5;S.clock(T_END);seconds=S.seconds
def phi_of(t):
 if t<T_R0:return 0.
 if t<T_TOP:return (PI/2)*smooth((t-T_R0)/RISE)
 if t<T_P1+.5:return PI/2
 return (PI/2)*(1-smooth((t-(T_P1+.5))/5.0))
def D_of(t):return D_END*smooth((t-T_S0)/SINK)
def psi_of(t):return .022*math.sin(.45*t)*(1-smooth((t-T_P1)/2.0))
def M_root(t):return Matrix.Translation((0,0,-D_of(t)))@Matrix.Rotation(psi_of(t),4,'Z')
def palm_top(phi):return Vector((SX,-ARM*math.sin(phi)-2.6*math.cos(phi),SZ-ARM*math.cos(phi)+1.5))
# ---------------------------------------------------------------------------------------------------------- the giant
ROOT=bpy.data.objects.new('GolemRoot',None);S.link(ROOT)
STONE=(.42,.4,.38);STONE2=(.36,.34,.33)
def box(name,c,h,color=STONE,parent=ROOT):return S.prim('cube',name,c,color,scale=h,parent=parent)
for sx_ in (-1,1):
 box('GolemFoot',(sx_*5,-1,1.5),(2.5,3.5,1.5),STONE2);box('GolemShin',(sx_*5,0,8),(1.7,1.7,5));box('GolemThigh',(sx_*5,0,17.5),(1.9,1.9,4.5))
box('GolemPelvis',(0,0,24),(6.5,3.4,2));box('GolemTorso',(0,0,34),(8,5,12));box('GolemHead',(0,-.4,50),(3.5,3.5,4));box('GolemBrow',(0,-3.9,51.2),(3.7,.6,.6),STONE2)
box('GolemShoulderL',(-9.5,0,25.5),(1.6,1.6,1.6),STONE2);box('GolemShoulderR',(SX,0,25.5),(1.6,1.6,1.6),STONE2)
armL=box('GolemArmL',(-9.5,0,SZ-ARM/2),(1.5,1.5,ARM/2),STONE);box('GolemFistL',(-9.5,0,SZ-ARM-.8),(1.9,1.9,1.4),STONE2)
for i in range(12):S.prim('cube','GolemRune',(math.sin(i*1.3)*6.5,-5.02,26+i*1.4),(.9,.5,.2),scale=(.35,.03,.35+.15*(i%3)),emit=2.0,parent=ROOT)
eyes=[S.prim('sphere','GolemEye',(sx_*1.4,-3.95,50.4),(1,.55,.1),scale=(.4,.2,.4),emit=10.,subdivisions=1,parent=ROOT) for sx_ in (-1,1)]
for e in eyes:
 m=e.data.materials[0].copy();e.data.materials[0]=m;b=m.node_tree.nodes.get('Principled BSDF')
 e['mat']=m.name
for st_ in range(14):
 u=(st_+.5)/14;p=SA.lerp(SB,u);S.prim('cube','GolemStep',(p.x,p.y,p.z-.35),(.5,.47,.42),scale=(.5,.95,.35),parent=ROOT)
S.prim('cube','GolemPlatform',(SB.x,SB.y-.2,SB.z-.4),(.5,.47,.42),scale=(2.4,1.2,.4),parent=ROOT)
armR=bpy.data.objects.new('GolemArmR',None);S.link(armR);armR.parent=ROOT;armR.location=(SX,0,SZ)
S.prim('cube','GolemArmBox',(0,0,-ARM/2),STONE,scale=(1.5,1.5,ARM/2),parent=armR);S.prim('cube','GolemFistR',(0,0,-ARM-.2),STONE2,scale=(1.9,1.9,1.1),parent=armR)
palm=bpy.data.objects.new('GolemPalm',None);S.link(palm);palm.parent=ROOT;S.prim('cube','GolemPalmSlab',(0,0,-.25),STONE2,scale=(2.2,2.2,.25),parent=palm)
for f in S.keys():
 t=(f-1)/S.fps;ph=phi_of(t);M=M_root(t)
 ROOT.matrix_world=M;ROOT.location=M.translation;ROOT.rotation_euler=M.to_3x3().to_euler();ROOT.keyframe_insert('location',frame=f);ROOT.keyframe_insert('rotation_euler',frame=f)
 armR.rotation_euler=(-ph,0,0);armR.keyframe_insert('rotation_euler',frame=f)
 p=palm_top(ph);palm.location=p;palm.keyframe_insert('location',frame=f)
 for e in eyes:
  m=bpy.data.materials[e['mat']];b=m.node_tree.nodes.get('Principled BSDF')
  if b and 'Emission Strength' in b.inputs:b.inputs['Emission Strength'].default_value=10.*(1-smooth((t-T_P1)/1.5));b.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo (a state in the giant's frame)
t_land=T_R0
def local_state(t):
 """(local position, local heading, mode) once he is on the giant"""
 ph=phi_of(t)
 if t<T_TOP:return palm_top(ph),PI/2,'ride'
 if t<T_W1:r=ARM-V_ARM*(t-T_TOP);return Vector((SX,-r,SZ+1.5)),PI/2,'walk'
 if t<T_ST:u=(t-T_W1)/(T_ST-T_W1);return SA.lerp(SB,u),PI,'stairs'
 if t<T_TURN:u=smooth((t-T_ST)/(T_TURN-T_ST));return SB.copy(),PI+(PI/2-PI)*u,'stand'
 return SB.copy(),PI/2,'stand'
def leo_world(t):
 """(position, heading, mode, vertical extra)"""
 if t<T_STOOL:return STOOL+Vector((0,0,CO['stool_h'])),PI/2,'idle'
 if t<t_land:
  u=(t-T_STOOL)/HOP;p1=M_root(t_land)@palm_top(phi_of(t_land));p0=STOOL+Vector((0,0,CO['stool_h']));p=p0.lerp(p1,u);A=9.81*HOP*HOP/8+.15;p.z+=4*A*u*(1-u);return p,PI/2,'hop'
 if t<T_OFF:
  lp,lh,mode=local_state(t);M=M_root(t);return M@lp,lh+psi_of(t),mode
 lp,lh,mode=local_state(T_OFF);M=M_root(T_OFF);p0=M@lp;p1=Vector((-4.0,-15.0,0.));u=min(1.,(t-T_OFF)/WALKOFF);p=p0.lerp(p1,smooth(u));p.z=p0.z+(0.-p0.z)*smooth(min(1.,u*2.5));h=math.atan2(p1.y-p0.y,p1.x-p0.x);return p,h,('walkoff' if u<1 else 'cele')
leo=S.character('Leo',S.params['hero_tint']);root=leo['root'];IK,TG=S.ik(leo)
segs=[(0,T_STOOL-.1,'idle',1.),(T_STOOL-.1,t_land+.2,'jump',.8),(t_land+.2,T_TOP,'idle',1.),(T_TOP,T_W1,'climb',.55),(T_W1,T_ST,'climb',.65),(T_ST,T_OFF,'idle',1.),(T_OFF,T_OFF+WALKOFF,'climb',.7),(T_OFF+WALKOFF,S.seconds,'cele',1.)]
S.play(leo,[s for s in segs if s[1]-s[0]>.12])
CRY0=Vector((-5.0,-5.35,34.1))
def crystal_world(t):
 M=M_root(t)
 if t<T_P0:return M@CRY0
 if t<T_P1:
  u=smooth((t-T_P0)/(T_P1-T_P0));return M@(CRY0+Vector((0,-.6,0)))+(lp_chest(t)-(M@(CRY0+Vector((0,-.6,0)))))*0
 return lp_chest(t)
def lp_chest(t):
 p,h,mode,*_=leo_world(t)+(0,) if False else (leo_world(t)[0],leo_world(t)[1],leo_world(t)[2]);f=Vector((math.cos(h),math.sin(h),0));return p+f*.32+Vector((0,0,1.05))
def crystal_pos(t):
 M=M_root(t)
 if t<T_P0:return M@CRY0
 if t<T_P1+.5:
  u=smooth((t-T_P0)/(T_P1-T_P0+.5));start=M@CRY0;mid=M@(CRY0+Vector((0,-.6,0)));return start.lerp(mid,min(1,u*1.2)) if t<T_P1 else mid.lerp(lp_chest(t),smooth((t-T_P1)/.5))
 return lp_chest(t)
CRYS=S.prim('sphere','CoreCrystal',CRY0,(.4,.8,1.),scale=(.5,.5,.7),emit=10.,subdivisions=2)
for f in S.keys():
 t=(f-1)/S.fps;p,h,mode=leo_world(t)[:3];yaw=h+PI/2
 root.location=p;root.rotation_euler=(0,0,yaw);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 cp=crystal_pos(t);CRYS.location=cp;CRYS.keyframe_insert('location',frame=f)
 lat=Vector((-math.sin(h),math.cos(h),0));w=smooth((t-T_GRIP)/.5)
 for l,sg in (('LH',1),('RH',-1)):
  TG[l].location=cp+lat*.16*sg;TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(0,1,0))
for f in S.keys():
 t=(f-1)/S.fps;p,h,mode=leo_world(t)[:3];fw=Vector((math.cos(h),math.sin(h),0));gz.location=crystal_pos(t) if t>T_ST-1 else p+fw*6+Vector((0,0,1.2));gz.keyframe_insert('location',frame=f)
# dust at the foot of the giant while it sinks
PUF=[]
for i in range(10):
 a=i*2*PI/10;PUF.append((S.prim('sphere','DustSink%d'%i,(0,0,0),(.7,.62,.5),scale=(.001,.001,.001),subdivisions=1),Vector((math.cos(a)*11,math.sin(a)*11,0)),i*.4))
for pf,p0,off in PUF:
 for f in S.keys():
  t=(f-1)/S.fps;u=(t-T_S0-off)/4.0
  if 0<=u<1:sc=.5+5*smooth(u);pf.location=p0+Vector((0,0,1+3*u));s_=sc*(1-smooth((u-.5)/.5))+.001
  else:pf.location=p0;s_=.001
  pf.scale=(s_,s_,s_*.8);pf.keyframe_insert('location',frame=f);pf.keyframe_insert('scale',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('colossus',0,T_STOOL+.7,'wide'),('lift',T_R0-.3,T_R0+4.8,'ride'),('rising',T_R0+4.8,T_TOP+.4,'ride2'),('the arm',T_TOP+.4,T_W1-1.0,'arm'),('the shoulder',T_W1-1.0,T_ST-1.0,'stairs'),('the stairs',T_ST-1.0,T_TURN+.4,'stairs2'),('the core',T_TURN+.4,T_P1+1.2,'core'),('powering down',T_P1+1.2,T_S1,'sink'),('safe',T_S1,S.seconds,'end')]
cuts=[c for c in cuts if c[2]-c[1]>.4]
def pos_(kind,t,u):
 p,h,mode=leo_world(t)[:3];lp=p+Vector((0,0,1.0));M=M_root(t)
 if kind=='wide':return Vector((8,-72,26)),Vector((0,0,26)),24
 if kind=='ride':return Vector((p.x+14,p.y-18,p.z+2.5)),lp,30
 if kind=='ride2':return Vector((p.x+3,-58,max(8,p.z-6))),lp,28
 if kind=='arm':return Vector((p.x+3.5,p.y-8,p.z+3.5)),lp+Vector((0,3,0)),30
 if kind=='stairs':return Vector((p.x+14,p.y-20,p.z+2)),lp,32
 if kind=='stairs2':return Vector((p.x+9,p.y-12,p.z+3.5)),lp,34
 if kind=='core':return Vector((SB.x+3.0,SB.y-3.2,M_root(t).translation.z+SB.z+1.4)),crystal_pos(t),42
 if kind=='sink':return Vector((22,-48,max(6,p.z-10))),lp,26
 return Vector((-16,-28,4.0)),lp,32
S.cameras(cuts,pos_,('Golem','Core','DustSink'),cand=[(0,0,1.),(0,0,3.),(0,3.,0),(0,-3.,0),(3.,0,0),(-3.,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
pt=palm_top(PI/2);arm_top=Vector((SX,-ARM,SZ+1.5))
clr=min(((palm_top(ph)-Vector((SX,-ARM*math.sin(ph),SZ-ARM*math.cos(ph)))).dot(Vector((0,-math.cos(ph),math.sin(ph)))) for ph in np.linspace(0,PI/2,40)))
if clr<1.45:issues.append('AUDIT palm: the palm comes %.2f m from the arm axis (arm half-thickness 1.5)'%clr)
if (pt-arm_top).length>.05:issues.append('AUDIT palm: at the top of the lift the palm is %.2f m from the arm surface line'%(pt-arm_top).length)
if abs(phi_of(T_TOP+1)-PI/2)>1e-3:issues.append('AUDIT arm: the arm is not horizontal while Leo walks along it')
sink_leo=leo_world(T_S1)[0].z
if sink_leo>.8:issues.append('AUDIT sink: the platform ends %.2f m above the ground'%sink_leo)
zs=[leo_world(tt)[0].z for tt in np.arange(T_ST,T_S1,.2)]
if min(zs)<-.2:issues.append('AUDIT platform: Leo is below the ground while the giant sinks')
rer=[];worst={}
for f in range(S.F(T_GRIP+.6),S.F(T_OFF+WALKOFF),6):
 t=(f-1)/S.fps;S.settle(f);rig=leo['rig']
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),l,round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,t)
if rer:issues.append('AUDIT reach: hands beyond reach of the core %s (%d samples)'%(rer[:3],len(rer)))
for l,(g,t) in worst.items():
 if g>.09:issues.append('AUDIT grip: %s misses the core by %.0f cm at %.1f s'%(l,g*100,t))
print('COLOSSUS lift %.1f-%.1f s, walk to %.1f s, stairs to %.1f s, pull %.1f-%.1f s, sink ends %.1f s at %.2f m, GRIP %s, REACH over %d'%(T_R0,T_TOP,T_W1,T_ST,T_P0,T_P1,T_S1,sink_leo,{k:round(v[0]*100,1) for k,v in worst.items()},len(rer)))
def snd(A):
 A.track('wind',A.noise(A.N,30)*.3,.3)
 gr=A.buf()
 for (a,b) in ((T_R0,T_TOP),(T_P1+.5,T_P1+5.5),(T_S0,T_S1)):
  n=int((b-a)*A.SR);A.at(gr,a,A.noise(n,90)*np.sin(np.linspace(0,PI,n))*.9+np.sin(2*PI*38*np.arange(n)/A.SR)*.4*np.sin(np.linspace(0,PI,n)),1.)
 A.track('stone grinding',gr,.8);st=A.buf();k=A.burst(.1,5,40.)
 for t in np.arange(T_TOP,T_ST,.5):A.at(st,t,k,.5)
 for t in np.arange(T_OFF,T_OFF+WALKOFF,.4):A.at(st,t,k,.5)
 A.track('steps',st,.4);cr=A.buf();A.at(cr,T_P0,A.tone(1100,2.5,1.4,.7)+A.tone(1650,2.5,2.,.4),1.);A.at(cr,T_P1,A.tone(70,2.0,2.,.9)+A.burst(2.0,6,2.5),1.);A.track('core',cr,.7)
 A.track('music',A.chords(((98,123.5,146.8),(87.3,110,130.8),(82.4,103.8,123.5),(92.5,116.5,138.6)),.22),.4)
S.audio(snd)
S.finish(issues,[root],world=(.62,.7,.82))
