"""Final render of a whole movie from Unreal: PNG frames plus one audio track, through Movie Render Queue via the bridge (no mp4 is made).

    python unreal_render.py <movie_folder> [--out DIR] [--scenes 1,2] [--preset final|draft] [--size 1920x1080] [--first N] [--force] [--no-audio] [--bridge URL]

The scenes must already be in the editor (unreal_handoff.py). For every scene that was handed over, in movie order, the scene's Level Sequence is rendered to PNG; the frames are renamed into one continuous run
    <out>/frames/frame_000001.png ... frame_00NNNN.png
and the audio strips of every scene (as exported from Blender: file, start, volume) are mixed in Python into
    <out>/audio/scene_NN_<piece>.wav and <out>/audio/movie.wav        (16-bit stereo; frame N of the picture is at N/fps seconds of the audio)
<out>/render.json lists fps, size, frame count, the audio file and where every scene starts. --first N renders only the first N frames of every scene (a quick proof of the whole movie, audio cut to match). A render that stopped can be started again: finished scenes (listed in render.json) are skipped unless --force.
Default --out: <export root>/<movie>/final. The picture can be assembled with any tool from frames + movie.wav at the fps in render.json."""
import json,os,re,shutil,sys,wave
from pathlib import Path
import ue_common as uc,unreal_handoff as uh,unreal_send as us
def pick_sequence(assets,name):
 """the newest Level Sequence of a scene among the editor's assets (LS_<name>, LS_<name>_2, ...), or None"""
 best=None
 for a in assets:
  n=a['path'].split('/')[-1].split('.')[0];m=re.fullmatch(r'LS_%s(?:_(\d+))?'%re.escape(name),n)
  if m:
   k=int(m.group(1) or 1)
   if best is None or k>best[0]:best=(k,a['path'].split('.')[0])
 return best[1] if best else None
def frame_files(folder,ext='png'):
 """rendered frames of a folder in frame order (the number after the last dot)"""
 def num(p):
  m=re.search(r'(\d+)\.%s$'%ext,p.name,re.I);return int(m.group(1)) if m else -1
 return sorted((p for p in Path(folder).glob('*.'+ext) if num(p)>=0),key=num)
def plan_scenes(docs,fps_default=24,first=None):
 """[{name, frames, first}] with the movie-wide number of each scene's first frame (1-based) and its first audio sample position in seconds"""
 out=[];cum=0
 for d in docs:
  n=d['frame_end']-d['frame_start']+1;n=min(n,first) if first else n;out.append(dict(name=d['scene'],frames=n,first=cum+1,start_s=cum/float(d.get('fps') or fps_default)));cum+=n
 return out
# ---------------------------------------------------------------------------------------------------------- audio
def read_wav(path):
 """(rate, float32 array (n, 2) in -1..1) of a PCM wav (8, 16, 24 or 32 bit; mono is duplicated to both channels)"""
 import numpy as np
 with wave.open(str(path)) as w:
  n,rate,width,ch=w.getnframes(),w.getframerate(),w.getsampwidth(),w.getnchannels();raw=w.readframes(n)
 if width==1:a=(np.frombuffer(raw,dtype=np.uint8).astype(np.float32)-128.)/128.
 elif width==2:a=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.
 elif width==3:
  b=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3).astype(np.int32);v=b[:,0]|(b[:,1]<<8)|(b[:,2]<<16);v=np.where(v>=1<<23,v-(1<<24),v);a=v.astype(np.float32)/(1<<23)
 elif width==4:a=np.frombuffer(raw,dtype='<i4').astype(np.float32)/(1<<31)
 else:raise ValueError('unsupported wav sample width %d'%width)
 a=a[:len(a)//ch*ch].reshape(-1,ch)
 return rate,(np.repeat(a,2,axis=1) if ch==1 else a[:,:2])
def write_wav(path,arr,rate):
 """16-bit stereo wav from a float32 (n, 2) array"""
 import numpy as np
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 with wave.open(str(path),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(arr,-1,1)*32767.).astype('<i2').tobytes())
def resample(a,src,dst):
 import numpy as np
 if src==dst or len(a)==0:return a
 n=int(round(len(a)*dst/float(src)));x=np.linspace(0,len(a)-1,n);i=np.arange(len(a))
 return np.stack([np.interp(x,i,a[:,c]) for c in range(2)],axis=1).astype(np.float32)
