"""Synthesised sound for the performance engine (pure numpy): ambience beds, a small generative score, footsteps and sound effects. No Blender, no files; perf_scene writes the arrays as wav tracks.

    amb=perf_audio.ambience('wind',N,SR,rng)        wind | fire | sea | crowd | rain | night | hall | cave | market | none
    mus=perf_audio.music('calm',N,SR,seed)          calm | warm | tense | sad | bright | mystery | epic | comic | none     (a pad, a bass and a plucked melody on a scale; reproducible from the seed)
    x=perf_audio.sfx('door',SR,rng)                 knock, door, thud, clang, bell, gong, crash, scrape, splash, thunder, chime, step, clap
    track=perf_audio.mix_events(N,SR,[(t,x,gain)...])
Everything returns float arrays in -1..1 before the caller scales the track."""
import numpy as np
PI=np.pi
def _noise(rng,n,k=8):return np.convolve(rng.standard_normal(n),np.ones(k)/k,mode='same')
def _env(n,a=.005,d=8.,sr=22050):t=np.arange(n)/sr;return np.minimum(t/a,1)*np.exp(-t*d)
def ambience(kind,N,SR,rng):
 t=np.arange(N)/SR
 if kind=='none':return np.zeros(N)
 if kind=='wind':return _noise(rng,N,700)*(.6+.4*np.sin(t*.22+rng.uniform(0,6)))*2.2   # a low, slow swell, not hiss
 if kind=='fire':
  x=_noise(rng,N,40)*(.6+.4*np.sin(t*7.3));
  for _ in range(int(N/SR*3)):
   j=int(rng.uniform(0,max(1,N-400)));x[j:j+300]+=rng.standard_normal(min(300,N-j))*np.exp(-np.arange(min(300,N-j))/60.)*.8
  return x
 if kind=='sea':return _noise(rng,N,120)*(.55+.45*np.sin(t*.6+1))+_noise(rng,N,20)*.12*(np.sin(t*.6+1)>.6)
 if kind=='crowd':
  x=_noise(rng,N,18)*.5
  for f in (180,230,310):x+=np.sin(2*PI*f*t*(1+.03*np.sin(t*1.3+f)))*.04*(np.sin(t*.9+f)>0)
  return x
 if kind=='rain':return _noise(rng,N,3)*.6+_noise(rng,N,40)*.3
 if kind=='night':
  x=_noise(rng,N,900)*.5
  for k in range(int(N/SR*.6)):
   j=int(rng.uniform(0,max(1,N-3000)));f=rng.uniform(3000,4500);m=min(2000,N-j);x[j:j+m]+=np.sin(2*PI*f*np.arange(m)/SR)*np.sin(np.arange(m)/m*PI*8)**2*.05
  return x
 if kind=='hall':return _noise(rng,N,900)*.8+np.sin(2*PI*55*t)*.05
 if kind=='cave':return _noise(rng,N,900)*.6+np.sin(2*PI*45*t)*.06+(rng.random(N)<2e-5)*np.exp(-np.arange(N)%4000/500.)*.3
 if kind=='market':
  x=ambience('crowd',N,SR,rng)*.9
  for _ in range(int(N/SR*.5)):
   j=int(rng.uniform(0,max(1,N-6000)));m=min(5000,N-j);x[j:j+m]+=np.sin(2*PI*rng.uniform(500,900)*np.arange(m)/SR)*_env(m,.01,6,SR)*.1
  return x
 raise ValueError('unknown ambience %r'%kind)
AMBIENCES=('wind','fire','sea','crowd','rain','night','hall','cave','market','none')
SCALES={'major':[0,2,4,7,9],'minor':[0,2,3,7,8],'dorian':[0,2,3,5,7,9,10],'lydian':[0,2,4,6,7,9,11]}
MOODS=dict(calm=('major',90,.5),warm=('major',100,.6),tense=('minor',72,.5),sad=('minor',60,.45),bright=('major',124,.7),mystery=('dorian',66,.5),epic=('minor',96,.8),comic=('lydian',132,.6))
MUSIC=tuple(MOODS)+('none',)
def _freq(root,deg,scale,octave=0):
 s=SCALES[scale];o,i=divmod(deg,len(s));return root*2**((s[i]+12*(o+octave))/12.)
