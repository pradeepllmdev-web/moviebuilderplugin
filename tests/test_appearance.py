import unittest
from movie_production.appearance import targets_from_ratios,validate_preset

class AppearanceTests(unittest.TestCase):
    def test_large_eyes_and_narrow_nose(self):
        targets=targets_from_ratios({'eye_width':.24,'nose_width':.2,'mouth_width':.35,'chin_width':.78,'face_aspect':1.13})
        self.assertGreater(targets['eyes/l-eye-scale-incr'],0)
        self.assertEqual(targets['eyes/l-eye-scale-incr'],targets['eyes/r-eye-scale-incr'])
        self.assertGreater(targets['nose/nose-scale-horiz-decr'],0)
        self.assertGreater(targets['chin/chin-width-decr'],0)
    def test_extreme_ratios_capped(self):
        targets=targets_from_ratios(dict.fromkeys(['eye_width','nose_width','mouth_width','chin_width','face_aspect'],10.))
        self.assertTrue(all(0<=weight<=.65 for weight in targets.values()))
    def test_bad_measurements_rejected(self):
        with self.assertRaises(ValueError):targets_from_ratios({})
    def test_unsafe_target_rejected(self):
        with self.assertRaises(ValueError):validate_preset({'schema':'image-mpfb-preset/1','character_id':'test','targets':{'../outside':.2}})
