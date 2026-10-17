import asyncio,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import character_workflow as w
from fastapi import HTTPException
class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.p=patch.object(w,'ROOT',Path(self.temp.name));self.p.start();w.ACTIVE.clear()
 def tearDown(self):self.p.stop();self.temp.cleanup();w.ACTIVE.clear()
 def job(self,completed=None):
  j={'id':'a'*32,'name':'test','status':'running','stage':None,'completed':completed or [],'stages':w.STAGES,'demos':[]};w.folder(j['id']).mkdir();w.save(j);return j
 def test_path_traversal_rejected(self):
  with self.assertRaises(HTTPException):w.folder('../outside')
 def test_interruption_detected(self):
  j=self.job();self.assertEqual(w.read(j['id'])['status'],'interrupted')
 def test_landmarks_correct_scale(self):
  face={'boxes':{'image_left_eye':{'x0':200,'x1':300,'y0':200,'y1':300},'image_right_eye':{'x0':600,'x1':700,'y0':200,'y1':300},'mouth_opening':{'x0':350,'x1':550,'y0':400,'y1':500}}};face['boxes'].update({k:{'x0':350,'x1':550,'y0':300,'y1':600} for k in ('nose','chin','head')});w.validate_landmarks(face)
  face['boxes']['mouth_opening']['y0']=100
  with self.assertRaises(ValueError):w.validate_landmarks(face)
 def test_resume_skips_completed_stages(self):
  j=self.job(w.STAGES[:-1]);w.ACTIVE[j['id']]=True
  with patch.object(w,'demo',return_value=[{'mode':'standing','url':'demo.mp4'}]) as demo:
   asyncio.run(w.execute(j['id']))
  saved=w.read(j['id']);self.assertEqual(saved['status'],'needs_review');self.assertEqual(saved['completed'],w.STAGES);demo.assert_called_once()
 def test_failure_saved_for_review(self):
  j=self.job(w.STAGES[:-1]);w.ACTIVE[j['id']]=True
  with patch.object(w,'demo',side_effect=RuntimeError('missing run clip')):asyncio.run(w.execute(j['id']))
  saved=w.read(j['id']);self.assertEqual(saved['status'],'needs_attention');self.assertIn('missing run clip',saved['error']);self.assertNotIn('demo_videos',saved['completed'])
 def test_transient_windows_lock_retried(self):
  j=self.job();original=Path.replace;attempts=[]
  def locked_once(source,target):
   attempts.append(1)
   if len(attempts)==1:raise PermissionError('file is open')
   return original(source,target)
  with patch.object(Path,'replace',locked_once),patch.object(w.time,'sleep'):
   w.save(j)
  self.assertEqual(len(attempts),2)
 def test_file_escape_rejected(self):
  self.job()
  with self.assertRaises(HTTPException):w.artifact('a'*32,'../secret.env')
if __name__=='__main__':unittest.main()


