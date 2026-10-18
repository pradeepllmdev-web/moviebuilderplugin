import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
import activities,drink_actions
from sit_actions import SIT_ACTIONS,CLIPS,SEATED,validate as validate_sitting
from scene_prompt import ACTIONS,SYSTEM,validate as validate_scene,require_requested_controls
# Seated lion, measured once from the evaluated body (cm, rig space, forward is -Y).
LION={"bones":{"Hips":[-2.66,-14.85,37.61],"Spine":[-2.59,-11.25,49.74],"Spine1":[-1.4,-12.5,62.27],"Spine2":[-0.66,-14.4,75.15],"Neck":[-0.3,-15.77,84.58],"Head":[-0.37,-13.68,91.17],"RightArm":[-25.06,-16.12,76.19],"RightForeArm":[-29.88,-25.26,55.43],"RightHand":[-24.29,-41.18,38.57]},"snout_tip":[-1.8,-66.7,97.1],"arm_reach":47.0,"torso":{"y_front":-32.7,"z_top":72.6,"z_bottom":24.7},"thighs":{"y_front":-42.5,"z_top":42.9,"z_bottom":19.1},"lower_legs":{"y_front":-43.5,"z_top":31.4,"z_bottom":0.1},"feet":{"y_front":-56.7,"z_top":17.3,"z_bottom":-3.6}}
def beat(action,duration=3,dialogue=''):return dict(action=action,duration=duration,dialogue=dialogue)
def scene(segments):return dict(version=1,title='Tea',character='lion',environment='forest',mood='morning_fog',camera='full',segments=segments)
class ActivityTests(unittest.TestCase):
 def test_registry_feeds_every_consumer(self):
  for name in activities.beats():
   self.assertIn(name,ACTIONS)
  for name in activities.beats('seat'):self.assertIn(name,SIT_ACTIONS);self.assertIn(name,CLIPS)
  self.assertIn('drink',SEATED);self.assertIn('Drinking:',SYSTEM)
 def test_drink_needs_a_seat_and_stays_seated(self):
  self.assertTrue(validate_sitting([beat('sit_down'),beat('drink',5)]))
  with self.assertRaises(ValueError):validate_sitting([beat('drink',5)],False)
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',5),beat('walk')]))
  validate_scene(scene([beat('sit_down'),beat('drink',5),beat('stand_up')]))
 def test_duration_limits(self):
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',2),beat('stand_up')]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',9),beat('stand_up')]))
 def test_request_without_drink_beat_is_rejected(self):
  plan=scene([beat('sit_down'),beat('sit'),beat('stand_up')])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion sits down and drinks from a cup, then stands up')
  require_requested_controls(scene([beat('sit_down'),beat('drink',5),beat('stand_up')]),'The lion sits down and drinks from a cup, then stands up')
 def test_lion_drink_layout_is_feasible(self):
  l=activities.feasibility('drink',LION)
  self.assertTrue(l['ok']);self.assertLessEqual(l['hand_to_cup_cm'],6);self.assertEqual(l['reach_shortfall_cm'],0)
  self.assertGreater(l['table']['top_cm'],LION['feet']['z_top']+4);self.assertLess(l['table']['top_cm'],LION['bones']['RightArm'][2])
 def test_short_arms_are_reported_infeasible(self):
  short=copy.deepcopy(LION);short['arm_reach']=30.
  self.assertFalse(activities.feasibility('drink',short)['ok'])
 def test_nod_moves_the_muzzle_down_and_back(self):
  tip=drink_actions.nodded_tip(LION,25);self.assertLess(tip[2],LION['snout_tip'][2]);self.assertGreater(tip[1],LION['snout_tip'][1])
if __name__=='__main__':unittest.main()
class GestureTests(unittest.TestCase):
 def test_every_gesture_has_a_library_clip_preference(self):
  clips_file=Path(__file__).resolve().parents[2]/'blendplugin-next'/'scene_pipeline'/'realistic_clips.py'
  if not clips_file.exists():self.skipTest('shared clip library not checked out next to this repo')
  text=clips_file.read_text()
  for name in activities.GESTURES:self.assertIn("'"+name+"':",text)
 def test_gesture_requests_are_recognised_and_enforced(self):
  plan=scene([beat('idle',4)])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion waves hello')
  require_requested_controls(scene([beat('wave',4)]),'The lion waves hello')
 def test_gestures_validate_in_place_and_not_with_sitting(self):
  validate_scene(scene([beat('idle',2),beat('wave',4,'Hello!'),beat('bow',3)]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('wave',1),beat('idle')]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('wave',3),beat('stand_up')]))
 def test_planner_lists_the_gestures(self):
  for name in activities.GESTURES:self.assertIn(name+' (',SYSTEM)
class KnowledgeTests(unittest.TestCase):
 def test_unsupported_motions_must_be_reported(self):
  plan=scene([beat('idle',4)])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion points ahead and then walks')
  ok=dict(plan,unsupported=['point: no pointing clip'])
  require_requested_controls(ok,'The lion points ahead and then walks')
  self.assertEqual(activities.unsupported_requests('from this point of view'),[])
 def test_planner_states_the_gaps(self):
  self.assertIn('has no clip for',SYSTEM);self.assertIn('unsupported',SYSTEM)
 def test_catalog_lists_every_activity_for_clients(self):
  catalog=activities.summary()
  self.assertEqual(set(catalog['activities']),set(activities.ACTIVITIES));self.assertIn('cry',catalog['unsupported'])
  self.assertTrue(catalog['activities']['drink']['seated']);self.assertIn('lift a cup',catalog['activities']['drink']['caveat'])
class CharacterTests(unittest.TestCase):
 def test_clip_activities_declare_their_characters(self):
  for name,a in activities.ACTIVITIES.items():
   self.assertTrue(a['characters']);self.assertIn('lion',a['characters'])
   if a.get('family')=='clip':self.assertEqual(set(a['characters']),{'lion','cat','rowan'})
  self.assertEqual(activities.ACTIVITIES['drink']['characters'],['lion'])
