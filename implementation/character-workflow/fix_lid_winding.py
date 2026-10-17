import sys
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import pygltflib as gl
from blend_shapes import read_accessor
p='implementation/character-workflow/amber-face-refinement/character-conservative.glb';g=gl.GLTF2().load(p);blob=bytearray(g.binary_blob())
for mesh in g.meshes:
 for prim in mesh.primitives:
  if prim.material is None or g.materials[prim.material].name!='eyelids':continue
  a=g.accessors[prim.indices];v=g.bufferViews[a.bufferView];start=(v.byteOffset or 0)+(a.byteOffset or 0)
  indices=read_accessor(g,prim.indices).reshape(-1,3).copy()[:,[0,2,1]].copy();blob[start:start+indices.nbytes]=indices.tobytes()
g.set_binary_blob(bytes(blob));g.save(p)
