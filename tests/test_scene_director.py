import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_director import apply_controls
class DirectorTests(unittest.TestCase):
 def plan(self):return {'character':'cat','segments':[{'action':'idle','duration':4,'dialogue':'Hello'}]}
 def test_cues_preserve_dialogue_and_duration(self):
  p=self.plan();apply_controls(p,{'looks':[{'shot':0,'actor':'cat','segment':0,'yaw':20,'pitch':2}],'events':[{'shot':0,'type':'twig_snap','time':2}]});self.assertEqual(p['segments'][0]['dialogue'],'Hello');self.assertEqual(p['segments'][0]['duration'],4);self.assertEqual(p['segments'][0]['look_yaw_deg'],20)
 def test_unknown_actor_is_rejected(self):
  with self.assertRaises(ValueError):apply_controls(self.plan(),{'looks':[{'shot':0,'actor':'mouse','segment':0,'yaw':20,'pitch':2}]})
 def test_outside_shot_index_is_rejected(self):
  with self.assertRaises(ValueError):apply_controls(self.plan(),{'events':[{'shot':4,'type':'twig_snap','time':2}]})
 def test_semantic_target_does_not_require_guessed_angles(self):
  p=self.plan();apply_controls(p,{'looks':[{'shot':0,'actor':'cat','segment':0,'look_at':'partner'}]});self.assertEqual(p['segments'][0]['look_at'],'partner')
if __name__=='__main__':unittest.main()
