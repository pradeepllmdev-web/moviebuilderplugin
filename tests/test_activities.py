import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
import activities,drink_actions
from sit_actions import SIT_ACTIONS,CLIPS,SEATED,validate as validate_sitting
from scene_prompt import ACTIONS,SYSTEM,validate as validate_scene,require_requested_controls
# Seated lion, measured once from the evaluated body (cm, rig space, forward is -Y).
LION={"bones":{"Hips":[-2.66,-14.85,37.61],"Spine":[-2.59,-11.25,49.74],"Spine1":[-1.4,-12.5,62.27],"Spine2":[-0.66,-14.4,75.15],"Neck":[-0.3,-15.77,84.58],"Head":[-0.37,-13.68,91.17],"RightArm":[-25.06,-16.12,76.19],"RightForeArm":[-29.88,-25.26,55.43],"RightHand":[-24.29,-41.18,38.57]},"snout_tip":[-1.8,-66.7,97.1],"arm_reach":47.0,"torso":{"y_front":-32.7,"z_top":72.6,"z_bottom":24.7},"thighs":{"y_front":-42.5,"z_top":42.9,"z_bottom":19.1},"lower_legs":{"y_front":-43.5,"z_top":31.4,"z_bottom":0.1},"feet":{"y_front":-56.7,"z_top":17.3,"z_bottom":-3.6}}
def beat(action,duration=3,dialogue=''):return dict(action=action,duration=duration,dialogue=dialogue)
def scene(segments):return dict(version=1,title='Tea',character='lion',environment='forest',mood='morning_fog',camera='full',segments=segments)
class ActivityTests(unittest.TestCase):
 def test_registry_feeds_every_consumer(self):
  for name in activities.beats():
   self.assertIn(name,ACTIONS)
  for name in activities.beats('seat'):self.assertIn(name,SIT_ACTIONS);self.assertIn(name,CLIPS)
  self.assertIn('drink',SEATED);self.assertIn('Drinking:',SYSTEM)
 def test_drink_needs_a_seat_and_stays_seated(self):
  self.assertTrue(validate_sitting([beat('sit_down'),beat('drink',5)]))
  with self.assertRaises(ValueError):validate_sitting([beat('drink',5)],False)
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',5),beat('walk')]))
  validate_scene(scene([beat('sit_down'),beat('drink',5),beat('stand_up')]))
 def test_duration_limits(self):
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',2),beat('stand_up')]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('drink',9),beat('stand_up')]))
 def test_request_without_drink_beat_is_rejected(self):
  plan=scene([beat('sit_down'),beat('sit'),beat('stand_up')])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion sits down and drinks from a cup, then stands up')
  require_requested_controls(scene([beat('sit_down'),beat('drink',5),beat('stand_up')]),'The lion sits down and drinks from a cup, then stands up')
 def test_lion_drink_layout_is_feasible(self):
  l=activities.feasibility('drink',LION)
  self.assertTrue(l['ok']);self.assertLessEqual(l['hand_to_cup_cm'],6);self.assertEqual(l['reach_shortfall_cm'],0)
  self.assertGreater(l['table']['top_cm'],LION['feet']['z_top']+4);self.assertLess(l['table']['top_cm'],LION['bones']['RightArm'][2])
 def test_short_arms_are_reported_infeasible(self):
  short=copy.deepcopy(LION);short['arm_reach']=30.
  self.assertFalse(activities.feasibility('drink',short)['ok'])
 def test_nod_moves_the_muzzle_down_and_back(self):
  tip=drink_actions.nodded_tip(LION,25);self.assertLess(tip[2],LION['snout_tip'][2]);self.assertGreater(tip[1],LION['snout_tip'][1])
if __name__=='__main__':unittest.main()
class GestureTests(unittest.TestCase):
 def test_every_gesture_has_a_library_clip_preference(self):
  clips_file=Path(__file__).resolve().parents[2]/'blendplugin-next'/'scene_pipeline'/'realistic_clips.py'
  if not clips_file.exists():self.skipTest('shared clip library not checked out next to this repo')
  text=clips_file.read_text()
  for name in activities.GESTURES:self.assertIn("'"+name+"':",text)
 def test_gesture_requests_are_recognised_and_enforced(self):
  plan=scene([beat('idle',4)])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion waves hello')
  require_requested_controls(scene([beat('wave',4)]),'The lion waves hello')
 def test_gestures_validate_in_place_and_not_with_sitting(self):
  validate_scene(scene([beat('idle',2),beat('wave',4,'Hello!'),beat('bow',3)]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('wave',1),beat('idle')]))
  with self.assertRaises(ValueError):validate_scene(scene([beat('sit_down'),beat('wave',3),beat('stand_up')]))
 def test_planner_lists_the_gestures(self):
  for name in activities.GESTURES:self.assertIn(name+' (',SYSTEM)
