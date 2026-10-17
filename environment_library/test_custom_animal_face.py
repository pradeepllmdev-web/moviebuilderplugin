"""Test named custom face channels without loading any character mesh."""
import sys,types,importlib,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'blendplugin-next/scene_pipeline'))
class Key:
 def __init__(self,name):self.name=name;self.value=0;self.frames=[]
 def keyframe_insert(self,prop,frame):self.frames.append((frame,self.value))
class Blocks(dict):
 def __iter__(self):return iter(self.values())
class Faces(unittest.TestCase):
 def run_face(self,jaw,gentle=False):
  keys=Blocks({name:Key(name) for name in [jaw,'BlinkL','BlinkR','Round','MouthRound','LipSeal']})
  mesh=types.SimpleNamespace(type='MESH',data=types.SimpleNamespace(shape_keys=types.SimpleNamespace(key_blocks=keys)))
  rig=types.SimpleNamespace(children_recursive=[mesh],pose=types.SimpleNamespace(bones=[]),get=lambda key,default=None:gentle if key=="gentle_conversation" else default)
  with patch.dict(sys.modules,{'bpy':types.SimpleNamespace(),'expressions':types.SimpleNamespace(curves=lambda *a,**k:{})}):
   module=importlib.import_module('facerig')
   with patch.object(module,'visemes',return_value=({name:[0,1,.5,0] for name in module.VISEMES},[0,1,.5,0])):
    module.perform(rig,[],[],4,24)
  return keys
 def test_gentle_jaw_limits_frame_changes(self):
  keys=self.run_face("JawOpen",gentle=True);values=[v for f,v in keys["JawOpen"].frames]
  self.assertGreater(max(values),.1);self.assertLess(max(abs(b-a) for a,b in zip(values,values[1:])),.15)
 def test_cat_closes_in_silence(self):
  keys=self.run_face('JawClose');self.assertEqual(keys['JawClose'].frames,[(1,1),(2,0),(3,.5),(4,1)])
 def test_lion_opens_for_speech(self):
  keys=self.run_face('JawOpen');self.assertEqual(keys['JawOpen'].frames,[(1,0),(2,1),(3,.5),(4,0)])
if __name__=='__main__':unittest.main()


