import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_attention import attention
from scene_prompt import require_requested_controls
class AttentionTests(unittest.TestCase):
 def test_smooth_transition(self):
  s=[dict(start=0,end=2,look_yaw_deg=0),dict(start=2,end=4,look_yaw_deg=30)]
  self.assertEqual(attention(s,2)[0],0);self.assertAlmostEqual(attention(s,2.3)[0],15);self.assertEqual(attention(s,3)[0],30)
 def test_one_nod_then_hold(self):
  s=[dict(start=0,end=4,emotion='reassuring')]
  self.assertGreater(attention(s,.75)[1],0);self.assertAlmostEqual(attention(s,3)[1],0)
 def test_no_yaw_spike(self):
  s=[dict(start=0,end=2,look_yaw_deg=-30),dict(start=2,end=4,look_yaw_deg=30)];v=[attention(s,i/24)[0] for i in range(96)]
  self.assertLess(max(abs(b-a) for a,b in zip(v,v[1:])),7)
 def test_missing_requested_sound_is_rejected(self):
  with self.assertRaises(ValueError):require_requested_controls({'segments':[]},'A twig snaps.')
 def test_requested_head_turn_must_be_nonzero(self):
  with self.assertRaises(ValueError):require_requested_controls({'segments':[{'look_yaw_deg':0}]},'Cat turns her head.')
 def test_supplied_controls_are_accepted(self):
  p={'segments':[{'look_yaw_deg':20}],'events':[{'type':'twig_snap','time':2}]}
  self.assertIs(require_requested_controls(p,'Cat turns her head when a twig snaps.'),p)
if __name__=='__main__':unittest.main()
