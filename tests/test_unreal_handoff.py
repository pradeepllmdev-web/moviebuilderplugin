import json,os,sys,tempfile,threading,unittest,wave
from pathlib import Path
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import ue_common as uc,unreal_import as ui,unreal_check as chk,unreal_handoff as uh,unreal_render as ur,unreal_send as us
def doc(scene='m_01_swamp',audio=None):
 k=dict(frames=[1,2,3],loc=[[0,0,0]]*3,rot=[[0,0,0]]*3,scale=[[1,1,1]]*3)
 return dict(scene=scene,fps=24,frame_start=1,frame_end=3,units='',source='x.blend',look=dict(world_color=[.2,.3,.4],world_strength=1.,sun=dict(light='Sun',color=[1,1,1],energy=2.)),
  actors=[dict(id='a000',name='Cam0',role='camera',asset_key='Cam',keys=dict(k,lens=[35,35,35])),dict(id='a001',name='SparkFly1',role='effect',asset_key='SparkFly',keys=k,meshes=['SparkFly1'],parts=[dict(mesh='SparkFly1',self=True,loc=[0,0,0],rot=[0,0,0],dims_cm=[9,9,9])],bounds_cm=[9,9,9])],
  characters=[],cuts=[dict(name='c',camera='a000',start=1,end=3)],audio=audio or [],environment={})
class SwapMap(unittest.TestCase):
 M={'assets':{'Boulder':'/Game/R/Boulder','Crate':'/Game/G/Crate'},'props':{'Boulder7':'/Game/R/Special'},
  'scenes':{'swamp':{'props':{'Boulder':{'asset':'/Game/S/Mossy','scale':2.0}},'assets':{'Crate':'/Game/S/Crate'},'environment':'/Game/Levels/Swamp','look':{'sun_scale':.5},'animations':{'run':'/Game/S/Run'}},
            'movie_*_ice':{'assets':{'Boulder':'/Game/I/Ice'}},'_note':'x'}}
 def test_precedence(self):
  e=uc.swap_entry('Boulder7',self.M,'movie_01_other');self.assertEqual(e['asset'],'/Game/R/Special')       # global props by exact name beat global assets by key
  self.assertEqual(uc.swap_entry('Boulder3',self.M,'movie_01_other')['asset'],'/Game/R/Boulder')
  e=uc.swap_entry('Boulder7',self.M,'movie_05_swamp');self.assertEqual((e['asset'],e['scale']),('/Game/S/Mossy',2.0))   # scene props beat global props
  self.assertEqual(uc.swap_entry('Crate2',self.M,'movie_05_swamp')['asset'],'/Game/S/Crate');self.assertIsNone(uc.swap_entry('Tree',self.M,'movie_05_swamp'))
 def test_scene_patterns(self):
  self.assertEqual(uc.swap_entry('Boulder',self.M,'movie_09_ice')['asset'],'/Game/I/Ice');self.assertEqual(uc.swap_entry('Boulder',self.M,'movie_09_forge')['asset'],'/Game/R/Boulder')
 def test_names_env_look_clips(self):
  self.assertEqual(uc.swap_names(self.M,'movie_05_swamp'),['Boulder','Boulder7','Crate']);self.assertEqual(uc.swap_names({},'x'),[])
  self.assertEqual(uc.environment_swap(self.M,'movie_05_swamp'),{'asset':'/Game/Levels/Swamp'});self.assertIsNone(uc.environment_swap(self.M,'movie_09_ice'))
  self.assertEqual(uc.look_overrides(self.M,'movie_05_swamp'),{'sun_scale':.5});self.assertEqual(uc.resolve_clip('run','Leo',self.M,'/Game/Anim','movie_05_swamp'),('/Game/S/Run',True));self.assertFalse(uc.resolve_clip('run','Leo',self.M,'/Game/Anim','x')[1])
 def test_resolve_asset_keeps_old_contract(self):
  self.assertEqual(uc.resolve_asset('Boulder',{'assets':{'Boulder':'/X'}},'/Game/Proxy','s'),('/X',True));self.assertEqual(uc.resolve_asset('Tree',{},'/Game/Proxy','s'),('/Game/Proxy/s/SM_Tree',False))
 def test_set_swap_keeps_the_rest(self):
  m=json.loads(json.dumps(self.M));uc.set_swap(m,'Pillar','/Game/P',scene='swamp',scale=1.5);self.assertEqual(m['scenes']['swamp']['props']['Pillar'],{'asset':'/Game/P','scale':1.5});self.assertEqual(m['scenes']['swamp']['environment'],'/Game/Levels/Swamp')
  uc.set_swap(m,'Pillar',None,scene='swamp');self.assertNotIn('Pillar',m['scenes']['swamp']['props']);uc.set_swap(m,'Rock','/Game/R');self.assertEqual(m['props']['Rock'],'/Game/R')
  uc.set_environment(m,'ice','/Game/Ice');self.assertEqual(m['scenes']['ice']['environment'],'/Game/Ice')
