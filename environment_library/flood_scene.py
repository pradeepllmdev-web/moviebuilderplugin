"""Blender script: 'The Flood' - a wall of water sweeps down the valley; Leo outruns it, rescues a stranded child and carries it to the hill while the village flees (about 30 s).

blender -b --disable-autoexec --python flood_scene.py -- <ship_assets_dir> <out.blend>

New in this scene: a TERRAIN-AWARE WATER BORE and a PLANNED CROWD. The flood is one water body whose front advances at constant speed and whose level (2.4 m) intersects the real terrain (shared bank), so the
wet line follows the hill exactly. Forty villagers flee to slots on the hill by steering (house repulsion, separation); a planner raises the speed of any villager whose route would put them deeper than 0.5 m in water
(automation instead of manual fixes). Floating debris starts on the ground, lifts when the water reaches it and drifts. Leo kneels, lifts the child with IK hands (the child follows the hands), runs it uphill ahead of
the front and sets it down. Audit: water depth at every agent, at Leo and at the child over time; hands within reach; houses not entered; persistence; camera visibility. Clips: idle, run, kneel."""
import bpy,math,random,sys,os,wave
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_kit as kit,scene_params,locations
from mathutils import Vector,Euler
args=sys.argv[sys.argv.index('--')+1:];ASSETS,out=args[0],args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=24;scene.render.fps=fps;PI=math.pi;rnd=random.Random(12)
F=lambda t:1+int(round(t*fps));smooth=kit.smooth
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
_m={}
def mat(name,color,emit=0.):
 key=name+str(color)+str(emit)
 if key in _m:return _m[key]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:
  b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.3 if name.startswith('Flood') else .9
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
CTX=dict(link=link,mat=mat,prim=prim);FL=locations.FLOOD;LEV=FL['lev'];G=locations.flood_ground
locations.load('flood_valley',CTX,'intact')
# ---------------------------------------------------------------------------------------------------------- the story clock and the water
FRONT_V=6.5;FRONT_X0=-20.;T_WAVE=2.0
def front(t):return FRONT_X0+FRONT_V*max(0.,t-T_WAVE)
def depth(x,y,t):return max(0.,LEV-G(x,y)) if x<front(t) else 0.
PC=Vector((22.,4.,0.));A0=Vector((4.,-2.,0.));D=Vector((66.,0.,0.))
LEO_V=6.5;TL0=2.6;d1=(PC-A0).length;AIM1=(PC-A0).normalized();GPT=PC-AIM1*.32;TL1=TL0+(GPT-A0).length/LEO_V;TL2=TL1+2.2
AIM2=(D-GPT).normalized();TL3=TL2+(D-GPT).length/LEO_V;TL4=TL3+2.0;T_END=TL4+8.0;seconds=T_END;frames=int(seconds*fps);scene.frame_start=1;scene.frame_end=frames
wb=bpy.data.objects.new('FloodWater',None)
water=prim('cube','FloodWater',(0,0,0),(.12,.3,.4),scale=(1,1,1));crest=prim('cyl','FloodCrest',(0,0,LEV),(.9,.94,.96),scale=(.9,FL['hw'],.9),rot=(PI/2,0,0),vertices=12,radius=1,depth=2)
foam=[prim('sphere','FloodFoam',(0,0,LEV),(.9,.94,.96),scale=(.5,.5,.4),subdivisions=1) for _ in range(14)];frng=random.Random(4);FOAMY=[frng.uniform(-24,24) for _ in foam];FOAMP=[frng.uniform(0,6.28) for _ in foam]
for f in range(1,frames+1,2):
 t=(f-1)/fps;fx=front(t);water.scale=((fx-FL['x0'])/2,FL['hw']+4,(LEV+1.2)/2);water.location=((fx+FL['x0'])/2,0,(LEV-1.2)/2);water.keyframe_insert('location',frame=f);water.keyframe_insert('scale',frame=f)
 wet=G(fx,0)<LEV-.1;crest.location=(fx,0,LEV+.15*math.sin(2*PI*1.7*t));crest.scale=(.9,FL['hw'],.9) if wet else (.001,.001,.001);crest.keyframe_insert('location',frame=f);crest.keyframe_insert('scale',frame=f)
 for i,fo in enumerate(foam):fo.location=(fx-1.2+.9*math.sin(2*PI*.9*t+FOAMP[i]),FOAMY[i],LEV+.35+.3*abs(math.sin(2*PI*1.1*t+FOAMP[i])));fo.scale=(.5,.5,.4) if G(fx,FOAMY[i])<LEV-.1 else (.001,.001,.001);fo.keyframe_insert('location',frame=f);fo.keyframe_insert('scale',frame=f)
