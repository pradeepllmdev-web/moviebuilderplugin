import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import pygltflib
from blend_shapes import read_accessor
p=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65/body-rig.glb');g=pygltflib.GLTF2().load(str(p))
for n in g.nodes:
 if n.mesh is not None:
  a=read_accessor(g,g.meshes[n.mesh].primitives[0].attributes.POSITION)
  print(json.dumps({'name':n.name,'mesh':n.mesh,'skin':n.skin,'translation':n.translation,'rotation':n.rotation,'scale':n.scale,'bounds_min':a.min(axis=0).tolist(),'bounds_max':a.max(axis=0).tolist()}))