class Build(unittest.TestCase):
 def test_swap_environment_and_look_reach_the_backend(self):
  m={'scenes':{'swamp':{'props':{'SparkFly1':'/Game/FX/Fly'},'environment':{'asset':'/Game/Levels/Swamp','offset':[0,0,10]},'look':{'isolate':False}}}}
  b=ui.build(doc(),m,ui.DryRun());spawns={x[1]:x for x in b.log if x[0]=='spawn'}
  self.assertEqual(spawns['SparkFly1'][3:],('/Game/FX/Fly',{'asset':'/Game/FX/Fly'}));self.assertIn('SparkFly',b.counts['mapped'])
  env=[x for x in b.log if x[0]=='environment'][0];self.assertEqual(env[1]['asset'],'/Game/Levels/Swamp');lk=[x for x in b.log if x[0]=='look'][0][1];self.assertFalse(lk['isolate'])
 def test_unmapped_prop_stays_proxy(self):
  b=ui.build(doc(),{},ui.DryRun());self.assertIn('SparkFly',b.counts['unmapped']);self.assertIsNone([x for x in b.log if x[0]=='spawn' and x[1]=='SparkFly1'][0][4])
 def test_exposure_op_rebuilds_nothing(self):
  b=ui.build(dict(scene='s',op='set_exposure',exposure_bias=1.25),{},ui.DryRun());self.assertEqual(b.log,[('set_exposure','s',1.25)]);self.assertEqual(b.counts['actors'],0)
 def test_old_export_without_look_builds(self):
  d=doc();del d['look'];b=ui.build(d,{},ui.DryRun());self.assertFalse([x for x in b.log if x[0]=='look'])
class Look(unittest.TestCase):
 def test_derive(self):
  lk=uc.derive_look(dict(world_color=[.2,.4,.6],world_strength=1.,sun=dict(energy=2.)),{'sky_scale':.5,'sun_scale':2});self.assertTrue(lk['isolate']);self.assertEqual(lk['sun']['lux_scale'],2.0)
  base=uc.derive_look(dict(world_color=[.2,.4,.6],world_strength=1.))['sky']['intensity'];self.assertAlmostEqual(lk['sky']['intensity'],base*.5,places=2);self.assertIsNone(uc.derive_look({})['sun'])
  self.assertEqual(uc.derive_look(dict(world_color=[1,1,1],world_strength=100))['sky']['intensity'],4.0);self.assertGreaterEqual(uc.derive_look(dict(world_color=[0,0,0],world_strength=0))['sky']['intensity'],.02)
  self.assertEqual(uc.derive_look({},{'sky_color':[1,0,0]})['sky']['color'],[1,0,0])
 def test_exposure_step(self):
  self.assertEqual(uc.exposure_step(2.0,.32),2.0);self.assertEqual(uc.exposure_step(2.0,.33),2.0)     # within tolerance: left alone
  self.assertGreater(uc.exposure_step(0.,.1),0.);self.assertLess(uc.exposure_step(2.,.8),2.)
  self.assertLessEqual(uc.exposure_step(3.9,.02),4.);self.assertGreaterEqual(uc.exposure_step(-2.4,1.),-2.5)
 def test_proxy_mesh_paths_find_new_and_old_names(self):
  p=uc.proxy_mesh_paths('s','Croc.001');self.assertEqual(p[0],'/Game/Proxy/s/M_Croc_001');self.assertIn('/Game/Proxy/s/Croc_0011',p)