# ---------------------------------------------------------------------------------------------------------- floating debris
DEB=[]
for k in range(12):
 x=rnd.uniform(-5,34);y=rnd.choice((-1,1))*rnd.uniform(1.5,7);kind=k%3
 if kind==0:o=prim('cyl','Barrel',(x,y,.4),(.45,.3,.15),scale=(.35,.35,.45),vertices=10,radius=1,depth=2)
 elif kind==1:o=prim('cube','Crate',(x,y,.35),(.5,.38,.2),scale=(.4,.4,.35))
 else:o=prim('cube','Plank',(x,y,.1),(.5,.36,.2),scale=(1.1,.14,.05))
 DEB.append(dict(o=o,x0=x,y0=y,tc=T_WAVE+(x-FRONT_X0)/FRONT_V,drift=rnd.uniform(7,13),spin=rnd.uniform(-1.5,1.5),ph=rnd.uniform(0,6.28)))
def debris_state(d,t):
 tc=d['tc']
 if t<tc:return Vector((d['x0'],d['y0'],G(d['x0'],d['y0'])+.4)),0.
 u=t-tc;x=d['x0']+d['drift']*(1-math.exp(-u/1.6));x=min(x,52.);y=d['y0'];z=max(G(x,y)+.3,LEV-.1+.08*math.sin(2*PI*.8*t+d['ph']))
 return Vector((x,y,z)),d['spin']*u*(1-math.exp(-u/2))
for d in DEB:
 for f in range(1,frames+1,2):
  p,r=debris_state(d,(f-1)/fps);d['o'].location=p;d['o'].rotation_euler=(0,0,r);d['o'].keyframe_insert('location',frame=f);d['o'].keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- the crowd (planned)
