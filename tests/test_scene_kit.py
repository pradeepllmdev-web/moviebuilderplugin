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
 def test_paths_and_projectiles(self):
  segs=kit.run_path(0,0,30,[(10,11.4),(20,21.4)],4.)
  self.assertEqual([x[0] for x in segs],['run','jump','run','jump','run']);self.assertAlmostEqual(kit.path_x(segs,segs[-1][2]),30);self.assertAlmostEqual(kit.path_x(segs,segs[1][1]),9.75)
  p=kit.ballistic_to((0,0,3.2),(20,6,0),1.2,.6);self.assertAlmostEqual(p[0],10);self.assertAlmostEqual(p[1],3)
  self.assertAlmostEqual(kit.ballistic_to((0,0,3.2),(20,6,0),1.2,1.2)[2],0,places=6)
  self.assertAlmostEqual(kit.flight_time_to_ground(0,5),2*5/9.81)
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
  self.assertEqual(set_pieces.match('a prisoner escapes along the roof of a speeding train')[0],'great_escape')
  self.assertEqual(set_pieces.match('an avalanche hits the village and the crowd runs to the shelter')[0],'avalanche')
  self.assertEqual(set_pieces.match('an army besieges a castle with catapults')[0],'siege')
  self.assertEqual(set_pieces.match('six lions debate around a round table in the council hall')[0],'council')
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
class MoviePipeline(unittest.TestCase):
 def test_scene_params_validation(self):
  import scene_params as sp
  self.assertEqual(sp.get('{"time_of_day":"night","hero_tint":[1,0.5,0.5],"title":"x"}'),dict(time_of_day='night',hero_tint=(1.,.5,.5),title='x',location_state=None))
  d=sp.get('{"time_of_day":"moon","hero_tint":[9,0,0]}');self.assertIsNone(d['time_of_day']);self.assertIsNone(d['hero_tint'])
  self.assertEqual(sp.get('not json'),sp.defaults());self.assertEqual(sp.get(''),sp.defaults())
 def test_story_plan_routes_and_warns(self):
  import story_plan
  sep='\n\n'
  p=story_plan.plan(sep.join(['At dawn a prison train races over the plains.','At night an avalanche hits the village.','They talk quietly by the fire.']),hero_tint=(1,.8,.7))
  self.assertEqual([s['piece'] for s in p['scenes']],['great_escape','avalanche',None])
  self.assertEqual(p['scenes'][0]['params'],dict(time_of_day='dawn',hero_tint=[1,.8,.7]));self.assertEqual(p['scenes'][1]['params']['time_of_day'],'night')
  self.assertEqual(p['scenes'][2]['builder'],'shots');self.assertTrue(any('no set piece' in w for w in p['warnings']))
  q=story_plan.plan(sep.join(['It is night and a siege begins.','In bright daylight the army attacks the castle again.']))
  self.assertTrue(any('jump between night and day' in w for w in q['warnings']));self.assertTrue(any('same set piece' in w for w in q['warnings']))
 def test_build_movie_sequence_and_reuse(self):
  import build_movie,tempfile
  calls=[]
  def fake(piece,out=None,seconds=None,params=None):
   calls.append(piece);open(out,'w').write('x');return dict(ok=True,missing=[],audit=[],out=str(out))
  with tempfile.TemporaryDirectory() as d:
   story='\n\n'.join(['A train escape on the roof.','An avalanche hits at night.'])
   build_movie.run(story,d,build=fake);self.assertEqual(calls,['great_escape','avalanche'])
   build_movie.run(story,d,build=fake);self.assertEqual(calls,['great_escape','avalanche'])          # unchanged scenes are reused
   build_movie.run(story.replace('night','dusk'),d,build=fake);self.assertEqual(calls,['great_escape','avalanche','avalanche'])   # only the changed scene is rebuilt
class SharedLocations(unittest.TestCase):
 def test_registry_and_hash_paths(self):
  import locations
  self.assertEqual(set(locations.REGISTRY),{'mountain_village','citadel','arena_ruins','railway_plains','train_consist','catapult','winch','banner','ladder','egg_nest','council_hall','museum_hall','workshop','rapids','flood_valley','goblet','scroll','gavel','dino_valley','cliff_face','galleon','open_sea','knife'})
  a=locations.bank_path('citadel','intact');b=locations.bank_path('citadel','breached');self.assertNotEqual(a,b);self.assertTrue(a.name.startswith('citadel_intact_'))
  with self.assertRaises(ValueError):locations.ensure('castle_of_oz')
  with self.assertRaises(ValueError):locations.ensure('citadel','flooded')
 def test_hash_is_per_builder_and_params(self):
  import locations
  self.assertNotEqual(locations.bank_path('catapult').name.split('_')[-1],locations.bank_path('banner').name.split('_')[-1])
  self.assertNotEqual(locations.bank_path('ladder','intact',dict(height=5)),locations.bank_path('ladder','intact',dict(height=9)))
  self.assertEqual(locations.bank_path('ladder','intact',dict(height=5)),locations.bank_path('ladder','intact',dict(height=5)))
 def test_railway_params_pure(self):
  import locations
  p=locations.railway_params(54.);self.assertGreater(p['xv0'],600);self.assertAlmostEqual(p['xv1']-p['xv0'],95.);self.assertGreater(p['xmax'],p['xv1']);self.assertLess(p['x_br'],p['xv0'])
  self.assertEqual(p,locations.railway_params(54.))
 def test_every_piece_with_shared_assets_is_known(self):
  import locations,set_pieces
  for piece,props in locations.PROPS_OF.items():
   self.assertIn(piece,set_pieces.SET_PIECES)
   for pid,_ in props:self.assertIn(pid,locations.REGISTRY)
 def test_pure_terrain(self):
  import locations
  self.assertAlmostEqual(locations.village_terrain(100,0),-3.76);self.assertGreater(locations.village_terrain(-50,0),20);self.assertAlmostEqual(locations.village_terrain(50,0),-2.,delta=.5)
 def test_story_carries_damage_between_scenes(self):
  import story_plan
  p=story_plan.plan(chr(10).join(['']*0)+(chr(10)*2).join(['An avalanche hits the village at night.','Later, another avalanche hits the village.','An army besieges the castle.','At dusk the army attacks the castle again.']))
  self.assertEqual(p['scenes'][1]['params'].get('location_state'),'buried');self.assertNotIn('location_state',p['scenes'][0]['params'])
  self.assertTrue(any('revisits citadel after it was breached' in w for w in p['warnings']))
 def test_scene_params_location_state(self):
  import scene_params as sp
  self.assertEqual(sp.get('{"location_state":"buried"}')['location_state'],'buried');self.assertIsNone(sp.get('{"location_state":"flooded"}')['location_state'])
if __name__=='__main__':unittest.main()
