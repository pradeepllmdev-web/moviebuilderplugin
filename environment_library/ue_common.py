"""Unreal bridge, shared pure-Python part (no bpy, no unreal): coordinate conversion, key reduction, asset lookup, validation.

Conventions (Blender -> Unreal): metres -> centimetres; Blender is right-handed Z-up, Unreal is left-handed Z-up, so Y is negated:
  location  (x, y, z) m        -> (100 x, -100 y, 100 z) cm
  rotation  Blender XYZ euler  -> Unreal rotator (roll = rx, pitch = -ry, yaw = -rz) in degrees
  scale     unchanged
These follow the common FBX-importer convention and are NOT yet verified inside Unreal; keep the numbers in ue_* functions so one place fixes them if a check shows a flip."""
import json,math,re
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
def resolve_asset(key,asset_map,default_dir,scene):
 """Unreal asset path for a placeholder key: the mapped one if present, else the imported proxy FBX mesh"""
 m=asset_map.get('assets',{})
 if key in m:return m[key],True
 return '%s/%s/SM_%s'%(default_dir.rstrip('/'),scene,key),False
def resolve_clip(clip,char_tag,asset_map,default_dir):
 m=asset_map.get('animations',{})
 if clip in m:return m[clip],True
 return '%s/%s/A_%s'%(default_dir.rstrip('/'),char_tag,clip),False
def validate(doc):
 """problems in an exported scene document (empty list when it is consistent)"""
 p=[]
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
def load(path):return json.load(open(path,encoding='utf-8'))
