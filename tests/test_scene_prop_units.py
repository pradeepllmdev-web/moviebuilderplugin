import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from prop_units import world_length_to_local
class PropUnitsTests(unittest.TestCase):
 def test_centimetre_rig(self):self.assertEqual(world_length_to_local(.05,.01),5)
 def test_metre_rig(self):self.assertEqual(world_length_to_local(.05,1),.05)
 def test_invalid_rig_scale(self):
  with self.assertRaises(ValueError):world_length_to_local(.05,0)
