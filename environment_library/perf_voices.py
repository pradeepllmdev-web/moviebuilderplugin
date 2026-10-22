"""Character voices for the performance engine: real speech from Piper neural text-to-speech, one distinct voice per character, cached as wav files.

    python perf_voices.py download             fetch the Piper models (pip install piper-tts first)
    python perf_voices.py catalogue            measure the pitch of candidate voices once (voices/catalogue.json)
    python perf_voices.py prepare films/ember_road.py      assign voices to the cast and synthesise every line (cached, parallel)

Pieces (pure Python + numpy except synth/catalogue, which need `pip install piper-tts` and the models in voices/*.onnx; Blender never needs Piper because it only reads the cache):
  assign(registry)  -> {character id: voice}    each character gets the free voice whose pitch is closest to its registry pitch (species range), reused never inside one film;
                       a voice is dict(model, speaker, f0, shift, rate): shift is the pitch ratio applied by resampling (the synthesis is slowed or sped by the same ratio so the length stays natural),
                       rate the personality speed (tired slower, hurried faster)
  key(voice,text,mood) / wav_path / duration(voice,text,mood) / load(voice,text,mood) -> samples   the cache the planner (line lengths) and the Blender player (audio) read
  prepare(film)     -> synthesises every missing line of a film with a process pool
Mood shapes the delivery: sad and tired are slower, joy and anger a little faster and louder."""
import hashlib,json,os,sys,wave
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
VOICE_DIR=H/'voices';CACHE=VOICE_DIR/'cache';CATALOGUE=VOICE_DIR/'catalogue.json';SR=22050
MOOD_RATE={'sad':1.12,'serious':1.0,'warm':1.0,'concern':1.04,'angry':.95,'joy':.96}
BASE_RATE=1.2       # a little slower than the model's default: clearer
SHIFT=(.93,1.09)    # more pitch shifting than this distorts the voice; the nearest voice is used instead
MOOD_GAIN={'sad':.8,'serious':.95,'warm':.95,'concern':.9,'angry':1.15,'joy':1.1}
POSTURE_RATE={'tired':1.12,'hunched':1.1,'proud':1.02,'neutral':1.0,'jaunty':.94,'tense':1.0,'angry':.95,'hurried':.88}
def models():return sorted(p.name[:-5] for p in VOICE_DIR.glob("*.onnx"))
def f0_estimate(x,sr=SR,lo=60,hi=420):
 """median fundamental frequency of the voiced frames of x (autocorrelation); None when nothing is voiced"""
 x=np.asarray(x,float);n=int(.04*sr);hop=int(.01*sr);out=[];lag0,lag1=int(sr/hi),int(sr/lo)
 if len(x)<n*2:return None
 gate=np.sqrt(np.mean(x**2))*.8
 for i in range(0,len(x)-n,hop):
  f=x[i:i+n]
  if np.sqrt(np.mean(f**2))<gate:continue
  f=f-f.mean();ac=np.correlate(f,f,'full')[n-1:]
  if ac[0]<=1e-9:continue
  seg=ac[lag0:lag1];k=int(np.argmax(seg))
  if seg[k]/ac[0]>.4:out.append(sr/(lag0+k))
 return float(np.median(out)) if out else None
def key(voice,text,mood='serious'):
 s='|'.join(str(v) for v in ('v4',voice['model'],voice['speaker'],round(voice.get('shift',1.),3),round(voice.get('rate',1.),3),mood,text))
 return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]
def wav_path(k):return CACHE/(k+'.wav')
def read_wav(p):
 with wave.open(str(p),'rb') as w:
  sr,nf=w.getframerate(),w.getnframes();x=np.frombuffer(w.readframes(nf),dtype='<i2').astype(float)/32768.
 return x,sr
def duration(voice,text,mood='serious'):
 """seconds of the cached line, or None when it has not been synthesised"""
 p=wav_path(key(voice,text,mood))
 if not p.exists():return None
 with wave.open(str(p),'rb') as w:return w.getnframes()/w.getframerate()
def load(voice,text,mood='serious'):
 p=wav_path(key(voice,text,mood))
 return read_wav(p) if p.exists() else None
# ---------------------------------------------------------------------------------------------------------------- choosing voices
def catalogue_voices():
 try:return json.loads(CATALOGUE.read_text())
 except (OSError,ValueError):return []
