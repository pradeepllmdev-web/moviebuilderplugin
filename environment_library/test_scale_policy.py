import unittest
from scale_policy import metres,building_height,fit_dimensions,grounded_location
class ScaleTests(unittest.TestCase):
 def test_units(self):self.assertEqual(metres(1.85),185)
 def test_floors(self):self.assertEqual(building_height(20,'office',200),8200)
 def test_preserve_proportions(self):
  fit=fit_dimensions([200,100,50],axis='z',target_cm=75)
  self.assertEqual(fit['dimensions_cm'],[300,150,75])
 def test_offcentre_pivot(self):self.assertEqual(grounded_location([10,-20,30],[40,50,80],2),[-20,40,100])
 def test_invalid(self):
  for value in [float('nan'),float('inf'),0,-1,True]:
   with self.assertRaises(ValueError):metres(value)
  with self.assertRaises(ValueError):building_height(2.5)
  with self.assertRaises(ValueError):fit_dimensions([1,0,3],profile='chair')
if __name__=='__main__':unittest.main()
