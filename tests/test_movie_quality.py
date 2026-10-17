import json,sys,tempfile,unittest,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'environment_library'))
from movie_quality import check_movie
from movie_pipeline import ProgressJob

class QualityTests(unittest.TestCase):
 def setUp(self):
  workspace=Path(__file__).resolve().parents[1];scratch=workspace/'.verification/quality-tests';scratch.mkdir(parents=True,exist_ok=True)
  assert workspace in scratch.resolve().parents
  self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.d=self.root/'scene_jobs'/'test';self.d.mkdir(parents=True);(self.d/'performance').mkdir()
  self.movie={'shots':[{'scene_id':'test','title':'Test'}]}
  with wave.open(str(self.d/'voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0\0'*24000)
  self.put('native.json',{'characters':[{'name':'Rowan','body_tracks':53,'facial':{'missing_animated_targets':[]}}]})
  self.put('scene.json',{'duration':2,'lines':[{'speaker':'Rowan','start':0,'audio':str(self.d/'voice.wav')}],'actors':[{'segments':[{'action':'talk'}]}]})
  self.put('contact-check.json',{'ok':True})
  self.put('performance/manifest.json',{'characters':[{'name':'Rowan','facial_channels':[{'name':'jawOpen','values':[0,.5,0]}]}]})
 def put(self,path,data):(self.d/path).write_text(json.dumps(data))
 def test_good_motion_passes(self):self.assertTrue(check_movie(self.movie,self.root)['ok'])
 def test_flat_jaw_blocks_speech(self):
  self.put('performance/manifest.json',{'characters':[{'name':'Rowan','facial_channels':[{'name':'jawOpen','values':[0,0,0]}]}]})
  self.assertFalse(check_movie(self.movie,self.root)['ok'])
 def test_missing_body_blocks(self):
  self.put('native.json',{'characters':[{'name':'Rowan','body_tracks':0}]})
  self.assertFalse(check_movie(self.movie,self.root)['ok'])
 def test_joint_discontinuity_blocks(self):
  (self.d/'actor_0').mkdir();self.put('actor_0/motion-safety.json',{'ok':False})
  self.assertFalse(check_movie(self.movie,self.root)['ok'])
 def test_child_completion_does_not_finish_pipeline(self):
  parent={'status':'running'};child=ProgressJob(parent,status='running');child.update(status='complete',stage='Master next')
  self.assertEqual(parent['status'],'running');self.assertEqual(parent['stage'],'Master next')