class Check(unittest.TestCase):
 def folder(self,files):
  d=tempfile.mkdtemp()
  for n,c in files.items():Path(d,n).write_bytes(c)
  return d
 def test_clean_scene(self):
  d=self.folder({'props.fbx':b'xx M_SparkFly1 xx'});codes=[i['code'] for i in chk.check_scene(doc(),d)];self.assertEqual(codes,['silent_scene'])
 def test_missing_mesh_character_and_files(self):
  dd=doc();dd['actors'].append(dict(id='a002',name='Ghost',role='prop',asset_key='Ghost',keys=dd['actors'][0]['keys'],meshes=[],parts=[]));dd['actors'][1]['parts'].append(dict(mesh='SparkFly2',dims_cm=[0.01,0.01,0.01]))
  dd['characters']=[dict(name='Leo',root='a009',clips=[],skeletal_mesh='character_Leo.fbx',ik_targets=[])];dd['environment']=dict(static_meshes=3,mesh='E')
  iss=chk.check_scene(dd,self.folder({'props.fbx':b'M_SparkFly1'}));codes=sorted(i['code'] for i in iss)
  self.assertEqual(codes,['character_unresolved','file_missing','mesh_missing','mesh_tiny','prop_no_mesh','silent_scene']);self.assertEqual(len(chk.blocking(iss)),4)
  self.assertTrue(any('Ghost' in i['msg'] for i in iss))
 def test_character_files_and_clips(self):
  dd=doc();dd['actors'].append(dict(id='a002',name='LeoRoot',role='character',asset_key='LeoRoot',keys=dd['actors'][0]['keys']));dd['characters']=[dict(name='Leo',root='a002',clips=[dict(clip='run',anim_file='anim_run_1_9',start=1,end=3)],skeletal_mesh='character_Leo.fbx',ik_targets=[])]
  iss=chk.check_scene(dd,self.folder({'props.fbx':b'M_SparkFly1','character_Leo.fbx':b'x'*100}));codes=sorted(i['code'] for i in iss);self.assertEqual(codes,['character_empty','file_missing','silent_scene'])
 def test_audio_missing_silent_short_and_ok(self):
  d=self.folder({'props.fbx':b'M_SparkFly1'})
  def wav(name,amp,sec):
   p=os.path.join(d,name)
   with wave.open(p,'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes((int(amp).to_bytes(2,'little',signed=True))*int(8000*sec))
   return p
  strips=lambda *fs:[dict(name=os.path.basename(f),file=f,start=1,volume=1.) for f in fs]
  codes=lambda a:sorted(i['code'] for i in chk.check_scene(doc(audio=a),d))
  self.assertEqual(codes(strips(os.path.join(d,'nope.wav'))),['audio_missing']);self.assertEqual(codes(strips(wav('s.wav',0,1))),['silent_audio'])
  dd=doc();dd['frame_end']=240;self.assertEqual([i['code'] for i in chk.check_scene(dict(dd,audio=strips(wav('q.wav',900,1))),d)],['audio_short'])
  self.assertEqual(codes(strips(wav('l.wav',900,.2))),[]);self.assertEqual(chk.format_issues([chk.issue('error','x','boom')]),['ERROR boom'])
class Summary(unittest.TestCase):
 def test_group_messages(self):
  g=uh.group_messages(['no imported mesh for SparkFly1','no imported mesh for SparkFly2','other']);self.assertEqual([(t,n) for t,n,e in g],[('no imported mesh for SparkFly#',2),('other',1)])
 def test_diag_missing(self):
  d=doc();diag=[dict(label='m_01_swamp/SparkFly1',mesh=None),dict(label='m_01_swamp/SparkFly1/SparkFly1',mesh=None)];self.assertEqual(uh.diag_missing(d,diag),['SparkFly1/SparkFly1'])
  swapped=[dict(label='m_01_swamp/SparkFly1',mesh='/Engine/BasicShapes/Sphere')];self.assertEqual(uh.diag_missing(d,swapped),[])
  diag[1]['mesh']='/Game/Proxy/x';self.assertEqual(uh.diag_missing(d,diag),[]);self.assertEqual(uh.diag_missing(d,[]),['SparkFly1/SparkFly1'])
 def test_format_is_compact_and_complete(self):
  rows=[dict(index=1,piece='talk',export='cached',unreal='cached',exposure=2.31,issues=[],warnings=[],missing=[]),
   dict(index=5,piece='swamp',export='ran',export_s=41.,unreal='applied',unreal_s=63.,exposure=.35,issues=[chk.issue('warn','silent_scene','swamp is silent')],warnings=['no imported mesh for SparkFly%d'%i for i in range(1,5)],missing=['A/B']),
   dict(index=6,piece='jungle',export='ran',unreal='blocked',issues=[chk.issue('error','x','Ghost has no mesh')],warnings=[],missing=[]),dict(index=7,piece='ruins',export='cached',unreal='failed',error='boom',issues=[],warnings=[],missing=[])]
  t=uh.format_summary('m',rows,75.);lines=t.split('\n');self.assertIn('export 2 ran, 2 cached',lines[0]);self.assertIn('1 blocked, 1 failed',lines[0]);self.assertIn('75s',lines[0])
  self.assertTrue(any('SparkFly# (x4' in l for l in lines));self.assertTrue(any('swamp is silent' in l for l in lines));self.assertTrue(any('Ghost has no mesh' in l for l in lines));self.assertTrue(any('FAILED: boom' in l for l in lines));self.assertIn('+2.31',t)
class FakeBridge:
 def __init__(self):self.calls=[];self.seqs=set()
 def get(self,path):
  if path.startswith('/assets'):return {'assets':[{'path':'/Game/Movie/'+s} for s in sorted(self.seqs)]}
  return {'actors':[{'label':s[3:]+'/Cam0'} for s in self.seqs]}
 def clear_proxy(self,scene):self.calls.append(('clear_proxy',scene))
 def drop_sequences(self,scene):self.calls.append(('drop_sequences',scene))
 def command(self,name,params=None):
  self.calls.append((name,params))
  if name=='apply_movie_scene':
   d=json.loads(Path(params['scene_json']).read_text(encoding='utf-8'))
   if d.get('op')=='set_exposure':return {'sequence':'/Game/Movie/LS_'+d['scene']}
   self.seqs.add('LS_'+d['scene']);return {'sequence':'/Game/Movie/LS_'+d['scene'],'warnings':['no imported mesh for SparkFly1']}
  return {}
class Handoff(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.movie=self.d/'mv';self.movie.mkdir();self.root=self.d/'exp'
  rep=[]
  for i,p in ((1,'ice'),(2,'swamp'),(3,'forge')):
   b=self.movie/('scene_%02d_%s.blend'%(i,p));b.write_text('blend %s v1'%p);rep.append(dict(index=i,piece=p,file=str(b),status='built in 5s',audit=[]))
  (self.movie/'report.json').write_text(json.dumps(dict(report=rep)));self.exports=[];self.lock=threading.Lock();self.old=os.environ.get('MOVIEBUILDER_EXPORT_ROOT');os.environ['MOVIEBUILDER_EXPORT_ROOT']=str(self.root)
  self.bridge=FakeBridge();self.orig_cal=us.calibrate_exposure;self.cal=[]
  def fake_cal(bridge,j,seq,start_bias=None,**k):self.cal.append(seq);return 1.5,.2
  us.calibrate_exposure=fake_cal
 def tearDown(self):
  us.calibrate_exposure=self.orig_cal;self.tmp.cleanup()
  if self.old is None:os.environ.pop('MOVIEBUILDER_EXPORT_ROOT',None)
  else:os.environ['MOVIEBUILDER_EXPORT_ROOT']=self.old
 def export(self,blend,out,name):
  with self.lock:self.exports.append(name)
  out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'props.fbx').write_bytes(b'M_SparkFly1');j=out/(name+'.ue.json');j.write_text(json.dumps(doc(name)));return j
 def run_(self,**kw):
  kw.setdefault('amap',{});return uh.handoff(self.movie,self.bridge,export=self.export,**kw)
 def test_second_run_does_nothing(self):
  r1=self.run_();self.assertEqual([x['unreal'] for x in r1['rows']],['applied']*3);self.assertEqual(len(self.exports),3);self.assertEqual(len(self.cal),3)
  n=len(self.bridge.calls);r2=self.run_();self.assertEqual([(x['export'],x['unreal']) for x in r2['rows']],[('cached','cached')]*3);self.assertEqual(len(self.exports),3);self.assertEqual(len(self.bridge.calls),n);self.assertEqual(r2['rows'][0]['exposure'],1.5)
  self.assertIn('unreal 0 applied, 3 cached',r2['summary']);self.assertTrue((self.root/'mv'/'handoff_summary.txt').exists())
 def test_changed_blend_redoes_only_that_scene_and_reuses_exposure(self):
  self.run_();(self.movie/'scene_02_swamp.blend').write_text('blend swamp v2');self.cal.clear();r=self.run_()
  self.assertEqual([(x['export'],x['unreal']) for x in r['rows']],[('cached','cached'),('ran','applied'),('cached','cached')]);self.assertEqual(self.exports[3:],['mv_02_swamp']);self.assertEqual(self.cal,[])      # exposure remembered: no render
  self.assertEqual(r['rows'][1]['exposure'],1.5);d=json.loads((self.root/'mv'/'mv_02_swamp'/'mv_02_swamp.ue.json').read_text());self.assertEqual(d['exposure_bias'],1.5)
 def test_map_change_reimports_only_concerned_scene_without_export(self):
  self.run_(amap={'scenes':{'swamp':{'props':{'SparkFly1':'/Game/A'}}}});self.exports.clear()
  r=self.run_(amap={'scenes':{'swamp':{'props':{'SparkFly1':'/Game/B'}}}})     # same swap names, new asset: export reused, only the swamp is imported again
  self.assertEqual([(x['export'],x['unreal']) for x in r['rows']],[('cached','cached'),('cached','applied'),('cached','cached')]);self.assertEqual(self.exports,[])
  self.exports.clear();r=self.run_(amap={'scenes':{'swamp':{'props':{'SparkFly1':'/Game/B','Extra':'/Game/C'}}}})      # a new swapped name changes what the exporter keeps separate: swamp exports again
  self.assertEqual(self.exports,['mv_02_swamp'])
 def test_editor_without_the_scene_is_imported_again(self):
  self.run_();self.bridge.seqs.discard('LS_mv_01_ice');r=self.run_();self.assertEqual([x['unreal'] for x in r['rows']],['applied','cached','cached'])
 def test_force_and_dry_run_and_scenes(self):
  self.run_();self.exports.clear();r=self.run_(force=True);self.assertEqual(len(self.exports),3);self.assertEqual([x['unreal'] for x in r['rows']],['applied']*3)
  r=self.run_(only={2},force=True);self.assertEqual(len(r['rows']),1)
  r=self.run_(dry_run=True,force=True);self.assertEqual({x['unreal'] for x in r['rows']},{'dry run'})
 def test_exports_run_in_parallel(self):
  barrier=threading.Barrier(2,timeout=5);orig=self.export
  def ex(blend,out,name):
   if name!='mv_03_forge':barrier.wait()
   return orig(blend,out,name)
  r=uh.handoff(self.movie,self.bridge,export=ex,amap={},jobs=2,calibrate=False);self.assertFalse([x for x in r['rows'] if x.get('error')])
 def test_blocked_scene_is_not_sent_but_others_are(self):
  def ex(blend,out,name):
   j=self.export(blend,out,name)
   if name=='mv_02_swamp':(Path(out)/'props.fbx').write_bytes(b'nothing')
   return j
  r=uh.handoff(self.movie,self.bridge,export=ex,amap={},calibrate=False);self.assertEqual([x['unreal'] for x in r['rows']],['applied','blocked','applied']);self.assertIn('SparkFly1',r['summary'])
  r=uh.handoff(self.movie,self.bridge,export=ex,amap={},calibrate=False,send_anyway=True,force=True);self.assertEqual([x['unreal'] for x in r['rows']],['applied']*3)
 def test_check_only_needs_no_bridge(self):
  r=uh.handoff(self.movie,None,export=self.export,amap={},check_only=True);self.assertEqual({x['unreal'] for x in r['rows']},{'not sent'});self.assertTrue(any(i['code']=='silent_scene' for i in r['rows'][0]['issues']))
 def test_one_export_failure_does_not_stop_the_rest(self):
  def ex(blend,out,name):
   if name=='mv_01_ice':raise us.BridgeError('export failed for x')
   return self.export(blend,out,name)
  r=uh.handoff(self.movie,self.bridge,export=ex,amap={},calibrate=False);self.assertEqual([bool(x.get('error')) for x in r['rows']],[True,False,False]);self.assertIn('FAILED',r['summary'])
 def test_pinned_exposure_is_not_measured(self):
  r=self.run_(amap={'scenes':{'swamp':{'look':{'exposure':.7}}}});self.assertEqual([x['exposure'] for x in r['rows']],[1.5,.7,1.5]);self.assertEqual(len(self.cal),2)
  d=json.loads((self.root/'mv'/'mv_02_swamp'/'mv_02_swamp.ue.json').read_text());self.assertEqual(d['exposure_bias'],.7)
 def test_single_scene_unit(self):
  b=self.movie/'one.blend';b.write_text('x');row=uh.handoff_scene(b,'solo_01_ice',self.bridge,export=self.export,amap={},calibrate=False)
  self.assertEqual((row['export'],row['unreal']),('ran','applied'));self.assertEqual(row['name'],'solo_01_ice');self.assertIn('LS_solo_01_ice',row['sequence']);self.assertEqual(self.exports,['solo_01_ice'])
  row=uh.handoff_scene(b,'solo_01_ice',self.bridge,export=self.export,amap={},calibrate=False);self.assertEqual((row['export'],row['unreal']),('cached','cached'))
 def test_in_place_exposure_document(self):
  j=self.export(None,self.d/'e','mv_09_x');seen=[]
  class B(FakeBridge):
   def command(s,name,params=None):seen.append((name,json.loads(Path(params['scene_json']).read_text())));return {}
  us.set_exposure(B(),j,1.75);self.assertEqual(seen[0][1]['op'],'set_exposure');self.assertEqual(seen[0][1]['exposure_bias'],1.75);self.assertEqual(seen[0][1]['scene'],'mv_09_x');self.assertFalse(Path(str(j).replace('.ue.json','.exposure.ue.json')).exists())
  self.assertEqual(ui.build(seen[0][1],{},ui.DryRun()).log,[('set_exposure','mv_09_x',1.75)]);self.assertEqual(uc.validate(seen[0][1]),[])
class Contract(unittest.TestCase):
 def test_format_version(self):
  d=doc();self.assertEqual(uc.validate(d),[]);d['format_version']=uc.FORMAT_VERSION;self.assertEqual(uc.validate(d),[])
  d['format_version']=uc.FORMAT_VERSION+1;self.assertTrue(any('format' in x for x in uc.validate(d)))
  with self.assertRaises(ValueError):ui.build(d,{},ui.DryRun())
 def test_registry_roundtrip_and_sha(self):
  t=tempfile.mkdtemp();old=os.environ.get('MOVIEBUILDER_EXPORT_ROOT');os.environ['MOVIEBUILDER_EXPORT_ROOT']=t
  try:
   self.assertEqual(uc.load_registry(),{});uc.save_registry({'Leo':{'mesh':'a','clips':{'run':'b'}}});self.assertEqual(uc.load_registry()['Leo']['clips']['run'],'b')
   f=Path(t)/'x.fbx';f.write_bytes(b'1');s1=uc.file_sha(f);f.write_bytes(b'2');self.assertNotEqual(s1,uc.file_sha(f));self.assertEqual(uc.file_sha(Path(t)/'none'),'missing')
  finally:
   if old is None:os.environ.pop('MOVIEBUILDER_EXPORT_ROOT',None)
   else:os.environ['MOVIEBUILDER_EXPORT_ROOT']=old
class Clean(unittest.TestCase):
 def test_movie_scenes_and_purge(self):
  self.assertEqual(uh.movie_scenes('mv',{'LS_mv_01_ice','LS_mv_01_ice_2','LS_mv_02_swamp','LS_other_01_x'},{'mv_03_forge','mv_01_ice','zz_01_a'}),['mv_01_ice','mv_02_swamp','mv_03_forge'])
  b=FakeBridge();seen=[]
  def cmd(name,params=None):seen.append((name,json.loads(Path(params['scene_json']).read_text())));return {}
  b.command=cmd;t=tempfile.mkdtemp();us.purge_scene(b,t,'mv_01_ice');self.assertEqual(seen[0][1]['op'],'purge');self.assertEqual(uc.validate(seen[0][1]),[])
  self.assertEqual(ui.build(seen[0][1],{},ui.DryRun()).log,[('purge','mv_01_ice')])
class Keys(unittest.TestCase):
 def test_keys_follow_inputs(self):
  d=Path(tempfile.mkdtemp());b=d/'a.blend';b.write_text('1');k1=uh.export_key(b,{},'s');self.assertEqual(k1,uh.export_key(b,{},'s'));b.write_text('2');self.assertNotEqual(k1,uh.export_key(b,{},'s'))
  self.assertNotEqual(uh.export_key(b,{'props':{'X':'/a'}},'s'),uh.export_key(b,{},'s'));self.assertEqual(uh.export_key(b,{'props':{'X':'/a'}},'s'),uh.export_key(b,{'props':{'X':'/b'}},'s'))
  a1=uh.apply_key(k1,{'props':{'X':'/a'}},'s');self.assertNotEqual(a1,uh.apply_key(k1,{'props':{'X':'/b'}},'s'));self.assertEqual(a1,uh.apply_key(k1,{'props':{'X':'/a'},'scenes':{'other':{'props':{'Y':'/z'}}}},'s'))
  self.assertNotEqual(a1,uh.apply_key(k1,{'props':{'X':'/a'},'scenes':{'s':{'look':{'sun_scale':2}}}},'s'))
  self.assertEqual(uh.load_state(d)['scenes'],{});uh.save_state(d,{'version':uh.STATE_VERSION,'scenes':{'a':{'x':1}}});self.assertEqual(uh.load_state(d)['scenes']['a']['x'],1)
class Render(unittest.TestCase):
 def test_pick_sequence_takes_the_newest(self):
  A=lambda *n:[{'path':'/Game/Movie/'+x} for x in n];self.assertEqual(ur.pick_sequence(A('LS_a','LS_a_2','LS_ab','LS_a_10'),'a'),'/Game/Movie/LS_a_10');self.assertEqual(ur.pick_sequence(A('LS_a_2'),'a'),'/Game/Movie/LS_a_2');self.assertIsNone(ur.pick_sequence(A('LS_b'),'a'))
 def test_frame_order_and_plan(self):
  d=Path(tempfile.mkdtemp())
  for n in (10,2,1):(d/('LS_x.%04d.png'%n)).write_text('')
  (d/'notes.txt').write_text('');self.assertEqual([p.name for p in ur.frame_files(d)],['LS_x.0001.png','LS_x.0002.png','LS_x.0010.png'])
  p=ur.plan_scenes([doc('a'),dict(doc('b'),frame_end=10)]);self.assertEqual([(x['first'],x['frames']) for x in p],[(1,3),(4,10)]);self.assertAlmostEqual(p[1]['start_s'],3/24.)
 def wavfile(self,d,name,rate,val,sec,ch=1):
  p=str(Path(d)/name)
  with wave.open(p,'wb') as w:
   w.setnchannels(ch);w.setsampwidth(2);w.setframerate(rate);w.writeframes(int(val).to_bytes(2,'little',signed=True)*int(rate*sec)*ch)
  return p
 def test_mix_places_scales_and_clips(self):
  d=tempfile.mkdtemp();a=self.wavfile(d,'a.wav',8000,16384,1.);b=self.wavfile(d,'b.wav',4000,16384,1.)
  out,bad=ur.mix_scene([dict(file=a,start=1,volume=1.),dict(file=b,start=25,volume=.5)],24,1,8000*3,8000);self.assertEqual(bad,[]);self.assertEqual(out.shape,(24000,2))
  self.assertAlmostEqual(float(out[100,0]),.5,places=2);self.assertAlmostEqual(float(out[8000+100,0]),.25,places=2);self.assertEqual(float(out[2*8000+10,0]),0.)    # b starts 1 s in, resampled from 4 kHz, half volume
  out,bad=ur.mix_scene([dict(file=a,start=1,volume=3.),dict(file=a,start=1,volume=3.)],24,1,100,8000);self.assertEqual(float(out.max()),1.0)
  out,bad=ur.mix_scene([dict(file=os.path.join(d,'none.wav'),start=1)],24,1,100,8000);self.assertEqual(len(bad),1);self.assertEqual(float(abs(out).max()),0.)
 def test_render_movie_numbers_frames_across_scenes_and_mixes_audio(self):
  tmp=tempfile.TemporaryDirectory();d=Path(tmp.name);movie=d/'mv';movie.mkdir();root=d/'exp';old=os.environ.get('MOVIEBUILDER_EXPORT_ROOT');os.environ['MOVIEBUILDER_EXPORT_ROOT']=str(root)
  try:
   w=self.wavfile(d,'s.wav',8000,8000,1.);rep=[]
   for i,p in ((1,'ice'),(2,'swamp')):
    n='mv_%02d_%s'%(i,p);rep.append(dict(index=i,piece=p,file='x.blend',status='built in 1s',audit=[]));(root/'mv'/n).mkdir(parents=True);dd=doc(n,audio=[dict(name='s',file=w,start=1,volume=1.)]);(root/'mv'/n/(n+'.ue.json')).write_text(json.dumps(dd))
   (movie/'report.json').write_text(json.dumps(dict(report=rep)));rendered=[]
   def fake(seq,raw,preset,size,frames):
    rendered.append(raw.name)
    for i in range(frames):(raw/('LS_x.%04d.png'%(i+1))).write_text(raw.name)
   m=ur.render_movie(movie,None,out=d/'out',preset='draft',size=(64,36),render=fake,progress=lambda s:None)
   fr=sorted(p.name for p in (d/'out'/'frames').glob('*.png'));self.assertEqual(fr,['frame_%06d.png'%i for i in range(1,7)]);self.assertEqual((d/'out'/'frames'/'frame_000004.png').read_text(),'mv_02_swamp');self.assertEqual(m['frames'],6)
   with wave.open(str(d/'out'/'audio'/'movie.wav')) as a:self.assertEqual((a.getnchannels(),a.getsampwidth(),a.getframerate(),a.getnframes()),(2,2,44100,int(round(6/24.*44100))))
   self.assertTrue((d/'out'/'audio'/'scene_02_swamp.wav').exists());self.assertEqual(json.loads((d/'out'/'render.json').read_text())['scenes'][1]['first'],4)
   m=ur.render_movie(movie,None,out=d/'out_first',preset='draft',size=(64,36),render=fake,progress=lambda s:None,first=2);self.assertEqual(m['frames'],4);self.assertEqual(len(list((d/'out_first'/'frames').glob('*.png'))),4);self.assertEqual(m['scenes'][1]['first'],3)
   rendered.clear();ur.render_movie(movie,None,out=d/'out',preset='draft',size=(64,36),render=fake,progress=lambda s:None);self.assertEqual(rendered,[])     # resume: nothing is rendered again
   ur.render_movie(movie,None,out=d/'out',preset='draft',size=(64,36),render=fake,progress=lambda s:None,force=True);self.assertEqual(len(rendered),2)
   def short(seq,raw,preset,size,frames):(raw/'LS_x.0001.png').write_text('')
   with self.assertRaises(us.BridgeError):ur.render_movie(movie,None,out=d/'out2',render=short,progress=lambda s:None)
   (root/'mv'/'mv_02_swamp'/'mv_02_swamp.ue.json').unlink()
   with self.assertRaises(us.BridgeError):ur.render_movie(movie,None,out=d/'out3',render=fake,progress=lambda s:None)
  finally:
   if old is None:os.environ.pop('MOVIEBUILDER_EXPORT_ROOT',None)
   else:os.environ['MOVIEBUILDER_EXPORT_ROOT']=old
   tmp.cleanup()
if __name__=='__main__':unittest.main()
