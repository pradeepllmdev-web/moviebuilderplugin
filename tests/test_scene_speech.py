import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from human_speech import speech_values
class SpeechTests(unittest.TestCase):
 def test_closed_consonant_overrides_open_jaw(self):
  opened=speech_values({'MBP':[0]},0,1)
  closed=speech_values({'MBP':[1]},0,1)
  self.assertLess(closed['jawOpen'],opened['jawOpen']*.2)
  self.assertGreater(closed['mouthClose'],.5)
 def test_round_and_wide_are_distinct(self):
  round=speech_values({'O':[1]},0,.3);wide=speech_values({'E':[1]},0,.3)
  self.assertGreater(round['mouthFunnel'],wide['mouthFunnel'])
  self.assertGreater(wide['mouthStretchLeft'],round['mouthStretchLeft'])
