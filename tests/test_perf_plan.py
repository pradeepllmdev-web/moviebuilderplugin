import math,os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import cast_registry as cr,perf_plan as pp,perf_camera as pc,perf_locations as pl,perf_audio as pa,gaits
import numpy as np
REG=cr.Registry([dict(id='mara',name='Mara',species='fox',posture='jaunty'),dict(id='bram',name='Bram',species='bear',posture='tired'),dict(id='leo',name='Leo',species='lion')])
def spec(steps,cast=None,props=None,loc=None):
 return dict(id='t',location=loc or dict(preset='village_square'),cast=cast or [dict(id='mara',at=[-8,-6],face=[0,0]),dict(id='bram',at=[6,-5],face='mara')],props=props or [],steps=steps)
def go(who,to,**k):return dict(do='go',who=who,to=to,**k)
class Routing(unittest.TestCase):
 def test_direct_when_clear(self):self.assertEqual(len(pp.route((0,0),(10,0),[(5,8,1)])),2)
 def test_detours_around_a_circle(self):
  path=pp.route((0,0),(10,0),[(5,0,1.5)])
  self.assertGreater(len(path),2)
  for a,b in zip(path,path[1:]):
   for k in range(21):
    x=a[0]+(b[0]-a[0])*k/20;y=a[1]+(b[1]-a[1])*k/20;self.assertGreaterEqual(math.hypot(x-5,y),1.5)
 def test_steady_speed(self):
  smp=pp.polyline_samples([(0,0),(3,0),(3,4)],1.4);d=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(smp,smp[1:])]
  self.assertAlmostEqual(max(d)*24,1.4,1);self.assertAlmostEqual(sorted(d)[len(d)//2]*24,1.4,1)
class Compile(unittest.TestCase):
 def run_(self,steps,**k):return pp.compile(spec(steps,**k),REG)
 def test_walk_reaches_target_with_gait_speed_and_clean_audit(self):
  P=self.run_([go('mara','well',stop=2.)]);a=P.actors['mara'];self.assertAlmostEqual(math.hypot(a.X[-1]-0,a.Y[-1]-0),2.,0);self.assertEqual(P.audit(),[])
  (t0,t1,g,sc,speed)=a.walks[0];self.assertEqual(g,'bounce');self.assertAlmostEqual(speed,gaits.natural_speed('bounce')*a.size,3)
  self.assertAlmostEqual(gaits.play_scale(g,speed,a.size),1.,3)
 def test_clips_are_contiguous_and_cover_everything(self):
  P=self.run_([go('mara','well',stop=2.),dict(do='say',who='mara',text='Hello there friend.',to='bram'),dict(do='act',who='bram',clip='wave')])
  for a in P.actors.values():
   self.assertAlmostEqual(a.clips[0][0],0.);self.assertAlmostEqual(a.clips[-1][1],P.seconds,1)
   for c,d in zip(a.clips,a.clips[1:]):self.assertAlmostEqual(c[1],d[0],3)
 def test_lines_never_overlap_and_listener_reacts(self):
  P=self.run_([dict(do='say',who='mara',text='We should leave before the storm arrives.',mood='concern',to='bram'),dict(do='say',who='bram',text='No.',mood='serious',to='mara')])
  self.assertEqual(len(P.lines),2);self.assertLess(P.lines[0]['t1'],P.lines[1]['t0']);self.assertTrue(any(c[2]=='think' for c in P.actors['bram'].clips))
 def test_two_lines_at_once_rejected(self):
  with self.assertRaises(pp.SpecError):self.run_([[dict(do='say',who='mara',text='a b c'),dict(do='say',who='bram',text='d e f')]])
 def test_unknown_character_and_beat(self):
  with self.assertRaises(pp.SpecError):self.run_([go('zed','well')])
  with self.assertRaises(pp.SpecError):self.run_([dict(do='dance',who='mara')])
 def test_same_actor_twice_in_a_step_rejected(self):
  with self.assertRaises(pp.SpecError):self.run_([[go('mara','well'),dict(do='act',who='mara',clip='wave')]])
 def test_getup_needs_a_fall(self):
  with self.assertRaises(pp.SpecError):self.run_([dict(do='act',who='mara',clip='getup')])
  P=self.run_([dict(do='act',who='mara',clip='fall'),dict(do='act',who='mara',clip='getup')]);self.assertEqual(P.actors['mara'].state,'stand')
 def test_cannot_act_while_down(self):
  with self.assertRaises(pp.SpecError):self.run_([dict(do='act',who='mara',clip='fall'),dict(do='act',who='mara',clip='wave')])
 def test_sit_and_stand(self):
  P=self.run_([dict(do='sit',who='mara',on='bench_a.0',face='well'),dict(do='wait',dur=2),dict(do='stand',who='mara')]);c=[x for x in P.actors['mara'].clips if x[2]=='sit']
  self.assertEqual(len(c),2);self.assertTrue(c[0][4].get('hold'));self.assertTrue(c[1][4].get('reverse'));self.assertEqual(P.audit(),[])
 def test_seat_taken_and_unknown(self):
  with self.assertRaises(pp.SpecError):self.run_([dict(do='sit',who='mara',on='bench_a.0'),dict(do='sit',who='bram',on='bench_a.0')])
  with self.assertRaises(pp.SpecError):self.run_([dict(do='sit',who='mara',on='nowhere.0')])
 def test_cannot_act_while_seated(self):
  with self.assertRaises(pp.SpecError):self.run_([dict(do='sit',who='mara',on='bench_a.0'),dict(do='act',who='mara',clip='wave')])
 def test_collision_is_audited(self):
  P=self.run_([[go('mara',[0,0],stop=0.),go('bram',[0,0],stop=0.)]]);self.assertTrue(any('collision' in a for a in P.audit()))
 def test_walking_through_a_room_is_routed_around(self):
  P=pp.compile(spec([go('mara',[4,0])],cast=[dict(id='mara',at=[-3,0],face=[1,0]),dict(id='bram',at=[0,-3],face=[0,1])],loc=dict(preset='room')),REG);self.assertEqual([a for a in P.audit() if 'obstacle' in a],[])
class Props(unittest.TestCase):
 def base(self,steps):
  return pp.compile(spec(steps,props=[dict(id='cup',kind='cup',at=[-1,0],z=.9),dict(id='crate',kind='crate',at=[2,3],z=.9)],cast=[dict(id='mara',at=[-4,0],face=[1,0]),dict(id='bram',at=[4,0],face=[-1,0])],loc=dict(preset='meadow')),REG)
 def test_take_carries_the_prop_in_the_hand(self):
  P=self.base([dict(do='take',who='mara',prop='cup')]);e=[x for x in P.events if x['kind']=='take'][0];t=P.seconds-.5;a=P.actors['mara']
  infl,hp=P.hand_target(a,'R',t);cp=P.props['cup'].at(t,P);self.assertAlmostEqual(infl,1.);self.assertLess(math.dist(hp,cp),.05)
  self.assertEqual(a.holding,'cup');self.assertGreater(e['t_grasp'],e['t0'])
 def test_take_out_of_reach_is_a_spec_error(self):
  with self.assertRaises(pp.SpecError):pp.compile(spec([dict(do='take',who='mara',prop='cup')],props=[dict(id='cup',kind='cup',at=[0,0],z=.1)],cast=[dict(id='mara',at=[-4,0],face=[1,0])],loc=dict(preset='meadow')),REG)
 def test_boulder_cannot_be_carried(self):
  with self.assertRaises(pp.SpecError):pp.compile(spec([dict(do='take',who='mara',prop='b')],props=[dict(id='b',kind='boulder',at=[0,0],z=.9)],cast=[dict(id='mara',at=[-4,0])],loc=dict(preset='meadow')),REG)
 def test_put_leaves_it_at_the_place(self):
  P=self.base([dict(do='take',who='mara',prop='cup'),dict(do='put',who='mara',at=[0,2])]);x,y,z=P.props['cup'].at(P.seconds,P);self.assertAlmostEqual(x,0,2);self.assertAlmostEqual(y,2,2);self.assertEqual(P.actors['mara'].holding,None)
 def test_give_hands_it_over(self):
  P=self.base([dict(do='take',who='mara',prop='cup'),dict(do='give',who='mara',to='bram')]);self.assertEqual(P.actors['bram'].holding,'cup');self.assertIsNone(P.actors['mara'].holding)
  t=P.seconds-.4;self.assertLess(math.dist(P.hand_target(P.actors['bram'],'R',t)[1],P.props['cup'].at(t,P)),.06)
 def test_push_moves_the_prop(self):
  P=self.base([dict(do='push',who='mara',prop='crate',dist=1.5,dir=0)]);x,y,z=P.props['crate'].at(P.seconds,P);self.assertAlmostEqual(x,2+1.5,1)
 def test_cannot_hold_two(self):
  with self.assertRaises(pp.SpecError):self.base([dict(do='take',who='mara',prop='cup'),dict(do='take',who='mara',prop='crate')])
class Queries(unittest.TestCase):
 def test_footsteps_alternate_feet_and_follow_the_gait(self):
  P=pp.compile(spec([go('mara','well',stop=2.)]),REG);st=P.footsteps();self.assertGreater(len(st),8);self.assertEqual([s[2] for s in st[:4]],['L','R','L','R'])
  (t0,t1,g,sc,sp)=P.actors['mara'].walks[0];self.assertAlmostEqual(st[1][0]-st[0][0],gaits.cycle_seconds(g,sc)/2,3)
 def test_gaze_goes_to_the_speaker_then_rests(self):
  P=pp.compile(spec([dict(do='say',who='mara',text='Look over there now.',to='bram')]),REG);L=P.lines[0];m=(L['t0']+L['t1'])/2
  self.assertEqual(P.gaze('mara',m),('char','bram'));self.assertEqual(P.gaze('bram',m),('char','mara'))
class Camera(unittest.TestCase):
 def plan(self):
  return pp.compile(spec([go('mara','well',stop=2.),dict(do='say',who='mara',text='We should not be here after dark.',mood='concern',to='bram'),dict(do='say',who='bram',text='Nonsense, sit down.',to='mara'),dict(do='say',who='mara',text='Fine, only for a moment.',to='bram'),dict(do='act',who='bram',clip='wave')]),REG)
 def test_cuts_cover_the_scene_without_gaps_and_end_wide(self):
  P=self.plan();C=pc.direct(P);self.assertAlmostEqual(C[0]['t0'],0.);self.assertAlmostEqual(C[-1]['t1'],P.seconds,1);self.assertEqual(C[0]['kind'],'wide')
  for a,b in zip(C,C[1:]):self.assertAlmostEqual(a['t1'],b['t0'],3)
  self.assertEqual(C[-1]['kind'],'wide')
 def test_no_short_or_long_shots(self):
  for c in pc.direct(self.plan()):self.assertGreaterEqual(c['t1']-c['t0'],pc.MIN_SHOT-1e-6);self.assertLessEqual(c['t1']-c['t0'],pc.MAX_SHOT+pc.MIN_SHOT)
 def test_every_line_is_covered_by_its_speaker_or_a_two_shot(self):
  P=self.plan();C=pc.direct(P)
  for L in P.lines:
   mid=(L['t0']+L['t1'])/2;c=[c for c in C if c['t0']<=mid<c['t1']][0];self.assertIn(c['kind'],('ots','two','single','wide'))
 def test_frames_are_finite_and_cameras_above_ground(self):
  P=self.plan()
  for c in pc.direct(P):
   for u in (.1,.5,.9):
    pos,aim,lens=pc.frame(P,c,c['t0']+(c['t1']-c['t0'])*u);self.assertTrue(all(math.isfinite(v) for v in list(pos)+list(aim)));self.assertGreater(pos[2],.2);self.assertGreater(lens,15)
class Locations(unittest.TestCase):
 def test_every_preset_lays_out(self):
  for k in pl.PRESETS:
   L=pl.layout(dict(preset=k,seed=3));ids=[o['id'] for o in L['objects']];self.assertEqual(len(ids),len(set(ids)))
   for p in pl.prims(L['loc']):
    if isinstance(p,tuple):continue
    self.assertTrue(all(math.isfinite(v) for v in p['loc']+p['scale']))
 def test_unknown_kind_and_preset(self):
  with self.assertRaises(ValueError):pl.layout(dict(objects=[dict(kind='ufo')]))
  with self.assertRaises(ValueError):pl.layout(dict(preset='moon'))
 def test_duplicate_ids_rejected(self):
  with self.assertRaises(ValueError):pl.layout(dict(objects=[dict(kind='rock',id='a'),dict(kind='tree',id='a')]))
 def test_same_seed_same_location(self):self.assertEqual(pl.layout(dict(preset='forest_clearing',seed=4))['obstacles'],pl.layout(dict(preset='forest_clearing',seed=4))['obstacles'])
 def test_seats_and_surfaces(self):
  L=pl.layout(dict(objects=[dict(kind='bench',id='b',at=[0,0],w=2.1),dict(kind='table',id='t',at=[5,0])]));self.assertEqual(len([k for k in L['seats'] if k.startswith('b.')]),3);self.assertIn('t',L['surfaces']);self.assertAlmostEqual(L['surfaces']['t'][2],.8)
 def test_prop_kinds_have_sizes_and_carry(self):
  for k,v in pl.PROP_KINDS.items():self.assertEqual(len(v['size']),3);self.assertIn(v['carry'],('both','R','L',None))
class Audio(unittest.TestCase):
 def test_everything_renders_finite(self):
  rng=np.random.default_rng(1);N=22050*3
  for k in pa.AMBIENCES:x=pa.ambience(k,N,22050,rng);self.assertEqual(len(x),N);self.assertTrue(np.isfinite(x).all())
  for k in pa.MUSIC:x=pa.music(k,N,22050,2);self.assertEqual(len(x),N);self.assertTrue(np.isfinite(x).all())
  for k in pa.SFX:self.assertTrue(np.isfinite(pa.sfx(k,22050,rng)).all())
 def test_music_is_reproducible_per_seed(self):
  a=pa.music('calm',22050*4,22050,5);self.assertTrue(np.array_equal(a,pa.music('calm',22050*4,22050,5)));self.assertFalse(np.array_equal(a,pa.music('calm',22050*4,22050,6)))
 def test_mix_places_events(self):
  x=pa.mix_events(22050,22050,[(.5,np.ones(100),1.)]);self.assertEqual(np.nonzero(x)[0][0],11025)
class Gaits(unittest.TestCase):
 def test_speed_table(self):
  for g in gaits.GAITS:self.assertGreater(gaits.natural_speed(g),.1)
  self.assertAlmostEqual(gaits.play_scale('walk',gaits.natural_speed('walk')*1.5,1.5),1.)
  self.assertTrue(gaits.natural_speed('run')>gaits.natural_speed('walk')>gaits.natural_speed('shuffle'))
if __name__=='__main__':unittest.main()
