"""Film score for the performance engine: a theme per film, motifs per character, instruments that fit the place, cues that follow the action, music that gives way to speech.

    notes,programs,bpm=perf_score.compose(plan, theme, mood, location_preset, time, seed, spec_cues)     pure Python: MIDI-style notes (seconds) from the compiled plan
    x=perf_score.render(plan, theme, ...)                                                           numpy samples through FluidSynth + SoundFont (cached by the notes); None without the tools

What makes it follow the film instead of being a loop:
 * THEME (per film, in the film module): root note, mode, tempo, the main motif (degree, beats) pairs, an instrument palette. The melody of every scene is the SAME motif, varied (transposed to the chord, inverted, in sequence, diminished), so the whole film sounds like one piece.
 * Character motifs (cast record 'motif': a list of scale degrees) are played on the lead the first time that character speaks in the scene.
 * The place picks the lead instrument (accordion in a market, flute in a clearing, horn in ruins, vibraphone in a cave ...), the time of day the register (night lower and softer, dawn brighter).
 * Intensity (0..1) per bar comes from the plan: running, falling, startles, pushing, crashes and thunder raise it, sad lines lower it, the mood sets the base.
 * Speech wins: bars with a line keep only a soft pad and sparse harp, the melody waits for the gaps.
 * Events become hits: crash/thunder (timpani and a low stab), a startle (string stinger), cheering and laughing (a rising glockenspiel run), a fall (descending notes), taking/giving (celesta).
 * Last bar resolves on the tonic and thins out."""
import hashlib,json,math
import numpy as np
SCALES={'major':[0,2,4,5,7,9,11],'minor':[0,2,3,5,7,8,10],'dorian':[0,2,3,5,7,9,10],'lydian':[0,2,4,6,7,9,11],'mixolydian':[0,2,4,5,7,9,10]}
MOODS={   # base intensity, tempo factor, mode override (None = theme mode), melody density
 'calm':dict(base=.35,tempo=.85,mode=None,dens=.5),'warm':dict(base=.45,tempo=.95,mode=None,dens=.6),'tense':dict(base=.55,tempo=1.05,mode='minor',dens=.4),'sad':dict(base=.3,tempo=.7,mode='minor',dens=.4),
 'bright':dict(base=.65,tempo=1.15,mode='major',dens=.8),'mystery':dict(base=.4,tempo=.8,mode='dorian',dens=.4),'epic':dict(base=.8,tempo=1.05,mode='minor',dens=.7),'comic':dict(base=.6,tempo=1.2,mode='lydian',dens=.8),'none':dict(base=0.,tempo=1.,mode=None,dens=0.)}
PROGRESSIONS={'major':[[0,3,4,0],[0,5,3,4],[0,4,5,3],[0,3,0,4]],'minor':[[0,5,2,6],[0,3,6,4],[0,6,5,4],[0,2,5,0]],'dorian':[[0,3,0,6],[0,6,3,0],[0,2,6,3]],'lydian':[[0,1,0,4],[0,4,1,5],[0,1,4,0]],'mixolydian':[[0,6,3,0],[0,4,6,3]]}
PLACE_LEAD={'market':21,'harbor':21,'village_square':71,'hall':19,'room':8,'workshop':8,'cave':11,'ruins':60,'courtyard':60,'forest_clearing':73,'campfire_night':24,'meadow':73,'hilltop':40}
PALETTE=dict(pad=48,bass=43,pluck=46,lead=73,hit=47,sparkle=9,stinger=45,celesta=8)
def hash_unit(s):return (int(hashlib.sha1(s.encode()).hexdigest()[:8],16)%10000)/10000.
def pitch_of(theme,mode,degree,octave=0):
 sc=SCALES[mode];o,i=divmod(degree,7);return int(theme.get('root',57)+sc[i]+12*(o+octave))
