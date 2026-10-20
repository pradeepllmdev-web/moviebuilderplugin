"""Blender script: export a built scene for Unreal.

blender -b <scene.blend> --python unreal_export.py -- <out_dir> [scene_name]

Writes <out_dir>/<scene>.ue.json (actors with per-frame transforms in Unreal axes and centimetres, characters with their clip strips, IK targets, cameras with lens keys, lights,
cut list, audio strips, static environment listing) and FBX files: environment.fbx (all static meshes), props.fbx (animated non-character objects at their frame-1 pose),
character_<tag>.fbx (skeletal mesh at rest) and anim_<clip>.fbx for every clip the characters use. Unreal then rebuilds the scene from the JSON (unreal_import.py), swapping
placeholder ids for real assets through unreal_asset_map.json. See UNREAL_BRIDGE.md."""
import bpy,json,math,os,re,sys
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ue_common as ub
args=sys.argv[sys.argv.index('--')+1:];OUT=args[0];sc=bpy.context.scene;NAME=args[1] if len(args)>1 else os.path.splitext(os.path.basename(bpy.data.filepath))[0].replace('_scene','')
os.makedirs(OUT,exist_ok=True);FS,FE=sc.frame_start,sc.frame_end;FPS=sc.render.fps
from mathutils import Vector
EFFECTS=('Dust','Spark','Splash','Steam','Puff','Bolt','Snow')
def top(o):
 while o.parent is not None:o=o.parent
 return o
def anim(o):
 while o is not None:
  if o.animation_data and (o.animation_data.action or o.animation_data.nla_tracks):return True
  if o.constraints and any(c.type in ('TRACK_TO','CHILD_OF','DAMPED_TRACK','COPY_LOCATION') for c in o.constraints) and o.type=='CAMERA':return True
  o=o.parent
 return False
objs=list(sc.objects)
chars=[];char_objs=set()
for o in objs:
 if o.type=='ARMATURE':
  r=top(o);chars.append(dict(rig=o,root=r,tag=r.name.replace('Root','') or o.name))
  stack=[r]
  while stack:
   x=stack.pop();char_objs.add(x.name);stack+=list(x.children)
ik=[o for o in objs if o.name.startswith('Wrist_')]
cams=[o for o in objs if o.type=='CAMERA'];lights=[o for o in objs if o.type=='LIGHT']
animated_roots=[]
for o in objs:
 if o.name in char_objs or o.type in ('CAMERA','LIGHT') or o in ik or o.name.startswith('Aim') or o.name.startswith('Pole_') or o.name.startswith('Gaze_'):continue
 if anim(o) and not anim(o.parent) if o.parent else anim(o):animated_roots.append(o)
# anim(o.parent) is true when the parent is animated: only the topmost animated object is exported as the actor
animated_roots=[o for o in animated_roots if not (o.parent and anim(o.parent))]
role_of=lambda o:'effect' if o.name.startswith(EFFECTS) else 'prop'
static=[o for o in objs if o.type=='MESH' and o.name not in char_objs and not anim(o) and not o.name.startswith(('Wrist_','Aim'))]
# ---------------------------------------------------------------------------------------------------------- per-frame sampling of the actors
tracked=[(o,'character',None) for o in [c['root'] for c in chars]]+[(o,'ik_target',None) for o in ik]+[(o,'camera',None) for o in cams]+[(o,role_of(o),None) for o in animated_roots]
samples={o.name:{'frames':[],'loc':[],'rot':[],'scale':[],'lens':[]} for o,_,_ in tracked};lightkeys={l.name:[] for l in lights}
for f in range(FS,FE+1):
 sc.frame_set(f)
 for o,role,_ in tracked:
  M=o.matrix_world;s=samples[o.name];e=M.to_euler('XYZ');s['frames'].append(f);s['loc'].append(ub.ue_loc(M.translation));s['scale'].append(ub.ue_scale(M.to_scale()))
  if o.type=='CAMERA':fw=M.to_3x3()@Vector((0,0,-1));s['rot'].append(ub.ue_look_rot_deg((fw.x,fw.y,fw.z)));s['look']=True
  else:s['rot'].append([e.x,e.y,e.z])
  if o.type=='CAMERA':s['lens'].append(o.data.lens)
 for l in lights:lightkeys[l.name].append((f,l.data.energy))
def finish(o):
 s=samples[o.name]
 if s.get('look'):rot=[list(r) for r in s['rot']];rot=[[ub.unwrap_deg([r[c] for r in rot])[i] for c in range(3)] for i in range(len(rot))]
 else:rot=np.array(s['rot']);rot=np.unwrap(rot,axis=0);rot=[ub.ue_rot_deg(r) for r in rot];rot=[[ub.unwrap_deg([r[c] for r in rot])[i] for c in range(3)] for i in range(len(rot))]
 fr=s['frames'];vals=[l+r+sc_ for l,r,sc_ in zip(s['loc'],rot,s['scale'])];keep=ub.reduce_keys(fr,vals,.05)
 d=dict(frames=[fr[i] for i in keep],loc=[s['loc'][i] for i in keep],rot=[[round(x,4) for x in rot[i]] for i in keep],scale=[s['scale'][i] for i in keep])
 if s['lens']:d['lens']=[s['lens'][i] for i in keep]
 d['loc']=[[round(x,3) for x in v] for v in d['loc']];d['scale']=[[round(x,4) for x in v] for v in d['scale']];return d
