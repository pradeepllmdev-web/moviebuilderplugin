import unittest
from movie_production.attention import attention_commands
SHOTS=[{'speaker':'snow','start':0,'duration':4},{'speaker':'jacob','start':4,'duration':4}]
class AttentionTests(unittest.TestCase):
    def test_partner_direction_is_mirrored(self):
        self.assertGreater(attention_commands('snow',2,SHOTS,1)['head_yaw'],0)
        self.assertLess(attention_commands('jacob',2,SHOTS,-1)['head_yaw'],0)
    def test_listener_looks_more_toward_partner(self):
        speaking=attention_commands('snow',2,SHOTS,1)['head_yaw']
        listening=attention_commands('snow',6,SHOTS,1)['head_yaw']
        self.assertGreater(listening,speaking)
    def test_turns_ease_across_dialogue_boundary(self):
        a=attention_commands('snow',3.99,SHOTS,1)['head_yaw']
        b=attention_commands('snow',4.01,SHOTS,1)['head_yaw']
        self.assertLess(abs(a-b),.03)
    def test_nod_has_held_neutral_rest_and_peak(self):
        self.assertEqual(attention_commands('snow',.1,SHOTS,1)['head_nod'],0)
        self.assertGreater(attention_commands('snow',1.25,SHOTS,1)['head_nod'],.6)
    def test_invalid_partner_side_rejected(self):
        with self.assertRaises(ValueError):attention_commands('snow',1,SHOTS,0)
