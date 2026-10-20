import os,sys,tempfile,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import cast_registry as cr,gaits
def rec(**k):return dict(dict(id='mara',name='Mara',species='fox'),**k)
class Records(unittest.TestCase):
 def test_validate_catches_each_mistake(self):
  for bad in (dict(id='Mara'),dict(species='dragon'),dict(accessories=['jetpack']),dict(posture='slouch'),dict(tint=[3,0,0]),dict(height=9),dict(voice_pitch=10),dict(pace=3),dict(accessories=['crown','hat_top'])):
   self.assertTrue(cr.validate(rec(**bad)),bad)
  self.assertEqual(cr.validate(rec(accessories=['scarf','satchel','hat_cap'])),[])
 def test_resolve_scales_from_species_height_and_overrides(self):
  L=cr.resolve(rec());self.assertAlmostEqual(L['scale'][2],cr.SPECIES['fox']['height']/cr.LION_HEIGHT,3);self.assertLess(L['scale'][0],L['scale'][2])
  L2=cr.resolve(rec(height=1.71,width=1.0,depth=1.0));self.assertEqual(L2['scale'],(1.0,1.0,1.0))
  self.assertEqual(cr.resolve(rec(tint=[1,0,0]))['tint'],(1,0,0))
 def test_parts_override_by_kind_and_can_be_removed(self):
  L=cr.resolve(rec(parts=[dict(kind='ears',shape='long')]));self.assertEqual([p['shape'] for p in L['parts'] if p['kind']=='ears'],['long']);self.assertTrue(any(p['kind']=='tuft' for p in L['parts']))
  self.assertFalse(any(p['kind']=='tuft' for p in cr.resolve(rec(no_parts=['tuft']))['parts']))
 def test_gait_follows_posture_and_exists(self):
  for p in cr.POSTURES:
   self.assertEqual(cr.GAIT_BY_POSTURE[p],gaits.POSTURE_GAIT[p]);self.assertIn(cr.GAIT_BY_POSTURE[p],gaits.GAITS)
  self.assertEqual(cr.resolve(rec(posture='tired'))['gait'],'shuffle')
 def test_pitch_is_stable_and_in_species_range(self):
  a=cr.resolve(rec())['pitch'];self.assertEqual(a,cr.resolve(rec())['pitch']);lo,hi=cr.SPECIES['fox']['pitch'];self.assertTrue(lo<=a<=hi)
  self.assertEqual(cr.resolve(rec(voice_pitch=120))['pitch'],120)
class Registry(unittest.TestCase):
 def test_roundtrip_json(self):
  r=cr.Registry([rec(),rec(id='bram',name='Bram',species='bear',accessories=['staff'])]);p=os.path.join(tempfile.mkdtemp(),'c.json');r.save(p);r2=cr.Registry.load(p)
  self.assertEqual(r2.ids(),['mara','bram']);self.assertEqual(r2.resolve('bram')['accessories'][0]['kind'],'staff')
 def test_unknown_id_names_the_known_ones(self):
  with self.assertRaises(KeyError) as e:cr.Registry([rec()]).get('zed')
  self.assertIn('mara',str(e.exception))
 def test_add_rejects_invalid(self):
  with self.assertRaises(cr.CastError):cr.Registry().add(rec(species='dragon'))
 def test_merge_reports_replaced(self):
  a=cr.Registry([rec()]);b=cr.Registry([rec(posture='proud'),rec(id='x',name='X')]);self.assertEqual(a.merge(b),['mara']);self.assertEqual(a.get('mara')['posture'],'proud');self.assertIn('x',a.ids())
 def test_distinct_report_flags_twins(self):
  r=cr.Registry([rec(id='a',name='A'),rec(id='b',name='B'),rec(id='c',name='C',species='ox')]);rep=r.distinct_report();self.assertEqual([(x[0],x[1]) for x in rep],[('a','b')])
 def test_story_export(self):
  r=cr.Registry([rec(accessories=['scarf'])]);o=r.export_story_records()[0];self.assertEqual(o['name'],'Mara');self.assertIn('scarf',o['description']);self.assertEqual(o['species'],'fox')
class FromSeries(unittest.TestCase):
 def test_words_become_a_look(self):
  r=cr.from_series_character({'name':'Old Bram','details':'a gruff old bear in a wizard hat with a staff and a scarf','character_type':'animal'})
  self.assertEqual(r['id'],'old_bram');self.assertEqual(r['species'],'bear');self.assertIn('hat_wizard',r['accessories']);self.assertIn('staff',r['accessories']);self.assertEqual(r['posture'],'angry');self.assertEqual(cr.validate(r),[])
 def test_unknown_species_is_stable(self):
  a=cr.from_series_character({'name':'Zog','details':'a quiet figure'});self.assertEqual(a,cr.from_series_character({'name':'Zog','details':'a quiet figure'}));self.assertEqual(cr.validate(a),[])
 def test_size_words(self):
  self.assertLess(cr.from_series_character({'name':'Pip','details':'a tiny mouse'})['height'],cr.SPECIES['mouse']['height'])
if __name__=='__main__':unittest.main()
import cast_builder as cb
class Builder(unittest.TestCase):
 def look(self,**k):return cr.resolve(dict(dict(id='t',name='T',species='lion',accessories=list(cr.ACCESSORIES)[:0]),**k))
 def test_every_accessory_builds_known_bones_and_sane_sizes(self):
  for a in cr.ACCESSORIES:
   if a.startswith(('hat','crown','helmet')) is False or True:
    ps=cb.accessory_prims(self.look(accessories=[a]))
    self.assertTrue(ps,a)
    for p in ps:
     self.assertIn(p['bone'],cb.BONES);self.assertTrue(all(0<x<2.5 for x in p['scale']),(a,p['scale']));self.assertTrue(all(abs(v)<3 for v in p['loc']))
 def test_head_items_sit_on_the_head(self):
  for a in ('hat_top','hat_wizard','crown','helmet','hat_cap','hat_straw'):
   for p in cb.accessory_prims(self.look(accessories=[a])):self.assertGreater(p['loc'][2],1.6,a)
 def test_every_species_part_builds(self):
  for sp in cr.SPECIES:
   for p in cb.part_prims(self.look(species=sp)):self.assertIn(p['bone'],cb.BONES)
 def test_staff_follows_the_hand(self):
  ps=cb.accessory_prims(self.look(accessories=['staff']),hand_r=(-.4,-.2,.7));self.assertTrue(all(p['loc'][:2]==(-.4,-.2) for p in ps));self.assertTrue(all(p['bone']=='hand_r' for p in ps))
 def test_unnamed_colour_is_stable_per_character(self):
  a=cb.accessory_prims(self.look(accessories=['scarf']))[0]['color'];self.assertEqual(a,cb.accessory_prims(self.look(accessories=['scarf']))[0]['color'])
