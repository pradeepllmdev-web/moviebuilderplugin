import json,tempfile,unittest
from pathlib import Path
import numpy as np
from movie_production.performance_tracks import TypedPerformanceBank

class PerformanceBankTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);refs={}
        time=np.arange(21)/10;expression=np.tile([.45,.1,.5,0.],(21,1));expression[10,0]=.9
        for name,kind in [('talk_body','talk_gestures'),('head_attention','head_attention'),('face_expression','blink_brow_expression')]:
            refs[name]={'types':[kind]}
            np.savez(self.root/(name+'.npz'),time=time,head_angles=np.zeros((21,3)),expression=expression)
            (self.root/(name+'-capture.json')).write_text(json.dumps({'tracking_coverage':1}))
        (self.root/'bank.json').write_text(json.dumps({'schema':'performance-reference-bank/1','references':refs}))
    def tearDown(self):self.temp.cleanup()
    def bank(self):return TypedPerformanceBank(self.root/'bank.json')
    def test_types_are_not_interchangeable(self):
        with self.assertRaisesRegex(ValueError,'motion type'):self.bank().sample('talk_body',0,'blink_brow_expression')
    def test_narrow_neutral_eyes_do_not_become_a_blink(self):
        self.assertEqual(self.bank().facial_commands(0)['blink'],0)
        self.assertEqual(self.bank().facial_commands(1)['blink'],1)
    def test_target_speech_is_not_overwritten(self):
        commands=self.bank().facial_commands(1)
        self.assertNotIn('jaw',commands);self.assertNotIn('spread',commands)
    def test_failed_capture_cannot_be_selected(self):
        (self.root/'talk_body-capture.json').write_text(json.dumps({'tracking_coverage':.5}))
        with self.assertRaisesRegex(ValueError,'tracking gate'):self.bank()
