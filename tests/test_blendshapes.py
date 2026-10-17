import unittest
from types import SimpleNamespace
from movie_production.blendshapes import expression_weights,BlendshapeController

class ExpressionTests(unittest.TestCase):
    def test_neutral_and_blink_independence(self):
        values=expression_weights({'blink':1})
        self.assertEqual(values['jawOpen'],0)
        self.assertEqual(values['eyeBlinkLeft'],1)
        self.assertEqual(values['eyeBlinkRight'],1)
    def test_signed_gaze_uses_opposite_eye_controls(self):
        left=expression_weights({'gaze':-1});right=expression_weights({'gaze':1})
        self.assertGreater(left['eyeLookInLeft'],0);self.assertEqual(left['eyeLookOutLeft'],0)
        self.assertGreater(right['eyeLookOutLeft'],0);self.assertEqual(right['eyeLookInLeft'],0)
    def test_funnel_and_stretch_exclusive(self):
        values=expression_weights({'spread':-1})
        self.assertGreater(values['mouthFunnel'],0);self.assertEqual(values['mouthStretchLeft'],0)
    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):expression_weights({'jaw':float('nan')})
    def test_lip_closure_does_not_open_jaw(self):
        weights=expression_weights({'mouth_close':.8,'lip_press':.4})
        self.assertEqual(weights['jawOpen'],0)
        self.assertEqual(weights['mouthClose'],.8)
        self.assertEqual(weights['mouthPressLeft'],weights['mouthPressRight'])
    def test_bone_jaw_profile_requires_explicit_opt_out(self):
        keys={'left':object(),'right':object()}
        obj=SimpleNamespace(data=SimpleNamespace(shape_keys=SimpleNamespace(key_blocks=keys)))
        profile={'schema':'blendshape-controls/1','mapping':{'eyeBlinkLeft':'left','eyeBlinkRight':'right'}}
        with self.assertRaises(ValueError):BlendshapeController([obj],profile)
        profile['require_jaw_morph']=False
        self.assertEqual(len(BlendshapeController([obj],profile).bindings),2)
