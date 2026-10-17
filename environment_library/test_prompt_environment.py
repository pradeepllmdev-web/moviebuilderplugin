import unittest
from prompt_environment import validate,catalogue,candidates
class PromptPlans(unittest.TestCase):
 def plan(self):return dict(mood='golden_hour',buildings=[dict(position_cm=[1000,1000],width_tiles=3,depth_tiles=2)],roads=[dict(id='r',kind='straight',cell=[0,0])],assets=[],unsupported=[])
 def test_exact_id_priority(self):
  asset=catalogue()[-1]
  self.assertEqual(candidates('Use asset '+asset['id'])[0]['id'],asset['id'])
 def test_unknown_exact_id(self):
  with self.assertRaises(ValueError):candidates('Use tree.0000000000')
 def test_duplicate_exact_id(self):
  key=catalogue()[-1]['id'];selected=candidates(key+' '+key)
  self.assertEqual(sum(a['id']==key for a in selected),1)
 def test_mountain_backdrop(self):
  p=self.plan();p['mountains']={'enabled':True}
  out=validate(p);self.assertEqual(out['mountains']['height_cm'],50000)
 def test_mountain_collision(self):
  p=self.plan();p['mountains']={'enabled':True,'size_cm':500000,'distance_cm':100000}
  with self.assertRaises(ValueError):validate(p)
 def test_mountain_invalid(self):
  p=self.plan();p['mountains']={'enabled':True,'height_cm':float('nan')}
  with self.assertRaises(ValueError):validate(p)
 def test_valid_combination(self):
  out=validate(self.plan());self.assertGreater(len(out['boxes']),20)
 def test_building_road_overlap(self):
  p=self.plan();p['buildings'][0]['position_cm']=[0,0]
  with self.assertRaises(ValueError):validate(p)
 def test_unknown_asset(self):
  p=self.plan();p['assets']=[dict(asset_id='invented',position_cm=[4000,4000])]
  with self.assertRaises(ValueError):validate(p)
 def test_tree_road_overlap(self):
  p=self.plan();p['assets']=[dict(asset_id=catalogue()[0]['id'],position_cm=[0,0])]
  with self.assertRaises(ValueError):validate(p)
 def test_asset_bounds(self):
  p=self.plan();p['assets']=[dict(asset_id=catalogue()[0]['id'],position_cm=[9000,9000],scale=1)]
  self.assertEqual(len(validate(p)['asset_placements']),1)
if __name__=='__main__':unittest.main()