doc=dict(scene=NAME,fps=FPS,frame_start=FS,frame_end=FE,units='cm, Unreal axes (Blender Y negated); rotations roll,pitch,yaw degrees',source=os.path.basename(bpy.data.filepath),actors=[],characters=[],cuts=[],audio=[],environment=dict(fbx='environment.fbx',static_meshes=len(static)),props_fbx='props.fbx')
idmap={}
for o,role,_ in tracked:
 aid='a%03d'%len(idmap);idmap[o.name]=aid
 a=dict(id=aid,name=o.name,role=role,asset_key=ub.asset_key(o.name),keys=finish(o))
 if o.type=='CAMERA':a['camera']=dict(sensor_width=o.data.sensor_width,clip_end=o.data.clip_end)
 if role in ('prop','effect'):a['meshes']=[c.name for c in o.children_recursive if c.type=='MESH'] or ([o.name] if o.type=='MESH' else [])
 doc['actors'].append(a)
sc.frame_set(FS)
from mathutils import Vector
def wdims(p):
 bb=[Vector(c) for c in p.bound_box];ws=p.matrix_world.to_scale();return [round(abs(max(v[i] for v in bb)-min(v[i] for v in bb))*abs(ws[i])*100,2) for i in range(3)]
for a in doc['actors']:
 if a['role'] in ('prop','effect'):
  ro=bpy.data.objects.get(a['name']);parts=[]
  if ro is not None:
   from mathutils import Matrix
   l0,q0,s0=ro.matrix_world.decompose();Rinv=(Matrix.Translation(l0)@q0.to_matrix().to_4x4()).inverted()   # root space WITHOUT the root's scale: the document's part sizes (dims_cm) are world sizes, so the offsets must be world-sized too
   for p in [ro]+list(ro.children_recursive):
    if p.type!='MESH':continue
    Mr=Rinv@p.matrix_world;ee=Mr.to_3x3().normalized().to_euler('XYZ');parts.append(dict(mesh=p.name,self=(p is ro),loc=[round(x,3) for x in ub.ue_loc(Mr.translation)],rot=[round(x,4) for x in ub.ue_rot_deg([ee.x,ee.y,ee.z])],dims_cm=wdims(p)))
  a['parts']=parts
for a in doc['actors']:
 if a['role'] in ('prop','effect') and a.get('meshes'):
  lo=[1e9]*3;hi=[-1e9]*3
  for mn in a['meshes']:
   ob=bpy.data.objects.get(mn)
   if ob is None or ob.type!='MESH':continue
   for corner in ob.bound_box:
    w=ob.matrix_world@Vector(corner)
    for i in range(3):lo[i]=min(lo[i],w[i]);hi[i]=max(hi[i],w[i])
  if lo[0]<1e8:a['bounds_cm']=[round((hi[i]-lo[i])*100,1) for i in range(3)]
