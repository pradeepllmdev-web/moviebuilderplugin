import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from movie_prompt import validate
class MoviePlanTests(unittest.TestCase):
 def scene(self,duration=4):return dict(version=1,title='Shot',character='lion',environment='forest',mood='golden_hour',camera='close',segments=[dict(action='talk',duration=duration,dialogue='Hi')])
 def test_nested_unsupported_stops_build_contract(self):
  s=self.scene();s['unsupported']=['grasp'];p=validate(dict(version=1,title='Test',unsupported=[],shots=[s,self.scene()]));self.assertIn('grasp',p['unsupported'])
 def test_single_shot_not_movie(self):
  with self.assertRaises(ValueError):validate(dict(version=1,title='Test',unsupported=[],shots=[self.scene()]))
 def test_nested_defaults_preserve_dialogue(self):
  p=validate(dict(version=1,title='Test',unsupported=[],shots=[self.scene(),self.scene()]));self.assertEqual(p['shots'][0]['segments'][0]['dialogue'],'Hi')
 def test_unsafe_environment_does_not_enter_movie(self):
  s=self.scene();s['environment_id']='../secret'
  with self.assertRaises(ValueError):validate(dict(version=1,title='Test',unsupported=[],shots=[s,self.scene()]))
if __name__=='__main__':unittest.main()
