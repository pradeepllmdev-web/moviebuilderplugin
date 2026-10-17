import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import face_on_glb,pygltflib
from blend_shapes import read_accessor
H=Path(__file__).resolve().parent/'amber-face-refinement';src=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65/body-rig.glb')
face=json.loads((H/'face.json').read_text());face['separate_mouth']=False
result=face_on_glb.add_face(src,H/'character-conservative.glb',face,.25)
g=pygltflib.GLTF2().load(str(H/'character-conservative.glb'));blob=bytearray(g.binary_blob())
for mesh in g.meshes:
 names=(mesh.extras or {}).get('targetNames',[])
 for p in mesh.primitives:
  for name,target in zip(names,p.targets or []):
   if name not in ('jawOpen','mouthPucker','mouthWide','mouthClose','lowerLipBite'):continue
   idx=target['POSITION'] if isinstance(target,dict) else target.POSITION
   a=g.accessors[idx];v=g.bufferViews[a.bufferView];start=(v.byteOffset or 0)+(a.byteOffset or 0)
   data=read_accessor(g,idx).copy();data*=.35 if name=='jawOpen' else .4
   blob[start:start+data.nbytes]=data.tobytes();a.min=data.min(axis=0).tolist();a.max=data.max(axis=0).tolist()
g.set_binary_blob(bytes(blob));g.save(str(H/'character-conservative.glb'));print('Conservative fit ready')
