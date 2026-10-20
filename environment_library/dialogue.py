"""Dialogue for the movie flow (pure Python + numpy, no Blender): parse a script out of story text, time it, voice it, and derive the mouth timing from the voice.

Script formats found in a story paragraph (screenplay lines, or prose with a speech verb):
    Leo (warm): "We made it."          Leo: "We made it."
    Mara says, "Not yet," and Leo replies, "Then we keep going."
parse(text) -> {'lines': [{'speaker','mood','text'}...], 'setting': 'campfire'|'hall'}; at least two lines make a conversation.
Voices: every line is voiced by a provider, by default a formant synthesiser (stable pitch per speaker, mood changes pitch and energy). Real recordings override it: put line_<k>.wav (k = 0-based index of the line in the
scene, mono or stereo PCM16) in the folder named by the environment variable VOICE_DIR (or pass voice_dir) and that file is used instead, its length sets the line's length, and the syllable (mouth) timing is taken from the
file's own energy envelope, so recordings from a text-to-speech service or an actor lip-sync without any other change. register_voice_provider(name, fn) adds a provider (fn(line, index) -> (samples, sample_rate) or None)."""
import hashlib,os,re,wave
import numpy as np
SR=22050
MOODS=('serious','angry','warm','concern','sad','joy')
SPEECH_VERBS=r'says|asks|replies|answers|shouts|whispers|laughs|sighs|cries|murmurs|calls|declares'
SCREENPLAY=re.compile(r'^[ \t]*([A-Z][A-Za-z]{1,15})(?:[ \t]*\(([A-Za-z]+)\))?[ \t]*:[ \t]*["“]?(.+?)["”]?[ \t]*$',re.M)
PROSE=re.compile(r'([A-Z][a-z]{1,15})[ \t]+(?:%s)[ \t]*(?:[a-z]+[ \t]+)?[,:]?[ \t]*["“]([^"”]+)["”]'%SPEECH_VERBS)
def infer_mood(text,verb_hint=''):
 t=text.strip()
 if re.search(r'whisper|murmur',verb_hint):return 'concern'
 if re.search(r'laugh',verb_hint):return 'joy'
 if t.endswith('!'):return 'joy' if re.search(r'\b(yes|made it|we did|thank|wonderful|great|love|won|saved|free)\b',t,re.I) else 'angry'
 if t.endswith('?'):return 'concern'
 if re.search(r'\b(sorry|lost|alone|gone|miss|afraid)\b',t,re.I):return 'sad'
 return 'serious'
def setting_of(text):
 if re.search(r'\b(hall|council|table|throne|chamber)\b',text,re.I):return 'hall'
 return 'campfire'
def parse(text):
 lines=[]
 for m in SCREENPLAY.finditer(text):
  sp,mood,t=m.group(1),(m.group(2) or '').lower(),m.group(3).strip().strip('"')
  if not t:continue
  lines.append(dict(speaker=sp,mood=mood if mood in MOODS else infer_mood(t),text=t))
 if len(lines)<2:
  lines=[]
  for m in PROSE.finditer(text):
   verb=re.search(SPEECH_VERBS,m.group(0));lines.append(dict(speaker=m.group(1),mood=infer_mood(m.group(2),verb.group(0) if verb else ''),text=m.group(2).strip()))
 return dict(lines=lines,setting=setting_of(text))
def cast(lines):
 """speakers in order of first appearance"""
 out=[]
 for l in lines:
  if l['speaker'] not in out:out.append(l['speaker'])
 return out
def syllables(text):
 out=[]
 for w in re.findall(r"[A-Za-z']+",text):
  for g in (re.findall(r'[aeiouy]+',w.lower()) or ['a']):out.append(g[0] if g[0] in 'aeiou' else 'e')
 return out
def pitch_of(name):
 h=int(hashlib.sha1(name.lower().encode()).hexdigest()[:6],16);return 88.+(h%1000)/1000.*130.
def schedule(lines,t0=2.5,gap=.5,line_seconds=None):
 """timed lines: each gets t0/t1 and its syllable list; line_seconds[k] (real recording length) overrides the estimate"""
 t=t0;out=[]
 for k,l in enumerate(lines):
  syl=syllables(l['text']);dur=(line_seconds[k] if line_seconds and line_seconds.get(k) else max(1.6,len(syl)*.2+.5))
  out.append(dict(k=k,speaker=l['speaker'],mood=l['mood'],text=l['text'],t0=t,t1=t+dur,syl=syl,dur=dur));t+=dur+gap
 return out
