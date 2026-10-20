"""Unreal bridge, shared pure-Python part (no bpy, no unreal): coordinate conversion, key reduction, asset lookup, validation.

Conventions (Blender -> Unreal): metres -> centimetres; Blender is right-handed Z-up, Unreal is left-handed Z-up, so Y is negated:
  location  (x, y, z) m        -> (100 x, -100 y, 100 z) cm
  rotation  Blender XYZ euler  -> Unreal rotator (roll = rx, pitch = -ry, yaw = -rz) in degrees
  scale     unchanged
These follow the common FBX-importer convention and are NOT yet verified inside Unreal; keep the numbers in ue_* functions so one place fixes them if a check shows a flip."""
import json,math,re
FORMAT_VERSION=2   # the scene package (<scene>.ue.json + FBX + audio files) is the contract between Blender and Unreal or any other tool; 2 added look and M_-prefixed prop meshes (a package without the field is version 1)
def ue_loc(v):return [100.0*v[0],-100.0*v[1],100.0*v[2]]
def ue_rot_deg(e_rad):return [math.degrees(e_rad[0]),-math.degrees(e_rad[1]),-math.degrees(e_rad[2])]
def ue_scale(s):return [float(s[0]),float(s[1]),float(s[2])]
def asset_key(name):
 """'Boulder.003' -> 'Boulder'; 'CrateStack12' -> 'CrateStack'; names are the placeholder ids the asset map is keyed by"""
 base=name.split('.')[0];return re.sub(r'\d+$','',base) or base
def unwrap_deg(seq):
 """unwrap a list of angles in degrees so there are no 360-degree jumps between consecutive keys"""
 out=[];prev=None
 for a in seq:
  if prev is None:out.append(a)
  else:
   d=a-prev;d-=360.0*round(d/360.0);out.append(out[-1]+d)
  prev=a
 return out
def reduce_keys(frames,values,tol):
 """drop keys whose value is within tol of the straight line between the kept neighbours (Douglas-Peucker on the value curve); always keeps the first and last key. values: list of equal-length lists"""
 n=len(frames)
 if n<=2:return list(range(n))
 keep=[0,n-1];stack=[(0,n-1)]
 while stack:
  a,b=stack.pop();worst=-1;wd=0.
  for i in range(a+1,b):
   u=(frames[i]-frames[a])/max(1e-9,frames[b]-frames[a]);d=max(abs(values[i][c]-(values[a][c]+(values[b][c]-values[a][c])*u)) for c in range(len(values[i])))
   if d>wd:wd=d;worst=i
  if wd>tol and worst>0:keep.append(worst);stack.append((a,worst));stack.append((worst,b))
 return sorted(set(keep))
def _scene_matches(pattern,scene):
 """a scene entry of the asset map is addressed by the full scene name, a glob ('movie_*_swamp') or just the piece ('swamp')"""
 import fnmatch
 return pattern==scene or fnmatch.fnmatch(scene,pattern) or scene.endswith('_'+pattern)
def scene_section(asset_map,scene,section):
 """the layers of one map section that apply to a scene, most specific first: [scene-specific entries..., global entries]"""
 out=[]
 for pat,body in (asset_map.get('scenes') or {}).items():
  if not pat.startswith('_') and isinstance(body,dict) and _scene_matches(pat,scene) and isinstance(body.get(section),dict):out.append(body[section])
 if isinstance(asset_map.get(section),dict):out.append(asset_map[section])
 return out
def swap_entry(name,asset_map,scene):
 """the environment-swap entry for an object, or None. Order of precedence: this scene's props[exact name], this scene's assets[placeholder key], the global props[name], the global assets[key].
 An entry is an Unreal asset path or {'asset': path, 'scale': uniform scale, 'fit': false to keep the asset at its own size, 'offset': [x,y,z] cm, 'rotation': [roll,pitch,yaw]}; the result is always the dict form."""
 key=asset_key(name);hit=None
 scoped=[(pat,body) for pat,body in (asset_map.get('scenes') or {}).items() if not pat.startswith('_') and isinstance(body,dict) and _scene_matches(pat,scene)]
 layers=[b.get('props') for _,b in scoped]+[b.get('assets') for _,b in scoped]+[asset_map.get('props'),asset_map.get('assets')]
 for i,layer in enumerate(layers):
  if not isinstance(layer,dict):continue
  is_props=i<len(scoped) or i==2*len(scoped)
  for k in ((name,key) if is_props else (key,)):
   if k in layer:hit=layer[k];break
  if hit is not None:break
 if hit is None:return None
 return dict(hit) if isinstance(hit,dict) and hit.get('asset') else ({'asset':hit} if isinstance(hit,str) and hit else None)
