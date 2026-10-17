import unittest
from layout import compile_layout
class LayoutTests(unittest.TestCase):
 def test_top_left_percent_to_centered_world_centimeters(self):
  l=compile_layout({'width_m':120,'depth_m':100,'rivers':[{'points':[[0,0],[100,100]],'width_m':7}]})
  self.assertEqual(l['rivers'][0]['points'],[[-6000,5000],[6000,-5000]]);self.assertEqual(l['rivers'][0]['width'],700)
 def test_camera_height_and_clear_region(self):
  l=compile_layout({'clear':[{'center':[50,50],'radius_m':10}],'camera':{'position':[50,80],'target':[50,50],'height_m':2.4}})
  self.assertEqual(l['clear'][0],[0,0,1000]);self.assertEqual(l['camera']['location'][2],240)
 def test_unknown_river_bridge_rejected(self):
  with self.assertRaises(ValueError):compile_layout({'bridges':[{'river':0,'at':[50,50]}]})
 def test_invalid_coordinates_and_nan_rejected(self):
  for p in ([101,0],[0,float('nan')]):
   with self.assertRaises(ValueError):compile_layout({'rivers':[{'points':[p,[50,50]]}]})
 def test_degenerate_route_rejected(self):
  with self.assertRaises(ValueError):compile_layout({'paths':[{'points':[[50,50],[50,50]]}]})
 def test_scene_size_bounded(self):
  with self.assertRaises(ValueError):compile_layout({'width_m':100000})
if __name__=='__main__':unittest.main()
