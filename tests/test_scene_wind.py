import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_prompt import validate
class WindTests(unittest.TestCase):
 def plan(self):return dict(version=1,title='Wind',character='rowan',environment='forest',mood='morning_fog',camera='medium',segments=[dict(action='idle',duration=3,look_at='point',look_target_cm=[0,800,160])],events=[dict(type='wind_gust',time=1,duration=2)])
 def test_shared_target_and_gust(self):self.assertEqual(validate(self.plan())['events'][0]['type'],'wind_gust')
 def test_hold_ball_is_lion_only(self):
  p=self.plan();p['character']='lion';p['segments']=[dict(action='hold_ball',duration=3,dialogue='Steady.')];self.assertEqual(validate(p)['segments'][0]['action'],'hold_ball')
  p['character']='rowan'
  with self.assertRaises(ValueError):validate(p)
 def test_missing_point_rejected(self):
  p=self.plan();del p['segments'][0]['look_target_cm']
  with self.assertRaises(ValueError):validate(p)
 def test_moving_point_target_rejected(self):
  p=self.plan();p['segments'][0].update(action='walk',distance_cm=120)
  with self.assertRaises(ValueError):validate(p)
 def test_unbounded_gust_rejected(self):
  p=self.plan();p['events'][0]['duration']=100
  with self.assertRaises(ValueError):validate(p)
