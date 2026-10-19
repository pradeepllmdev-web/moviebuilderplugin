"""Blender script: 'The Observatory' - Leo turns four mirror wheels one after another until a moonbeam bounces through all of them onto a crystal, which opens the dome (about 45 s).

blender -b --disable-autoexec --python observatory_scene.py -- <ship_assets_dir> <out.blend>

Technique: A LIVE RAY TRACE DRIVEN BY THE ACTORS. The beam is traced every frame from the lamp: it is intersected with the mirror discs (their normals follow the mirrors' current yaw), reflected, and continued until it hits
the crystal, a wall or leaves a mirror's back; the beam cylinders are placed on the traced points, so while Leo turns a wheel you see the beam sweep round the room and snap onto the next mirror. The planner computes the yaw each mirror
needs from the points of the intended path (normal = normalised (d_out - d_in)), the mirrors start misaligned, and Leo visits them in order: he walks to the wheel, both hands grip the rim (IK) and follow it round as the mirror
turns through its angle. When the last mirror lands the traced beam reaches the crystal, the crystal glows and the dome shutters slide open. Audit: each mirror's final yaw error, the final trace hitting the crystal,
the beam never blocked by the telescope, wheel hands within reach, persistence, camera visibility. Clips: idle, climb, cele."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('observatory');PI=math.pi;smooth=kit.smooth;O=w2.OBS;rnd=random.Random(8)
S.load_env('observatory')
ZB=O['zb'];LAMP=Vector(O['S']);MIR=[Vector(m) for m in O['mirrors']];TGT=Vector(O['T']);RM=O['mr'];WALL=O['R']-.5;NM=len(MIR)
def unit(v):return v/v.length
# ---------------------------------------------------------------------------------------------------------- required yaws and the live trace
pts_chain=[LAMP]+MIR+[TGT];REQ=[]
for i in range(NM):
 din=unit(MIR[i]-pts_chain[i]);dout=unit(pts_chain[i+2]-MIR[i]);n=unit(dout-din);REQ.append(math.atan2(n.y,n.x))
START=[r+d for r,d in zip(REQ,(1.1,-1.3,.9,-1.0))]
def trace(yaws):
 """beam points (2D) from the lamp: reflect off the mirrors, end on the crystal or the wall"""
 p=Vector(LAMP);d=unit(MIR[0]-LAMP);pts=[Vector(p)];hit_t=False;used=set()
 for b in range(7):
  best=None
  for i,m in enumerate(MIR):
   n=Vector((math.cos(yaws[i]),math.sin(yaws[i])));den=d.dot(n)
   if abs(den)<1e-6 or i in used:continue
   tt=(m-p).dot(n)/den
   if tt>1e-3:
    h=p+d*tt
    if (h-m).length<=RM and (best is None or tt<best[0]):best=(tt,'m',i,h,den)
  # crystal: ray-circle
  oc=p-TGT;bq=oc.dot(d);cq=oc.dot(oc)-.35**2;disc=bq*bq-cq
  if disc>=0:
   tt=-bq-math.sqrt(disc)
   if tt>1e-3 and (best is None or tt<best[0]):best=(tt,'t',-1,p+d*tt,0)
  bq=p.dot(d);cq=p.dot(p)-WALL**2;tw=-bq+math.sqrt(max(0,bq*bq-cq))
  if best is None or tw<best[0]:
   pts.append(p+d*tw);break
  tt,kind,i,h,den=best;pts.append(h)
  if kind=='t':hit_t=True;break
  if den>0:break          # the back of a mirror: the beam stops there
  n=Vector((math.cos(yaws[i]),math.sin(yaws[i])));d=unit(d-n*2*d.dot(n));p=h;used.add(i)
 return pts,hit_t
# ---------------------------------------------------------------------------------------------------------- the timeline
INW=[unit(-m)*1.0 for m in MIR];STAND=[m+i*1.0 for m,i in zip(MIR,INW)];WALKV=1.9
t=3.0;cur=Vector((LAMP.x+2.2,LAMP.y+1.8));H0=math.atan2(MIR[0].y-cur.y,MIR[0].x-cur.x);SEQ=[];pos_hist=[(0.,cur,H0)]
for i in range(NM):
 d=(STAND[i]-cur).length;tw=d/WALKV;SEQ.append(dict(i=i,t_walk0=t,t_arr=t+tw,a=Vector(cur),b=STAND[i]));t=t+tw;tt=t+.5;SEQ[-1].update(t_grip=t+.1,t_turn0=t+.8,t_turn1=t+3.4,t_rel=t+3.7);t=t+4.0;cur=Vector(STAND[i])
T_FINAL=SEQ[-1]['t_turn1'];T_SHUT=T_FINAL+.8;T_END=T_SHUT+7.0;S.clock(T_END);seconds=S.seconds
def yaw_of(i,tt):
 q=SEQ[i];u=smooth((tt-q['t_turn0'])/(q['t_turn1']-q['t_turn0']));return START[i]+(REQ[i]-START[i])*u
def yaws(tt):return [yaw_of(i,tt) for i in range(NM)]
def leo_pos_head(tt):
 """Leo walks stand point to stand point, turns to face each mirror on arrival"""
 for q in SEQ:
  if q['t_walk0']<=tt<q['t_arr']:
   u=(tt-q['t_walk0'])/(q['t_arr']-q['t_walk0']);p=q['a'].lerp(q['b'],u);hw=math.atan2(q['b'].y-q['a'].y,q['b'].x-q['a'].x);hm=math.atan2(MIR[q['i']].y-q['b'].y,MIR[q['i']].x-q['b'].x)
   h=hw+((hm-hw+PI)%(2*PI)-PI)*smooth((u-.75)/.25);return p,h,True
  if q['t_arr']<=tt<(SEQ[q['i']+1]['t_walk0'] if q['i']+1<NM else 1e9):
   hm=math.atan2(MIR[q['i']].y-q['b'].y,MIR[q['i']].x-q['b'].x)
   if q['i']+1<NM:
    n=SEQ[q['i']+1];hw=math.atan2(n['b'].y-q['b'].y,n['b'].x-q['b'].x)
    if tt>=n['t_walk0']-.5:h=hm+((hw-hm+PI)%(2*PI)-PI)*smooth((tt-(n['t_walk0']-.5))/.5);return q['b'],h,False
   return q['b'],hm,False
 p0=SEQ[0]['a'];return p0,H0,False
def lp_fix(tt):
 if tt<SEQ[0]['t_walk0']:return SEQ[0]['a'],H0,False
 return leo_pos_head(tt)
# ---------------------------------------------------------------------------------------------------------- mirrors, wheels, beam
MOBJ=[];WOBJ=[]
for i,m in enumerate(MIR):
 mo=S.prim('cyl','MirrorDisc%d'%i,(m.x,m.y,ZB),(.72,.88,.95),scale=(RM,RM,.02),rot=(0,PI/2,START[i]),vertices=24,radius=1,depth=2,emit=.4);S.prim('cyl','MirrorFrame%d'%i,(m.x,m.y,ZB),(.75,.6,.25),scale=(RM+.07,RM+.07,.015),rot=(0,PI/2,START[i]),vertices=24,radius=1,depth=2)
 MOBJ.append(mo)
 wc=m+INW[i]*.62;w=S.prim('cyl','WheelRim%d'%i,(wc.x,wc.y,.95),(.6,.42,.2),scale=(.2,.2,.025),vertices=20,radius=1,depth=2);WOBJ.append((w,wc))
 for a in range(2):S.prim('cube','WheelSpoke',(wc.x,wc.y,.95),(.6,.42,.2),scale=(.2,.02,.02),rot=(0,0,a*PI/2),parent=w).location=(0,0,0)
 S.prim('cyl','WheelStem%d'%i,(wc.x,wc.y,.7),(.5,.4,.2),scale=(.03,.03,.25),vertices=6,radius=1,depth=2)
KEEP=[]
for i in range(NM):KEEP.append(S.prim('cyl','MirrorYawMarker%d'%i,(0,0,-3),(1,1,1),scale=(.001,.001,.001),vertices=4,radius=1,depth=2))
BEAM=[S.prim('cyl','Beam%d'%k,(0,0,ZB),(1,.95,.7),scale=(.001,.001,.001),vertices=6,radius=1,depth=2,emit=7.) for k in range(8)]
GLOW=[S.prim('cyl','BeamGlow%d'%k,(0,0,ZB),(1,.9,.5),scale=(.001,.001,.001),vertices=6,radius=1,depth=2,emit=1.5) for k in range(8)]
crystal=S.prim('sphere','Crystal',(TGT.x,TGT.y,1.2),(.5,.9,1.),scale=(.26,.26,.4),emit=0.,subdivisions=2)
cm=crystal.data.materials[0].copy();crystal.data.materials[0]=cm;cb=cm.node_tree.nodes.get('Principled BSDF')
def apply_beam(pts,f):
 for k in range(8):
  if k<len(pts)-1:
   a=Vector((pts[k].x,pts[k].y,ZB));b=Vector((pts[k+1].x,pts[k+1].y,ZB));d=b-a;L=d.length
   for obj,rad in ((BEAM[k],.035),(GLOW[k],.1)):
    obj.location=(a+b)/2;obj.scale=(rad,rad,max(1e-3,L/2));obj.rotation_euler=d.to_track_quat('Z','Y').to_euler()
  else:
   for obj in (BEAM[k],GLOW[k]):obj.scale=(.001,.001,.001)
  for obj in (BEAM[k],GLOW[k]):obj.keyframe_insert('location',frame=f);obj.keyframe_insert('scale',frame=f);obj.keyframe_insert('rotation_euler',frame=f)
LIT=[]
for f in S.keys():
 tt=(f-1)/S.fps;ys=yaws(tt);pts,hit=trace(ys);apply_beam(pts,f);LIT.append(hit)
 for i,mo in enumerate(MOBJ):mo.rotation_euler=(0,PI/2,ys[i]);mo.keyframe_insert('rotation_euler',frame=f)
 for i,(w,wc) in enumerate(WOBJ):w.rotation_euler=(0,0,.25*(ys[i]-START[i]));w.keyframe_insert('rotation_euler',frame=f)
 if cb and 'Emission Strength' in cb.inputs:cb.inputs['Emission Strength'].default_value=12.*smooth((tt-T_FINAL)/.6) if hit else 0.;cb.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# the frames themselves hold the keys of the mirror frames (frames are separate objects): turn them too
for o in bpy.data.objects:
 if o.name.startswith('MirrorFrame'):
  i=int(o.name[11:].split('.')[0])
  for f in S.keys():o.rotation_euler=(0,PI/2,yaw_of(i,(f-1)/S.fps));o.keyframe_insert('rotation_euler',frame=f)
# dome shutters
SH=[S.prim('cube','DomeShutter%d'%k,(0,sy*O['R']*.25,O['wall_h']+.55),(.3,.3,.4),scale=(O['R']*.55,O['R']*.25,.25)) for k,sy in enumerate((-1,1))]
for f in S.keys():
 tt=(f-1)/S.fps;u=smooth((tt-T_SHUT)/3.0)
 for k,sy in enumerate((-1,1)):SH[k].location=(0,sy*(O['R']*.25+u*O['R']*.62),O['wall_h']+.55);SH[k].keyframe_insert('location',frame=f)
mlight=bpy.data.objects.new('MoonShaft',bpy.data.lights.new('MoonShaft','SUN'));S.link(mlight);mlight.rotation_euler=(math.radians(25),0,math.radians(30))
for f in S.keys():
 tt=(f-1)/S.fps;mlight.data.energy=.2+3.5*smooth((tt-T_SHUT)/3.0);mlight.data.keyframe_insert('energy',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root'];IK,TG=S.ik(leo)
segs=[(0,SEQ[0]['t_walk0'],'idle',1.)]
for q in SEQ:
 segs.append((q['t_walk0'],q['t_arr'],'climb',.7))
 nxt=SEQ[q['i']+1]['t_walk0'] if q['i']+1<NM else T_FINAL+1.0
 segs.append((q['t_arr'],nxt,'idle',1.))
segs.append((T_FINAL+1.0,S.seconds,'cele',1.))
S.play(leo,[s for s in segs if s[1]-s[0]>.12])
for f in S.keys():
 tt=(f-1)/S.fps;p,h,walking=lp_fix(tt);root.location=(p.x,p.y,0);root.rotation_euler=(0,0,h+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 w=0.;i_act=None
 for q in SEQ:
  ww=smooth((tt-q['t_grip'])/.5)*(1-smooth((tt-q['t_rel'])/.4))
  if ww>w:w=ww;i_act=q['i']
 if i_act is None:i_act=0
 wc=WOBJ[i_act][1];ys=yaws(tt);psi=.25*(ys[i_act]-START[i_act]);hm=math.atan2(MIR[i_act].y-STAND[i_act].y,MIR[i_act].x-STAND[i_act].x)
 for l,sgn in (('RH',1),('LH',-1)):
  a=hm+PI+psi+sgn*.7;TG[l].location=(wc.x+.2*math.cos(a),wc.y+.2*math.sin(a),.97);TG[l].keyframe_insert('location',frame=f);IK[l].influence=w;IK[l].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 tt=(f-1)/S.fps;p,h,wk=lp_fix(tt);q=None
 for qq in SEQ:
  if qq['t_walk0']-.2<=tt<qq['t_rel']:q=qq
 tg=(Vector((MIR[q['i']].x,MIR[q['i']].y,ZB)) if q else (Vector((TGT.x,TGT.y,1.3)) if tt>T_FINAL else Vector((MIR[0].x,MIR[0].y,ZB))));gz.location=tg;gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('observatory',0,SEQ[0]['t_walk0']+.5,'wide')];last=cuts[0][2]
for q in SEQ:
 i=q['i'];cuts.append(('to mirror %d'%(i+1),last,q['t_arr'],'walk%d'%i));cuts.append(('wheel %d'%(i+1),q['t_arr'],q['t_turn0']+1.0,'wheel%d'%i));cuts.append(('beam %d'%(i+1),q['t_turn0']+1.0,q['t_rel']+.3,'beam%d'%i));last=q['t_rel']+.3
cuts.append(('crystal',last,T_SHUT+.5,'crystal'));cuts.append(('the dome opens',T_SHUT+.5,S.seconds,'dome'))
cuts=[c for c in cuts if c[2]-c[1]>.4]
def pos_(kind,t,u):
 p,h,wk=lp_fix(t);lp=Vector((p.x,p.y,1.1))
 if kind=='wide':return Vector((-3,-10.5,7.5)),Vector((0,1,1.6)),22
 if kind.startswith('walk'):i=int(kind[4:]);return lp+Vector((-3.2*math.cos(h),-3.2*math.sin(h),1.8)),lp,32
 if kind.startswith('wheel'):
  i=int(kind[5:]);m=MIR[i];ins=INW[i];side=Vector((-ins.y,ins.x));c=STAND[i];return Vector((c.x+side.x*1.6+ins.x*.4,c.y+side.y*1.6+ins.y*.4,1.5)),Vector((m.x+ins.x*.4,m.y+ins.y*.4,1.0)),42
 if kind.startswith('beam'):
  i=int(kind[4:]);m=MIR[i];prevp=pts_chain[i];dirb=unit(m-prevp);return Vector((m.x-dirb.x*3.2+(-dirb.y)*2.2,m.y-dirb.y*3.2+dirb.x*2.2,2.6)),Vector((m.x,m.y,ZB)),30
 if kind=='crystal':return Vector((TGT.x+2.4,TGT.y+2.2,1.7)),Vector((TGT.x,TGT.y,1.2)),40
 return Vector((0,-6,2.0)),Vector((0,0,12)),26
S.cameras(cuts,pos_,('Beam','Mirror','Wheel','Crystal','DomeShutter'),cand=[(0,0,1.),(0,0,2.5),(0,2.,0),(0,-2.,0),(2.,0,0),(-2.,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
fin=trace(yaws(T_FINAL+.1))
if not fin[1]:issues.append('AUDIT beam: the final trace does not reach the crystal')
for i in range(NM):
 e=abs((yaw_of(i,T_FINAL+.1)-REQ[i]+PI)%(2*PI)-PI)
 if e>.01:issues.append('AUDIT mirror: mirror %d ends %.3f rad off its required yaw'%(i+1,e))
# nothing blocks the planned path: the telescope pillar is at the centre
clr=1e9
for a,b in zip(pts_chain[:-1],pts_chain[1:]):
 ab=b-a;tt_=max(0,min(1,(-a).dot(ab)/ab.dot(ab)));clr=min(clr,(a+ab*tt_).length)
if clr<2.0:issues.append('AUDIT beam path: the planned beam passes %.2f m from the telescope'%clr)
lit_frames=[i for i,h in enumerate(LIT) if h];first_lit=(lit_frames[0]/S.fps) if lit_frames else None
rer=[];worst={}
for f in range(S.F(SEQ[0]['t_grip']+.6),S.F(T_FINAL),6):
 tt=(f-1)/S.fps;S.settle(f);rig=leo['rig']
 for l,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  if IK[l].influence<.99:continue
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),l,round(tt,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l].matrix_world.translation).length
  if g>worst.get(l,(0,0))[0]:worst[l]=(g,tt)
if rer:issues.append('AUDIT reach: wheel hands beyond arm reach %s (%d samples)'%(rer[:3],len(rer)))
for l,(g,tt) in worst.items():
 if g>.09:issues.append('AUDIT grip: %s misses the wheel rim by %.0f cm at %.1f s'%(l,g*100,tt))
print('OBSERVATORY required yaws %s, beam lit crystal first at %s s, telescope clearance %.2f m, GRIP %s, REACH over %d'%([round(r,2) for r in REQ],round(first_lit,1) if first_lit else None,clr,{k:round(v[0]*100,1) for k,v in worst.items()},len(rer)))
def snd(A):
 A.track('hum',(np.sin(2*PI*65*A.t)+.3*np.sin(2*PI*130*A.t))*.12+A.noise(A.N,60)*.1,.25)
 w=A.buf();k=A.burst(.08,4,50.)
 for q in SEQ:
  for tt in np.arange(q['t_turn0'],q['t_turn1'],.18):A.at(w,tt,k,.6)
 A.track('wheels',w,.5);bm=np.zeros(A.N)
 for q in SEQ:
  i0=int(q['t_turn0']*A.SR);i1=int(q['t_turn1']*A.SR);kk=np.arange(i1-i0)/A.SR;bm[i0:i1]+=np.sin(2*PI*(420+260*kk/ max(1e-3,kk[-1]))*kk)*.15
 A.track('beam tone',bm,.3);cs=A.buf();A.at(cs,T_FINAL,A.tone(1560,2.5,1.5,.8)+A.tone(2340,2.5,1.8,.4)*1,1.);A.at(cs,T_SHUT,A.noise(int(3*A.SR),30)*np.sin(np.linspace(0,PI,int(3*A.SR))),.6);A.track('crystal and shutter',cs,.7)
 A.track('music',A.chords(((110,138.6,164.8),(123.5,155.6,185),(98,123.5,146.8),(116.5,146.8,174.6)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.02,.03,.08))
