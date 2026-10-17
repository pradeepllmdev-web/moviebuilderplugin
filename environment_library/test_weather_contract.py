import unittest
from weather_contract import validate_weather,infer_weather
class Weather(unittest.TestCase):
 def test_defaults(self):self.assertEqual(validate_weather()['type'],'none')
 def test_rain(self):self.assertEqual(infer_weather('Heavy rain at the village')['type'],'rain')
 def test_snow(self):self.assertEqual(infer_weather('Snowy mountain village')['type'],'snow')
 def test_negation(self):self.assertIsNone(infer_weather('Village without snow'))
 def test_ranges(self):
  for value in [{'intensity':3},{'wetness':float('nan')},{'type':'hail'},{'wind_cm_s':[999,0]},{'snow_cover':True}]:
   with self.assertRaises(ValueError):validate_weather(value)
if __name__=='__main__':unittest.main()
