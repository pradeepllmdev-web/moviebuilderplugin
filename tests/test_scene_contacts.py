import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from scene_contacts import validate_routes
class RouteTests(unittest.TestCase):
 def rows(self,x,y=0):return [{'location_cm':[x,y,0]},{'location_cm':[x,y+10,0]}]
 def test_overlap_rejected(self):
  with self.assertRaises(ValueError):validate_routes({'Leo':self.rows(0),'Amber':self.rows(50)})
 def test_separated_parallel_routes(self):self.assertEqual(validate_routes({'Leo':self.rows(-120),'Amber':self.rows(120)})['minimum_actor_separation_cm'],240)
 def test_route_outside_stage(self):
  with self.assertRaises(ValueError):validate_routes({'Leo':self.rows(800)})
 def test_root_jump_rejected(self):
  with self.assertRaises(ValueError):validate_routes({'Leo':[{'location_cm':[0,0,0]},{'location_cm':[0,0,100]}]})
 def test_bad_timeline_rejected(self):
  with self.assertRaises(ValueError):validate_routes({'Leo':self.rows(0),'Amber':[]})
 def test_heading_snap_rejected(self):
  rows=self.rows(0);rows[0]['yaw']=0;rows[1]['yaw']=90
  with self.assertRaises(ValueError):validate_routes({'Leo':rows})
 def test_heading_wrap_is_continuous(self):
  rows=self.rows(0);rows[0]['yaw']=179;rows[1]['yaw']=-179
  self.assertEqual(validate_routes({'Leo':rows})['maximum_heading_step_deg'],2)
if __name__=='__main__':unittest.main()
