"""Blender script: 'The Volcano Forge' - Leo forges a sword in a cavern beside a lava river: heats the billet, hammers it in three rounds (14 blows), quenches it and raises the finished blade (about 45 s).

blender -b --disable-autoexec --python forge_scene.py -- <ship_assets_dir> <out.blend>

Technique: FORGING WITH A TIMED HEAT MODEL. The whole film is built from an event list (heat, walk, strike xN, quench, raise). The blade's glow is a heat variable that rises in the furnace and decays between stations
(time constant 10 s); the planner schedules blows only while it is above 0.45. The left hand carries the tongs and blade (IK), the right hand swings the hammer: the head rides a 0.63 m arc about the wrist, from the raised
pose to the strike point on the blade; the impact instant is the moment the head reaches that point, where sparks (ballistic, sized by heat) leave and the blade lengthens a little. The blade dips into the trough
(steam puffs) and is finally raised. Audit: heat at every blow, hammer head on the strike point at impact, both wrists within reach, persistence, camera visibility. Clips: idle, climb."""
import bpy,math,random,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector,Euler,Matrix
S=sb.Scene('forge');PI=math.pi;smooth=kit.smooth;FG=w2.FORGE;ST=FG['stations'];SY=FG['stand_y'];TZ=FG['top_z'];rnd=random.Random(8);G_=9.81
S.load_env('forge')
# ---------------------------------------------------------------------------------------------------------- the event list becomes a timeline
EV=[('look',3.0),('heat',2.6),('walk','A',1.4),('strike',5),('walk','F',1.4),('heat',2.0),('walk','A',1.4),('strike',5),('walk','F',1.4),('heat',2.0),('walk','A',1.4),('strike',4),('walk','T',1.4),('quench',3.0),('raise',3.6),('end',3.0)]
t=0.;cur='F';segs=[];strikes=[];heats=[];quench=None;raise_=None;prep=.6;post=.5;cycles=[]
for e in EV:
 k=e[0]
 if k=='look':segs.append(dict(m='stand',t0=t,t1=t+e[1],a=cur,b=cur));t+=e[1]
 elif k=='heat':segs.append(dict(m='stand',t0=t,t1=t+e[1],a=cur,b=cur));heats.append((t,t+e[1]));t+=e[1]
 elif k=='walk':segs.append(dict(m='walk',t0=t,t1=t+e[2],a=cur,b=e[1]));t+=e[2];cur=e[1]
 elif k=='strike':
  d=prep+e[1]*1.0+post;segs.append(dict(m='stand',t0=t,t1=t+d,a=cur,b=cur));cycles.append((t,t+d,e[1],t+prep))
  for i in range(e[1]):strikes.append(t+prep+i*1.0+.68)
  t+=d
 elif k=='quench':segs.append(dict(m='stand',t0=t,t1=t+e[1],a=cur,b=cur));quench=(t,t+e[1]);t+=e[1]
 elif k=='raise':segs.append(dict(m='stand',t0=t,t1=t+e[1],a=cur,b=cur));raise_=(t,t+e[1]);t+=e[1]
 elif k=='end':segs.append(dict(m='stand',t0=t,t1=t+e[1],a=cur,b=cur));t+=e[1]
S.clock(t);seconds=S.seconds;T_LH=heats[0][0]-.2
print('TIMELINE %.1f s, %d blows, heats %s, quench %s'%(seconds,len(strikes),[(round(a,1),round(b,1)) for a,b in heats],[round(x,1) for x in quench]))
def station_at(tt):
 for s in segs:
  if s['t0']<=tt<s['t1']:return s
 return segs[-1]
def leo_xy_h(tt):
 s=station_at(tt)
 if s['m']=='stand':return Vector((ST[s['a']],SY,0)),PI/2
 u=(tt-s['t0'])/(s['t1']-s['t0']);x=ST[s['a']]+(ST[s['b']]-ST[s['a']])*smooth(u);hw=0. if ST[s['b']]>ST[s['a']] else PI
 turn=smooth(u/.25)*(1-smooth((u-.75)/.25));return Vector((x,SY,0)),PI/2+(hw-PI/2)*turn
def fl(h):return Vector((math.cos(h),math.sin(h),0)),Vector((-math.sin(h),math.cos(h),0))
# heat: rises in the furnace, decays between stations
def heat(tt):
 h=0.;
 for (a,b) in heats:
  if tt>=a:
   if tt<b:h=max(h,.0+smooth((tt-a)/(b-a)));
   else:h=max(h,math.exp(-(tt-b)/10.))
 if quench and tt>=quench[0]+.6:h*=max(0.,1-(tt-quench[0]-.6)/.6)
 return h
