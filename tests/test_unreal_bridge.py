import math,os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import unreal_bridge as ub,unreal_import as ui
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