def vary(motif,k):
 """the main motif [(degree, beats)] varied: 0 as is, 1 inverted, 2 in sequence (up a third), 3 diminished (half the lengths)"""
 if k%4==1:return [(-d,b) for d,b in motif]
 if k%4==2:return [(d+2,b) for d,b in motif]
 if k%4==3:return [(d,max(.25,b/2)) for d,b in motif]
 return list(motif)
# small bands (General MIDI programs): pad, bass, pluck (the figure), lead (the motif), counter-line; arp = note length of the figure in beats; pattern = eighth-note accents of the figure; perc = rhythm style
BANDS={'folk':dict(pad=21,bass=32,pluck=24,lead=40,counter=71,arp=.5,pattern=[1,0,1,1,0,1,1,0],perc='oompah',oompah=True),
 'cozy':dict(pad=0,bass=32,pluck=46,lead=73,counter=42,arp=.5,pattern=[1,1,0,1,1,0,1,0],perc='brush'),
 'orchestral':dict(pad=48,bass=43,pluck=45,lead=60,counter=42,arp=.5,pattern=[1,0,0,1,0,1,0,0],perc='epic'),
 'whimsy':dict(pad=89,bass=58,pluck=12,lead=71,counter=105,arp=.5,pattern=[1,0,1,0,1,1,0,1],perc='comic',hi=True),
 'night':dict(pad=89,bass=43,pluck=8,lead=11,counter=42,arp=1.,pattern=[1,0,0,0,1,0,0,0],perc='heartbeat'),
 'piano':dict(pad=0,bass=32,pluck=0,lead=40,counter=42,arp=1.,pattern=[1,0,1,0,1,0,1,0],perc=None)}