class KnowledgeTests(unittest.TestCase):
 def test_unsupported_motions_must_be_reported(self):
  plan=scene([beat('idle',4)])
  with self.assertRaises(ValueError):require_requested_controls(plan,'The lion points ahead and then walks')
  ok=dict(plan,unsupported=['point: no pointing clip'])
  require_requested_controls(ok,'The lion points ahead and then walks')
  self.assertEqual(activities.unsupported_requests('from this point of view'),[])
 def test_planner_states_the_gaps(self):
  self.assertIn('has no clip for',SYSTEM);self.assertIn('unsupported',SYSTEM)
 def test_catalog_lists_every_activity_for_clients(self):
  catalog=activities.summary()
  self.assertEqual(set(catalog['activities']),set(activities.ACTIVITIES));self.assertIn('cry',catalog['unsupported'])
  self.assertTrue(catalog['activities']['drink']['seated']);self.assertIn('lift a cup',catalog['activities']['drink']['caveat'])
class CharacterTests(unittest.TestCase):
 def test_clip_activities_declare_their_characters(self):
  for name,a in activities.ACTIVITIES.items():
   self.assertTrue(a['characters']);self.assertIn('lion',a['characters'])
   if a.get('family')=='clip':self.assertEqual(set(a['characters']),{'lion','cat','rowan'})
  self.assertEqual(activities.ACTIVITIES['drink']['characters'],['lion'])
class ContactTests(unittest.TestCase):
 def test_world_and_rig_transforms_are_inverse(self):
  import contact_actions as ca
  for yaw in (0,35,-90,170):
   rig=to=ca.to_rig((120,-40,95),(100,-60),yaw);back=ca.to_world((rig[0]*100,rig[1]*100,rig[2]*100),(100,-60),yaw)
   self.assertAlmostEqual(back[0],120,4);self.assertAlmostEqual(back[1],-40,4);self.assertAlmostEqual(back[2],95,4)
 def test_actor_forward_is_rig_minus_y(self):
  import contact_actions as ca
  # An actor facing +Y (yaw 0) sees a point 50 cm ahead at rig -Y, and a point on its right at rig -X.
  ahead=ca.to_rig((0,50,0),(0,0),0);right=ca.to_rig((50,0,0),(0,0),0)
  self.assertAlmostEqual(ahead[1],-.5);self.assertAlmostEqual(right[0],-.5)
 def test_facing_points_at_the_partner(self):
  import contact_actions as ca
  self.assertAlmostEqual(ca.facing([0,0],[0,100]),0);self.assertAlmostEqual(ca.facing([0,0],[-100,0]),90)
 def test_stairs_rise_in_steps_and_never_fall(self):
  import contact_actions as ca
  h=[ca.stairs_height(d) for d in range(0,220,5)];self.assertEqual(h[0],0);self.assertTrue(all(b>=a for a,b in zip(h,h[1:])))
  self.assertAlmostEqual(h[-1],ca.STEP['rise_cm']*ca.STEP['count'],1)
 def test_pair_actions_check_spacing_and_matching_beats(self):
  import contact_actions as ca
  def actor(ch,x,action='handshake'):return dict(character=ch,position_cm=[x,0],segments=[dict(action=action,duration=4)])
  heights={'lion':185,'rowan':180}
  low,high=ca.window('handshake','lion','rowan');gap=(low+high)/2
  fields=ca.pair_inputs([actor('lion',-gap/2),actor('rowan',gap/2)],0,heights);self.assertIn('partner_contact',fields);self.assertAlmostEqual(fields['facing_yaw_deg'],0)
  with self.assertRaises(ValueError):ca.pair_inputs([actor('lion',-100),actor('rowan',100)],0,heights)
  with self.assertRaises(ValueError):ca.pair_inputs([actor('lion',-5),actor('rowan',5)],0,heights)
  with self.assertRaises(ValueError):ca.pair_inputs([actor('lion',-gap/2),actor('rowan',gap/2,'hug')],0,heights)
 def test_handshake_and_hug_need_two_actors(self):
  with self.assertRaises(ValueError):validate_scene(scene([beat('idle',2),beat('handshake',4)]))
 def test_pair_check_compares_wrists(self):
  import contact_actions as ca,tempfile,json
  row=lambda w:dict(frame=1,weight=1.,right_wrist_world=w,right_palm_world=w)
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'a',Path(d)/'b';a.mkdir();b.mkdir()
   (a/'contact-track.json').write_text(json.dumps(dict(action='handshake',track=[row([0,0,90])])));(b/'contact-track.json').write_text(json.dumps(dict(action='handshake',track=[row([3,0,90])])))
   self.assertTrue(ca.pair_check(a,b)['ok'])
   (b/'contact-track.json').write_text(json.dumps(dict(action='handshake',track=[row([30,0,90])])));self.assertFalse(ca.pair_check(a,b)['ok'])
