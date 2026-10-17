import sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from human_face_controls import eye_values
from scene_prompt import validate

class HumanControlsTests(unittest.TestCase):
 def test_known_saved_set_in_preset_field_is_preserved(self):
  with patch('scene_prompt.resolve_environment',return_value='/Game/EnvironmentDemos/Known'):
   p=validate(dict(version=1,title='Set',character='rowan',environment='Known',mood='morning_fog',camera='close',segments=[dict(action='talk',duration=3,dialogue='Hello.')]))
  self.assertEqual(p['environment_id'],'Known')
 def test_blink_closes_and_reopens(self):
  self.assertEqual(eye_values(1.5)['eyeBlinkLeft'],1)
  self.assertEqual(eye_values(1.8)['eyeBlinkLeft'],0)
 def test_eye_tracks_bounded_and_not_opposing(self):
  for f in range(960):
   v=eye_values(f/24)
   self.assertTrue(all(0<=x<=1 for x in v.values()))
   self.assertEqual(v['eyeLookInLeft']*v['eyeLookOutLeft'],0)
 def test_rowan_plan(self):
  p=validate(dict(version=1,title='Human',character='rowan',environment='forest',mood='morning_fog',camera='close',focus='rowan',segments=[dict(action='talk',duration=3,dialogue='Hello.')]))
  self.assertEqual(p['character'],'rowan')
