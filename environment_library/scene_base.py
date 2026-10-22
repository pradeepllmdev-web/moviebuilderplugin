"""Shared scaffolding for the second-generation scenes (one file per scene, each about 150 lines of story logic).

Usage inside a scene script (blender -b --disable-autoexec --python x_scene.py -- <ship_assets_dir> <out.blend>):
    import scene_base as sb
    S=sb.Scene('ice');S.load_env('ice_cave');leo=S.character('Leo');S.play(leo,[(0,5,'idle'),(5,9,'run')]);IK,TG=S.ik(leo)
    S.cameras(cuts,pos_fn,family=...);S.audio(...);S.finish(extra_issues,subjects=[leo['root']])
It wraps what every scene repeats: materials and primitives, characters from the lion rig, NLA clip playing, IK hands, head gaze, generated camera cuts with automatic clearing of the view, the persistence and camera audits,
synthesised sound tracks, saving. Nothing here makes creative decisions."""
import bpy,math,os,sys,wave
import numpy as np
from mathutils import Vector,Euler,Matrix
import scene_kit as kit,scene_params,locations
PI=math.pi;smooth=kit.smooth
MIX=dict(head='mixamorig:Head',LH_fore='mixamorig:LeftForeArm',RH_fore='mixamorig:RightForeArm',LH_up='mixamorig:LeftArm',RH_up='mixamorig:RightArm',lfoot='mixamorig:LeftFoot',rfoot='mixamorig:RightFoot',lhand='mixamorig:LeftHand',rhand='mixamorig:RightHand')
def B(ch,k):
 """bone name of a role (head, forearms, upper arms, feet, hands) on this character's skeleton: the lion's Mixamo names unless the character carries its own map ch['bn']"""
 return ch.get('bn',MIX)[k]
