import math
import unittest
from pathlib import Path
from movie_production.characters import load_profile,evaluate_targets,speech_commands,RigController

ROOT=Path(__file__).resolve().parents[1]
class ProfileTests(unittest.TestCase):
    def test_full_lip_closure_suppresses_open_jaw(self):
        vis={'MBP':[1], 'FV':[0], 'E':[0], 'O':[0]}
        self.assertEqual(speech_commands(vis,[1],0)['jaw'],0)

    def test_same_semantics_produce_calibrated_native_axes(self):
        snow=evaluate_targets(load_profile(ROOT/'movie_production/profiles/snow.json'),{'jaw':1,'blink':1})
        fox=evaluate_targets(load_profile(ROOT/'movie_production/profiles/jacob.json'),{'jaw':1,'blink':1})
        self.assertAlmostEqual(snow[('Jaw','rotation','LOCAL')][0],math.radians(14))
        self.assertAlmostEqual(fox[('CTRL-JAW','rotation','LOCAL')][2],-math.radians(14))
        self.assertEqual(fox[('CTRL-EYE-BLINK.L','location','LOCAL')][2],.019)
        self.assertEqual(snow[('MSTR-Eyelid_Upper.L','location','LOCAL')][1],-.028)

    def test_missing_controls_fail_before_animation(self):
        class Pose: bones={}
        class Rig: pose=Pose()
        with self.assertRaisesRegex(ValueError,'missing controls'):
            RigController(Rig(),load_profile(ROOT/'movie_production/profiles/jacob.json'),1.8)

    def test_unknown_or_nonfinite_commands_rejected(self):
        profile=load_profile(ROOT/'movie_production/profiles/jacob.json')
        with self.assertRaises(ValueError):evaluate_targets(profile,{'typo':1})
        with self.assertRaises(ValueError):evaluate_targets(profile,{'jaw':float('nan')})

    def test_control_limits_and_neutral_reset(self):
        profile=load_profile(ROOT/'movie_production/profiles/jacob.json')
        self.assertEqual(evaluate_targets(profile,{'jaw':4}),evaluate_targets(profile,{'jaw':1}))
        self.assertTrue(all(all(value==0 for value in vector) for vector in evaluate_targets(profile,{}).values()))

if __name__=='__main__':unittest.main()
