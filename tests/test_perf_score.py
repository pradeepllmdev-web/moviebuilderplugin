import os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
import cast_registry as cr,perf_plan as pp,perf_score as ps,perf_midi as pmid
REG=cr.Registry([dict(id='mara',name='Mara',species='fox'),dict(id='bram',name='Bram',species='bear')])
THEME=dict(root=57,mode='dorian',tempo=96,motif=[(0,1),(2,.5),(4,.5)],motifs=dict(mara=[4,5,6]))
def plan(steps,preset='meadow'):
 return pp.compile(dict(id='s',location=dict(preset=preset),cast=[dict(id='mara',at=[-3,0],face=[1,0]),dict(id='bram',at=[3,0],face=[-1,0])],steps=steps),REG)
SAY=[dict(do='say',who='mara',text='We should not be here after dark.',to='bram'),dict(do='say',who='bram',text='Nonsense, sit down.',to='mara')]
QUIET=[dict(do='wait',dur=12)]
class Compose(unittest.TestCase):
 def test_deterministic_and_in_range(self):
  P=plan(SAY+QUIET);a=ps.compose(P,THEME,'calm','meadow','day','x');b=ps.compose(P,THEME,'calm','meadow','day','x');self.assertEqual(a,b)
  for n in a[0]:self.assertTrue(20<=n['pitch']<=110 and 1<=n['vel']<=127 and n['t']>=0 and n['dur']>0 and 0<=n['ch']<16)
 def test_no_music_means_no_notes(self):self.assertEqual(ps.compose(plan(QUIET),THEME,'none')[0],[])
 def test_the_place_picks_the_lead_instrument(self):
  self.assertEqual(ps.compose(plan(QUIET,'market'),THEME,'calm','market')[1][3],ps.BANDS['folk']['lead']);self.assertEqual(ps.compose(plan(QUIET,'room'),THEME,'calm','room')[1][3],ps.BANDS['cozy']['lead'])    # the place chooses the band, the band the instruments
 def test_melody_waits_for_speech(self):
  P=plan(SAY+QUIET);notes=ps.compose(P,THEME,'calm','meadow','day','x')[0];mel=[n for n in notes if n['ch']==3]
  for n in mel:
   for L in P.lines:self.assertFalse(L['t0']<n['t']<L['t1']-.5 and n['t']>2,'melody note at %.1f inside a line'%n['t'])
  self.assertTrue(mel)
 def test_the_film_motif_is_the_melody(self):
  notes,pr,bpm=ps.compose(plan(QUIET),THEME,'calm','meadow','day','x');lead=sorted([n for n in notes if n['ch']==3],key=lambda n:n['t'])[:3];beat=60./bpm
  self.assertEqual([round(n['dur']/beat/.95,2) for n in lead],[1.0,.5,.5])   # the film motif's rhythm, whatever chord it sits on
 def test_character_motif_on_the_first_line(self):
  P=plan(SAY);notes=ps.compose(P,THEME,'calm','meadow','day','x')[0];m=[n for n in notes if n['ch']==6];self.assertEqual(len(m),3);self.assertLess(m[0]['t'],P.lines[0]['t0'])
 def test_thunder_brings_hits_and_intensity(self):
  quiet=plan(QUIET+QUIET);storm=plan([dict(do='sfx',name='thunder',at=1.0),dict(do='wait',dur=12)]+QUIET)
  self.assertEqual([n for n in ps.compose(quiet,THEME,'calm')[0] if n['ch']==4],[]);self.assertTrue([n for n in ps.compose(storm,THEME,'calm')[0] if n['ch']==4])
 def test_cheering_adds_a_run(self):
  P=plan([dict(do='act',who='mara',clip='cele'),dict(do='wait',dur=8)]);self.assertTrue([n for n in ps.compose(P,THEME,'bright')[0] if n['ch']==8])
 def test_last_bar_resolves_on_the_tonic(self):
  P=plan(QUIET);notes=ps.compose(P,THEME,'calm')[0];last=max(n['t'] for n in notes if n['ch']==0);tone=[n['pitch']%12 for n in notes if n['ch']==0 and n['t']==last];self.assertIn(THEME['root']%12,tone)
 def test_night_is_lower_than_day(self):
  P=plan(QUIET);d=[n['pitch'] for n in ps.compose(P,THEME,'calm','meadow','day','x')[0] if n['ch']==0];n_=[n['pitch'] for n in ps.compose(P,THEME,'calm','meadow','night','x')[0] if n['ch']==0];self.assertLess(sum(n_)/len(n_),sum(d)/len(d))
