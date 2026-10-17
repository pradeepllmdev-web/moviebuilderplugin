import sys,json
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import pygltflib
from blend_shapes import read_accessor
p='implementation/character-workflow/amber-face-refinement/character-conservative.glb';g=pygltflib.GLTF2().load(p)
for m in g.meshes:
 for p in m.primitives:
  if p.material is not None and g.materials[p.material].name=='eyelids':
   print('color range',read_accessor(g,p.attributes.COLOR_0).min(axis=0).tolist(),read_accessor(g,p.attributes.COLOR_0).max(axis=0).tolist());print('normal average',read_accessor(g,p.attributes.NORMAL).mean(axis=0).tolist())