class StoryToolsTests(unittest.TestCase):
 def _plan(self,shots):
  import previs
  return previs.lenient_validate(dict(version=1,title='t',unsupported=[],shots=shots))
 def _shot(self,title,actors):
  return dict(version=1,title=title,environment='forest',mood='morning_fog',camera='full',unsupported=[],notes=[],actors=actors)
 def _actor(self,ch,x,y,segments,**extra):return dict(character=ch,position_cm=[x,y],segments=segments,**extra)
 def test_layout_flags_actor_walking_into_stairs(self):
  import story_layout
  shots=[self._shot('a',[self._actor('lion',0,-100,[beat('climb_stairs',6)])]),self._shot('b',[self._actor('lion',0,-100,[dict(action='walk',duration=4,dialogue='',distance_cm=200)])])]
  findings=story_layout.layout(self._plan(shots),{})['findings']
  self.assertTrue(any(f['rule']=='blocking.scenery' and f['shot']==2 for f in findings))
 def test_layout_flags_walker_facing_sideways(self):
  import story_layout
  shots=[self._shot('a',[self._actor('lion',0,0,[dict(action='walk',duration=4,dialogue='',distance_cm=200)],facing_yaw_deg=90)])]
  self.assertTrue(any(f['rule']=='facing.walker' for f in story_layout.layout(self._plan(shots),{})['findings']))
 def test_lint_catches_place_change_without_travel(self):
  import story_lint
  shots=[self._shot('a',[self._actor('lion',0,0,[beat('wave',4)])]),self._shot('b',[self._actor('lion',0,0,[beat('wave',4)])])]
  direction=dict(sets=[dict(kind='forest',origin_cm=[0,0]),dict(kind='river',origin_cm=[6000,0])],shots={'a':dict(origin_cm=[0,0]),'b':dict(origin_cm=[6000,0])})
  self.assertTrue(any(f['rule']=='continuity.place_change' for f in story_lint.lint(self._plan(shots),direction)))
 def test_lint_requires_object_named_in_dialogue(self):
  import story_lint
  shots=[self._shot('a',[self._actor('lion',0,0,[beat('wave',4,'I found the little one!')])])]
  self.assertTrue(any(f['rule']=='dialogue.needs_object' for f in story_lint.lint(self._plan(shots),{})))
 def test_camera_solver_stays_out_of_walls_and_rooms(self):
  import story_camera,story_layout
  boxes=[story_layout.box(-280,-8,-51,8,'DoorWallL'),story_layout.box(51,-8,280,8,'DoorWallR'),story_layout.box(-280,430,280,450,'HutBack'),story_layout.box(-290,0,-270,440,'HutSideA'),story_layout.box(270,0,290,440,'HutSideB'),story_layout.box(-280,0,280,440,'Room','room')]
  shot=self._plan([self._shot('in',[self._actor('lion',0,200,[beat('wave',4)])])])['shots'][0]
  cam=story_camera.solve_shot(shot,(0,0),boxes)
  self.assertTrue(-235<cam['pos_cm'][0]<235 and 45<cam['pos_cm'][1]<395,cam)   # inside the room with the actor
  outside=self._plan([self._shot('out',[self._actor('lion',0,-200,[beat('wave',4)])])])['shots'][0]
  c2=story_camera.solve_shot(outside,(0,0),boxes);self.assertFalse(-290<c2['pos_cm'][0]<290 and -10<c2['pos_cm'][1]<450,c2)   # outside the building