def swap_names(asset_map,scene):
 """every object name / placeholder key the map swaps in this scene (sorted): the exporter keeps those objects out of the joined environment mesh so each can be replaced on its own; it is part of the export cache key"""
 out=set()
 for sec in ('props','assets'):
  for layer in scene_section(asset_map,scene,sec):out.update(k for k,v in layer.items() if not k.startswith('_') and (isinstance(v,str) or (isinstance(v,dict) and v.get('asset'))))
 return sorted(out)
def swaps_object(name,asset_map,scene):return swap_entry(name,asset_map,scene) is not None
def environment_swap(asset_map,scene):
 """a real Unreal environment for the whole scene: scenes.<scene>.environment = path or {'asset': path, 'offset': [x,y,z], 'rotation': [r,p,y], 'scale': s, 'keep_proxy': true to also show the low-poly one}"""
 for pat,body in (asset_map.get('scenes') or {}).items():
  if pat.startswith('_') or not isinstance(body,dict) or not _scene_matches(pat,scene):continue
  e=body.get('environment')
  if isinstance(e,str) and e:return {'asset':e}
  if isinstance(e,dict) and e.get('asset'):return dict(e)
 return None
def look_overrides(asset_map,scene):
 """scenes.<scene>.look = {'isolate': false, 'sun_scale': 1.5, 'sky_scale': 0.5, 'sky_color': [r,g,b], 'fill_scale': 1.0, 'exposure': 1.0 (pins the exposure bias, no measuring), 'exposure_target': 0.2 (mean brightness the measurement aims at; default .32, a dark scene wants less)}"""
 out={}
 for pat,body in (asset_map.get('scenes') or {}).items():
  if not pat.startswith('_') and isinstance(body,dict) and _scene_matches(pat,scene) and isinstance(body.get('look'),dict):out.update(body['look'])
 return out
def resolve_asset(key,asset_map,default_dir,scene,name=None):
 """Unreal asset path for a placeholder key: the mapped one if present (see swap_entry), else the imported proxy FBX mesh"""
 e=swap_entry(name or key,asset_map,scene)
 if e:return e['asset'],True
 return '%s/%s/SM_%s'%(default_dir.rstrip('/'),scene,key),False
def resolve_clip(clip,char_tag,asset_map,default_dir,scene=None):
 for m in (scene_section(asset_map,scene,'animations') if scene else [asset_map.get('animations') or {}]):
  if clip in m:return m[clip],True
 return '%s/%s/A_%s'%(default_dir.rstrip('/'),char_tag,clip),False
def validate(doc):
 """problems in an exported scene document (empty list when it is consistent)"""
 p=[]
 v=doc.get('format_version',1)
 if not isinstance(v,int) or v>FORMAT_VERSION or v<1:p.append('scene package format %r is not supported (this importer reads up to %d): update the importer or re-export'%(v,FORMAT_VERSION))
 fs,fe=doc['frame_start'],doc['frame_end']
 if fe<=fs:p.append('empty frame range')
 ids=set()
 for a in doc['actors']:
  if a['id'] in ids:p.append('duplicate actor id %s'%a['id'])
  ids.add(a['id'])
  k=a.get('keys')
  if k:
   n=len(k['frames'])
   if not (n==len(k['loc'])==len(k['rot'])==len(k['scale'])):p.append('actor %s: key arrays differ in length'%a['name'])
   if n and (min(k['frames'])<fs or max(k['frames'])>fe):p.append('actor %s: keys outside the frame range'%a['name'])
   for row in k['loc']+k['rot']+k['scale']:
    if any((not isinstance(x,(int,float))) or math.isnan(x) or math.isinf(x) for x in row):p.append('actor %s: non-finite key'%a['name']);break
 for c in doc['characters']:
  if c['root'] not in ids:p.append('character %s: unknown root actor'%c['name'])
  for s in c['clips']:
   if s['end']<s['start']:p.append('character %s: clip %s ends before it starts'%(c['name'],s['clip']))
 cams={a['id'] for a in doc['actors'] if a['role']=='camera'}
 last=fs-1
 for cut in doc['cuts']:
  if cut['camera'] not in cams:p.append('cut %s: unknown camera'%cut['name'])
  if cut['start']<=last-0 and cut['start']<last:p.append('cut %s overlaps the previous one'%cut['name'])
  if cut['end']<cut['start']:p.append('cut %s ends before it starts'%cut['name'])
  last=cut['end']
 if doc['cuts'] and doc['cuts'][-1]['end']<fe-1:p.append('the last cut does not reach the end of the scene')
 return p