PATTERNS=[[1,0,1,1,0,1,1,0],[1,1,0,1,1,0,1,0],[1,0,0,1,0,1,0,0],[1,0,1,0,1,1,0,1],[1,1,1,0,1,0,1,1],[1,0,0,0,1,0,0,1],[0,1,1,0,0,1,1,0],[1,0,1,0,0,1,0,1]]
def pick_pattern(seed,band,b=0):
 """a different figure for every scene (and a change at every eighth bar), so no two scenes plink the same rhythm"""
 return PATTERNS[int(hash_unit('pat'+str(seed)+band+str(b//8))*len(PATTERNS))%len(PATTERNS)]
ALT_BANDS={'calm':['cozy','folk','piano'],'warm':['cozy','folk','whimsy'],'bright':['folk','whimsy','cozy'],'comic':['whimsy','folk'],'mystery':['night','orchestral','piano'],'sad':['piano','night','cozy'],'tense':['orchestral','night'],'epic':['orchestral','folk']}
def scene_root(theme,seed):
 return theme.get('root',57)+[-4,-2,0,2,3,5][int(hash_unit('key'+str(seed))*6)%6]
def pick_band(mood,place,time,seed):
 """the band of a scene: the mood offers a few, the scene's own seed picks one (a market scene leans folk, a room cozy), so neighbouring scenes sound different"""
 r=hash_unit('band'+str(seed));opts=list(ALT_BANDS.get(mood,['cozy','folk']))
 lean={'market':'folk','harbor':'folk','village_square':'folk','courtyard':'folk','room':'cozy','hall':'cozy','workshop':'cozy','meadow':'cozy','hilltop':'orchestral'}.get(place)
 if time=='night' and 'night' not in opts:opts.append('night')
 if lean in BANDS and r<.4:return lean if (lean in opts or mood in ('calm','warm','bright')) else opts[int(r*10)%len(opts)]
 return opts[int(r*len(opts)*2.5)%len(opts)]
def perc_bar(style,a,beat,lv,sv,b,mood):
 """drum-channel hits (General MIDI: 36 kick, 38 snare, 39 clap, 42 closed hat, 41/45/47 toms, 76 wood block) for one bar"""
 out=[];g=lambda base,k=22:int((base+k*lv)*sv)
 def h(t,pitch,vel):out.append(dict(t=a+t*beat,dur=.1,pitch=pitch,vel=max(1,vel),ch=9))
 if style=='oompah':
  for k in (0,2):h(k,36,g(52))
  for k in (1,3):h(k,39,g(40))
  for k in range(8):h(k/2,42,g(22,10)) if k%2 else None
 elif style=='brush':
  for k in range(4):h(k,42,g(26,14))
  h(1,38,g(26,10));h(3,38,g(24,10));h(0,36,g(40))
 elif style=='epic':
  h(0,36,g(70,24));h(2,36,g(56,20));h(1.5,45,g(44,20));h(3,47,g(48,24))
  if b%4==3:
   for k in range(6):h(2.5+k*.25,38,g(38+k*4,10))
 elif style=='comic':
  for k in (0,2):h(k,36,g(50))
  for k in (1,3):h(k,76,g(44));h(k+.5,77,g(32))
 elif style=='heartbeat':
  h(0,41,g(54,16));h(.5,41,g(40,12))
  for k in range(4):h(k+.75,75,g(18,8))
 return out
def compose(plan,theme,mood='calm',place=None,time='day',seed='',cues=None,arc=None):
 m=MOODS.get(mood,MOODS['calm'])
 if mood=='none':return [],{},90.
 mode=m['mode'] or theme.get('mode','major');theme=dict(theme,root=scene_root(theme,seed));pal=dict(PALETTE,**theme.get('palette',{}));pal['lead']=PLACE_LEAD.get(place,pal['lead']) if theme.get('place_leads',True) else pal['lead']
 bpm=theme.get('tempo',90)*m['tempo']*(.88 if time=='night' else (1.05 if time=='dawn' else 1.))*(.92+.16*hash_unit('tempo'+str(seed)));beat=60./bpm;bar=beat*4;secs=plan.seconds;nbar=int(math.ceil(secs/bar))+1
 lowered=-12 if time in('night','dusk') else 0
 speech=[(L['t0']-.2,L['t1']+.3) for L in plan.lines];sad=[(L['t0'],L['t1']) for L in plan.lines if L['mood']=='sad']
 def in_speech(a,b):return any(a<e and b>s for s,e in speech)
 hot=[(e['t0'],e['t1']) for e in plan.events if (e['kind']=='go' and e.get('gait')=='run') or (e['kind']=='act' and e.get('clip') in('fall','startle','jump','kick','hit','punch','getup')) or e['kind']=='push']
 hits=[(t,nm) for (t,nm,who,g) in plan.sfx if nm in('crash','thunder','gong')]
 rnd=np.random.default_rng(int(hash_unit(str(seed)+mood)*1e6))
 prog=PROGRESSIONS[mode][int(hash_unit('p'+str(seed))*len(PROGRESSIONS[mode]))%len(PROGRESSIONS[mode])]
 arc=.5 if arc is None else float(arc);base=m['base']+(arc-.5)*.4;cur=base;I=[]
 for b in range(nbar):
  a,e=b*bar,(b+1)*bar;lv=base
  if any(s<e and t>a for s,t in hot) or any(a<=t<e for t,_ in hits):lv+=.28
  if any(s<e and t>a for s,t in sad):lv-=.12
  if cues:
   for t,mm in cues:
    if t<=a and mm in MOODS:lv=MOODS[mm]['base']+(lv-base)
  I.append(min(1.,max(.12,lv)))
 notes=[];motif=theme.get('motif',[(0,1),(2,.5),(4,.5),(2,1),(1,1)]);phrase=0
 band=pick_band(mood,place,time,seed);pc=BANDS[band]   # a different small band for each kind of scene, the same motif in all of them
 for b in range(nbar):
  a=b*bar;e=a+bar;lv=I[b];sp=in_speech(a,e);d=prog[b%len(prog)];last=b>=nbar-2
  if last:d=0
  tri=[pitch_of(theme,mode,d+k,0)+lowered for k in (0,2,4)];root=pitch_of(theme,mode,d,-1)+lowered;fifth=pitch_of(theme,mode,d+4,-1)+lowered
  fade=.55 if (b==0) else (.5 if last else 1.);sv=(.6 if sp else 1.)    # under speech everything stays, only quieter: the music keeps its groove and the voices keep the front
  if (b%2==0 or last) and (lv>.3 or b==0):    # the pad breathes: a swell every second bar, never a drone
   for p_ in tri:notes.append(dict(t=a,dur=bar*(1.9 if not last else 2.4),pitch=p_,vel=int((22+26*lv)*sv*fade),ch=0))
  step=pc['arp']*beat if lv>.5 else beat;idx=0;t=a;pat=pick_pattern(seed,band,b)
  breakdown=(b%8==7 and not last)     # every eighth bar the figure and the groove drop out for a breath
  while t<e-1e-6 and not last:       # the plucked figure: a pattern of the band, on the chord tones, sparser under speech
   k8=int(round((t-a)/(beat/2)))
   if pat[k8%len(pat)] and not breakdown and ((not sp) or k8%4==0) and rnd.random()<(.6+.4*m['dens']):
    notes.append(dict(t=t,dur=step*1.5,pitch=tri[idx%3]+12*(1 if idx%6<3 else 0)+(12 if pc.get('hi') else 0),vel=int((34+34*lv)*sv),ch=2))
   idx+=1;t+=step
  if not last:      # bass: root on one, fifth on three (an oom-pah for the folk band)
   notes.append(dict(t=a,dur=beat*.9,pitch=root,vel=int((44+30*lv)*sv*fade),ch=1))
   if lv>.3 or pc['pattern'] is not None:notes.append(dict(t=a+beat*2,dur=beat*.9,pitch=fifth if pc.get('oompah') else root,vel=int((38+28*lv)*sv),ch=1))
   if pc.get('oompah'):
    for k_ in (1,3):notes.append(dict(t=a+beat*k_,dur=beat*.4,pitch=tri[1]-12,vel=int((28+22*lv)*sv),ch=1))
  else:notes.append(dict(t=a,dur=beat*3.6,pitch=root,vel=int(40*fade),ch=1))
  if not sp and b%2==0 and not last and m['dens']>0 and (b>0 or lv>.4) and rnd.random()<(.6+.35*m['dens']):   # the film motif on the lead: A A' B A over eight bars, some phrases left silent
   mt=vary(motif,[0,1,0,2][(b//2)%4]);phrase+=1;tt=a+beat*(.5 if b==0 else 0);root_d=d;nm=len(mt)
   for j,(deg,bt) in enumerate(mt):
    if tt>=e+bar-1e-6:break
    notes.append(dict(t=tt,dur=bt*beat*.95,pitch=pitch_of(theme,mode,root_d+deg,1)+lowered,vel=int((52+40*lv)*(.85+.3*j/max(1,nm-1))),ch=3));tt+=bt*beat
  if lv>.35 and not last and (b%2==1 or sp):    # a counter-line in long notes under the gaps
   notes.append(dict(t=a+beat*(0 if b%4<2 else 2),dur=bar*1.4,pitch=tri[1]-(12 if band!='night' else 0),vel=int((30+26*lv)*sv),ch=11))
  if not last and pc['perc'] and mood!='none' and not breakdown:      # percussion: a groove per band, a fill every fourth bar
   for ev_ in perc_bar(pc['perc'],a,beat,lv,sv,b,mood):notes.append(ev_)
  if any(s_<e and t_>a for s_,t_ in hot) and not last:      # the action bars: a driving eighth-note ostinato on the chord root
   for k8 in range(8):notes.append(dict(t=a+k8*beat/2,dur=beat*.4,pitch=root+12+(7 if k8%4==3 else 0),vel=int(48+34*lv),ch=2))
  if lv>.45 and not last and b%4==3 and pc['perc'] in ('epic','oompah','comic'):    # rising run into the next phrase
   for kk,dg in enumerate((0,2,4,7)):notes.append(dict(t=e-beat*.9+kk*beat*.2,dur=beat*.3,pitch=pitch_of(theme,mode,d+dg,1)+lowered,vel=int(44+20*lv),ch=2))
 firsts={}
 for L in plan.lines:
  mot=plan.actors[L['speaker']].look.get('motif') or theme.get('motifs',{}).get(L['speaker'])
  if mot and L['speaker'] not in firsts:
   firsts[L['speaker']]=L['t0']
   for k,deg in enumerate(mot):notes.append(dict(t=max(0,L['t0']-.9)+k*beat*.5,dur=beat*.45,pitch=pitch_of(theme,mode,deg,1)+lowered,vel=58,ch=6))
 for t,nm in hits:
  notes.append(dict(t=t,dur=1.5,pitch=36,vel=100,ch=4));notes.append(dict(t=t,dur=1.2,pitch=pitch_of(theme,'minor',0,-2)+lowered,vel=95,ch=5))
 for e in plan.events:
  t=e['t0']
  if e['kind']=='act':
   c=e.get('clip')
   if c=='startle':
    for p in (pitch_of(theme,'minor',0,0),pitch_of(theme,'minor',2,0),pitch_of(theme,'minor',4,1)):notes.append(dict(t=t+.1,dur=.35,pitch=p+lowered,vel=92,ch=7))
   elif c in('cele','laugh'):
    for k,deg in enumerate((0,2,4,7)):notes.append(dict(t=t+.2+k*.12,dur=.35,pitch=pitch_of(theme,mode,deg,2)+lowered,vel=72,ch=8))
   elif c=='fall':
    for k,deg in enumerate((4,3,1,0)):notes.append(dict(t=t+.3+k*.22,dur=.4,pitch=pitch_of(theme,mode,deg,0)+lowered,vel=78,ch=7))
  elif e['kind'] in('take','give','put'):
   for k,deg in enumerate((4,6)):notes.append(dict(t=e.get('t_grasp',t)+k*.15,dur=.4,pitch=pitch_of(theme,mode,deg,2)+lowered,vel=60,ch=10))
 programs={0:pc['pad'],1:pc['bass'],2:pc['pluck'],3:pc['lead'],4:pal['hit'],5:57,6:pc['lead'],7:pal['stinger'],8:pal['sparkle'],10:pal['celesta'],11:pc['counter']}
 for n in notes:n['t']=round(n['t'],3);n['dur']=round(n['dur'],3)
 notes=[n for n in notes if n['t']<secs+2.];return notes,programs,bpm
def notes_key(notes,programs,bpm):
 return hashlib.sha1(json.dumps([notes,sorted(programs.items()),round(bpm,2)],sort_keys=True).encode()).hexdigest()[:16]
def render(plan,theme,mood='calm',place=None,time='day',seed='',cues=None,sr=22050,arc=None):
 """audio of the score (cached as a wav by the notes), or None when FluidSynth / the SoundFont are missing"""
 import perf_midi as pm
 notes,programs,bpm=compose(plan,theme,mood,place,time,seed,cues,arc)
 if not notes:return np.zeros(int(plan.seconds*sr))
 if not pm.available():return None
 cache=pm.TOOLS/'cache';cache.mkdir(exist_ok=True);p=cache/(notes_key(notes,programs,bpm)+'.npy')
 if p.exists():x=np.load(p)
 else:
  x=pm.render(notes,programs,plan.seconds+3,sr,bpm)
  if x is None:return None
  np.save(p,x.astype(np.float32))
 n=int(plan.seconds*sr);x=np.pad(x,(0,max(0,n-len(x))))[:n].astype(float);fade=np.minimum(np.arange(n)/(sr*1.2),1)*np.minimum((n-np.arange(n))/(sr*2.5),1)
 return x*fade
