import sys,numpy as np
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import pygltflib as gl
from blend_shapes import read_accessor
H=Path(__file__).resolve().parent/'amber-face-refinement';g=gl.GLTF2().load(str(H/'character-conservative.glb'));blob=bytearray(g.binary_blob())
def put(idx,data):
 a=g.accessors[idx];v=g.bufferViews[a.bufferView];start=(v.byteOffset or 0)+(a.byteOffset or 0);blob[start:start+data.nbytes]=data.tobytes()
 if a.type=='VEC3':a.min=data.min(axis=0).tolist();a.max=data.max(axis=0).tolist()
for mesh in g.meshes:
 names=(mesh.extras or {}).get('targetNames',[])
 for p in mesh.primitives:
  if p.material is None or g.materials[p.material].name!='eyelids':continue
  pos=read_accessor(g,p.attributes.POSITION).copy();colors=read_accessor(g,p.attributes.COLOR_0).copy()
  skin=np.median(colors[colors[:,:3].sum(axis=1)>.4,:3],axis=0)
  colors[:,:3]=skin
  for side,start in enumerate((0,221)):
   index=names.index('eyeBlinkLeft' if side==0 else 'eyeBlinkRight');acc=p.targets[index]['POSITION'];d=read_accessor(g,acc)
   closed=pos[start:start+221]+d[start:start+221]
   pos[start:start+221,2]=np.median(closed[:,2])+.008
   colors[start+204:start+221,:3]=skin*.6
  put(p.attributes.POSITION,pos);put(p.attributes.COLOR_0,colors)
  for name,target in zip(names,p.targets):
   if name in ('eyeBlinkLeft','eyeBlinkRight','eyeLookDown'):
    d=read_accessor(g,target['POSITION']).copy();d[:,2]=0;put(target['POSITION'],d)
g.set_binary_blob(bytes(blob));g.save(str(H/'character-conservative.glb'));print('Eyelid depth flattened and fur color preserved')