class AnchorTests(unittest.TestCase):
 def _story(self,actors,place='hut'):
  shot=dict(version=1,title='s',environment='forest',mood='morning_fog',camera='full',unsupported=[],notes=[],actors=actors)
  direction=dict(sets=[dict(name='hut',kind='village',origin_cm=[18000,0])],shots={'s':dict(place=place)})
  return dict(version=1,title='t',unsupported=[],shots=[shot]),direction
 def _actor(self,ch,at,segments):return dict(character=ch,at=at,position_cm=[0,0],segments=segments)
 def test_anchor_becomes_coordinates_and_place_origin(self):
  import previs_anchors as pa
  plan,direction=self._story([self._actor('lion','door_front',[beat('open_door',5)])])
  p,d=pa.resolve(plan,direction);self.assertEqual(p['shots'][0]['actors'][0]['position_cm'],[-63,-60]);self.assertEqual(d['shots']['s']['origin_cm'],[18000,0]);self.assertTrue(d['auto_camera'])
 def test_pair_slots_face_each_other_when_talking_and_side_by_side_for_contact(self):
  import previs_anchors as pa
  plan,direction=self._story([self._actor('lion',('inside_center','left'),[beat('wave',4)]),self._actor('rowan',('inside_center','right'),[beat('wave',4)])])
  a=pa.resolve(plan,direction)[0]['shots'][0]['actors'];self.assertEqual((a[0]['facing_yaw_deg'],a[1]['facing_yaw_deg']),(-90.0,90.0));self.assertAlmostEqual(a[1]['position_cm'][0]-a[0]['position_cm'][0],pa.TALK_SPACING_CM)
  plan,direction=self._story([self._actor('lion',('inside_near','left'),[beat('hug',5)]),self._actor('rowan',('inside_near','right'),[beat('hug',5)])])
  a=pa.resolve(plan,direction)[0]['shots'][0]['actors'];self.assertEqual((a[0]['facing_yaw_deg'],a[1]['facing_yaw_deg']),(0,0))
  low,high=__import__('contact_actions').window('hug','lion','rowan');gap=a[1]['position_cm'][0]-a[0]['position_cm'][0];self.assertTrue(low<=gap<=high)
 def test_unknown_anchor_is_a_clear_error(self):
  import previs_anchors as pa
  plan,direction=self._story([self._actor('lion','nowhere',[beat('wave',4)])])
  with self.assertRaises(ValueError) as e:pa.resolve(plan,direction)
  self.assertIn('door_front',str(e.exception))
 def test_plans_without_anchors_are_untouched(self):
  import previs_anchors as pa
  plan,direction=self._story([dict(character='lion',position_cm=[1,2],segments=[beat('wave',4)])]);p,d=pa.resolve(plan,direction);self.assertIs(p,plan)
class StillnessAndDressingTests(unittest.TestCase):
 def _plan(self,segments):
  import previs
  shot=dict(version=1,title='s',environment='forest',mood='morning_fog',camera='full',unsupported=[],notes=[],actors=[dict(character='lion',position_cm=[0,0],segments=segments)])
  return previs.lenient_validate(dict(version=1,title='t',unsupported=[],shots=[shot]))
 def test_gesture_without_line_or_purpose_is_flagged(self):
  import story_lint
  rules=[f['rule'] for f in story_lint.lint(self._plan([beat('wave',4)]),{})];self.assertIn('purpose.gesture',rules)
  rules=[f['rule'] for f in story_lint.lint(self._plan([beat('wave',4,'Hello!')]),{})];self.assertNotIn('purpose.gesture',rules)
  p=self._plan([dict(beat('nod',4),purpose='agrees')]);self.assertNotIn('purpose.gesture',[f['rule'] for f in story_lint.lint(p,{})])
  self.assertNotIn('purpose.gesture',[f['rule'] for f in story_lint.lint(self._plan([beat('idle',4)]),{})])
 def test_limb_bones_are_held_but_head_and_spine_are_not(self):
  import stillness
  for name in ('LeftArm','RightForeArm','LeftHand','LeftHandIndex1','RightUpLeg','LeftFoot','RightToeBase','Hips'):
   self.assertTrue(any(k in name for k in stillness.HELD),name)
  for name in ('Head','Neck','Spine1','Spine2'):
   self.assertFalse(any(k in name for k in stillness.HELD),name)   # head, neck and spine keep moving
 def test_dressing_keeps_the_acting_zone_clear(self):
  import set_dressing as sd
  for theme in ('cafe','bakery','home'):
   for x0,y0,x1,y1,name in sd.solids(theme,0,0):
    inside=y1>0 and y0<sd.ROOM_DEPTH_CM
    if inside:self.assertFalse(x0<190 and x1>-190 and y0<520 and y1>120,(theme,name,x0,y0,x1,y1))   # |lat|<=190, depth 120..520 is where actors stand
 def test_every_theme_has_furniture_and_street_dressing(self):
  import set_dressing as sd
  for theme in ('cafe','bakery','home'):self.assertGreater(len(sd.interior(theme)),8);self.assertGreater(len(sd.exterior(theme)),8)