for l in lights:
 aid='a%03d'%len(idmap);idmap[l.name]=aid;M=l.matrix_world;e=M.to_euler('XYZ');ev=[v for f,v in lightkeys[l.name]];anim_l=(max(ev)-min(ev))>1e-3
 doc['actors'].append(dict(id=aid,name=l.name,role='light',asset_key=l.data.type,light=dict(type=l.data.type,color=list(l.data.color),energy=l.data.energy,energy_keys=[[f,v] for f,v in lightkeys[l.name]][::max(1,len(ev)//200)] if anim_l else None,spot_size=getattr(l.data,'spot_size',None)),keys=dict(frames=[FS],loc=[ub.ue_loc(M.translation)],rot=[ub.ue_look_rot_deg(tuple(M.to_3x3()@Vector((0,0,-1))))],scale=[[1,1,1]])))
# characters: clips from the NLA strips, ik targets, the root actor
for c in chars:
 rig=c['rig'];clips=[]
 if rig.animation_data:
  for tr in rig.animation_data.nla_tracks:
   for st in tr.strips:
    if st.action:clips.append(dict(clip=re.sub(r'\.\d+$','',st.action.name).replace('leo_',''),action=st.action.name,start=int(round(st.frame_start)),end=int(round(st.frame_end)),scale=st.scale,repeat=st.repeat,action_start=st.action_frame_start,action_end=st.action_frame_end,blend_in=st.blend_in,blend_out=st.blend_out))
 for c_ in clips:
  c_['anim_file']='anim_%s_%d_%d'%(c_['clip'],int(round(c_['action_start'])),int(round(c_['action_end'])))
 clips.sort(key=lambda x:x['start'])
 doc['characters'].append(dict(name=c['tag'],root=idmap[c['root'].name],rig=rig.name,skeletal_mesh='character_%s.fbx'%c['tag'],clips=clips,ik_targets=[dict(limb=o.name.split('_')[-1],actor=idmap[o.name]) for o in ik if o.name.startswith('Wrist_%s'%c['tag'])or (o.name in ('Wrist_LH','Wrist_RH') and len(chars)==1)]))
# cuts
mk=sorted(sc.timeline_markers,key=lambda m:m.frame)
for i,m in enumerate(mk):
 end=(mk[i+1].frame-1) if i+1<len(mk) else FE
 if m.camera:doc['cuts'].append(dict(name=m.name,camera=idmap[m.camera.name],start=m.frame,end=end))
# audio strips
if sc.sequence_editor:
 for s in sc.sequence_editor.strips_all:
  if s.type=='SOUND':doc['audio'].append(dict(name=s.name,file=bpy.path.abspath(s.sound.filepath) if s.sound else '',start=int(s.frame_start),volume=s.volume))
# ---------------------------------------------------------------------------------------------------------- the FBX files
def fbx(path,sel,anim_=False,frames=None):
 bpy.ops.object.select_all(action='DESELECT')
 for o in sel:o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=path,use_selection=True,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=anim_,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,add_leaf_bones=False,object_types={'MESH','ARMATURE','EMPTY'})
sc.frame_set(FS)
if static:
 # one joined mesh (every static object at its world position) so the environment can be placed as a single actor at the origin
 bpy.ops.object.select_all(action='DESELECT');copies=[]
 for o in static:
  c=o.copy();c.data=o.data.copy();c.parent=None;c.matrix_world=o.matrix_world;sc.collection.objects.link(c);copies.append(c)
 for c in copies:
  c.select_set(True)
 bpy.context.view_layer.objects.active=copies[0]
 bpy.ops.object.join();env=bpy.context.view_layer.objects.active;env.name='Environment_'+NAME;env.data.name='Environment_'+NAME
 fbx(os.path.join(OUT,'environment.fbx'),[env]);doc['environment']['mesh']=env.name
 bpy.data.objects.remove(env,do_unlink=True)
pm=[]
for o in animated_roots:
 pm+=[x for x in ([o]+list(o.children_recursive)) if x.type=='MESH']
pm=list({x.name:x for x in pm}.values())
if pm:
 # every prop mesh is exported at the identity transform (pivot at the object origin): the actor (and the part offsets in the document) supply where it stands, so a world position baked into the vertices would be applied twice
 from mathutils import Matrix
 flat=[]
 for x in pm:
  nm=x.name;x.name=nm+'~src';c=x.copy();c.data=x.data.copy();c.animation_data_clear();c.parent=None;c.matrix_world=Matrix.Identity(4);c.name=nm;sc.collection.objects.link(c);flat.append((x,c,nm))
 fbx(os.path.join(OUT,'props.fbx'),[c for x,c,nm in flat])
 for x,c,nm in flat:
  bpy.data.objects.remove(c,do_unlink=True);x.name=nm
def in_root_space(root,grp):
# the character's skeletal mesh and animations are authored relative to its root actor: the root's own world transform (where it stands at the export frame, and where the path takes it) is what Sequencer's transform track supplies, so it must not also be baked into the FBX
 Rinv=root.matrix_world.inverted();saved=[]
 for o in grp:
  if o.parent is None or o.parent not in grp:
   saved.append((o,o.parent,o.matrix_parent_inverse.copy(),o.matrix_basis.copy()));w=Rinv@o.matrix_world;o.parent=None;o.matrix_basis=w
 bpy.context.view_layer.update();return saved
def restore_space(saved):
 for o,p,pi,mb in saved:o.parent=p;o.matrix_parent_inverse=pi;o.matrix_basis=mb
 bpy.context.view_layer.update()
for c in chars:
 grp=[c['rig']]+[x for x in c['rig'].children_recursive]+[x for x in c['root'].children_recursive if x.type=='MESH'];grp=list({o.name:o for o in grp}.values())
 ad=c['rig'].animation_data;saved_mute=[t.mute for t in ad.nla_tracks] if ad else []
 saved_space=in_root_space(c['root'],grp)
 fbx(os.path.join(OUT,'character_%s.fbx'%c['tag']),grp)
 # one animation FBX per clip
 for cl in {x['anim_file']:x for x in doc['characters'][chars.index(c)]['clips']}.values():
  act=bpy.data.actions.get(cl['action']);
  if act is None:continue
  for t in ad.nla_tracks:t.mute=True
  prev=ad.action;ad.action=act
  try:ad.action_slot=act.slots[0]
  except Exception:pass
  sc.frame_start=int(round(cl['action_start']));sc.frame_end=max(sc.frame_start+1,int(round(cl['action_end'])));fbx(os.path.join(OUT,cl['anim_file']+'.fbx'),grp,anim_=True)
  ad.action=prev
 for t,m in zip(ad.nla_tracks,saved_mute):t.mute=m
 restore_space(saved_space)
 sc.frame_start,sc.frame_end=FS,FE
problems=ub.validate(doc)
with open(os.path.join(OUT,NAME+'.ue.json'),'w',encoding='utf-8') as fh:json.dump(doc,fh)
print('UE_EXPORT',json.dumps(ub.summary(doc)),'problems',problems,'files',sorted(os.listdir(OUT)))
