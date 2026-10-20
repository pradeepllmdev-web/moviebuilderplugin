import os,sys,tempfile,unittest,wave
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
import perf_voices as pv,cast_registry as cr,perf_plan as pp
CAT=[dict(model='m',speaker=i,f0=f) for i,f in enumerate((85,100,130,160,200,240))]
REG=cr.Registry([dict(id='bear',name='B',species='bear'),dict(id='mouse',name='M',species='mouse'),dict(id='fox',name='F',species='fox'),dict(id='owl',name='O',species='owl')])
class Pitch(unittest.TestCase):
 def test_f0_of_a_tone(self):
  t=np.arange(22050)/22050.;x=np.sin(2*np.pi*140*t)+.3*np.sin(2*np.pi*280*t);self.assertAlmostEqual(pv.f0_estimate(x),140,delta=4)
 def test_silence_has_no_pitch(self):self.assertIsNone(pv.f0_estimate(np.zeros(22050)))
class Assign(unittest.TestCase):
 def test_each_character_gets_a_different_voice_close_to_its_pitch(self):
  v=pv.assign(REG,CAT);self.assertEqual(set(v),set(REG.ids()));self.assertEqual(len({(x['model'],x['speaker']) for x in v.values()}),4)
  self.assertLess(v['bear']['f0'],v['mouse']['f0']);self.assertGreater(v['mouse']['f0'],v['owl']['f0'])
  for i,x in v.items():self.assertTrue(.72<=x['shift']<=1.55)
 def test_deterministic(self):self.assertEqual(pv.assign(REG,CAT),pv.assign(REG,CAT))
 def test_no_catalogue_means_no_voices(self):self.assertEqual(pv.assign(REG,[]),{})
class Cache(unittest.TestCase):
 def test_key_depends_on_everything_that_changes_the_sound(self):
  v=dict(model='m',speaker=1,shift=1.0,rate=1.0);k=pv.key(v,'hi','joy')
  for w,t,m in ((dict(v,speaker=2),'hi','joy'),(dict(v,shift=1.1),'hi','joy'),(dict(v,rate=.9),'hi','joy'),(v,'hi!','joy'),(v,'hi','sad'),(dict(v,model='n'),'hi','joy')):self.assertNotEqual(k,pv.key(w,t,m))
  self.assertEqual(k,pv.key(dict(v),'hi','joy'))
 def test_missing_line_has_no_duration(self):self.assertIsNone(pv.duration(dict(model='zz',speaker=0),'never spoken','joy'))
 def test_planner_uses_the_recorded_length(self):
  reg=cr.Registry([dict(id='a',name='A',species='fox',voice=dict(model='m',speaker=1)),dict(id='b',name='B',species='bear')])
  sp=dict(id='t',location=dict(preset='meadow'),cast=[dict(id='a',at=[0,0],face=[1,0]),dict(id='b',at=[3,0],face=[-1,0])],steps=[dict(do='say',who='a',text='Hello there my friend',to='b'),dict(do='say',who='b',text='Hello there my friend',to='a')])
  pp.DURATION_PROVIDER=lambda v,t,m:7.0
  try:P=pp.compile(sp,reg)
  finally:pp.DURATION_PROVIDER=None
  self.assertAlmostEqual(P.lines[0]['dur'],7.1,2);self.assertLess(P.lines[1]['dur'],4)    # only the character with a voice uses it
if __name__=='__main__':unittest.main()
