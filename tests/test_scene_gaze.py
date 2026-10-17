import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_gaze import partner_angles,conversation_context
from scene_attention import attention
from scene_prompt import require_requested_controls
class GazeTests(unittest.TestCase):
 def test_both_partners_face_opposite_directions(self):
  a=partner_angles([-120,0],[120,0],-55,163,132);b=partner_angles([120,0],[-120,0],55,132,163)
  self.assertEqual(a['head_yaw_deg'],-35);self.assertEqual(b['head_yaw_deg'],35);self.assertEqual(a['remaining_yaw_error_deg'],0);self.assertLess(a['head_pitch_deg'],0);self.assertGreater(b['head_pitch_deg'],0)
 def test_close_partners_rejected(self):
  with self.assertRaises(ValueError):partner_angles([0,0],[20,0],0,150,150)
 def test_moving_partner_not_silently_approximated(self):
  a={'character':'lion','segments':[{'action':'talk','look_at':'partner'}]};b={'character':'cat','segments':[{'action':'walk'}]}
  with self.assertRaises(ValueError):conversation_context({'actors':[a,b]},a)
 def test_manual_looks_are_preserved(self):self.assertIsNone(conversation_context({}, {'character':'lion','segments':[{'action':'talk'}]}))
 def test_partner_orientation_is_preserved_at_cut(self):
  s=[{'start':0,'end':4,'look_yaw_deg':35,'look_from_yaw_deg':35}]
  self.assertEqual(attention(s,0)[0],35)
 def test_eye_contact_prompt_cannot_silently_use_manual_angles(self):
  with self.assertRaises(ValueError):require_requested_controls({'actors':[{'segments':[{'look_yaw_deg':20}]}]},'Look at each other.')
 def test_semantic_partner_target_satisfies_prompt(self):
  p={'actors':[{'segments':[{'look_at':'partner'}]},{'segments':[{'look_at':'partner'}]}]}
  self.assertIs(require_requested_controls(p,'Look at each other.'),p)
 def test_partner_behind_uses_initial_body_orientation(self):
  a={'character':'lion','position_cm':[0,120],'segments':[{'action':'idle','look_at':'partner'}]};b={'character':'cat','position_cm':[0,-120],'segments':[{'action':'idle'}]};r=conversation_context({'actors':[a,b]},a);self.assertEqual(r['remaining_yaw_error_deg'],0)
 def test_explicit_impossible_facing_is_rejected(self):
  a={'character':'lion','position_cm':[-120,0],'facing_yaw_deg':90,'segments':[{'action':'idle','look_at':'partner'}]};b={'character':'cat','position_cm':[120,0],'segments':[{'action':'idle'}]}
  with self.assertRaises(ValueError):conversation_context({'actors':[a,b]},a)
if __name__=='__main__':unittest.main()
