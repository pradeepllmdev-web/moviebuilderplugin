import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_prompt import validate
class ScenePlanTests(unittest.TestCase):
 def plan(self):return dict(version=1,title='Test',character='lion',environment='forest',mood='golden_hour',camera='full',segments=[dict(action='walk',duration=4,distance_cm=240,dialogue='Hi')],unsupported=[],notes=[])
 def test_scene_events_alias_is_normalized(self):
  p=self.plan();p['scene_events']=[{'type':'twig_snap','time':2}];self.assertEqual(validate(p)['events'],p['scene_events'])
 def test_nonfinite_rejected(self):
  p=self.plan();p['segments'][0]['distance_cm']=float('nan')
  with self.assertRaises(ValueError):validate(p)
 def test_unregistered_action_rejected(self):
  p=self.plan();p['segments'][0]['action']='drive'
  with self.assertRaises(ValueError):validate(p)
 def test_character_not_silently_replaced(self):
  p=self.plan();p['character']='mouse'
  with self.assertRaises(ValueError):validate(p)
 def test_two_actor_timelines_must_match(self):
  p=self.plan();p['actors']=[dict(character='lion',segments=p['segments']),dict(character='cat',segments=[dict(action='idle',duration=3)])]
  with self.assertRaises(ValueError):validate(p)
 def test_cat_profile_supported(self):
  p=self.plan();p['character']='cat';self.assertEqual(validate(p)['character'],'cat')
 def test_same_character_cannot_be_duplicated(self):
  p=self.plan();p['actors']=[dict(character='lion',segments=p['segments'])]*2
  with self.assertRaises(ValueError):validate(p)
 def test_environment_path_rejected(self):
  p=self.plan();p['environment_id']='../../other'
  with self.assertRaises(ValueError):validate(p)
 def test_unsafe_jump_combination_rejected(self):
  p=self.plan();p['segments'].append(dict(action='jump',duration=3,gap_cm=40))
  with self.assertRaises(ValueError):validate(p)
 def test_plan_is_not_mutated(self):
  p=self.plan();before=copy.deepcopy(p);validate(p);self.assertEqual(p,before)
 def test_movement_requires_full_camera(self):
  p=self.plan();p['camera']='medium';self.assertEqual(validate(p)['camera'],'full')
 def test_duration_limit(self):
  p=self.plan();p['segments']=[dict(action='idle',duration=12)]*4
  with self.assertRaises(ValueError):validate(p)
if __name__=='__main__':unittest.main()
