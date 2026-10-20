import ast,os,sys,tempfile,types,unittest
from pathlib import Path
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import llm,story_writer as sw,prompt_router as pr,scaffold_scene,set_pieces,unreal_import as ui
class LLM(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();llm.CACHE=Path(self.tmp.name);self.calls=[];os.environ['LLM_PROVIDER']='fake'
  def fake(system,prompt):
   self.calls.append(prompt);return self.answers.pop(0)
  llm.register_provider('fake',fake)
 def tearDown(self):os.environ.pop('LLM_PROVIDER',None);llm.PROVIDERS.pop('fake',None);self.tmp.cleanup()
 def test_valid_answer_is_cached(self):
  self.answers=[{'n':1}];v=lambda r:r if r['n']==1 else (_ for _ in ()).throw(ValueError('bad'))
  self.assertEqual(llm.plan_json('s','p',v),{'n':1});self.assertEqual(llm.plan_json('s','p',v),{'n':1});self.assertEqual(len(self.calls),1)
 def test_one_repair_round(self):
  self.answers=[{'n':2},{'n':1}]
  def v(r):
   if r['n']!=1:raise ValueError('want 1')
   return r
  self.assertEqual(llm.plan_json('s','p',v),{'n':1});self.assertIn('rejected',self.calls[1])
 def test_gives_none_when_it_keeps_failing(self):
  self.answers=[{'n':2},{'n':3}]
  def v(r):raise ValueError('no')
  self.assertIsNone(llm.plan_json('s','p',v))
 def test_none_provider_returns_none(self):
  os.environ['LLM_PROVIDER']='none';self.assertIsNone(llm.plan_json('s','p'));self.assertFalse(llm.available())
class Story(unittest.TestCase):
 def test_every_sentence_selects_its_own_scene(self):
  for k,v in sw.SENT.items():self.assertEqual(set_pieces.match(v)[0],k,k)
 def test_every_scene_type_has_a_sentence(self):self.assertEqual(set(sw.SENT),set(set_pieces.SET_PIECES))
 def test_offline_story_names_requested_scenes_first_and_reaches_length(self):
  text,notes=sw.write_story('Leo rides a dragon and then crosses the ice cave',minutes=6,use_model=False)
  paras=[p for p in text.split('\n\n') if p.strip()];first=[set_pieces.match(p)[0] for p in paras[:2]]
  self.assertEqual(set(first),{'flight','ice'});self.assertGreaterEqual(sum(sw.seconds_of(set_pieces.match(p)[0]) for p in paras),360)
 def test_no_scene_twice(self):
  text,_=sw.write_story('anything',minutes=20,use_model=False);ids=[set_pieces.match(p)[0] for p in text.split('\n\n') if p.strip()];self.assertEqual(len(ids),len(set(ids)))
class Router(unittest.TestCase):
 def test_rules(self):
  self.assertEqual(pr.route('Leo climbs the cliff')['engine'],'set_piece')
  self.assertEqual(pr.route('At night the council meets.\n\nAt dawn Leo crosses the rapids.')['engine'],'story')
  self.assertEqual(pr.route('build a small village with a river')['engine'],'environment')
  self.assertEqual(pr.route('Leo waves hello')['engine'],'shot')
 def test_legacy_switch(self):
  os.environ['PROMPT_ENGINE']='legacy'
  try:self.assertEqual(pr.route('Leo climbs the cliff')['engine'],'shot')
  finally:os.environ.pop('PROMPT_ENGINE')
class Scaffold(unittest.TestCase):
 def test_template_is_valid_python(self):
  src=scaffold_scene.TEMPLATE.format(id='demo',title='Demo',seconds=20,upper='DEMO');ast.parse(src)
  ast.parse('import math\nreg=lambda *a:None\n'+scaffold_scene.LOCATION.format(id='demo',upper='DEMO'))
 def test_rejects_bad_ids(self):
  with self.assertRaises(ValueError):scaffold_scene.make('Bad Id','t','k')
class UnrealGuard(unittest.TestCase):
 def fake(self,project,dirty_maps=(),dirty_content=()):
  u=types.SimpleNamespace();u.Paths=types.SimpleNamespace(get_project_file_path=lambda:project);u.EditorLoadingAndSavingUtils=types.SimpleNamespace(get_dirty_map_packages=lambda:list(dirty_maps),get_dirty_content_packages=lambda:list(dirty_content));return u
 def test_accepts_clean_verification_project(self):ui.guard(self.fake('C:/x/LatestSceneVerification/p.uproject'),{})
 def test_refuses_wrong_project_and_dirty_editor(self):
  with self.assertRaises(RuntimeError):ui.guard(self.fake('C:/x/Other/p.uproject'),{})
  with self.assertRaises(RuntimeError):ui.guard(self.fake('C:/x/LatestSceneVerification/p.uproject',dirty_maps=['m']),{})
  with self.assertRaises(RuntimeError):ui.guard(self.fake('C:/x/LatestSceneVerification/p.uproject',dirty_content=['c']),{})
 def test_override_and_unique_names(self):
  ui.guard(self.fake('C:/x/Other/p.uproject'),{'UNREAL_IMPORT_ANY_PROJECT':'1'});self.assertEqual(ui.unique_name(lambda p:p.endswith('LS_a'),'LS_a'),'LS_a_2')
if __name__=='__main__':unittest.main()

import json,threading
import unreal_send as us,ue_common as uc,movie_to_unreal as m2u
class FakeBridge:
 def __init__(self):self.calls=[]
 def command(self,name,params=None):
  self.calls.append((name,params));return {'sequence':'/Game/Movie/LS_x'} if name=='apply_movie_scene' else {'assets':['a']}
class Send(unittest.TestCase):
 def test_bridge_url_rules(self):
  us.Bridge('http://127.0.0.1:8500');us.Bridge('http://localhost:8501')
  for bad in ('https://127.0.0.1:8500','http://example.com:8500','http://127.0.0.1:8500/x','http://u:p@127.0.0.1:8500'):
   with self.assertRaises(ValueError):us.Bridge(bad)
 def test_scene_path_validation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'root';(root/'m').mkdir(parents=True);good=root/'m'/'a.ue.json';good.write_text('{}');(root/'m'/'b.json').write_text('{}');outside=Path(d)/'c.ue.json';outside.write_text('{}')
   self.assertEqual(uc.validate_scene_path(good,root),good.resolve())
   for bad in (root/'m'/'b.json',outside,root/'m'/'..'/'..'/'c.ue.json',root/'m'/'missing.ue.json'):
    with self.assertRaises(ValueError):uc.validate_scene_path(bad,root)
 def test_send_scene_imports_meshes_then_applies(self):
  with tempfile.TemporaryDirectory() as d:
   j=Path(d)/'s.ue.json';j.write_text(json.dumps({'scene':'s'}));[(Path(d)/n).write_text('x') for n in ('environment.fbx','props.fbx','character_Leo.fbx','anim_run.fbx')]
   b=FakeBridge();res=us.send_scene(b,j);names=[c[0] for c in b.calls]
   self.assertEqual(names,['import_asset','import_asset','apply_movie_scene']);self.assertEqual(res['imported'],['environment.fbx','props.fbx']);self.assertEqual(b.calls[-1][1]['dry_run'],False)
 def test_dry_run_imports_nothing(self):
  with tempfile.TemporaryDirectory() as d:
   j=Path(d)/'s.ue.json';j.write_text(json.dumps({'scene':'s'}));(Path(d)/'environment.fbx').write_text('x');b=FakeBridge();us.send_scene(b,j,dry_run=True);self.assertEqual([c[0] for c in b.calls],['apply_movie_scene'])
 def test_send_movie_skips_scenes_with_problems(self):
  with tempfile.TemporaryDirectory() as d:
   rep=dict(report=[dict(index=1,piece='ice',file='a.blend',status='built in 5s',audit=[]),dict(index=2,piece='ruins',file='b.blend',status='built in 5s',audit=['AUDIT x']),dict(index=3,piece=None,file=None,status='needs the shot-by-shot planner',audit=[])])
   (Path(d)/'report.json').write_text(json.dumps(rep));made=[]
   def fake_export(blend,out,name):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);j=out/(name+'.ue.json');j.write_text(json.dumps({'scene':name}));made.append(name);return j
   os.environ['MOVIEBUILDER_EXPORT_ROOT']=str(Path(d)/'exp')
   try:res=us.send_movie(d,FakeBridge(),export=fake_export)
   finally:os.environ.pop('MOVIEBUILDER_EXPORT_ROOT')
   self.assertEqual(len(res['sent']),1);self.assertEqual([s['index'] for s in res['skipped']],[2,3])
class StudioJob(unittest.TestCase):
 def test_refuses_when_busy_and_bad_bridge(self):
  lock=threading.Lock();lock.acquire();job={'id':'a'*32};m2u.worker(job,lock,prompt='Leo climbs a cliff');self.assertEqual(job['status'],'failed');lock.release()
  job={'id':'b'*32};
  with self.assertRaises(ValueError):m2u.worker(job,threading.Lock(),prompt='Leo climbs a cliff',bridge_url='http://example.com:1')
 def test_needs_prompt_or_story(self):
  with self.assertRaises(ValueError):m2u.worker({'id':'c'*32},threading.Lock())
class Hygiene(unittest.TestCase):
 def test_no_backspace_characters_in_sources(self):
  """a regex written as '\b' in a non-raw string becomes a backspace and silently never matches"""
  root=Path(__file__).resolve().parent.parent/'environment_library'
  bad=[p.name for p in root.glob('*.py') if chr(8) in p.read_text(encoding='utf-8',errors='ignore')]
  self.assertEqual(bad,[])