FORM={'a':(800,1200),'e':(500,1900),'i':(350,2300),'o':(500,900),'u':(350,700)}
def synth_line(line,sr=SR,seed=0):
 """formant-style voice for one scheduled line; returns (samples, syllable_times) with times relative to the start of the line"""
 n=int(line['dur']*sr);out=np.zeros(n);rng=np.random.default_rng(seed+line['k']);f0=pitch_of(line['speaker'])*(1.0+.06*(line['mood'] in('angry','joy'))-.05*(line['mood']=='sad'))
 syl=line['syl'];d=(line['dur']-.6)/max(1,len(syl));times=[]
 for j,v in enumerate(syl):
  tc=.3+(j+.5)*d;times.append((tc,d,v));m=int(max(.08,d*.85)*sr);k=np.arange(m)/sr;pitch=f0*(1+.06*np.sin(2*np.pi*5.5*k)+.04*(line['mood']=='angry'));ph=2*np.pi*np.cumsum(pitch)/sr
  f1,f2=FORM[v];x=np.sin(ph)+.5*np.sin(2*ph)+.3*np.sin(3*ph);x=x*(.6+.4*np.sin(ph*(f1/f0)/6.))+.15*rng.standard_normal(m)*(v in 'ei');env=np.sin(np.pi*np.arange(m)/m)**.7
  i=int((tc-d*.4)*sr)
  if 0<=i<n:
   ln=min(m,n-i);out[i:i+ln]+=x[:ln]*env[:ln]*.5
 return out,times
def load_wav(path):
 with wave.open(str(path),'rb') as w:
  ch,sw,sr,nf=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes();raw=w.readframes(nf)
 if sw!=2:raise ValueError('only 16-bit PCM wav files are supported')
 x=np.frombuffer(raw,dtype='<i2').astype(float)/32768.
 if ch>1:x=x.reshape(-1,ch).mean(axis=1)
 return x,sr
def resample(x,sr,to=SR):
 if sr==to or len(x)==0:return x
 n=int(len(x)*to/sr);return np.interp(np.linspace(0,len(x)-1,n),np.arange(len(x)),x)
def envelope_syllables(x,sr,vowels,thresh=.12):
 """(time, spacing, vowel) for each syllable placed at equal shares of the recording's energy (the voiced part), so the mouth follows where the speech actually is"""
 if len(x)==0 or not vowels:return []
 win=max(1,int(.01*sr));e=np.convolve(np.abs(x),np.ones(win)/win,mode='same');voiced=e>thresh*e.max();idx=np.nonzero(voiced)[0]
 if len(idx)==0:return []
 a,b=idx[0],idx[-1];seg=e[a:b+1];cum=np.cumsum(seg);cum=cum/cum[-1];n=len(vowels);times=[]
 for j in range(n):
  q=(j+.5)/n;i=int(np.searchsorted(cum,q));times.append((a+i)/sr)
 d=max(.05,(b-a)/sr/n);return [(t,d,v) for t,v in zip(times,vowels)]
PROVIDERS={}
def register_voice_provider(name,fn):PROVIDERS[name]=fn
def voice_for(line,voice_dir=None,sr=SR):
 """(samples at SR, syllable times relative to the line start, real_length or None) for one scheduled line"""
 vd=voice_dir or os.environ.get('VOICE_DIR')
 for name,fn in PROVIDERS.items():
  got=fn(line,line['k'])
  if got is not None:x,r=got;x=resample(np.asarray(x,float),r,sr);return x,envelope_syllables(x,sr,line['syl']),len(x)/sr
 if vd:
  p=os.path.join(vd,'line_%d.wav'%line['k'])
  if os.path.exists(p):x,r=load_wav(p);x=resample(x,r,sr);return x,envelope_syllables(x,sr,line['syl']),len(x)/sr
 x,t=synth_line(line,sr);return x,t,None
def real_lengths(lines,voice_dir=None):
 """seconds of each recorded line that exists (so the schedule can use them before the scene is built)"""
 vd=voice_dir or os.environ.get('VOICE_DIR');out={}
 if vd:
  for k in range(len(lines)):
   p=os.path.join(vd,'line_%d.wav'%k)
   if os.path.exists(p):
    try:x,r=load_wav(p);out[k]=len(x)/r+.4
    except (ValueError,OSError):pass
 return out
MOOD_KEYS={'serious':dict(Concern=.25),'angry':dict(Frown=.5,ActingBrowL=.5,ActingBrowR=.5),'warm':dict(WarmSmile=.5),'concern':dict(Concern=.6,ActingBrowL=.4,ActingBrowR=.4),'sad':dict(ConcernStrong=.5,Frown=.25),'joy':dict(WarmSmile=.85,ActingBrowL=.25,ActingBrowR=.25)}
VOWEL_KEYS={'a':(.85,0,.2),'e':(.5,0,.8),'i':(.4,0,.9),'o':(.65,.8,0),'u':(.5,.9,0)}   # JawOpen, Round, Wide
SPEAK_CLIP={'serious':'talk','angry':'argue','warm':'talk','concern':'talk','sad':'shrug','joy':'laugh'}
LISTEN_CLIP={'serious':'nod','angry':None,'warm':'nod','concern':'think','sad':None,'joy':'laugh'}
