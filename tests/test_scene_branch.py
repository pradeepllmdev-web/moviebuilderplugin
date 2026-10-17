import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_prompt import validate,require_requested_controls

class BranchTests(unittest.TestCase):
 def plan(self):
  return dict(version=1,title='Branch warning',character='lion',environment='forest',mood='morning_fog',camera='medium',segments=[dict(action='idle',duration=5)],events=[dict(type='branch_fall',time=1,duration=1,position_cm=[0,200],length_cm=90)])
 def test_valid_stationary_branch(self):self.assertEqual(validate(self.plan())['events'][0]['length_cm'],90)
 def test_landing_near_actor_rejected(self):
  p=self.plan();p['events'][0]['position_cm']=[0,10]
  with self.assertRaises(ValueError):validate(p)
 def test_second_actor_clearance_checked(self):
  p=self.plan();p['actors']=[dict(character='lion',position_cm=[-120,0],segments=p['segments']),dict(character='rowan',position_cm=[0,200],segments=p['segments'])]
  with self.assertRaises(ValueError):validate(p)
 def test_fall_overrun_rejected(self):
  p=self.plan();p['events'][0]['time']=4.5
  with self.assertRaises(ValueError):validate(p)
 def test_moving_observation_rejected(self):
  p=self.plan();p['segments'][0].update(action='run',distance_cm=400)
  with self.assertRaises(ValueError):validate(p)
 def test_prompt_cannot_silently_drop_branch(self):
  p=self.plan();p['events']=[]
  with self.assertRaises(ValueError):require_requested_controls(p,'A falling branch nearby.')