def summary(doc):
 roles={}
 for a in doc['actors']:roles[a['role']]=roles.get(a['role'],0)+1
 return dict(scene=doc['scene'],frames=doc['frame_end']-doc['frame_start']+1,fps=doc['fps'],actors=roles,characters=len(doc['characters']),clips=sum(len(c['clips']) for c in doc['characters']),cuts=len(doc['cuts']),audio=len(doc['audio']))
def validate_scene_path(path,root):
 """the only files the Unreal bridge will read: <root>/**/<name>.ue.json, resolved (no .., no links out of the root). Returns the resolved Path or raises ValueError."""
 from pathlib import Path
 p=Path(str(path)).resolve();r=Path(str(root)).resolve()
 if not p.name.endswith('.ue.json'):raise ValueError('scene file must end in .ue.json')
 if r != p and r not in p.parents:raise ValueError('scene file is outside the export root')
 if not p.is_file():raise ValueError('scene file does not exist')
 return p
def load(path):
 d=json.load(open(path,encoding='utf-8'))
 if isinstance(d,dict) and str(path).endswith('.ue.json'):
  import os;d['_dir']=os.path.dirname(os.path.abspath(str(path)))   # where the FBX files of this scene are
 return d

SYNONYMS={'Boulder':('rock','boulder','stone'),'Rock':('rock','boulder','stone'),'StoneDoor':('door','gate'),'Statue':('statue','sculpture','monument'),'StatueBase':('plinth','pedestal','statue'),'Crate':('crate','box','chest'),'CrateA':('crate','box'),'CrateB':('crate','box'),
 'Barrel':('barrel','cask'),'Plank':('plank','board','wood'),'House':('house','building','cottage'),'Tree':('tree',),'Trunk':('tree','trunk'),'Pillar':('column','pillar'),'Cliff':('cliff','rock'),'Stalactite':('stalactite','rock'),'Boat':('boat','canoe'),
 'Coral':('coral',),'Spire':('rock','spire','cliff'),'Tower':('tower',),'Anvil':('anvil',),'Torch':('torch','lamp'),'Cloud':('cloud',),'Mountain':('mountain','rock')}
def pick_catalog_asset(key,dims_cm,catalog,max_ratio=4.0):
  """closest catalog mesh for a placeholder: by name/category words, then by size. dims_cm = the placeholder's bounding box (x,y,z in cm). Returns (path, uniform_scale) or None.
  Size is compared on the sorted dimensions; the uniform scale makes the asset's geometric-mean size equal the placeholder's. Anything more than max_ratio off in shape is rejected."""
  words=SYNONYMS.get(key) or (key.lower(),)
  items=[a for a in catalog.get('assets',[]) if a.get('mesh_type')=='static' and any(w in (a.get('category','')+' '+a.get('name','')+' '+' '.join(a.get('tags',[]))).lower() for w in words)]
  if not items or not dims_cm or min(dims_cm)<=0:return None
  want=sorted(abs(x) for x in dims_cm);best=None
  for a in items:
   have=sorted(abs(x) for x in a.get('dimensions_cm',[0,0,0]))
   if min(have)<=0:continue
   ratios=[w/h for w,h in zip(want,have)];spread=max(ratios)/min(ratios)
   if spread>max_ratio:continue
   score=spread
   if best is None or score<best[0]:best=(score,a,(ratios[0]*ratios[1]*ratios[2])**(1/3.))
  return (best[1]['path'],best[2]) if best else None
def constant_scale(scale_keys,tol=1e-3):
  """True when an actor's scale never changes (so it can be replaced by a fitted uniform scale)"""
  return all(max(abs(a-b) for a,b in zip(row,scale_keys[0]))<tol for row in scale_keys)

def ue_look_rot_deg(forward_blender):
 """Unreal rotator [roll, pitch, yaw] (degrees) for an object that looks along a Blender world direction (cameras and lights look along their local -Z in Blender, along +X in Unreal), no roll"""
 x,y,z=forward_blender;yaw=math.degrees(math.atan2(-y,x));pitch=math.degrees(math.atan2(z,math.hypot(x,y)));return [0.0,pitch,yaw]
POINT_CD_PER_W=.05      # Blender point/spot watts -> Unreal candela (a rough visual match; exposure differs per project)
SUN_LUX_PER_STRENGTH=3.0
SCENE_SPACING_CM=100000.   # 1 km between scenes
def scene_offset(scene):
 """where a scene sits in the shared level: scene <movie>_<NN>_<piece> is placed NN kilometres along +Y so the scenes of one film never overlap and none sits on the level's own origin (the level keeps its sky sphere, water zone and post process there)"""
 m=re.search(r'_(\d+)_[A-Za-z]',scene or '');n=int(m.group(1)) if m else 1
 return [0.,SCENE_SPACING_CM*n,0.]