# blade length grows with each blow
def blade_len(tt):n=sum(1 for x in strikes if x<=tt);return .35+.6*n/len(strikes)
# ---------------------------------------------------------------------------------------------------------- hammer geometry in Leo's frame
HL=.63
def pose_rest_strike(pos,h):
 f,l=fl(h);P_h=pos+f*.07+l*(-.2)+Vector((0,0,1.27));head=pos+f*.55+l*.1+Vector((0,0,TZ+.01));d_s=(head-P_h).normalized();d_u=(f*.35+Vector((0,0,.94))+l*.1).normalized();return P_h,d_s,d_u
def carry_pose(pos,h):
 f,l=fl(h);return pos+f*.1+l*(-.3)+Vector((0,0,.95)),(f*.25+Vector((0,0,-.97))).normalized()
def psi(tt):
 """0 = at the blow, 1 = raised; None when not in a striking round"""
 for (a,b,n,c0) in cycles:
  if a<=tt<b:
   if tt<c0:return .55*smooth((tt-a)/(c0-a))
   u=((tt-c0)%1.0);k=int((tt-c0)//1.0)
   if k>=n:return .55*(1-smooth((tt-(c0+n))/post))
   if u<.55:p0=.55 if k>0 or True else .55;return p0+(1-p0)*smooth(u/.55)
   if u<.68:v=(u-.55)/.13;return 1-v*v
   w_=(u-.68)/.32;return .55*(1-(1-w_)**2)
 return None
def hammer(tt):
 pos,h=leo_xy_h(tt);P_h,d_s,d_u=pose_rest_strike(pos,h);hc,dc=carry_pose(pos,h);p=psi(tt)
 if p is None:return hc,dc
 d=(d_s*(1-p)+d_u*p).normalized();hand=P_h
 a=[c for c in cycles if c[0]<=tt<c[1]][0];ca=smooth((tt-a[0])/prep) if tt<a[0]+prep else 1.
 cb=1.-smooth((tt-(a[1]-post))/post) if tt>a[1]-post else 1.
 c=min(ca,cb);return hc.lerp(hand,c),(dc*(1-c)+d*c).normalized()
# blade rear point (the left hand holds the tongs there), with the quench dip and the final raise
def blade_state(tt):
 pos,h=leo_xy_h(tt);f,l=fl(h);bp=pos+f*.37+l*.1+Vector((0,0,TZ+.02));pitch=0.
 if quench:
  q=smooth((tt-(quench[0]+.4))/.6)*(1-smooth((tt-(quench[1]-1.0))/.6));bp.z-=.05*q;pitch=-.75*q
 if raise_:
  r=smooth((tt-(raise_[0]+.3))/1.6);bp.z+=.28*r;pitch=pitch+(PI/2)*r
 return bp,h,pitch
# ---------------------------------------------------------------------------------------------------------- props that move
blade=bpy.data.objects.new('BladeRoot',None);S.link(blade);bl=S.prim('cube','Blade',(0,.5,0),(.72,.74,.78),scale=(.045,.5,.012),parent=blade);S.prim('cube','Guard',(0,-.02,0),(.5,.4,.2),scale=(.1,.015,.02),parent=blade)
m=bl.data.materials[0].copy();bl.data.materials[0]=m;bnode=m.node_tree.nodes.get('Principled BSDF')
for k in ('Emission Color','Emission'):
 if bnode and k in bnode.inputs:bnode.inputs[k].default_value=(1,.38,.06,1);break
tongs=bpy.data.objects.new('TongsRoot',None);S.link(tongs);S.prim('cyl','Tongs',(0,-.2,0),(.3,.3,.32),scale=(.016,.2,.016),rot=(PI/2,0,0),vertices=6,radius=1,depth=2,parent=tongs).rotation_euler=(PI/2,0,0)
ham=bpy.data.objects.new('Hammer',None);S.link(ham);S.prim('cyl','HammerHandle',(0,0,HL/2),(.5,.33,.15),scale=(.022,.022,HL/2),vertices=6,radius=1,depth=2,parent=ham);S.prim('cube','HammerHead',(0,0,HL),(.45,.45,.5),scale=(.07,.035,.04),parent=ham)
prev={'b':None,'h':None}
for f in S.keys():
 tt=(f-1)/S.fps;bp,h,pitch=blade_state(tt);L=blade_len(tt)
 e=Euler((pitch,0,h-PI/2),'XYZ') if False else (Matrix.Rotation(h-PI/2,3,'Z')@Matrix.Rotation(pitch,3,'X')).to_euler()
 blade.location=bp;blade.rotation_euler=e;blade.scale=(1,L,1);blade.keyframe_insert('location',frame=f);blade.keyframe_insert('rotation_euler',frame=f);blade.keyframe_insert('scale',frame=f)
 tongs.location=bp;tongs.rotation_euler=e;tongs.keyframe_insert('location',frame=f);tongs.keyframe_insert('rotation_euler',frame=f)
 if bnode and 'Emission Strength' in bnode.inputs:bnode.inputs['Emission Strength'].default_value=9.*heat(tt)**1.3;bnode.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
 hp,d=hammer(tt);ham.location=hp;ham.rotation_euler=d.to_track_quat('Z','Y').to_euler();ham.keyframe_insert('location',frame=f);ham.keyframe_insert('rotation_euler',frame=f)
# sparks at every blow, steam at the quench
SP=[]
for n,te in enumerate(strikes):
 pos,h=leo_xy_h(te);P_h,d_s,d_u=pose_rest_strike(pos,h);head=P_h+d_s*HL;hh=heat(te)
 for j in range(9):
  s=S.prim('sphere','Spark%d_%d'%(n,j),(0,0,0),(1,.7,.2),scale=(.001,.001,.001),emit=8.,subdivisions=1);ang=rnd.uniform(0,6.28);sp=rnd.uniform(1.2,3.2);SP.append((s,te,head,Vector((math.cos(ang)*sp,math.sin(ang)*sp,rnd.uniform(1.5,3.8))),.03+.03*hh))
for s,te,head,v,size in SP:
 for f in S.keys():
  tt=(f-1)/S.fps;u=tt-te
  if 0<=u<.8:s.location=head+v*u+Vector((0,0,-.5*G_*u*u));sc=size*(1-smooth(u/.8))+.001
  else:s.location=head;sc=.001
  s.scale=(sc,sc,sc);s.keyframe_insert('location',frame=f);s.keyframe_insert('scale',frame=f)
STM=[]
for j in range(8):STM.append(S.prim('sphere','Steam%d'%j,(0,0,0),(.9,.92,.95),scale=(.001,.001,.001),subdivisions=1))
tq=quench[0]+.9;tx=ST['T']
for j,s in enumerate(STM):
 off=j*.18;ox=rnd.uniform(-.1,.1);oy=rnd.uniform(.05,.25)
 for f in S.keys():
  tt=(f-1)/S.fps;u=tt-tq-off
  if 0<=u<2.2:s.location=(tx-.1+ox,.3+oy,.9+.5*u);sc=.05+.18*smooth(u/1.2)
  else:s.location=(tx,.3,.9);sc=.001
  if u>1.4:sc=max(.001,sc*(1-smooth((u-1.4)/.8)))
  s.scale=(sc,sc,sc*1.2);s.keyframe_insert('location',frame=f);s.keyframe_insert('scale',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root'];IK,TG=S.ik(leo,influence=0.)
clips=[]
for s in segs:clips.append((s['t0'],s['t1'],'climb' if s['m']=='walk' else 'idle',.7 if s['m']=='walk' else 1.))
S.play(leo,clips)
for f in S.keys():
 tt=(f-1)/S.fps;pos,h=leo_xy_h(tt);root.location=pos;root.rotation_euler=(0,0,h+PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
 wl=smooth((tt-T_LH)/.6);wr=smooth((tt-.5)/.6);bp,_,_=blade_state(tt);hp,d=hammer(tt)
 TG['LH'].location=bp;TG['LH'].keyframe_insert('location',frame=f);IK['LH'].influence=wl;IK['LH'].keyframe_insert('influence',frame=f)
 TG['RH'].location=hp;TG['RH'].keyframe_insert('location',frame=f);IK['RH'].influence=wr;IK['RH'].keyframe_insert('influence',frame=f)
gz=S.gaze(leo,(0,1,0))
for f in S.keys():
 tt=(f-1)/S.fps;bp,h,pitch=blade_state(tt);gz.location=bp+Vector((0,.0,.05)) if tt>T_LH else Vector((ST['F'],.5,1.0));gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('forge',0,3.0,'wide')];alt=0
for s in segs[1:]:
 a,b=s['t0'],s['t1']
 if s['m']=='walk':cuts.append(('walk',a,b,'follow'))
 elif quench and abs(a-quench[0])<.01:cuts.append(('quench',a,b,'trough'))
 elif raise_ and abs(a-raise_[0])<.01:cuts.append(('the blade',a,b,'raise'))
 elif s is segs[-1]:cuts.append(('end',a,b,'wide2'))
 elif any(abs(a-c[0])<.01 for c in cycles):
  n=max(1,int((b-a)//2.6));seg=(b-a)/n
  for j in range(n):cuts.append(('blows',a+j*seg,a+(j+1)*seg,('side','front','top')[alt%3]));alt+=1
 else:cuts.append(('heat',a,b,'furn'))
def pos_(kind,t,u):
 pos,h=leo_xy_h(t);f,l=fl(h);bp,_,_=blade_state(t);ax=pos.x
 if kind=='wide':return Vector((0,-6.2,3.4)),Vector((0,0,1.3)),26
 if kind=='wide2':return Vector((1.5,-5.0,2.4)),Vector((0.5,0,1.5)),28
 if kind=='follow':return pos+Vector((0,-3.0,1.5))+Vector((-1.2*(1 if f.x>=0 else -1),0,0)),pos+Vector((0,0,1.1)),32
 if kind=='furn':return Vector((ST['F']+1.4,-1.7,1.4)),Vector((ST['F'],0,1.1)),40
 if kind=='side':return Vector((ax+2.3,-.35,1.3)),Vector((ax-.05,-.15,1.1)),48
 if kind=='front':return Vector((ax+.5,1.9,1.55)),Vector((ax-.1,-.35,1.2)),42
 if kind=='top':return Vector((ax-.2,-.45,3.0)),Vector((ax-.1,-.1,1.0)),36
 if kind=='trough':return Vector((ST['T']+1.3,-1.6,1.4)),Vector((ST['T']-.1,.1,.95)),42
 if kind=='raise':return Vector((ax+.4,-2.4,.7)),bp+Vector((0,0,.6)),32
 return Vector((0,-5,2.5)),pos+Vector((0,0,1.2)),28
S.cameras(cuts,pos_,('Blade','Tongs','Hammer','Spark','Steam'),cand=[(0,0,.6),(0,0,1.4),(0,-1.2,0),(1.2,0,0),(-1.2,0,0)])
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
cold=[round(x,1) for x in strikes if heat(x)<.45]
if cold:issues.append('AUDIT heat: blows struck below the working heat at %s'%cold)
worst_head=0.
for te in strikes:
 pos,h=leo_xy_h(te-.001);hp,d=hammer(te);head=hp+d*HL;bp,hh,pc=blade_state(te);f,l=fl(hh);tgt=pos+f*.55+l*.1+Vector((0,0,TZ+.01));worst_head=max(worst_head,(head-tgt).length)
if worst_head>.03:issues.append('AUDIT hammer: the head misses the strike point by %.1f cm at a blow'%(worst_head*100))
rer=[];worst={}
for f in range(S.F(T_LH+.8),S.F(raise_[1]),8):
 tt=(f-1)/S.fps;S.settle(f);rig=leo['rig']
 for l_,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[l_].matrix_world.translation-sh).length
  if d>.47:rer.append((round(d-.44,3),l_,round(tt,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[l_].matrix_world.translation).length
  if g>worst.get(l_,(0,0))[0]:worst[l_]=(g,tt)
if rer:issues.append('AUDIT reach: wrist target beyond arm reach %s (%d samples)'%(rer[:3],len(rer)))
for l_,(g,tt) in worst.items():
 if g>.08:issues.append('AUDIT grip: %s misses its target by %.0f cm at %.1f s'%(l_,g*100,tt))
print('FORGE blows %d, heat at blows %s, hammer head error %.1f cm, GRIP %s, REACH over %d, final blade %.2f m'%(len(strikes),[round(heat(x),2) for x in strikes][:14],worst_head*100,{k:round(v[0]*100,1) for k,v in worst.items()},len(rer),blade_len(seconds)))
def snd(A):
 A.track('cavern',A.noise(A.N,60)*.5+A.noise(A.N,5)*.04,.45)
 cl=A.buf();k=np.arange(int(1.0*A.SR))/A.SR
 for te in strikes:A.at(cl,te,(np.sin(2*PI*1800*k)+.6*np.sin(2*PI*2650*k)+.3*np.sin(2*PI*3900*k))*np.exp(-k*9)+A.burst(.15,3,60.)[:1]*0 if False else (np.sin(2*PI*1800*k)+.6*np.sin(2*PI*2650*k)+.3*np.sin(2*PI*3900*k))*np.exp(-k*9),.8)
 A.track('hammer',cl,.8)
 fn=A.buf()
 for (a,b) in heats:A.at(fn,a,A.noise(int((b-a)*A.SR),20)*np.sin(np.linspace(0,PI,int((b-a)*A.SR))),.7)
 A.track('furnace',fn,.5);hs=A.buf();A.at(hs,quench[0]+.9,A.noise(int(2.2*A.SR),4)*np.exp(-np.arange(int(2.2*A.SR))/A.SR*1.1),.9);A.track('quench',hs,.6)
 A.track('music',A.chords(((98,123.5,146.8),(92.5,116.5,138.6),(87.3,110,130.8),(82.4,103.8,123.5)),.22),.35)
S.audio(snd)
S.finish(issues,[root],world=(.06,.04,.04))
