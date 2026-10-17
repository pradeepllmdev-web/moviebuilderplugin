import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from box_timeline import build,movie_stands
from box_camera import choose,blocks
from character_profiles import profile
from scene_prompt import validate
CARRY=profile('lion')['box']
PICKUP=[dict(action='box_pickup',duration=4),dict(action='box_back',duration=2,distance_cm=40),dict(action='turn',duration=3,angle_deg=-90,radius_cm=60),dict(action='box_carry',duration=4,distance_cm=120),dict(action='box_hold',duration=2)]
LANDING=[dict(action='box_bump',duration=3),dict(action='box_hold',duration=2),dict(action='box_setdown',duration=4),dict(action='idle',duration=2)]
def chain(*shots):
 stands=movie_stands(list(shots),CARRY);state=None;position=[0,0];heading=0;results=[]
 for segments in shots:
  result=build(segments,position,state,24,heading,CARRY,stands);results.append(result);state=result['end_state'];last=result['rows'][-1]
  position=[position[0]+last['root_cm'][0],position[1]+last['root_cm'][1]];heading=last['yaw']
 return results
class BoxTests(unittest.TestCase):
 def test_carry_requires_pickup(self):
  with self.assertRaises(ValueError):build([dict(action='box_carry',duration=3,distance_cm=100)])
 def test_state_survives_cut(self):
  first,second=chain(PICKUP,LANDING)
  self.assertEqual(first['rows'][-1]['location_cm'],second['rows'][0]['location_cm']);self.assertEqual(second['end_state']['phase'],'placed');self.assertEqual(first['end_state']['id'],second['end_state']['id'])
 def test_placed_box_stays_put_when_actor_idles(self):
  a=build([dict(action='box_pickup',duration=4),dict(action='box_setdown',duration=4)],carry=CARRY)
  b=build([dict(action='idle',duration=3)],[0,0],a['end_state'],carry=CARRY);self.assertEqual(b['rows'][0]['location_cm'],b['rows'][-1]['location_cm']);self.assertEqual(b['rows'][0]['hand_weight'],0)
 def test_box_root_steps_are_bounded(self):
  a=build(PICKUP,carry=CARRY)
  self.assertLess(max(math.dist(x['root_cm'],y['root_cm']) for x,y in zip(a['rows'],a['rows'][1:])),3)
 def test_held_box_clears_chin_and_belly(self):
  # Measured lion: chin/mane underside ~107cm, belly front 42.5cm at z95.
  w,d,h=CARRY['size_cm'];self.assertLessEqual(CARRY['hold_height_cm']+h/2,104);self.assertGreaterEqual(CARRY['hold_forward_cm']-d/2,43)
 def test_grips_are_within_arm_reach(self):
  w=CARRY['size_cm'][0];shoulder=(24,8,112);hand=(w/2+CARRY['grip_out_cm'],CARRY['hold_forward_cm']-CARRY['grip_back_cm'],CARRY['hold_height_cm']+CARRY['grip_up_cm'])
  self.assertLess(math.dist(shoulder,hand),.92*48)
 def test_walking_through_the_stand_is_rejected(self):
  with self.assertRaises(ValueError):build([dict(action='box_pickup',duration=4),dict(action='box_carry',duration=4,distance_cm=160)],carry=CARRY)
 def test_back_step_and_turn_clear_the_stand(self):
  first,second=chain(PICKUP,LANDING);self.assertGreater(first['stand_clearance']['minimum_gap_cm'],5);self.assertEqual(first['rows'][-1]['yaw'],-90)
 def test_future_stand_exists_in_first_shot(self):
  first,_=chain(PICKUP,LANDING);self.assertEqual(len(first['stands']),2)
 def test_box_turns_with_carrier(self):
  first,_=chain(PICKUP,LANDING);last=first['rows'][-1]
  self.assertEqual(last['box_yaw'],-90);self.assertAlmostEqual(last['location_cm'][0]-last['root_cm'][0],CARRY['hold_forward_cm'],3)
 def test_setdown_rests_on_stand(self):
  _,second=chain(PICKUP,LANDING);stand=second['end_state']['stands'][-1];box=second['rows'][-1]['location_cm']
  self.assertAlmostEqual(box[2]-CARRY['size_cm'][2]/2,stand['location_cm'][2],3);self.assertLess(math.dist(box[:2],stand['location_cm'][:2]),1)
 def test_side_camera_keeps_face_clear(self):
  for result in chain(PICKUP,LANDING):
   route=[{'location_cm':[r['root_cm'][0],r['root_cm'][1],0],'yaw':r['yaw']} for r in result['rows']]
   self.assertEqual(choose(route,result,'full',135)['covered_samples'],0)
 def test_front_camera_through_box_is_detected(self):
  self.assertTrue(blocks([0,400,95],[0,0,95],[0,57,88],0,[36,26,24]));self.assertFalse(blocks([400,57,95],[0,140,95],[0,-57,88],0,[36,26,24]))
 def test_only_lion_is_calibrated(self):
  p=dict(version=1,title='Box',character='rowan',environment='forest',mood='morning_fog',camera='full',segments=[dict(action='box_pickup',duration=4)])
  with self.assertRaises(ValueError):validate(p)
 def test_plan_validation_accepts_turning_carry(self):
  p=dict(version=1,title='Box',character='lion',environment='forest',mood='morning_fog',camera='full',segments=[dict(s) for s in PICKUP])
  self.assertEqual(validate(p)['segments'][1]['action'],'box_back')
if __name__=='__main__':unittest.main()
