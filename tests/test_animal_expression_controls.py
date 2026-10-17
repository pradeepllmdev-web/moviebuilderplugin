import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from animal_expression_controls import values
class Expressions(unittest.TestCase):
 def test_shapes_are_bounded_and_blinks_are_not_enabled(self):
  result=values({'O':[1],'E':[1]},0,'reassuring',0)
  self.assertEqual(result['Round'],.4);self.assertEqual(result['Wide'],.3);self.assertGreater(result['WarmSmile'],0);self.assertFalse(any('Blink' in name for name in result))
 def test_silence_has_no_rounding(self):self.assertEqual(values({},0,'neutral',0)['Round'],0)
