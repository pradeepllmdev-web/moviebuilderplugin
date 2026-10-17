import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from turn_routes import route
from scene_prompt import validate,require_requested_controls
class TurnTests(unittest.TestCase):
 def test_right_turn_and_forward_walk(self):
  rows=route([dict(action='turn',duration=2,angle_deg=-90,radius_cm=80),dict(action='walk',duration=2,distance_cm=100)])
  self.assertAlmostEqual(rows[47]['location_cm'][0],80);self.assertAlmostEqual(rows[47]['location_cm'][1],80)
  self.assertAlmostEqual(rows[-1]['location_cm'][0],180);self.assertAlmostEqual(rows[-1]['location_cm'][1],80);self.assertEqual(rows[-1]['yaw'],-90)
 def test_headings_and_positions_continuous(self):
  rows=route([dict(action='walk',duration=2,distance_cm=80),dict(action='idle',duration=2),dict(action='turn',duration=2,angle_deg=-90,radius_cm=80),dict(action='idle',duration=2)])
  self.assertLess(max(abs(b['yaw']-a['yaw']) for a,b in zip(rows,rows[1:])),3)
  self.assertLess(max(math.dist(a['location_cm'],b['location_cm']) for a,b in zip(rows,rows[1:])),5)
 def test_initial_heading_rotates_travel(self):
  self.assertAlmostEqual(route([dict(action='walk',duration=2,distance_cm=100)],heading=-90)[-1]['location_cm'][0],100)
 def test_validate_turn(self):
  p=dict(version=1,title='Turn',character='lion',environment='forest',mood='morning_fog',camera='medium',segments=[dict(action='turn',duration=2,angle_deg=-90,radius_cm=80)])
  self.assertEqual(validate(p)['camera'],'full')
  p['character']='rowan'
  with self.assertRaises(ValueError):validate(p)
 def test_excessive_turn_rejected(self):
  p=dict(version=1,title='Turn',character='lion',environment='forest',mood='morning_fog',camera='full',segments=[dict(action='turn',duration=2,angle_deg=180,radius_cm=80)])
  with self.assertRaises(ValueError):validate(p)
 def test_prompt_cannot_omit_body_turn(self):
  p=dict(segments=[dict(action='idle')],unsupported=[])
  with self.assertRaises(ValueError):require_requested_controls(p,'Leo makes a stepping turn.')