def music(mood,N,SR,seed=1):
 if mood=='none':return np.zeros(N)
 scale,bpm,vol=MOODS[mood];rng=np.random.default_rng(seed);root=float(rng.choice([110,98,87.3,123.5]));beat=60./bpm;x=np.zeros(N+SR*3);t=np.arange(int(SR*beat*4+SR))/SR
 prog=[0,3,4,0] if scale in('major','lydian') else [0,5,3,4];nbar=int(N/SR/(beat*4))+1
 for b in range(nbar):
  d=prog[b%4];t0=int(b*beat*4*SR)
  for k,deg in enumerate((d,d+2,d+4)):
   f=_freq(root,deg,scale);pad=np.sin(2*PI*f*t)*np.minimum(t/.4,1)*np.exp(-t*.5)*.22;n=min(len(pad),len(x)-t0);x[t0:t0+n]+=pad[:n]
  fb=_freq(root,d,scale,-1);bass=np.sin(2*PI*fb*t[:int(SR*beat*2)])*np.exp(-t[:int(SR*beat*2)]*1.6)*.35
  for h in (0,2):
   i0=int((b*4+h)*beat*SR);n=min(len(bass),len(x)-i0);x[i0:i0+n]+=bass[:n]
 deg=int(rng.integers(0,5));step=beat/2 if mood in('bright','comic','epic') else beat
 nn=int(N/SR/step)
 for i in range(nn):
  if rng.random()<(.7 if mood not in('sad','calm') else .5):
   deg=int(np.clip(deg+rng.choice([-2,-1,-1,0,1,1,2]),-2,9));f=_freq(root,deg,scale,1);tt=np.arange(int(SR*.9))/SR;pl=(np.sin(2*PI*f*tt)+.3*np.sin(4*PI*f*tt))*_env(len(tt),.006,4.5,SR)*.16;i0=int(i*step*SR);n=min(len(pl),len(x)-i0)
   if n>0:x[i0:i0+n]+=pl[:n]
 if mood=='tense':
  for i in range(int(N/SR/beat)):
   i0=int(i*beat*SR);tk=np.sin(2*PI*900*np.arange(600)/SR)*np.exp(-np.arange(600)/90.)*.08;n=min(600,len(x)-i0);x[i0:i0+n]+=tk[:n]
 x=x[:N];fade=np.minimum(np.arange(N)/(SR*1.5),1)*np.minimum((N-np.arange(N))/(SR*3.),1);return x*fade*vol