N=40;slots=[Vector((60+(i%5)*3.2+rnd.uniform(-.5,.5),-9+(i//5)*2.4+rnd.uniform(-.4,.4),0)) for i in range(N)];rnd.shuffle(slots)
starts=[Vector((rnd.uniform(6,40),rnd.uniform(-5.5,5.5),0)) for _ in range(N)]
for i,s in enumerate(starts):
 if (s-PC).length<2.0 or (s-A0).length<2.5:s.x+=4
base_speed=[rnd.uniform(2.8,3.9) for _ in range(N)];
for i in range(3):base_speed[i]=rnd.uniform(1.8,2.3)      # elders
react=[T_WAVE+.6+rnd.uniform(0,1.0) for _ in range(N)]
HOUSES=[(h[0],h[1],h[2]*.5*1.42) for h in FL['houses']]
def simulate(speeds):
 pos=np.array([[s.x,s.y] for s in starts]);hist=[pos.copy()];stop=np.zeros(N,bool);dt=1/fps
 tgt=np.array([[s.x,s.y] for s in slots])
 for fi in range(1,frames+1):
  t=(fi-1)/fps;pos=pos.copy()
  for i in range(N):
   if t<react[i] or stop[i]:continue
   d=tgt[i]-pos[i];dist=np.linalg.norm(d)
   if dist<.35:stop[i]=True;continue
   v=d/dist
   for (hx,hy,hr) in HOUSES:
    r=pos[i]-np.array([hx,hy]);rn=np.linalg.norm(r)
    if rn<hr+1.1:v=v+(r/(rn+1e-6))*(hr+1.1-rn)*1.6
   dd=pos-pos[i];dn=np.linalg.norm(dd,axis=1);dn[i]=9
   near=dn<.8
   if near.any():v=v-(dd[near]/dn[near][:,None]*(.8-dn[near])[:,None]).sum(0)*1.2
   v=v/(np.linalg.norm(v)+1e-9);pos[i]=pos[i]+v*speeds[i]*dt
  hist.append(pos.copy())
 return np.array(hist)
speeds=list(base_speed)
for it in range(14):
 H=simulate(speeds);bad=[]
 for i in range(N):
  dmax=max(depth(H[fi,i,0],H[fi,i,1],fi/fps) for fi in range(0,frames,3))
  if dmax>.5:bad.append(i)
 if not bad:break
 for i in bad:speeds[i]=min(5.2,speeds[i]*1.12)
print('CROWD planner: %d iterations, %d still too deep'%(it+1,len(bad)))
CROWD_BAD=bad
def agent_state(i,fi):
 p=H[min(fi,len(H)-1),i];q=H[max(0,min(fi,len(H)-1)-2),i];v=p-q;moving=np.linalg.norm(v)>.02
 yaw=math.atan2(v[1],v[0]) if moving else PI
 return Vector((p[0],p[1],G(p[0],p[1]))),yaw,moving
cols=[(.7,.25,.2),(.2,.4,.7),(.75,.6,.2),(.3,.55,.3),(.6,.3,.55),(.8,.8,.75)]
VILL=[]
for i in range(N):
 r=bpy.data.objects.new('Villager%d'%i,None);link(r);c=cols[i%6];sc=.9 if i<3 else .8+rnd.random()*.25
 prim('cone','VillBody',(0,0,.55*sc),c,scale=(.26*sc,.26*sc,.55*sc),vertices=10,radius1=1,depth=2,parent=r);prim('sphere','VillHead',(0,0,1.22*sc),(.85,.65,.5),scale=(.13*sc,.13*sc,.13*sc),subdivisions=1,parent=r);VILL.append(r)
prevy=[None]*N
for f in range(1,frames+1,2):
 fi=f-1
 for i,r in enumerate(VILL):
  p,yaw,mv=agent_state(i,fi);ph=(f/fps)*(5.5 if speeds[i]>3 else 4.2)+i;r.location=(p.x,p.y,p.z+(.05*abs(math.sin(ph)) if mv else 0.));e=Euler((0,0,yaw))
  if prevy[i] is not None:e.make_compatible(prevy[i])
  prevy[i]=e.copy();r.rotation_euler=e;r.keyframe_insert('location',frame=f);r.keyframe_insert('rotation_euler',frame=f)
# ---------------------------------------------------------------------------------------------------------- Leo and the child
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
def adiff(a,b):return (a-b+PI)%(2*PI)-PI
def leo_seg(t):
 if t<TL0:return A0,AIM1,'idle',0
 if t<TL1:u=(t-TL0)/(TL1-TL0);return A0.lerp(GPT,u),AIM1,'run',1
 if t<TL2:return GPT,AIM1 if t<TL1+.5 else AIM2,'kneel',2
 if t<TL3:u=(t-TL2)/(TL3-TL2);return GPT.lerp(D,u),AIM2,'run',3
 if t<TL4:return D,AIM2,'kneel',4
 return D,AIM2,'idle',5
def leo_head(t):
 p,a,m,k=leo_seg(t);h=math.atan2(a.y,a.x)
 # smooth the heading across segment starts
 starts_=[0,TL0,TL1,TL2,TL3,TL4]
 for s0 in starts_[1:]:
  if s0<=t<s0+.4:
   pp,aa,mm,kk=leo_seg(s0-.01);h0=math.atan2(aa.y,aa.x);h=h0+adiff(h,h0)*smooth((t-s0)/.4)
 return h
def leo_state(t):
 p,a,m,k=leo_seg(t);return Vector((p.x,p.y,G(p.x,p.y))),leo_head(t),m
def fl_(h):return Vector((math.cos(h),math.sin(h),0)),Vector((-math.sin(h),math.cos(h),0))
CH=bpy.data.objects.new('Child',None);link(CH)
prim('cone','ChildBody',(0,0,.3),(.95,.8,.2),scale=(.17,.17,.3),vertices=10,radius1=1,depth=2,parent=CH);prim('sphere','ChildHead',(0,0,.72),(.88,.68,.52),scale=(.11,.11,.11),subdivisions=1,parent=CH)
CHC=.55
prim('cube','Cart',(PC.x,PC.y,G(PC.x,PC.y)+.225),(.45,.3,.15),scale=(.55,.55,.225));prim('cube','Rock',(D.x+AIM2.x*.5,D.y+AIM2.y*.5,G(D.x,D.y)+.225),(.4,.38,.35),scale=(.55,.55,.225))
def child_center(t):
 p,h,m=leo_state(t);f,l=fl_(h);chest=Vector((p.x,p.y,p.z+1.05))+f*.30;pc0=Vector((PC.x,PC.y,G(PC.x,PC.y)+.45+CHC))
 if t<TL1+1.0:return pc0
 if t<TL2:u=smooth((t-(TL1+1.0))/(TL2-TL1-1.1));return pc0.lerp(Vector((GPT.x,GPT.y,G(GPT.x,GPT.y)+1.05))+fl_(math.atan2(AIM2.y,AIM2.x))[0]*.30,u)
 if t<TL3:return chest
 end=Vector((D.x,D.y,G(D.x,D.y)+.45+CHC))+f*.5
 if t<TL3+.2:return chest
 if t<TL4:u=smooth((t-(TL3+.2))/1.5);return chest.lerp(end,u)
 return end
def clip_for(m):return {'idle':('idle',None,None,1.),'run':('run',None,None,.5),'kneel':('idle',None,None,1.)}[m]
CLIPS={}
for c in ('idle','run'):
 with bpy.data.libraries.load(os.path.join(ASSETS,'leo_%s.blend'%c),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%c]
 CLIPS[c]=dst.actions[0]
def add_strip(tr,clip,a,b,scale=1.,hold=False,f0=None,f1=None):
 act=CLIPS[clip];st=tr.strips.new(clip,F(a),act);st.action_slot=act.slots[0];n=(f1 or act.frame_range[1])-(f0 or act.frame_range[0])+1
 if f0:st.action_frame_start=f0
 if f1:st.action_frame_end=f1
 st.scale=scale;need=(F(b)-st.frame_start)/(n*scale)
 if need>=1:st.repeat=need
 else:st.action_frame_end=st.action_frame_start+max(2,need*n)-1
 st.extrapolation='HOLD' if hold else 'NOTHING';st.blend_in=6;st.blend_out=6;return st
segs=[(0,TL0,'idle'),(TL0,TL1,'run'),(TL1,TL2,'kneel'),(TL2,TL3,'run'),(TL3,TL4,'kneel'),(TL4,seconds,'idle')]
tracks=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()]
for k,(a,b,m) in enumerate(segs):
 clip,f0,f1,sc=clip_for(m);add_strip(tracks[k%2],clip,a if not k else a-.25,b,sc,hold=(k==0),f0=f0,f1=f1)
IK={};TG={}
for limb,bone in (('LH','LeftForeArm'),('RH','RightForeArm')):
 tg=bpy.data.objects.new('Wrist_'+limb,None);tg.empty_display_size=.04;link(tg);TG[limb]=tg
 pole=bpy.data.objects.new('Pole_'+limb,None);link(pole);pole.parent=LEO['root'];sgn=1 if limb=='LH' else -1;pole.location=(.5*sgn,.5,.9)
 k_=rig.pose.bones['mixamorig:'+bone].constraints.new('IK');k_.target=tg;k_.pole_target=pole;k_.pole_angle=math.radians(-90 if limb=='LH' else 90);k_.chain_count=2;k_.use_stretch=False;k_.influence=0;IK[limb]=k_
def hand_w(t):return smooth((t-(TL1+.3))/.5)*(1-smooth((t-(TL3+1.3))/.5))
prev=None;reach_err=[];worst={}
for f in range(1,frames+1,2):
 t=(f-1)/fps;p,h,m=leo_state(t);e=Euler((0,0,h+PI/2))
 if prev is not None:e.make_compatible(prev)
 prev=e.copy();LEO['root'].location=p;LEO['root'].rotation_euler=e;LEO['root'].keyframe_insert('location',frame=f);LEO['root'].keyframe_insert('rotation_euler',frame=f)
 cc=child_center(t);CH.location=cc-Vector((0,0,CHC));CH.rotation_euler=(0,0,h+PI);CH.keyframe_insert('location',frame=f);CH.keyframe_insert('rotation_euler',frame=f)
 ff,ll=fl_(h);w=hand_w(t)
 for limb,sg in (('LH',1),('RH',-1)):
  TG[limb].location=cc+ll*.16*sg+ff*.0;TG[limb].keyframe_insert('location',frame=f);IK[limb].influence=w;IK[limb].keyframe_insert('influence',frame=f)
# gaze: ahead while running, at the child while kneeling, back at the flood at the end
scene.frame_set(1);bpy.context.view_layer.update()
hm=(rig.matrix_world@rig.pose.bones['mixamorig:Head'].matrix).to_3x3();fwd0=Vector((math.cos(leo_head(0)),math.sin(leo_head(0)),0))
AXES={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
FACE_AXIS=max(AXES,key=lambda k:AXES[k].normalized().dot(fwd0));gz=bpy.data.objects.new('Gaze',None);link(gz)
k_=rig.pose.bones['mixamorig:Head'].constraints.new('DAMPED_TRACK');k_.target=gz;k_.track_axis=FACE_AXIS;k_.influence=.85
for f in range(1,frames+1,2):
 t=(f-1)/fps;p,h,m=leo_state(t);ff,ll=fl_(h)
 if t<TL0:g=Vector((front(t)+6,0,1.5))
 elif t<TL1:g=Vector((PC.x,PC.y,1.0))
 elif t<TL3+1.5:g=child_center(t)+Vector((0,0,.1))
 else:g=Vector((front(t)-3,0,2.0))
 gz.location=g;gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('establish',0,TL0+.6,'wide'),('the wave',TL0+.6,TL0+2.0,'bore'),('run to the child',TL0+2.0,TL1+.3,'follow'),('the lift',TL1+.3,TL2,'lift'),('run uphill',TL2,TL2+3.5,'follow2'),('the crowd',TL2+3.5,TL2+6.5,'crowd'),('hilltop',TL2+6.5,TL3+.6,'hill'),('set down',TL3+.6,TL4+.4,'lift2'),('the water arrives',TL4+.4,seconds,'wide2')]
cams=[];CAMKEYS=[]
for k,(name,a,b,kind) in enumerate(cuts):
 cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=400;link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.hide_viewport=True
 con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
 for f in range(F(a),F(b)+1,2):
  t=(f-1)/fps;u=(t-a)/max(.1,b-a);p,h,m=leo_state(t);ff,ll=fl_(h);lp_=p+Vector((0,0,1.0));cam.data.lens=32;q=lp_;fx=front(t)
  if kind=='wide':P=Vector((30,-26,12));q=Vector((12,0,1));cam.data.lens=24
  elif kind=='bore':P=Vector((fx+18,-12,7.0));q=Vector((fx,0,1.2));cam.data.lens=28
  elif kind=='follow':P=lp_-ff*5.5+ll*1.6+Vector((0,0,.6))
  elif kind=='lift':P=p+ff*1.8+ll*1.3+Vector((0,0,.9));q=child_center(t);cam.data.lens=42
  elif kind=='follow2':P=lp_+ff*5.5+ll*2.0+Vector((0,0,.5));q=lp_
  elif kind=='crowd':P=Vector((48,-14,3.2+G(48,-14)*0));q=Vector((52,0,G(52,0)+1.2));cam.data.lens=26
  elif kind=='hill':P=lp_-ff*6.0+ll*2.5+Vector((0,0,1.5));q=lp_+ff*2.0
  elif kind=='lift2':P=p+ff*1.6-ll*1.4+Vector((0,0,.9));q=child_center(t);cam.data.lens=42
  else:P=Vector((86,-14,G(86,-14)+4.5));q=Vector((fx-6,0,1.6));cam.data.lens=24
  cam.location=P;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f);CAMKEYS.append((k,cam,aim,f))
 scene.timeline_markers.new(name,frame=F(a)).camera=cam
scene.camera=cams[0]
def settle(f):scene.frame_set(f);bpy.context.view_layer.update()
FAMILY=set(kit._family(LEO['root']))|set(kit._family(CH))
for r in VILL:FAMILY|=set(kit._family(r))
for o in bpy.data.objects:
 if o.name.startswith(('Wrist','Barrel','Crate','Plank','FloodFoam','FloodCrest','FloodWater','Villager','Vill')):FAMILY.add(o.name)
CAND=[(0,0,1.),(0,0,2.5),(0,3.,1.),(0,-3.,1.),(3.,0,1.),(-3.,0,1.)]
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
if CROWD_BAD:issues.append('AUDIT crowd: villagers %s are still deeper than 0.5 m in the water at 5.2 m/s'%CROWD_BAD[:6])
dl=max(depth(*leo_state(t)[0].xy,t) for t in np.arange(0,seconds,.1));dc=max(depth(*child_center(t).xy,t) for t in np.arange(0,seconds,.1))
if dl>.3:issues.append('AUDIT leo: the water is %.2f m deep at Leo (the front catches him)'%dl)
if dc>.3:issues.append('AUDIT child: the water is %.2f m deep at the child'%dc)
for t in np.arange(0,seconds,.1):
 p=leo_state(t)[0]
 if any(math.hypot(p.x-hx,p.y-hy)<hr-.9 for hx,hy,hr in HOUSES):issues.append('AUDIT house: Leo walks into a house at %.1f s'%t);break
gap=min(leo_state(t)[0].x-front(t) for t in np.arange(TL2,TL3,.1))
for i in range(N):
 for fi in range(0,frames,6):
  x,y=H[fi,i]
  if any(math.hypot(x-hx,y-hy)<hr-.9 for hx,hy,hr in HOUSES):issues.append('AUDIT house: villager %d walks into a house at %.1f s'%(i,fi/fps));break
for f in range(F(TL1+.8),F(TL3+1.4),4):
 settle(f);t=(f-1)/fps
 for limb,b,a_ in (('LH','LeftForeArm','LeftArm'),('RH','RightForeArm','RightArm')):
  sh=rig.matrix_world@rig.pose.bones['mixamorig:'+a_].head;d=(TG[limb].matrix_world.translation-sh).length
  if d>.46 and hand_w(t)>.99:reach_err.append((round(d-.44,3),limb,round(t,1)))
  g=(rig.matrix_world@rig.pose.bones['mixamorig:'+b].tail-TG[limb].matrix_world.translation).length
  if g>worst.get(limb,(0,0))[0]:worst[limb]=(g,t)
if reach_err:issues.append('AUDIT reach: wrist target beyond arm reach %s (%d samples)'%(reach_err[:3],len(reach_err)))
for l,(g,t) in worst.items():
 if g>.07:issues.append('AUDIT grip: %s misses the child by %.0f cm at %.1f s'%(l,g*100,t))
print('FLOOD lead over the front while running uphill %.1f m; max depth at Leo %.2f, child %.2f; GRIP %s; speeds raised for %d villagers'%(gap,dl,dc,{k:round(v[0]*100,1) for k,v in worst.items()},sum(1 for i in range(N) if speeds[i]>base_speed[i]+1e-6)))
for i in issues:print(i)
print('AUDIT',len(issues),'issues')
# ---------------------------------------------------------------------------------------------------------- sound
SR=22050;N_=int(seconds*SR);adir=os.path.join(os.path.dirname(out),'audio_flood');os.makedirs(adir,exist_ok=True);nr=np.random.default_rng(3)
def wav(name,x,peak):
 x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(adir,name)
 with wave.open(p,'wb') as w_:w_.setnchannels(1);w_.setsampwidth(2);w_.setframerate(SR);w_.writeframes((x*32767).astype('<i2').tobytes())
 return p
lp=lambda x,k:np.convolve(x,np.ones(k)/k,mode='same')
tt=np.arange(N_)/SR;dist=np.maximum(1,np.abs(np.array([front(t) for t in tt[::441]])-60));env=np.interp(tt,tt[::441],2.5/dist**.7)
roar=lp(nr.standard_normal(N_),14)*np.clip(env,0,1)*np.minimum(tt/T_WAVE,1)
panic=lp(nr.standard_normal(N_),3)*(.3+.2*np.sin(2*PI*3.1*tt))*np.clip((tt-react[0])/1.5,0,1)*np.clip((TL3+3-tt)/3,0,1)*.15
feet=np.zeros(N_+SR);k=np.arange(int(.08*SR))/SR;fs=lp(nr.standard_normal(len(k)),6)*np.exp(-k*50)
t=TL0
while t<TL1:feet[int(t*SR):int(t*SR)+len(fs)]+=fs*.8;t+=.26
t=TL2
while t<TL3:feet[int(t*SR):int(t*SR)+len(fs)]+=fs*.8;t+=.26
horn=np.zeros(N_);hk=np.arange(int(1.6*SR))/SR;horn_=np.sin(2*PI*220*hk)*np.minimum(hk/.1,1)*np.minimum((1.6-hk)/.3,1);i0=int((T_WAVE-.3)*SR);horn[i0:i0+len(hk)]=horn_[:max(0,min(len(hk),N_-i0))]
mus=np.zeros(N_+SR*6)
for ci in range(int(seconds/4)+1):
 for f0 in ((98,123.5,146.8),(87.3,110,130.8),(82.4,98,123.5),(92.5,110,138.6))[ci%4]:
  kk=np.arange(int(4.2*SR))/SR;i=int(ci*4*SR);mus[i:i+len(kk)]+=np.sin(2*PI*f0*kk)*np.minimum(kk/.3,1)*np.exp(-kk*.6)*.2
mus=mus[:N_]*np.minimum(tt/2,1)*np.minimum((seconds-tt)/3,1)
paths=[wav('flood.wav',roar,.8),wav('panic.wav',panic,.5),wav('steps.wav',feet[:N_],.5),wav('horn.wav',horn,.5),wav('music.wav',mus,.35)]
se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
for ch,(p,n) in enumerate(zip(paths,('flood','crowd','steps','horn','music')),start=1):strips.new_sound(n,p,ch,1)
scene.world=bpy.data.worlds.new('Storm');scene.world.color=(.32,.36,.42)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1280;scene.render.resolution_y=720
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('FLOOD_DONE',frames,'frames')
