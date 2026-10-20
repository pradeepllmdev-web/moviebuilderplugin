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
def compose(plan,theme,mood='calm',place=None,time='day',seed='',cues=None,arc=None):
 m=MOODS.get(mood,MOODS['calm'])
 if mood=='none':return [],{},90.
 mode=m['mode'] or theme.get('mode','major');pal=dict(PALETTE,**theme.get('palette',{}));pal['lead']=PLACE_LEAD.get(place,pal['lead']) if theme.get('place_leads',True) else pal['lead']
 bpm=theme.get('tempo',90)*m['tempo']*(.88 if time=='night' else (1.05 if time=='dawn' else 1.));beat=60./bpm;bar=beat*4;secs=plan.seconds;nbar=int(math.ceil(secs/bar))+1
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
 for b in range(nbar):
  a=b*bar;e=a+bar;lv=I[b];sp=in_speech(a,e);d=prog[b%len(prog)];last=b>=nbar-2
  if last:d=0
  tri=[pitch_of(theme,mode,d+k,0)+lowered for k in (0,2,4)];root=pitch_of(theme,mode,d,-1)+lowered
  fade=.55 if (b==0) else (.5 if last else 1.)
  for p in tri:notes.append(dict(t=a,dur=bar*(1.0 if not last else 1.6),pitch=p,vel=int((26+30*lv)*(.65 if sp else 1.)*fade),ch=0))
  if lv>.25 or b>0:notes.append(dict(t=a,dur=beat*3.6,pitch=root,vel=int((40+34*lv)*(.7 if sp else 1.)*fade),ch=1))
  if lv>.38 and not last:notes.append(dict(t=a+beat*2,dur=beat*1.8,pitch=pitch_of(theme,mode,d+4,-1)+lowered,vel=int(36+30*lv),ch=1))
  step=beat/2 if lv>.5 else beat;idx=0;t=a
  while t<e-1e-6 and not last:       # harp / guitar / accordion figure on the chord tones, thinner under speech
   if (not sp) or int(round((t-a)/beat))%2==0 and rnd.random()<.6:
    if rnd.random()<(.55+.4*m['dens']):notes.append(dict(t=t,dur=step*1.6,pitch=tri[idx%3]+12,vel=int((36+36*lv)*(.55 if sp else 1.)),ch=2))
   idx+=1;t+=step
  if not sp and b%2==0 and not last and m['dens']>0 and (b>0 or lv>.4) and rnd.random()<(.6+.35*m['dens']):   # the film motif on the lead: A A' B A over eight bars, some phrases left silent
   mt=vary(motif,[0,1,0,2][(b//2)%4]);phrase+=1;tt=a+beat*(.5 if b==0 else 0);root_d=d;nm=len(mt)
   for j,(deg,bt) in enumerate(mt):
    if tt>=e+bar-1e-6:break
    notes.append(dict(t=tt,dur=bt*beat*.95,pitch=pitch_of(theme,mode,root_d+deg,1)+lowered,vel=int((52+40*lv)*(.85+.3*j/max(1,nm-1))),ch=3));tt+=bt*beat
  if lv>.38 and not sp and not last and b%2==1:    # a cello line in long notes under the gaps
   notes.append(dict(t=a,dur=bar*1.9,pitch=tri[1]-12,vel=int(34+28*lv),ch=11))
  if not sp and not last and (mood in('bright','comic','epic','warm') or arc>.7):    # a light rhythm section
   for k8 in range(8):
    tk=a+k8*beat/2
    if k8%2==1:notes.append(dict(t=tk,dur=.08,pitch=70,vel=int(24+22*lv),ch=9))
    if k8%4==0 and lv>.5:notes.append(dict(t=tk,dur=.1,pitch=36,vel=int(36+20*lv),ch=9))
    if k8%4==2 and mood=='comic':notes.append(dict(t=tk,dur=.08,pitch=37,vel=34,ch=9))
  elif mood=='tense' and not sp and not last:
   for k4 in range(4):notes.append(dict(t=a+k4*beat,dur=.06,pitch=75,vel=int(20+16*lv),ch=9))
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
 programs={0:pal['pad'] if arc<.75 else 49,1:pal['bass'],2:pal['pluck'],3:pal['lead'],4:pal['hit'],5:57,6:pal['lead'],7:pal['stinger'],8:pal['sparkle'],10:pal['celesta'],11:42}
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
