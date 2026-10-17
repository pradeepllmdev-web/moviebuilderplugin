import unittest,tempfile,json,runpy,sys,types
from pathlib import Path
from unittest.mock import patch
class OpenSafety(unittest.TestCase):
 def run_open(self,maps=False,content=False,scene=False):
  calls=[]
  fake=types.SimpleNamespace(Paths=types.SimpleNamespace(get_project_file_path=lambda:'LatestSceneVerification.uproject'),EditorLoadingAndSavingUtils=types.SimpleNamespace(get_dirty_map_packages=lambda:['dirty'] if maps else [],get_dirty_content_packages=lambda:['dirty'] if content else [],load_map=lambda path:calls.append(('map',path)) or True),EditorAssetLibrary=types.SimpleNamespace(does_asset_exist=lambda path:True),load_asset=lambda path:path,LevelSequenceEditorBlueprintLibrary=types.SimpleNamespace(open_level_sequence=lambda seq:calls.append(('sequence',seq)) or True))
  with tempfile.TemporaryDirectory() as tmp:
   h=Path(tmp);(h/'demos').mkdir();script=h/'open_saved_unreal.py';script.write_text((Path(__file__).parent/'open_saved_unreal.py').read_text(encoding='utf-8-sig'),encoding='utf-8');request={'id':'test','level':'/Game/EnvironmentDemos/Test'}
   if scene:request['sequence']='sequence'
   (h/'demos/open-request.json').write_text(json.dumps(request))
   with patch.dict(sys.modules,{'unreal':fake}):runpy.run_path(str(script))
   return json.loads((h/'demos/open-result-test.json').read_text()),calls
 def test_unsaved_map_blocks(self):
  result,calls=self.run_open(maps=True);self.assertFalse(result['ok']);self.assertEqual(calls,[])
 def test_unsaved_asset_blocks(self):
  result,calls=self.run_open(content=True);self.assertFalse(result['ok']);self.assertEqual(calls,[])
 def test_environment(self):
  result,calls=self.run_open();self.assertTrue(result['ok']);self.assertEqual(len(calls),1)
 def test_scene_sequence_order(self):
  result,calls=self.run_open(scene=True);self.assertTrue(result['ok']);self.assertEqual([c[0] for c in calls],['map','sequence'])
if __name__=='__main__':unittest.main()