def mix_scene(strips,fps,frame_start,n_samples,rate,read=read_wav):
 """one scene's sound as float32 (n_samples, 2): every strip {file, start (timeline frame), volume} placed at (start - frame_start)/fps seconds, resampled to `rate`, summed and clipped; a strip that cannot be read is skipped and named in the second result"""
 import numpy as np
 out=np.zeros((n_samples,2),dtype=np.float32);bad=[]
 for s in strips:
  try:r,a=read(s['file'])
  except Exception as e:bad.append('%s: %s'%(s.get('name') or s.get('file'),type(e).__name__));continue
  a=resample(a,r,rate)*float(s.get('volume',1.));at=int(round((s.get('start',frame_start)-frame_start)/float(fps)*rate))
  if at<0:a=a[-at:];at=0
  m=min(len(a),n_samples-at)
  if m>0:out[at:at+m]+=a[:m]
 return np.clip(out,-1,1),bad
def audio_rate(docs,read=read_wav,default=44100):
 """the highest sample rate among the scenes' audio (so nothing is downsampled), 44100 at the least"""
 best=default
 for d in docs:
  for s in d.get('audio',[]):
   try:
    with wave.open(s['file']) as w:best=max(best,w.getframerate())
   except (OSError,wave.Error,EOFError):pass
 return best