def assign(registry,catalogue=None):
 """{character id: voice} - closest free pitch first, extreme characters choose first; the same registry always gets the same voices"""
 cat=catalogue if catalogue is not None else catalogue_voices()
 if not cat:return {}
 want={i:registry.resolve(i) for i in registry.ids() if not registry.resolve(i).get('creature')};order=sorted(want,key=lambda i:-abs(np.log(want[i]['pitch']/150.)));used=set();out={}
 for i in order:
  L=want[i];tgt=L['pitch'];best=None
  for c in cat:
   if (c['model'],c['speaker']) in used:continue
   r=tgt/c['f0'];cost=abs(np.log(r))+(.5 if r<.7 or r>1.5 else 0)
   cost+=(-.45 if c['model'].endswith('high') else (.1 if 'vctk' in c['model'] else 0.))     # the high-quality models are the clearest+(.35*abs(np.log(r/np.clip(r,*SHIFT))) if True else 0.)
   if best is None or cost<best[0]:best=(cost,c,r)
  if best is None:break
  c=best[1];r=float(np.clip(best[2],*SHIFT));used.add((c['model'],c['speaker']))
  out[i]=dict(model=c['model'],speaker=c['speaker'],f0=c['f0'],shift=round(r,3),rate=round(POSTURE_RATE.get(L['posture'],1.0)*(1.0+.0*L['scale'][2]),3))
 return out
# ---------------------------------------------------------------------------------------------------------------- synthesis (needs piper)
_V={}
def _voice(model):
 if model not in _V:
  from piper import PiperVoice
  _V[model]=PiperVoice.load(str(VOICE_DIR/(model+'.onnx')))
 return _V[model]
