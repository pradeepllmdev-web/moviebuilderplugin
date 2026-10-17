import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from sit_actions import seated_span,validate,starts_seated,back_fraction,DEFAULT_SEAT
from scene_prompt import validate as validate_scene,require_requested_controls
from movie_prompt import validate as validate_movie
import test_sit_movie
def beat(action,duration=3):return dict(action=action,duration=duration,dialogue='')
def scene(segments,character='lion'):return dict(version=1,title='Seat',character=character,environment='forest',mood='morning_fog',camera='full',segments=segments)
class SitTests(unittest.TestCase):
 def test_order_is_enforced(self):
  self.assertTrue(validate([beat('sit_down'),beat('sit')]))
  self.assertFalse(validate([beat('sit_down'),beat('stand_up')]))
  with self.assertRaises(ValueError):validate([beat('sit_down'),beat('sit_down')],False)
  with self.assertRaises(ValueError):validate([beat('stand_up')],False)
  with self.assertRaises(ValueError):validate([beat('sit_down'),beat('idle')])
 def test_shot_can_continue_seated(self):
  self.assertTrue(starts_seated([beat('sit_talk'),beat('stand_up')]));self.assertFalse(starts_seated([beat('idle'),beat('sit_down')]))
 def test_root_eases_back_and_returns(self):
  self.assertEqual(back_fraction('sit_down',0),0);self.assertEqual(back_fraction('sit_down',3),1)
  self.assertEqual(back_fraction('stand_up',0),1);self.assertEqual(back_fraction('stand_up',3),0)
  values=[back_fraction('sit_down',t/24) for t in range(72)];self.assertTrue(all(b>=a for a,b in zip(values,values[1:])))
 def test_seat_is_behind_the_standing_feet(self):
  # Standing feet are ~18 cm ahead of the root; the seat ends up behind them once the root eases back.
  self.assertLess(DEFAULT_SEAT['hips_cm'][1]-DEFAULT_SEAT['back_cm'],0)
 def test_scene_validation(self):
  self.assertEqual(validate_scene(scene([beat('idle',2),beat('sit_down'),beat('sit')]))['camera'],'full')
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down',2),beat('sit')]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('sit')],'rowan'))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('walk')]))
 def test_movie_carries_seated_state(self):
  self.assertEqual(len(validate_movie(test_sit_movie.PLAN)['shots']),3)
  broken=dict(test_sit_movie.PLAN,shots=[test_sit_movie.PLAN['shots'][0],test_sit_movie.PLAN['shots'][0]])
  with self.assertRaises(ValueError):validate_movie(broken)
 def test_stand_up_only_shot_still_has_seated_frames(self):
  self.assertEqual(seated_span('stand_up',4,7),(4,4.4));self.assertEqual(seated_span('sit',0,3),(0,3))
  self.assertEqual(seated_span('sit_down',0,3),(1.8,3));self.assertIsNone(seated_span('idle',0,3))
 def test_prompt_asking_to_sit_needs_sit_beats(self):
  standing=validate_scene(scene([beat('idle'),beat('talk')]));seated=validate_scene(scene([beat('sit_down'),beat('sit_talk'),beat('stand_up')]))
  with self.assertRaises(ValueError):require_requested_controls(standing,'The lion sits down on a bench and talks')
  require_requested_controls(seated,'The lion sits down on a bench, talks, then stands up')
  require_requested_controls(standing,'The lion talks about the sunrise')
if __name__=='__main__':unittest.main()
