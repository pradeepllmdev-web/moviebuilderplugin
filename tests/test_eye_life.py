import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from eye_life import plan,CLOSE,HOLD,OPEN
from character_profiles import profile
FPS=24
TIMELINE=[dict(action='idle',start=0,end=3),dict(action='idle',start=3,end=6,look_yaw_deg=25),dict(action='talk',start=6,end=10,dialogue='Did you hear that?',look_yaw_deg=0)]
class EyeLifeTests(unittest.TestCase):
 def setUp(self):self.values=plan(240,FPS,TIMELINE,'Something in the trees',profile('lion')['eyes'])
 def test_blinks_before_line_and_attention_shift(self):
  starts=self.values['blink_starts']
  self.assertTrue(any(abs(s-round((3-.05)*FPS))<=1 for s in starts),starts)
  self.assertTrue(any(abs(s-round((6-.12)*FPS))<=1 for s in starts),starts)
 def test_blinks_are_spaced_and_inside_the_shot(self):
  starts=self.values['blink_starts']
  self.assertTrue(all(b-a>=1.2*FPS for a,b in zip(starts,starts[1:])));self.assertTrue(all(0<=s<=240-(CLOSE+HOLD+OPEN) for s in starts))
 def test_blink_closes_fully_and_reopens(self):
  s=self.values['blink_starts'][0];curve=self.values['blink']
  self.assertEqual(curve[s+CLOSE-1],1);self.assertEqual(curve[s+CLOSE+HOLD+OPEN-1],0);self.assertEqual(curve[s-1],0)
 def test_deterministic_per_shot(self):
  again=plan(240,FPS,TIMELINE,'Something in the trees',profile('lion')['eyes']);self.assertEqual(again['blink_starts'],self.values['blink_starts'])
 def test_gaze_stays_small_and_leads_head_turn(self):
  x=self.values['gaze_x'];self.assertLessEqual(max(map(abs,x)),.6)
  turn=round(3*FPS);self.assertGreater(x[turn-1],.3)
if __name__=='__main__':unittest.main()
