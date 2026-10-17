import unittest
from road_assembly import compile_streets,demo_recipe
class Roads(unittest.TestCase):
    def test_connected_cross(self):
        out=compile_streets(demo_recipe());self.assertEqual(len(out['links']),8);self.assertEqual(len(out['open_ports']),4)
        self.assertTrue(all(p['width_cm']==700 for p in out['connectors']))
    def test_closed_edge_rejected(self):
        with self.assertRaises(ValueError):compile_streets({'tiles':[dict(id='a',kind='straight',cell=[0,0]),dict(id='b',kind='straight',cell=[1,0],yaw=90)]})
    def test_duplicate_rejected(self):
        t=dict(id='a',kind='cross',cell=[0,0])
        with self.assertRaises(ValueError):compile_streets({'tiles':[t,t]})
    def test_turn(self):
        out=compile_streets({'tiles':[dict(id='a',kind='corner',cell=[0,0],yaw=90)]})
        self.assertEqual([p['normal'] for p in out['connectors']],[[1,0],[0,1]])
if __name__=='__main__':unittest.main()