def sfx(name,SR,rng):
 def T(d):return np.arange(int(d*SR))/SR
 if name=='knock':
  x=np.zeros(int(.9*SR))
  for k in range(3):
   i=int(k*.22*SR);tt=T(.12);x[i:i+len(tt)]+=np.sin(2*PI*140*tt)*np.exp(-tt*45)*.9+_noise(rng,len(tt),4)*np.exp(-tt*60)*.4
  return x
 if name=='door':tt=T(.9);return _noise(rng,len(tt),30)*np.exp(-tt*5)*.6+np.sin(2*PI*80*tt)*np.exp(-tt*8)*.5
 if name=='thud':tt=T(.35);return np.sin(2*PI*70*tt)*np.exp(-tt*14)+_noise(rng,len(tt),12)*np.exp(-tt*25)*.5
 if name=='step':tt=T(.14);return _noise(rng,len(tt),28)*np.exp(-tt*34)*.9+np.sin(2*PI*70*tt)*np.exp(-tt*45)*.3   # a soft thump, not a click
 if name=='clang':tt=T(1.2);return sum(np.sin(2*PI*f*tt)*a for f,a in ((520,1),(1310,.6),(2150,.4),(3300,.25)))*np.exp(-tt*5)*.5
 if name=='bell':tt=T(2.5);return sum(np.sin(2*PI*f*tt)*a*np.exp(-tt*d) for f,a,d in ((440,1,1.6),(880,.5,2.2),(1320,.3,3),(1850,.2,4)))*.5
 if name=='gong':tt=T(3.5);return sum(np.sin(2*PI*f*tt*(1+.002*np.sin(tt*3)))*a*np.exp(-tt*d) for f,a,d in ((110,1,.9),(165,.7,1.1),(230,.5,1.4),(330,.3,1.8)))*.6
 if name=='crash':tt=T(1.4);return _noise(rng,len(tt),6)*np.exp(-tt*4)*.8+np.sin(2*PI*60*tt)*np.exp(-tt*9)*.5
 if name=='scrape':tt=T(1.2);return _noise(rng,len(tt),3)*np.sin(np.minimum(tt/1.2,1)*PI)*.35
 if name=='splash':tt=T(1.0);return _noise(rng,len(tt),5)*np.exp(-tt*5)*.7
 if name=='thunder':tt=T(3.0);return _noise(rng,len(tt),90)*np.exp(-tt*1.1)*(1+.5*np.sin(tt*14))*.9
 if name=='chime':tt=T(1.6);return sum(np.sin(2*PI*f*tt)*np.exp(-tt*d) for f,d in ((1046,3),(1318,3.4),(1568,4)))*.3
 if name=='clap':tt=T(.25);return _noise(rng,len(tt),3)*np.exp(-tt*28)*.8
 if name=='sting':tt=T(1.4);return (sum(np.sin(2*PI*f*tt)*a for f,a in ((98,1),(104,.9),(147,.6),(233,.4)))*np.exp(-tt*2.6)*(1-np.exp(-tt*60)))*.45     # a low, dissonant stab: the story turns
 if name=='whoosh':tt=T(.7);return _noise(rng,len(tt),14)*np.sin(np.minimum(tt/.7,1)*PI)**2*.55
 if name=='hum':tt=T(2.4);return (np.sin(2*PI*110*tt)+.5*np.sin(2*PI*220.7*tt)+.25*np.sin(2*PI*331*tt))*np.sin(np.minimum(tt/2.4,1)*PI)*.18     # a warm lantern or beacon tone
 if name=='creak':tt=T(.9);return np.sin(2*PI*(260+90*np.sin(tt*9))*tt)*np.sin(np.minimum(tt/.9,1)*PI)*.22+_noise(rng,len(tt),8)*.08
 if name=='oink':tt=T(.55);return ((np.sign(np.sin(2*PI*(210+60*np.sin(tt*11))*tt)))*.5+_noise(rng,len(tt),12)*.2)*np.sin(np.minimum(tt/.55,1)*PI)**.6*.5
 if name=='moo':tt=T(1.6);f=150-45*tt/1.6+8*np.sin(tt*30);return (np.sin(2*PI*np.cumsum(f)/SR)+.5*np.sin(4*PI*np.cumsum(f)/SR))*np.sin(np.minimum(tt/1.6,1)*PI)**.5*.4
 if name=='baa':tt=T(1.0);f=380+60*np.sin(tt*34);return (np.sin(2*PI*np.cumsum(f)/SR)+.6*np.sin(6*PI*np.cumsum(f)/SR))*np.sin(np.minimum(tt/1.0,1)*PI)**.7*.32
 if name=='neigh':tt=T(1.2);f=420+380*np.sin(np.minimum(tt/1.2,1)*PI)-180*tt;return (np.sin(2*PI*np.cumsum(f)/SR)+.5*np.sin(4*PI*np.cumsum(f)/SR)+_noise(rng,len(tt),10)*.2)*np.sin(np.minimum(tt/1.2,1)*PI)**.5*.35
 if name=='bark':tt=T(.35);return (_noise(rng,len(tt),6)*.6+np.sin(2*PI*(330-250*tt)*tt)*.6)*np.exp(-tt*11)*.7
 if name=='roar':tt=T(2.2);return (_noise(rng,len(tt),50)*.7+np.sin(2*PI*(70+30*np.sin(tt*9))*tt)*.8)*np.sin(np.minimum(tt/2.2,1)*PI)**.6*.7
 if name=='chomp':tt=T(.5);return _noise(rng,len(tt),10)*(np.sin(tt*34)**2)*np.exp(-tt*3)*.5
 raise ValueError('unknown sound effect %r'%name)
SFX=('knock','door','thud','step','clang','bell','gong','crash','scrape','splash','thunder','chime','clap','sting','whoosh','hum','creak','oink','moo','baa','neigh','bark','roar','chomp')
def mix_events(N,SR,events):
 """events: (time seconds, samples, gain) -> one array"""
 out=np.zeros(N+SR*4)
 for t,x,g in events:
  i=int(t*SR)
  if 0<=i<N:n=min(len(x),len(out)-i);out[i:i+n]+=x[:n]*g
 return out[:N]
def footstep_events(steps,SR,rng,ground='dirt'):
 """steps: (time, who, foot, size) -> events; heavier characters step louder and lower, the ground colours the sound"""
 out=[];base=step_wave=sfx('step',SR,rng)
 for t,who,foot,size in steps:
  g=.35+.2*min(2,size);x=base*(1.0 if ground!='stone' else 1.25)
  if size>1.15:x=np.convolve(x,np.ones(3)/3,mode='same')*1.3
  out.append((t,np.roll(x,int(rng.integers(0,30))),g*(.8+.4*rng.random())))
 return out

def duck_mask(voice,SR,depth=.7,hold=.3,smooth=.15):
 """gain curve (1 = untouched) that dips by `depth` while the voices speak: the envelope of the summed voices, held for `hold` s and smoothed over `smooth` s, so music and ambience make room for every line"""
 e=np.abs(np.asarray(voice,float));k=max(1,int(.03*SR));e=np.convolve(e,np.ones(k)/k,mode='same');m=np.clip(e/(.02*max(1e-6,np.percentile(e,99)+1e-9)*1.0+1e-9),0,1)
 m=(np.convolve(m,np.ones(int(hold*SR))/int(hold*SR),mode='same')>.05).astype(float);k=max(1,int(smooth*SR));m=np.convolve(m,np.ones(k)/k,mode='same')
 return 1.-depth*np.clip(m,0,1)
