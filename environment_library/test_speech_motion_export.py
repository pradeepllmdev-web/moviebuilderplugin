import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'blendplugin-next/scene_pipeline'))
from performance_motion_checks import require_custom_speech_motion
class SpeechExport(unittest.TestCase):
 def test_static_dialogue_rejected(self):
  with self.assertRaises(ValueError):require_custom_speech_motion('Cat',[{'name':'JawClose','values':[1,1,1]}],[{'speaker':'Cat','text':'Hello'}])
 def test_moving_dialogue_accepted(self):require_custom_speech_motion('Cat',[{'name':'JawClose','values':[1,0,1]}],[{'speaker':'Cat','text':'Hello'}])
 def test_silent_actor_allowed(self):require_custom_speech_motion('Cat',[{'name':'JawClose','values':[1,1,1]}],[])
if __name__=='__main__':unittest.main()
