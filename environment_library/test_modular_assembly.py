import unittest
from modular_assembly import compile_recipe,room_recipe

class AssemblyTests(unittest.TestCase):
    def test_door_clearance(self):
        out=compile_recipe({'parts':[dict(id='entry',kind='door',position_cm=[0,0,0])]})
        self.assertEqual(out['anchors'][0]['clearance_cm'],[100,220])
        # No geometry intrudes into the walkable centre of the opening.
        for b in out['boxes']:
            x,y,z=b['position_cm'];w,d,h=b['size_cm']
            self.assertTrue(abs(x)-w/2>=50 or z-h/2>=220)
    def test_rotated_connector(self):
        out=compile_recipe({'parts':[dict(id='w',kind='wall',position_cm=[200,400,0],yaw=90)]})
        self.assertEqual([c['position_cm'] for c in out['connectors']],[[200,300,0],[200,500,0]])
    def test_recipe_sizes(self):
        for w,d in [(2,2),(4,3),(6,5)]:
            out=compile_recipe(room_recipe(w,d))
            self.assertEqual(sum(p.endswith('_floor') for p in out['parts']),w*d)
            self.assertEqual(len(out['anchors']),1)
    def test_invalid(self):
        for pos in ([1,0,0],[0,0,float('nan')]):
            with self.assertRaises(ValueError):compile_recipe({'parts':[dict(id='w',kind='wall',position_cm=pos)]})
        p=dict(id='a',kind='wall',position_cm=[0,0,0])
        with self.assertRaises(ValueError):compile_recipe({'parts':[p,p]})
if __name__=='__main__':unittest.main()
