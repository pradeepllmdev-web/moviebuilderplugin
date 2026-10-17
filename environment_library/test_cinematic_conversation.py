import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'3dobjectnew/server'))
from studio_plans import blender_shot
class Conversation(unittest.TestCase):
 def test_speaker_gestures_while_partner_listens(self):
  shot={'title':'Conversation','duration':8,'lines':[{'character':'Amber','start':1,'end':3,'text':'Hello','audio':'a.wav'},{'character':'Leo','start':4,'end':6,'text':'Hello back','audio':'b.wav'}]}
  plan=blender_shot(shot,['Amber','Leo'],cinematic=True)
  for actor,speaking_at,listening_at in zip(plan['actors'],[2,5],[5,2]):
   action=lambda at:next(s['action'] for s in actor['segments'] if s['start']<=at<s['end'])
   self.assertEqual(action(speaking_at),'talk');self.assertEqual(action(listening_at),'listen')
   self.assertEqual(actor['segments'][0]['start'],0);self.assertEqual(actor['segments'][-1]['end'],8)
if __name__=='__main__':unittest.main()