class Scene:
 def __init__(self,name):
  args=sys.argv[sys.argv.index('--')+1:];self.assets,self.out=args[0],args[1]
  bpy.ops.wm.read_factory_settings(use_empty=True);self.scene=bpy.context.scene;self.fps=24;self.scene.render.fps=24;self.name=name;self._m={};self.params=scene_params.get();self.clips={};self.chars=[]
  self.ctx=dict(link=self.link,mat=self.mat,prim=self.prim)
 def F(self,t):return 1+int(round(t*self.fps))
 def link(self,o):
  if o.name not in self.scene.collection.objects:self.scene.collection.objects.link(o)
 def mat(self,name,color,emit=0.):
  key=name+str(color)+str(emit)
  if key in self._m:return self._m[key]
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
  if b:
   b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.8
   if emit:
    for k in ('Emission Color','Emission'):
     if k in b.inputs:b.inputs[k].default_value=(*color,1);break
    if 'Emission Strength' in b.inputs:b.inputs['Emission Strength'].default_value=emit
  self._m[key]=m;return m
 def prim(self,kind,name,loc,color,scale=(1,1,1),rot=(0,0,0),emit=0.,parent=None,**kw):
  if kind=='cone':bpy.ops.mesh.primitive_cone_add(location=loc,rotation=rot,**kw)
  elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(location=loc,rotation=rot,**kw)
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(location=loc,rotation=rot,**kw)
  else:bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot,**kw)
  o=bpy.context.object;o.scale=scale;o.name=name;o.data.materials.append(self.mat(name.split('.')[0],color,emit))
  if parent:o.parent=parent
  return o
 def clock(self,seconds):
  self.seconds=seconds;self.frames=int(seconds*self.fps);self.scene.frame_start=1;self.scene.frame_end=self.frames;return self.frames
 def keys(self,step=2):return range(1,self.frames+1,step)
 def load_env(self,id_,state='intact',params=None):locations.load(id_,self.ctx,state,params) if params else locations.load(id_,self.ctx,state)
 def clip(self,name):
  if name not in self.clips:
   with bpy.data.libraries.load(os.path.join(self.assets,'leo_%s.blend'%name),link=False) as (src,dst):dst.actions=[n for n in src.actions if n=='leo_%s'%name]
   self.clips[name]=dst.actions[0]
  return self.clips[name]
 def character(self,tag,tint=None,parent=None):
  with bpy.data.libraries.load(os.path.join(self.assets,'leo_idle.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects]
  new=[]
  for o in dst.objects:
   if o.type in ('CAMERA','LIGHT','EMPTY') or (o.type=='MESH' and (o.hide_viewport or o.hide_render or o.name.startswith(('Floor','Wall','Ceiling','Rug','Grid')))):bpy.data.objects.remove(o);continue
   self.link(o);new.append(o)
  root=bpy.data.objects.new(tag+'Root',None);self.link(root)
  for o in new:
   if o.parent is None:o.parent=root
   if o.type!='ARMATURE' and o.animation_data:o.animation_data_clear()
   if tint and o.type=='MESH':
    for i,slot in enumerate(o.material_slots):
     if slot.material:
      m=slot.material.copy();c=slot.material.diffuse_color;m.diffuse_color=(c[0]*tint[0],c[1]*tint[1],c[2]*tint[2],1);o.material_slots[i].material=m
  rig=next(o for o in new if o.type=='ARMATURE');rig.animation_data_clear();rig.animation_data_create()
  if parent:root.parent=parent
  ch=dict(root=root,rig=rig,objs=new,tag=tag,tracks=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()],n=0);self.chars.append(ch);return ch
 def strip(self,ch,clip,a,b,scale=1.,hold=False,f0=None,f1=None):
  """Play a clip over [a,b] seconds (looped or trimmed to fit) on one of two alternating NLA tracks; consecutive calls blend."""
  act=self.clip(clip);tr=ch['tracks'][ch['n']%2];ch['n']+=1;st=tr.strips.new(clip,self.F(a),act);st.action_slot=act.slots[0]
  n=(f1 or act.frame_range[1])-(f0 or act.frame_range[0])+1
  if f0:st.action_frame_start=f0
  if f1:st.action_frame_end=f1
  st.scale=scale;need=(self.F(b)-st.frame_start)/(n*scale)
  if need>=1:st.repeat=need
  else:st.action_frame_end=st.action_frame_start+max(2,need*n)-1
  st.extrapolation='HOLD' if hold else 'NOTHING';st.blend_in=5 if ch['n']>1 else 0;st.blend_out=5;return st
 def play(self,ch,segs):
  """segs: list of (t0,t1,clip[,scale[,f0,f1]]); the first strip holds backwards, later ones start .2 s early to blend."""
  for k,s in enumerate(segs):
   a,b,clip=s[:3];sc=s[3] if len(s)>3 else 1.;f0=s[4] if len(s)>4 else None;f1=s[5] if len(s)>5 else None;self.strip(ch,clip,a if not k else max(0,a-.2),b,sc,hold=(k==0),f0=f0,f1=f1)
 def ik(self,ch,influence=0.,pole_y=.5):
  IK={};TG={};rig=ch['rig']
  for limb,bone in (('LH',B(ch,'LH_fore')),('RH',B(ch,'RH_fore'))):
   tg=bpy.data.objects.new('Wrist_%s_%s'%(ch['tag'],limb),None);tg.empty_display_size=.04;self.link(tg);TG[limb]=tg
   pole=bpy.data.objects.new('Pole_%s_%s'%(ch['tag'],limb),None);self.link(pole);pole.parent=ch['root'];sg=1 if limb=='LH' else -1;pole.location=(.5*sg,pole_y,.9)
   k=rig.pose.bones[bone].constraints.new('IK');k.target=tg;k.pole_target=pole;k.pole_angle=math.radians(-90 if limb=='LH' else 90);k.chain_count=2;k.use_stretch=False;k.influence=influence;IK[limb]=k
  ch['IK']=IK;ch['TG']=TG;return IK,TG
 def shoulders(self,ch):
  self.scene.frame_set(1);bpy.context.view_layer.update();rig=ch['rig']
  return {l:rig.matrix_world@rig.pose.bones[B(ch,l+'_up')].head for l in ('LH','RH')}
 def gaze(self,ch,facing,influence=.8):
  """Head damped-track to an empty (returned) keyed by the caller; facing = world direction the character faces at frame 1."""
  self.scene.frame_set(1);bpy.context.view_layer.update();rig=ch['rig'];hm=(rig.matrix_world@rig.pose.bones[B(ch,'head')].matrix).to_3x3()
  AX={'TRACK_X':hm.col[0],'TRACK_NEGATIVE_X':-hm.col[0],'TRACK_Y':hm.col[1],'TRACK_NEGATIVE_Y':-hm.col[1],'TRACK_Z':hm.col[2],'TRACK_NEGATIVE_Z':-hm.col[2]}
  fa=max(AX,key=lambda k:AX[k].normalized().dot(Vector(facing).normalized()));ch['face_axis']=fa;g=bpy.data.objects.new('Gaze_'+ch['tag'],None);self.link(g)
  k=rig.pose.bones[B(ch,'head')].constraints.new('DAMPED_TRACK');k.target=g;k.track_axis=fa;k.influence=influence;return g
 def face_dir(self,ch):
  """world direction the character's face points (needs gaze() to have run); call after settle(frame)"""
  rig=ch['rig'];hm=(rig.matrix_world@rig.pose.bones[B(ch,'head')].matrix).to_3x3();fa=ch['face_axis']
  v=hm.col[0] if fa=='TRACK_X' else hm.col['XYZ'.index(fa[-1])]*(-1 if 'NEGATIVE' in fa else 1)
  return Vector(v).normalized()
 def head_pos(self,ch):
  rig=ch['rig'];return rig.matrix_world@rig.pose.bones[B(ch,'head')].head
 def blinks(self,ch,seed=1,t0=0.):
  """natural blinking: a 0.16 s blink every 2.2-5.5 s on every mesh of the character that has BlinkL/BlinkR shape keys (the lids and creases)"""
  import random
  rnd=random.Random(seed*7919+len(ch['tag']));t=t0+rnd.uniform(.6,2.5);keys=[]
  for o in ch['objs']:
   kb=o.data.shape_keys if o.type=='MESH' else None
   if kb and ('BlinkL' in kb.key_blocks or 'BlinkR' in kb.key_blocks):
    if kb.animation_data is None:kb.animation_data_create()
    keys.append(kb)
  if not keys:return 0
  n=0
  while t<self.seconds-.3:
   f0,f1,f2=self.F(t),self.F(t+.07),self.F(t+.16)
   for kb in keys:
    for nm in ('BlinkL','BlinkR'):
     b=kb.key_blocks.get(nm)
     if b:b.value=0;b.keyframe_insert('value',frame=f0);b.value=1;b.keyframe_insert('value',frame=f1);b.value=0;b.keyframe_insert('value',frame=f2)
   n+=1;t+=rnd.uniform(2.2,5.5)
  return n
 def settle(self,f):self.scene.frame_set(f);bpy.context.view_layer.update()
 def cameras(self,cuts,pos_fn,family_prefixes=(),cand=None,lens=32,dof=True,fstop=4.0,shake=0.):
  """cuts: [(name,a,b,kind)]; pos_fn(kind,t,u)->(camera position, aim point[, lens]). Keys every 2 frames, marks the cuts, clears the view of anything in the way (smoothed over time)."""
  sc=self.scene;cams=[];ck=[]
  for k,(name,a,b,kind) in enumerate(cuts):
   cam=bpy.data.objects.new('Cam%d'%k,bpy.data.cameras.new('Cam%d'%k));cam.data.clip_end=3000;self.link(cam);cams.append(cam);aim=bpy.data.objects.new('Aim%d'%k,None);self.link(aim);aim.hide_viewport=True
   con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
   for f in range(self.F(a),self.F(b)+1,2):
    t=(f-1)/self.fps;u=(t-a)/max(.1,b-a);r=pos_fn(kind,t,u);P,q=Vector(r[0]),Vector(r[1]);cam.data.lens=r[2] if len(r)>2 else lens
    if shake:
     import math as _m;ph=f*.13+k*3.1;P=P+Vector((_m.sin(ph*1.7),_m.sin(ph*2.3+1),_m.sin(ph*1.1+2)))*shake;q=q+Vector((_m.sin(ph*2.9),_m.sin(ph*1.3+2),_m.sin(ph*2.1)))*shake*.6
    cam.location=P;cam.keyframe_insert('location',frame=f);aim.location=q;aim.keyframe_insert('location',frame=f);cam.data.keyframe_insert('lens',frame=f)
    if dof:
     cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=fstop;cam.data.dof.focus_distance=max(.5,(P-q).length);cam.data.dof.keyframe_insert('focus_distance',frame=f)
    ck.append((k,cam,aim,f))
   sc.timeline_markers.new(name,frame=self.F(a)).camera=cam
  sc.camera=cams[0];fam=set()
  for c in self.chars:fam|=set(kit._family(c['root']))
  for o in bpy.data.objects:
   if o.name.startswith(('Wrist',)+tuple(family_prefixes)):fam.add(o.name)
  cand=cand or [(0,0,1.),(0,0,2.5),(0,2.5,1.),(0,-2.5,1.),(2.5,0,1.),(-2.5,0,1.)];offs={}
  for k,cam,aim,f in ck:
   self.settle(f);d=bpy.context.evaluated_depsgraph_get();p=Vector(cam.location);q=Vector(aim.location);np_,idx=kit.clear_view(sc,d,p,q,fam,cand);offs[(k,f)]=np_-p
  for k in set(a for a,b in offs):
   fs=sorted(f for a,f in offs if a==k)
   for j,f in enumerate(fs):
    win=[offs[(k,g)] for g in fs[max(0,j-3):j+4]];offs[(k,f)]=Vector((sum(v.x for v in win)/len(win),sum(v.y for v in win)/len(win),max(v.z for v in win)))
  for k,cam,aim,f in ck:
   o=offs[(k,f)]
   if o.length>1e-6:cam.location=Vector(cam.location)+o;cam.keyframe_insert('location',frame=f)
  self.family=fam;return cams
 def audio(self,build):
  """build(A) fills named tracks: A.track(name,array,peak); helpers A.at(arr,t,x,g), A.noise(n,k) (low-passed noise), A.chords(seq,vol). Tracks are added as sound strips."""
  A=Audio(self);build(A);A.save()
 def finish(self,issues=None,subjects=None,world=(.3,.35,.4),color_type='MATERIAL'):
  for i,c in enumerate(self.chars):
   if not c.get('blinked'):self.blinks(c,i+1);c['blinked']=True
  sc=self.scene;issues=list(issues or [])+kit.persistence_audit(sc)+kit.camera_checks(sc,subjects or [c['root'] for c in self.chars[:1]])
  for i in issues:print(i)
  print('AUDIT',len(issues),'issues')
  sc.world=bpy.data.worlds.new('W');sc.world.color=world;getattr(self,'sky_hook',lambda sc:None)(sc);sc.display.shading.light='STUDIO';sc.display.shading.color_type=color_type;sc.render.resolution_x=1280;sc.render.resolution_y=720
  sc.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=self.out);print(self.name.upper()+'_DONE',self.frames,'frames');return issues
