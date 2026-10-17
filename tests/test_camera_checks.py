import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from camera_checks import in_frame,standard_full_report
class FramingTests(unittest.TestCase):
 def test_subject_at_target(self):self.assertTrue(in_frame([0,0,100],[300,200,180],[0,0,100],40))
 def test_behind_camera(self):self.assertFalse(in_frame([600,400,260],[300,200,180],[0,0,100],40))
 def test_high_point_cropped(self):self.assertFalse(in_frame([0,0,1000],[300,200,180],[0,0,100],40))
 def test_wider_full_camera_clears_near_character_feet(self):
  routes={'Leo':[{'location_cm':[-120,0,0]}],'Rowan':[{'location_cm':[180,160,0]}]};heights={'Leo':185,'Rowan':180}
  self.assertGreater(standard_full_report(routes,heights,32)['feet_outside_samples'],0)
  wide=standard_full_report(routes,heights,28);self.assertEqual(wide['feet_outside_samples'],0);self.assertEqual(wide['head_outside_samples'],0)