FILL_MIN_LUX=6.0       # a night world is nearly black but its Blender picture is still readable: the fill never drops below this (each of the two lights)
FILL_LUX_PER_SKY=4.0   # Blender's flat ambient is reproduced by two shadowless fill lights (one from each side) of the world colour, because a sky light alone left the scene dark
SKY_INTENSITY_PER_LUMA=2.0   # Blender world colour*strength (luma) -> Unreal sky light intensity
def luma(c):return .2126*c[0]+.7152*c[1]+.0722*c[2]
def derive_look(look,overrides=None):
 """per-scene lighting from what Blender had: its sun (exported as a light actor; here only the switches around it) and its world colour/strength (a sky light of the same colour). The level's shared Env_Sun then does not light the scene
 (isolate: the scene's meshes and lights use lighting channel 1 only). overrides come from scenes.<scene>.look in the asset map."""
 look=look or {};ov=overrides or {};col=list(ov.get('sky_color') or look.get('world_color') or [.3,.35,.4])[:3];st=float(look.get('world_strength',1.) or 0.)
 sky=dict(color=col,intensity=round(max(.02,min(4.,luma(col)*max(st,0.)*SKY_INTENSITY_PER_LUMA*float(ov.get('sky_scale',1.)))),3))
 sun=look.get('sun');sun=dict(sun,lux_scale=float(ov.get('sun_scale',1.))) if sun else None
 return dict(isolate=bool(ov.get('isolate',True)),sky=sky,sun=sun,fill_lux=round(max(FILL_MIN_LUX,sky['intensity']*FILL_LUX_PER_SKY)*float(ov.get('fill_scale',1.)),3))
EXPOSURE_TOLERANCE=.15   # stops: a measured error smaller than this is left alone
def exposure_step(current,measured,target=.32):
 """new exposure bias (stops) after measuring the mean brightness of frames rendered at `current`: display brightness follows light^(1/2.2) and the correction is damped to 0.8, the bias stays within [-2.5, 4]"""
 import math
 d=.8*2.2*math.log2(target/max(measured,.02));new=max(-2.5,min(4.,current+d))
 return round(current if abs(new-current)<EXPOSURE_TOLERANCE else new,2)
def proxy_mesh_paths(scene,mesh,proxy_dir='/Game/Proxy'):
 """candidate asset paths for the proxy mesh imported from props.fbx for a Blender mesh: the export prefixes mesh objects with 'M_' so no material of the same name can push Unreal into renaming them; older exports are found by their plain name plus the digit Unreal appended"""
 n=mesh.replace('.','_');base='%s/%s'%(proxy_dir.rstrip('/'),scene)
 return ['%s/M_%s'%(base,n)]+['%s/%s%s'%(base,n,s) for s in ('','1','2','3')]
def scene_name(movie,index,piece):return '%s_%02d_%s'%(movie,index,piece or 'shot')
def set_swap(asset_map,name,asset,scene=None,**opts):
 """record (or with asset=None remove) an environment swap in the asset map dict: scene=None -> global props[name]; scene='swamp' -> scenes.swamp.props[name]. Everything else in the map is kept."""
 m=asset_map.setdefault('scenes',{}).setdefault(scene,{}) if scene else asset_map
 layer=m.setdefault('props',{})
 if asset is None:layer.pop(name,None)
 else:layer[name]=dict(asset=asset,**{k:v for k,v in opts.items() if v is not None}) if opts and any(v is not None for v in opts.values()) else asset
 return asset_map
def set_environment(asset_map,scene,asset,**opts):
 body=asset_map.setdefault('scenes',{}).setdefault(scene,{})
 if asset is None:body.pop('environment',None)
 else:body['environment']=dict(asset=asset,**{k:v for k,v in opts.items() if v is not None}) if any(v is not None for v in opts.values()) else asset
 return asset_map

def file_sha(path):
 import hashlib
 h=hashlib.sha1()
 try:
  with open(path,'rb') as f:
   for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 except OSError:return 'missing'
 return h.hexdigest()
def registry_path():
 """where the imported characters are remembered (by content hash), next to the exports: one registry for every movie"""
 import os
 return os.path.join(os.environ.get('MOVIEBUILDER_EXPORT_ROOT') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'scenes','unreal_export'),'character_registry.json')
def load_registry():
 try:return json.load(open(registry_path(),encoding='utf-8'))
 except (OSError,ValueError):return {}
def save_registry(reg):
 import os
 p=registry_path()
 try:
  os.makedirs(os.path.dirname(p),exist_ok=True);t=p+'.tmp'
  with open(t,'w',encoding='utf-8') as f:json.dump(reg,f)
  os.replace(t,p)
 except OSError:pass