def synth(voice,text,mood='serious'):
 """synthesise one line into the cache (no-op when present); returns the wav path"""
 k=key(voice,text,mood);p=wav_path(k)
 if p.exists():return p
 from piper import SynthesisConfig
 CACHE.mkdir(parents=True,exist_ok=True);v=_voice(voice['model']);r=voice.get('shift',1.)
 cfg=SynthesisConfig(speaker_id=int(voice['speaker']) if v.config.num_speakers>1 else None,length_scale=float(BASE_RATE*voice.get('rate',1.)*MOOD_RATE.get(mood,1.)*r),noise_scale=.6+(.1 if mood in('angry','joy') else 0),noise_w_scale=.8)
 chunks=[c.audio_float_array for c in v.synthesize(text,syn_config=cfg)]
 x=np.concatenate(chunks) if chunks else np.zeros(2000);sr=v.config.sample_rate
 if abs(r-1.)>.01:     # pitch: play the (r times longer) synthesis r times faster; length is back to natural, pitch and formants move with r
  n=int(len(x)/r);x=np.interp(np.linspace(0,len(x)-1,n),np.arange(len(x)),x)
 if sr!=SR:n=int(len(x)*SR/sr);x=np.interp(np.linspace(0,len(x)-1,n),np.arange(len(x)),x)
 i=np.nonzero(np.abs(x)>.01)[0]
 if len(i):x=x[max(0,i[0]-int(.03*SR)):i[-1]+int(.12*SR)]      # trim silence, keep a breath at the end
 x=clarity(x)
 pk=np.max(np.abs(x))+1e-9;x=x/pk*.85*min(1.1,MOOD_GAIN.get(mood,1.));x=np.clip(x,-1,1)
 tmp=str(p)+'.tmp'
 with wave.open(tmp,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
 os.replace(tmp,p);return p
def clarity(x,sr=SR):
 """speech clarity: high-pass at 80 Hz, a presence lift around 2.5-4 kHz, then a soft compressor so quiet syllables are not lost under the score"""
 n=len(x)
 if n<64:return x
 X=np.fft.rfft(x);f=np.fft.rfftfreq(n,1./sr);g=np.clip(f/90.,0,1)**2*(1+.8*np.exp(-((f-3200.)/1200.)**2)+.25*np.exp(-((f-6500.)/1500.)**2));x=np.fft.irfft(X*g,n)
 rms=np.sqrt(np.mean(x**2))+1e-9;x=x/rms*.1;return np.tanh(3.2*x)/3.2*10.
def _job(a):
 voice,text,mood=a;synth(voice,text,mood);return key(voice,text,mood)
def lines_of(film,voices):
 """[(voice, text, mood)] for every spoken line of a film (mood guessed like the planner does when a line has none)"""
 import dialogue as dg
 out=[]
 for sp in film['scenes']:
  for st in sp['steps']:
   for b in (st if isinstance(st,list) else [st]):
    if b.get('do')=='say' and b['who'] in voices:out.append((voices[b['who']],b['text'],b.get('mood') or dg.infer_mood(b['text'])))
 return out
def prepare(film,registry,workers=4,echo=True):
 """assign voices (stored into the registry records as 'voice') and synthesise every missing line; returns {id: voice}"""
 voices=assign(registry)
 for i,v in voices.items():registry.rec[i]['voice']=v
 todo=[l for l in lines_of(film,voices) if not wav_path(key(*l)).exists()];todo=list({key(*l):l for l in todo}.values())
 if echo:print('voices: %d characters, %d lines to synthesise (%d cached)'%(len(voices),len(todo),len(lines_of(film,voices))-len(todo)),flush=True)
 if todo:
  CACHE.mkdir(parents=True,exist_ok=True)
  if workers>1 and len(todo)>6:
   from concurrent.futures import ProcessPoolExecutor
   with ProcessPoolExecutor(workers) as ex:list(ex.map(_job,todo,chunksize=4))
  else:
   for l in todo:_job(l)
 return voices
MODEL_URLS={'en_US-ryan-high':'en/en_US/ryan/high','en_US-lessac-high':'en/en_US/lessac/high','en_US-libritts-high':'en/en_US/libritts/high','en_GB-cori-high':'en/en_GB/cori/high','en_US-hfc_female-medium':'en/en_US/hfc_female/medium','en_US-hfc_male-medium':'en/en_US/hfc_male/medium','en_US-libritts_r-medium':'en/en_US/libritts_r/medium','en_GB-vctk-medium':'en/en_GB/vctk/medium','en_US-ryan-medium':'en/en_US/ryan/medium','en_US-amy-medium':'en/en_US/amy/medium','en_GB-alan-medium':'en/en_GB/alan/medium','en_GB-jenny_dioco-medium':'en/en_GB/jenny_dioco/medium'}
def download_models(names=None):
 """fetch the Piper voice models (about 400 MB, rhasspy/piper-voices on Hugging Face) into voices/"""
 import urllib.request
 VOICE_DIR.mkdir(exist_ok=True)
 for n,path in MODEL_URLS.items():
  if names and n not in names:continue
  for ext in ('onnx','onnx.json'):
   dst=VOICE_DIR/('%s.%s'%(n,ext))
   if not dst.exists():urllib.request.urlretrieve('https://huggingface.co/rhasspy/piper-voices/resolve/main/%s/%s.%s'%(path,n,ext),str(dst))
# ---------------------------------------------------------------------------------------------------------------- catalogue
SAMPLE='The old clock keeps its own time, and nobody has ever argued with it twice.'
def build_catalogue(n_multi=80,echo=True):
 """measure the pitch of single-voice models and of the first speakers of the multi-speaker ones"""
 from piper import SynthesisConfig
 out=[]
 for name in models():
  v=_voice(name);n=v.config.num_speakers;sp=range(0,n,max(1,n//n_multi)) if n>1 else [0]
  for s in list(sp)[:n_multi]:
   cfg=SynthesisConfig(speaker_id=s if n>1 else None);x=np.concatenate([c.audio_float_array for c in v.synthesize(SAMPLE,syn_config=cfg)]);f=f0_estimate(x,v.config.sample_rate)
   if f:out.append(dict(model=name,speaker=int(s),f0=round(f,1)))
  if echo:print(name,len(out),flush=True)
 CATALOGUE.write_text(json.dumps(out,indent=0));return out
if __name__=='__main__':
 a=sys.argv[1:]
 if a and a[0]=='download':download_models()
 elif a and a[0]=='catalogue':build_catalogue()
 elif a and a[0]=='prepare':
  import perf_movie as pm
  film=pm.load_film(a[1]);reg=pm.registry_of(film);prepare(film,reg)
 else:print(__doc__)
