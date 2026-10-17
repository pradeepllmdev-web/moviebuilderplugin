import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'server'))
from character_workflow_performance import speech_envelope,mouth_mode,jaw_deformation,scene_soundtrack

class PerformanceTests(unittest.TestCase):
 def test_music_mix_preserves_duration_and_channels(self):
  import tempfile,wave
  with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
   src=Path(d)/'speech.wav';dst=Path(d)/'mix.wav'
   with wave.open(str(src),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(8000);w.writeframes(np.zeros((8000,2),dtype='<i2').tobytes())
   scene_soundtrack(src,dst)
   with wave.open(str(dst)) as w:
    self.assertEqual(w.getnframes(),8000);self.assertEqual(w.getnchannels(),2)
    audio=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');self.assertGreater(np.max(np.abs(audio)),0);self.assertLess(np.max(np.abs(audio)),32767)
 def test_silent_actor_has_no_gestures(self):
  self.assertEqual(speech_envelope([0]*100,24),[0]*100)
 def test_speech_fades_to_quiet_and_has_no_syllable_spikes(self):
  e=speech_envelope([0]*24+[.4,0]*24+[0]*100,24)
  self.assertGreater(max(e),.15);self.assertLess(max(e),.181)
  self.assertLess(max(abs(a-b) for a,b in zip(e,e[1:])),.035)
  self.assertLess(e[-1],.001)
 def test_quiet_setting_disables_all_gestures(self):
  self.assertEqual(speech_envelope([.8]*40,24,0),[0]*40)
 def test_auto_mouth_and_explicit_override(self):
  b={'mouth_opening':{'x0':0,'x1':100,'y0':0,'y1':40}}
  self.assertEqual(mouth_mode(b),'open');self.assertEqual(mouth_mode(b,'closed'),'closed')
 def test_jaw_preserves_nose_and_reverses_open_source(self):
  parts={'mouth_opening':{'x':0,'y':.5,'w':.2,'h':.12},'nose':{'y':.67,'h':.08},'head':{'w':.5}}
  for front in (1,-1):
   v=np.array([[0,.44,.3*front],[.02,.48,.3*front],[0,.7,.32*front],[.8,.44,.3*front]])
   shift,jaw,top=jaw_deformation(v,parts,front,'open')
   self.assertGreater(np.linalg.norm(jaw[0]),0)
   np.testing.assert_allclose(shift+jaw,0,atol=1e-8)
   np.testing.assert_allclose(jaw[2:],0,atol=1e-8)
   shift2,jaw2,_=jaw_deformation(v,parts,front,'closed');np.testing.assert_allclose(shift2,0)
   self.assertLess(jaw2[0,1],0)
if __name__=='__main__':unittest.main()
