import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'environment_library'))
import scene_kit as kit,set_pieces
HB=lambda x:3.2*max(.02,(1-(x/9.)**4))**.65
class SceneKit(unittest.TestCase):
 def test_smooth_bounds(self):
  self.assertEqual(kit.smooth(-1),0);self.assertEqual(kit.smooth(2),1);self.assertAlmostEqual(kit.smooth(.5),.5)
 def test_catmull_hits_keys_and_clamps(self):
  pts=[(0,(0,0,0)),(1,(1,2,3)),(2,(4,2,0))]
  for t,p in pts:self.assertTrue(all(abs(a-b)<1e-9 for a,b in zip(kit.catmull(pts,t),p)))
  self.assertEqual(kit.catmull(pts,-5),(0,0,0));self.assertEqual(kit.catmull(pts,9),(4,2,0))
 def test_hull_pushes_up_or_out(self):
  s=[('hull',(9.,HB,1.6))]
  x,y,z=kit.push_out((0,0,1.0),.5,s);self.assertGreaterEqual(z,2.1-1e-9)          # inside the hull: lifted onto the deck
  x,y,z=kit.push_out((0,3.0,1.0),.5,s);self.assertGreater(abs(y),3.0)           # near the side: pushed outward
  self.assertEqual(kit.push_out((0,8,5),.5,s),(0,8,5))                           # free point untouched
 def test_mast_and_box(self):
  s=[('cyl',(0,0,1.6,13,.22)),('box',(-8.5,-5.5,-2,2,-5,2.85))]
  x,y,z=kit.push_out((.1,0,5),.5,s);self.assertGreaterEqual(math.hypot(x,y),.22+.45-1e-9)
  x,y,z=kit.push_out((-7,0,2),.5,s);self.assertTrue(z>=3.35-1e-9 or abs(x+7)>1.4 or abs(y)>2.4)
 def test_ground_lift(self):
  lift=kit.ground_lift({1:1.0,3:1.6,5:1.7,7:2.0},1.6,0.,1.,0)
  self.assertAlmostEqual(lift[1],.6);self.assertEqual(lift[5],0.);self.assertEqual(lift[7],0.)
  clamped=kit.ground_lift({1:-5},0,0,.5,0);self.assertEqual(clamped[1],.5)
  smooth=kit.ground_lift({1:0,3:-1,5:0},0,0,1,1);self.assertLess(smooth[3],1.)
 def test_stride_play_speed_stays_natural(self):
  play,slide=kit.stride_play_speed(9.,4.9,13);self.assertTrue(.8<=play<=1.2)
  play,slide=kit.stride_play_speed(20.,4.9,13);self.assertEqual(play,1.2);self.assertGreater(slide,1.2)   # too fast for the clip: report residual sliding instead of strobing
 def test_jump_physics(self):
  self.assertAlmostEqual(kit.flight_apex(.7),9.81*.49/8)
  self.assertAlmostEqual(kit.ballistic(.5,.6),.6);self.assertEqual(kit.ballistic(0,.6),0);self.assertEqual(kit.ballistic(1,.6),0)
  p=kit.jump_profile(5.35,5.0,5.7);self.assertEqual(p['tuck'],1.0)
  self.assertLess(kit.jump_profile(4.85,5.0,5.7)['dz'],0);self.assertLess(kit.jump_profile(5.85,5.0,5.7)['dz'],0);self.assertEqual(kit.jump_profile(9,5.0,5.7)['tuck'],0)
 def test_lessons_unique_and_complete(self):
  ids=[l['id'] for l in kit.LESSONS];self.assertEqual(len(ids),len(set(ids)))
  for l in kit.LESSONS:self.assertTrue(all(l[k] for k in('symptom','cause','rule')))
 def test_set_piece_routing(self):
  self.assertEqual(set_pieces.match('a lion fights a sea serpent on a ship in a storm')[0],'storm_ship')
  self.assertEqual(set_pieces.match('raptors chase a lion near a volcano and a triceratops')[0],'last_egg')
  self.assertEqual(set_pieces.match('a herd of horses gallops past a river')[0],'horse_herd')
  self.assertEqual(set_pieces.match('Rowan rides a horse across the meadow')[0],'rider')
  self.assertEqual(set_pieces.match('a lion free climbs a cliff and rappels down with a lost cub')[0],'cliff_rescue')
  self.assertEqual(set_pieces.match('two lions fight in a gladiator arena')[0],'arena_duel')
  self.assertEqual(set_pieces.match('lion drinks tea in a cafe'),[])
 def test_docs_cover_every_lesson_and_piece(self):
  text=set_pieces.docs()
  for l in kit.LESSONS:self.assertIn('| '+l['id']+' |',text)
  for k in set_pieces.SET_PIECES:self.assertIn('`'+k+'`',text)
 def test_planner_text_names_all_pieces(self):
  t=set_pieces.planner_text()
  for k in set_pieces.SET_PIECES:self.assertIn(k,t)
  import scene_prompt;self.assertIn('set_piece:<id>',scene_prompt.SYSTEM)
 def test_missing_reports_without_downloading(self):
  self.assertIsInstance(set_pieces.missing('last_egg'),list)
if __name__=='__main__':unittest.main()