class Arc(unittest.TestCase):
 def test_the_climax_is_busier_than_the_opening(self):
  P=plan(QUIET+QUIET);lo=ps.compose(P,THEME,'calm','meadow','day','x',None,0.1)[0];hi=ps.compose(P,THEME,'calm','meadow','day','x',None,1.0)[0];self.assertGreater(len(hi),len(lo));self.assertTrue([n for n in hi if n['ch']==9])
 def test_bright_scenes_get_a_rhythm_section_and_tense_ones_a_tick(self):
  P=plan(QUIET+QUIET);self.assertTrue([n for n in ps.compose(P,THEME,'bright','market')[0] if n['ch']==9]);self.assertTrue([n for n in ps.compose(P,THEME,'tense')[0] if n['ch']==9])    # every band but the piano has a groove
 def test_speech_bars_keep_a_quieter_rhythm_section(self):
  P=plan(SAY+QUIET+QUIET);notes=ps.compose(P,THEME,'bright','market')[0];inside=[n['vel'] for n in notes if n['ch']==9 and any(L['t0']<n['t']<L['t1'] for L in P.lines)];outside=[n['vel'] for n in notes if n['ch']==9 and not any(L['t0']-.3<n['t']<L['t1']+.3 for L in P.lines)]
  self.assertTrue(inside and outside);self.assertLess(sum(inside)/len(inside),sum(outside)/len(outside))    # the groove goes on under the voices, softer
class Duck(unittest.TestCase):
 def test_music_dips_while_the_voices_speak(self):
  import numpy as np,perf_audio as pa;SR=22050;v=np.zeros(SR*6);v[SR:2*SR]=.4*np.sin(np.arange(SR)*.3);m=pa.duck_mask(v,SR,.7)
  self.assertAlmostEqual(m[int(.3*SR)],1.,2);self.assertLess(m[int(1.5*SR)],.35);self.assertAlmostEqual(m[int(5*SR)],1.,2)
class Midi(unittest.TestCase):
 def test_file_is_a_valid_smf(self):
  import tempfile;p=os.path.join(tempfile.mkdtemp(),'a.mid');pmid.write(p,[dict(t=0,dur=1,pitch=60,vel=80,ch=0),dict(t=1,dur=.5,pitch=64,vel=70,ch=1)],{0:0,1:48},90);b=open(p,'rb').read();self.assertEqual(b[:4],b'MThd');self.assertIn(b'MTrk',b);self.assertTrue(b.endswith(bytes([0xFF,0x2F,0])))
 def test_vlq(self):self.assertEqual(pmid._vlq(0),b'\x00');self.assertEqual(pmid._vlq(128),b'\x81\x00');self.assertEqual(pmid._vlq(0x3fff),b'\xff\x7f')
 @unittest.skipUnless(pmid.available(),'FluidSynth and the SoundFont are not downloaded (python perf_midi.py download)')
 def test_render_is_not_silent(self):
  x=pmid.render([dict(t=0,dur=1,pitch=60,vel=90,ch=0)],{0:0},2.);self.assertEqual(len(x),44100);self.assertGreater(abs(x).max(),.01)
if __name__=='__main__':unittest.main()