# ---------------------------------------------------------------------------------------------------------- the render
def render_movie(movie_dir,bridge,out=None,only=None,preset='final',size=(1920,1080),force=False,audio=True,progress=print,render=None,first=None):
 """render every handed-over scene to numbered PNG frames and mix the audio; returns the manifest (also written to render.json). render(seq, raw_dir, preset, size, frames) -> None is injectable for tests."""
 movie_dir=Path(movie_dir);report=json.loads((movie_dir/'report.json').read_text(encoding='utf-8'));ok,_=us.scenes_to_send(report,only);root=us.export_root()/movie_dir.name;out=Path(out) if out else root/'final'
 docs=[];missing=[]
 for index,piece,blend,status,audit in ok:
  name=uc.scene_name(movie_dir.name,index,piece);j=root/name/(name+'.ue.json')
  if not j.exists():missing.append('%s (not exported)'%name);continue
  d=json.loads(j.read_text(encoding='utf-8'));d['_piece']=piece;d['_index']=index;docs.append(d)
 if render is None:
  assets=bridge.get('/assets?path=/Game/Movie')['assets']
  for d in docs:
   d['_seq']=pick_sequence(assets,d['scene'])
   if not d['_seq']:missing.append('%s (no Level Sequence in the editor)'%d['scene'])
 if missing:raise us.BridgeError('nothing rendered: run unreal_handoff.py first, these scenes are not ready: '+'; '.join(missing))
 if not docs:raise us.BridgeError('no scene of this movie to render')
 fps=docs[0]['fps']
 if any(d['fps']!=fps for d in docs):raise us.BridgeError('scenes have different frame rates: %s'%sorted({d['fps'] for d in docs}))
 plan=plan_scenes(docs,first=first);frames_dir=out/'frames';raw_root=out/'_raw';manifest_path=out/'render.json';out.mkdir(parents=True,exist_ok=True)
 try:old=json.loads(manifest_path.read_text(encoding='utf-8'))
 except (OSError,ValueError):old={}
 same=old.get('preset')==preset and old.get('size')==list(size) and old.get('first')==first and [s['name'] for s in old.get('scenes',[])]==[p['name'] for p in plan]
 done={s['name'] for s in old.get('scenes',[]) if s.get('rendered')} if same and not force else set()
 if not done and frames_dir.exists():shutil.rmtree(frames_dir)
 frames_dir.mkdir(parents=True,exist_ok=True)
 manifest=dict(movie=movie_dir.name,fps=fps,size=list(size),preset=preset,first=first,frames=sum(p['frames'] for p in plan),frame_pattern='frames/frame_%06d.png',audio=None,scenes=[dict(p,piece=d['_piece'],rendered=p['name'] in done) for p,d in zip(plan,docs)])
 def save():manifest_path.write_text(json.dumps(manifest,indent=1),encoding='utf-8')
 save()
 for p,d,m in zip(plan,docs,manifest['scenes']):
  if p['name'] in done:progress('%s already rendered'%p['name']);continue
  raw=raw_root/p['name']
  if raw.exists():shutil.rmtree(raw)
  raw.mkdir(parents=True);progress('Rendering %s (%d frames, %s)'%(p['name'],p['frames'],preset))
  if render:render(d.get('_seq'),raw,preset,size,p['frames'])
  else:
   params={'sequence_path':d['_seq'],'preset':preset,'format':'png','resolution':list(size),'output_dir':str(raw).replace(chr(92),'/')}
   if p['frames']<d['frame_end']-d['frame_start']+1:params.update(start_frame=d['frame_start'],end_frame=d['frame_start']+p['frames'])
   bridge.command('render_movie',params);us.wait_render(bridge,timeout=6*3600)
  got=frame_files(raw)
  if len(got)!=p['frames']:raise us.BridgeError('%s: Unreal wrote %d frames, expected %d (kept in %s)'%(p['name'],len(got),p['frames'],raw))
  for i,f in enumerate(got):os.replace(f,frames_dir/('frame_%06d.png'%(p['first']+i)))
  shutil.rmtree(raw,ignore_errors=True);m['rendered']=True;save()
 shutil.rmtree(raw_root,ignore_errors=True)
 if audio:
  rate=audio_rate(docs);total=0;apath=out/'audio'/'movie.wav';apath.parent.mkdir(parents=True,exist_ok=True);skipped=[]
  with wave.open(str(apath),'wb') as mw:
   mw.setnchannels(2);mw.setsampwidth(2);mw.setframerate(rate);cum=0
   for p,d in zip(plan,docs):
    n=int(round((cum+p['frames'])/float(fps)*rate))-int(round(cum/float(fps)*rate));a,bad=mix_scene(d.get('audio',[]),fps,d['frame_start'],n,rate)
    skipped+=['%s: %s'%(p['name'],b) for b in bad];write_wav(out/'audio'/('scene_%02d_%s.wav'%(d['_index'],d['_piece'])),a,rate)
    import numpy as np
    mw.writeframes((np.clip(a,-1,1)*32767.).astype('<i2').tobytes());cum+=p['frames']
  manifest['audio']='audio/movie.wav';manifest['audio_rate']=rate
  if skipped:manifest['audio_skipped']=skipped
  save()
 return manifest
def main(argv):
 a=list(argv)
 def val(f,cast=str,default=None):
  if f in a:i=a.index(f);v=cast(a[i+1]);del a[i:i+2];return v
  return default
 bridge_url=val('--bridge');out=val('--out');only=val('--scenes',lambda x:{int(y) for y in x.split(',')});preset=val('--preset',str,'final');size=val('--size',lambda x:tuple(int(y) for y in x.lower().split('x')),(1920,1080))
 first=val('--first',int);force='--force' in a;audio='--no-audio' not in a;a=[x for x in a if x not in('--force','--no-audio')]
 if not a:print(__doc__);return 2
 m=render_movie(a[0],us.Bridge(bridge_url),out,only,preset,size,force,audio,progress=lambda s:print(s,flush=True),first=first)
 print('Rendered %d frames at %d fps to %s%s'%(m['frames'],m['fps'],m['frame_pattern'],(', audio '+m['audio']) if m['audio'] else ''));return 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
