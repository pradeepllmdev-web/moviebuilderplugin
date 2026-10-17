import unittest
from reference_to_recipe import recipe_from_analysis,visible_missing_features
class ReferenceTests(unittest.TestCase):
 def test_absent_example_features_are_not_reported(self):
  a={'description':'A spruce forest','landmarks':['spruce trees','grass'],'missing_features':['bridges','houses','ocean','snow']}
  self.assertEqual(visible_missing_features(a),[])
 def test_visible_unsupported_bridge_is_preserved(self):
  a={'description':'A river and wooden footbridge','landmarks':['bridge'],'missing_features':['bridges']}
  self.assertEqual(visible_missing_features(a),['bridges'])
 def base(self):return {'category':'natural_outdoor','biome':'nordic_forest','terrain':'meadow','river':'none','mountains':False,'mood':'morning_fog','density':.8}
 def test_supported_recipe_preserves_controls(self):
  r=recipe_from_analysis(self.base(),'ForestTest');self.assertEqual(r['params']['biome'],'nordic_forest');self.assertEqual(r['params']['mood'],'morning_fog');self.assertEqual(r['id'],'ForestTest')
 def test_interior_is_not_silently_a_forest(self):
  a=self.base();a['category']='interior'
  with self.assertRaises(ValueError):recipe_from_analysis(a,'Room')
 def test_invalid_enum_rejected(self):
  a=self.base();a['biome']='ocean'
  with self.assertRaises(ValueError):recipe_from_analysis(a,'Ocean')
 def test_identifier_cannot_inject_commands_or_paths(self):
  with self.assertRaises(ValueError):recipe_from_analysis(self.base(),'../escape;quit')
 def test_unbounded_or_nan_density_rejected(self):
  for value in (999,float('nan')):
   a=self.base();a['density']=value
   with self.assertRaises(ValueError):recipe_from_analysis(a,'Forest')
if __name__=='__main__':unittest.main()