class Audio:
 SR=22050
 def __init__(self,S):
  self.S=S;self.N=int(S.seconds*self.SR);self.t=np.arange(self.N)/self.SR;self.dir=os.path.join(os.path.dirname(S.out),'audio_'+S.name);os.makedirs(self.dir,exist_ok=True);self.tracks=[];self.rng=np.random.default_rng(abs(hash(S.name))%10000)
 def track(self,name,arr,peak=.5):
  x=np.asarray(arr,float)[:self.N];x=np.pad(x,(0,self.N-len(x)));x=x/(np.max(np.abs(x))+1e-9)*peak;p=os.path.join(self.dir,name.replace(' ','_')+'.wav')
  with wave.open(p,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(self.SR);w.writeframes((x*32767).astype('<i2').tobytes())
  self.tracks.append((name,p))
 def buf(self,extra=3):return np.zeros(self.N+self.SR*extra)
 def at(self,arr,t,x,g=1.):
  i=int(t*self.SR)
  if 0<=i<len(arr):
   n=min(len(x),len(arr)-i);arr[i:i+n]+=x[:n]*g
 def noise(self,n,k=8):return np.convolve(self.rng.standard_normal(n),np.ones(k)/k,mode='same')
 def burst(self,dur=.3,k=6,decay=10.):
  kk=np.arange(int(dur*self.SR))/self.SR;return self.noise(len(kk),k)*np.exp(-kk*decay)
 def tone(self,f,dur,decay=3.,vol=1.):
  kk=np.arange(int(dur*self.SR))/self.SR;return (np.sin(2*PI*f*kk)+.3*np.sin(4*PI*f*kk))*np.minimum(kk/.01,1)*np.exp(-kk*decay)*vol
 def chords(self,seq,vol=.18,bar=4.):
  m=self.buf(6)
  for ci in range(int(self.S.seconds/bar)+1):
   for f0 in seq[ci%len(seq)]:
    kk=np.arange(int((bar+.2)*self.SR))/self.SR;self.at(m,ci*bar,np.sin(2*PI*f0*kk)*np.minimum(kk/.3,1)*np.exp(-kk*.7)*vol)
  return m[:self.N]*np.minimum(self.t/2,1)*np.minimum((self.S.seconds-self.t)/3,1)
 def save(self):
  sc=self.S.scene;se=sc.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
  for ch,(n,p) in enumerate(self.tracks,start=1):strips.new_sound(n,p,ch,1)
class Path:
 """Catmull-Rom path through 3D points with an arc-length table: at(s) position, tangent(s) unit direction, length, s_of(i) arc length of waypoint i."""
 def __init__(self,points,per=40):
  P=np.array([list(p) for p in points],float);pts=[];self.wp=[]
  for i in range(len(P)-1):
   p0=P[max(0,i-1)];p1=P[i];p2=P[i+1];p3=P[min(len(P)-1,i+2)]
   for u in np.linspace(0,1,per,endpoint=False):pts.append(.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3))
  pts.append(P[-1]);self.pts=np.array(pts);self.cum=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(self.pts,axis=0),axis=1))]);self.length=float(self.cum[-1])
  self.wp=[float(self.cum[min(i*per,len(self.cum)-1)]) for i in range(len(P))]
 def at(self,s):
  s=min(max(s,0.),self.length-1e-6);i=int(np.searchsorted(self.cum,s,side='right')-1);u=(s-self.cum[i])/max(1e-9,self.cum[i+1]-self.cum[i]);return Vector(self.pts[i]*(1-u)+self.pts[i+1]*u)
 def tangent(self,s,h=.6):return (self.at(s+h)-self.at(s-h)).normalized()
 def s_of(self,i):return self.wp[i]
