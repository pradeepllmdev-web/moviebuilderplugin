"""Pre-send check of an exported scene (no Blender, no Unreal): finds what would arrive in Unreal missing or silent before anything is sent.

    python unreal_check.py <scene>.ue.json [more.ue.json ...]

check_scene(doc, folder) returns a list of issues {level, code, msg}. level 'error' = the scene will be visibly wrong in Unreal (a mesh, a character or an animation file is missing); 'warn' = probably not intended (silent scene,
no cuts, tiny mesh). unreal_send.handoff skips scenes with errors unless told to send anyway, and prints every issue in the summary."""
import json,os,sys,wave
H=os.path.dirname(os.path.abspath(__file__))
def _fbx_names(path):
 """the file's raw bytes, searched for object names (binary and ASCII FBX both store them as plain text)"""
 try:
  with open(path,'rb') as f:return f.read()
 except OSError:return None
def _wav_info(path):
 """(seconds, peak 0..1) of a 16-bit PCM wav, or None when it cannot be read that way"""
 try:
  with wave.open(path) as w:
   n,rate,width,ch=w.getnframes(),w.getframerate(),w.getsampwidth(),w.getnchannels();sec=n/float(rate or 1)
   if width!=2:return sec,None
   import numpy as np
   a=np.frombuffer(w.readframes(n),dtype='<i2');return sec,(float(abs(a).max())/32768. if a.size else 0.)
 except (OSError,wave.Error,EOFError,ImportError,ValueError):return None
def issue(level,code,msg):return dict(level=level,code=code,msg=msg)
def check_scene(doc,folder,audio_check=True):
 out=[];folder=str(folder);scene=doc.get('scene','?')
 def need(fname,what):
  p=os.path.join(folder,fname)
  if not os.path.exists(p):out.append(issue('error','file_missing','%s: %s is missing (%s)'%(scene,fname,what)));return None
  return p
 actors=doc.get('actors',[])
 if not [a for a in actors if a['role']=='camera']:out.append(issue('error','no_camera','no camera in the scene: Unreal has nothing to shoot with'))
 elif not doc.get('cuts'):out.append(issue('warn','no_cuts','no camera cuts (no timeline markers bound to cameras): the sequence has no shot camera'))
 if (doc.get('environment') or {}).get('static_meshes'):
  p=need('environment.fbx','the static scene')
  if p is None:pass
  elif not doc['environment'].get('mesh'):out.append(issue('error','env_unnamed','environment.fbx was exported without a mesh name'))
 props=[a for a in actors if a['role'] in ('prop','effect')]
 pdata=None
 if props and any(a.get('parts') for a in props):
  p=need('props.fbx','the animated props');pdata=_fbx_names(p) if p else None
 gone=[]
 for a in props:
  parts=a.get('parts') or []
  if not parts:gone.append(a['name']);continue
  for q in parts:
   if pdata is not None and ('M_'+q['mesh']).encode() not in pdata and q['mesh'].encode() not in pdata:out.append(issue('error','mesh_missing','%s: mesh %s is not in props.fbx'%(a['name'],q['mesh'])))
   if max(q.get('dims_cm') or [0])<.05:out.append(issue('warn','mesh_tiny','%s: mesh %s is smaller than 0.05 cm'%(a['name'],q['mesh'])))
 firsts=[q['mesh'] for a in props for q in (a.get('parts') or [])][:1]
 if pdata is not None and firsts and ('M_'+firsts[0]).encode() not in pdata:out.append(issue('warn','legacy_mesh_names','props.fbx predates the M_ mesh prefix: Unreal may rename meshes whose material has the same name (SparkFly1 .. SparkFly4 style); re-export'))
 if gone:out.append(issue('error','prop_no_mesh','%d animated object(s) have no mesh and will not show: %s'%(len(gone),_names(gone))))
 for c in doc.get('characters',[]):
  tag=c.get('name') or ''
  if not tag or c.get('root') not in {a['id'] for a in actors}:out.append(issue('error','character_unresolved','character %r has no root actor in the scene'%tag));continue
  sk=need(c.get('skeletal_mesh') or 'character_%s.fbx'%tag,'skeletal mesh of %s'%tag)
  if sk and os.path.getsize(sk)<2048:out.append(issue('error','character_empty','%s: the skeletal mesh file holds no geometry'%tag))
  if not c.get('clips'):out.append(issue('warn','character_static','%s has no animation clips: it stands in its rest pose'%tag))
  for f in sorted({s.get('anim_file') for s in c.get('clips',[]) if s.get('anim_file')}):need(f+'.fbx','animation %s of %s'%(f,tag))
 audio=doc.get('audio') or []
 if not audio:out.append(issue('warn','silent_scene','%s has no audio strips: the scene is silent'%scene))
 else:
  secs=(doc['frame_end']-doc['frame_start']+1)/float(doc.get('fps') or 24);longest=0.;peak=0.;unknown=False
  for s in audio:
   f=s.get('file') or ''
   if not f or not os.path.exists(f):out.append(issue('error','audio_missing','audio strip %r: file %r does not exist'%(s.get('name'),f)));continue
   info=_wav_info(f) if audio_check and f.lower().endswith('.wav') else None
   if info is None:unknown=True;continue
   longest=max(longest,info[0]);peak=max(peak,info[1] or 0.) if info[1] is not None else peak
  if audio_check and not unknown and longest and peak<1e-4:out.append(issue('warn','silent_audio','%s: all audio files are silent'%scene))
  elif audio_check and longest and longest<.5*secs:out.append(issue('warn','audio_short','%s: audio runs %.0f s of a %.0f s scene'%(scene,longest,secs)))
 return out
def _names(names,n=6):return ', '.join(names[:n])+(' (+%d more)'%(len(names)-n) if len(names)>n else '')
def blocking(issues):return [i for i in issues if i['level']=='error']
def format_issues(issues):return ['%s %s'%('ERROR' if i['level']=='error' else 'warn ',i['msg']) for i in issues]
if __name__=='__main__':
 bad=0
 for p in sys.argv[1:]:
  doc=json.load(open(p,encoding='utf-8'));iss=check_scene(doc,os.path.dirname(os.path.abspath(p)));bad+=len(blocking(iss))
  print('%s: %s'%(doc['scene'],'ok' if not iss else '%d issue(s)'%len(iss)))
  for l in format_issues(iss):print('  '+l)
 sys.exit(1 if bad else 0)
