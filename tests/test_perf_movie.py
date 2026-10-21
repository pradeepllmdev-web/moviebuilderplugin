import json,os,sys,tempfile,unittest
from pathlib import Path
ENV=Path(__file__).resolve().parents[1]/'environment_library'
sys.path.insert(0,str(ENV))
import perf_dsl as d,perf_movie as pm,perf_plan as pp,cast_registry as cr
FILMS=sorted((ENV/'films').glob('*.py'))
class Dsl(unittest.TestCase):
 def test_scene_spreads_convo_but_keeps_par(self):
  s=d.scene('a','A',d.loc('hall'),[d.at('x',0,0)],[d.convo([('x','hi'),('y','yo','joy')]),d.par(d.say('x','a'),d.say('y','b')),d.go('x','center')])
  self.assertEqual(len(s['steps']),4);self.assertIsInstance(s['steps'][2],list)
 def test_helpers_build_plain_json(self):
  s=d.scene('a','A',d.loc('hall',3),[d.at('x',0,0,face=(1,2))],[d.take('x','cup','R'),d.put('x',at=(1,2)),d.push('x','box',2,90),d.sit('x','b.0',face='y'),d.sfx('bell',1.)],props=[d.prop('cup','cup',0,0,z=.9)])
  json.dumps(s)
class Films(unittest.TestCase):
 def test_there_are_two_films(self):self.assertGreaterEqual(len(FILMS),2)
 def test_every_film_plans_clean_and_is_about_fifteen_minutes(self):
  for f in FILMS:
   film=pm.load_film(f);rows=pm.plan_check(film)
   tm=film.get('target_minutes',15);self.assertGreaterEqual(len(film['scenes']),round(tm*1.2),f.name)
   for r in rows:
    self.assertIsNone(r['error'],'%s %s'%(f.name,r['error']));self.assertEqual(r['audit'],[],'%s scene %s'%(f.name,r['id']))
   tot=pm.total_seconds(rows);self.assertTrue(.9*tm*60<=tot<=1.17*tm*60,'%s is %.1f minutes (target %s)'%(f.name,tot/60,tm))
 def test_scene_ids_are_unique_and_use_only_cast_members(self):
  for f in FILMS:
   film=pm.load_film(f);ids=[s['id'] for s in film['scenes']];self.assertEqual(len(ids),len(set(ids)));cast={c['id'] for c in film['cast']}
   for s in film['scenes']:
    self.assertTrue({c['id'] for c in s['cast']}<=cast,s['id'])
 def test_casts_are_distinct_and_variety_is_real(self):
  for f in FILMS:
   film=pm.load_film(f);reg=pm.registry_of(film);self.assertEqual(reg.distinct_report(),[],f.name)
   looks=[reg.resolve(i) for i in reg.ids()];self.assertGreaterEqual(len({l['species'] for l in looks}),min(6,len(looks)));self.assertGreaterEqual(len({round(l['scale'][2],1) for l in looks}),min(5,len(looks)))
   self.assertGreaterEqual(len({l['gait'] for l in looks}),min(4,len(looks)))
 def test_films_use_different_premises_and_casts(self):
  a,b=[pm.load_film(f) for f in FILMS[:2]];self.assertNotEqual(a['id'],b['id']);self.assertFalse({c['id'] for c in a['cast']}&{c['id'] for c in b['cast']})
  la={s['location']['preset'] for s in a['scenes']};lb={s['location']['preset'] for s in b['scenes']};self.assertGreaterEqual(len(la|lb),9)
 def test_cache_key_changes_with_the_spec_and_the_cast(self):
  film=pm.load_film(FILMS[0]);sp=film['scenes'][0];k=pm.scene_key(sp,'{}','e');self.assertEqual(k,pm.scene_key(sp,'{}','e'));self.assertNotEqual(k,pm.scene_key(dict(sp,title='x'),'{}','e'));self.assertNotEqual(k,pm.scene_key(sp,'{"a":1}','e'));self.assertNotEqual(k,pm.scene_key(sp,'{}','f'))
 def test_plan_only_run_writes_the_report_and_story_records(self):
  out=Path(tempfile.mkdtemp());r=pm.run(FILMS[0],out,plan_only=True,echo=False,voices=False);self.assertTrue((out/'plan_report.md').exists());recs=json.loads((out/'cast_story.json').read_text());self.assertTrue(all('description' in x and 'species' in x for x in recs));self.assertGreater(r['total'],800)
if __name__=='__main__':unittest.main()
