import math,os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import ue_common as ub,unreal_import as ui
def doc():
 k=dict(frames=[1,2,3],loc=[[0,0,0],[100,-50,0],[200,-100,0]],rot=[[0,0,0],[0,0,10],[0,0,20]],scale=[[1,1,1]]*3)
 return dict(scene='t',fps=24,frame_start=1,frame_end=3,actors=[dict(id='a000',name='LeoRoot',role='character',asset_key='LeoRoot',keys=k),dict(id='a001',name='Cam0',role='camera',asset_key='Cam',keys=k),dict(id='a002',name='Boulder.001',role='prop',asset_key='Boulder',keys=k)],
  characters=[dict(name='Leo',root='a000',clips=[dict(clip='run',start=1,end=3,scale=.5)],ik_targets=[])],cuts=[dict(name='c',camera='a001',start=1,end=3)],audio=[],environment={})
class Convert(unittest.TestCase):
 def test_axes_and_units(self):
  self.assertEqual(ub.ue_loc([1,2,3]),[100.0,-200.0,300.0]);r=ub.ue_rot_deg([0,0,math.pi/2]);self.assertAlmostEqual(r[2],-90.0)
 def test_asset_key(self):
  self.assertEqual(ub.asset_key('Boulder.003'),'Boulder');self.assertEqual(ub.asset_key('CrateStack12'),'CrateStack')
 def test_unwrap(self):
  self.assertEqual([round(x) for x in ub.unwrap_deg([170,-170,-160])],[170,190,200])
 def test_reduce_keys_keeps_shape(self):
  fr=list(range(0,101));vals=[[float(f)] for f in fr];self.assertEqual(ub.reduce_keys(fr,vals,.01),[0,100])
  vals=[[abs(f-50)*1.0] for f in fr];keep=ub.reduce_keys(fr,vals,.01);self.assertIn(50,keep)
class Validate(unittest.TestCase):
 def test_ok(self):self.assertEqual(ub.validate(doc()),[])
 def test_problems(self):
  d=doc();d['cuts'][0]['camera']='zzz';self.assertTrue(ub.validate(d))
  d=doc();d['actors'][0]['keys']['loc'].pop();self.assertTrue(ub.validate(d))
class DryRunBuild(unittest.TestCase):
 def test_build_counts_and_fallbacks(self):
  b=ui.build(doc(),{'assets':{'Boulder':'/Game/X/SM_Boulder'}},ui.DryRun());c=b.counts
  self.assertEqual((c['actors'],c['cuts'],c['anim_sections']),(3,1,1));self.assertIn('Boulder',c['mapped']);self.assertIn('LeoRoot',c['unmapped'])
 def test_rejects_inconsistent_export(self):
  d=doc();d['cuts'][0]['end']=0
  with self.assertRaises(ValueError):ui.build(d,{},ui.DryRun())
if __name__=='__main__':unittest.main()
class Catalog(unittest.TestCase):
 CAT={'assets':[dict(id='r1',mesh_type='static',category='rock',name='Big Round Rock',path='/Game/Rocks/R1',dimensions_cm=[600,580,640],tags=['rock']),
  dict(id='r2',mesh_type='static',category='rock',name='Flat Slab',path='/Game/Rocks/R2',dimensions_cm=[900,900,60],tags=['rock']),
  dict(id='t1',mesh_type='static',category='tree',name='Oak',path='/Game/Trees/T1',dimensions_cm=[400,400,1200],tags=['tree']),
  dict(id='s1',mesh_type='skeletal',category='rock',name='Rock Golem',path='/Game/Skel/G1',dimensions_cm=[600,600,600],tags=[])]}
 def test_picks_by_word_then_shape_and_fits_scale(self):
  path,fit=ub.pick_catalog_asset('Boulder',[641,610,678],self.CAT);self.assertEqual(path,'/Game/Rocks/R1');self.assertAlmostEqual(fit,1.06,delta=.1)
 def test_rejects_wrong_shape_or_missing_words(self):
  self.assertIsNone(ub.pick_catalog_asset('Boulder',[100,100,1500],self.CAT));self.assertIsNone(ub.pick_catalog_asset('Statue',[100,100,335],self.CAT))
 def test_import_uses_catalog_and_fits_constant_scale(self):
  d=doc();d['actors'][2]['bounds_cm']=[640,600,680];d['actors'][2]['keys']['scale']=[[3.2,3.2,3.2]]*3
  b=ui.build(d,{},ui.DryRun(),catalog=self.CAT);self.assertIn('Boulder',b.counts['mapped'])
 def test_constant_scale(self):
  self.assertTrue(ub.constant_scale([[1,1,1],[1,1,1]]));self.assertFalse(ub.constant_scale([[1,1,1],[1,1,2]]))
