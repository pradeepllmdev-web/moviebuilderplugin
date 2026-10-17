import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent/'performance-verification';report={}
def sample():
 o=max((o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys and 'jawOpen' in o.data.shape_keys.key_blocks),key=lambda o:len(o.data.vertices))
 values=[]
 for f in range(1,73):
  bpy.context.scene.frame_set(f);values.append([o.data.shape_keys.key_blocks[k].value for k in ('jawOpen','eyeBlinkLeft','eyeBlinkRight')])
 return values
for mode in ('standing','scene'):
 bpy.ops.wm.open_mainfile(filepath=str(H/mode/'demo.blend'),use_scripts=False,load_ui=False);original=sample()
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=24
 bpy.ops.import_scene.gltf(filepath=str(H/mode/'performance.glb'));imported=sample()
 error=max(abs(a-b) for av,bv in zip(original,imported) for a,b in zip(av,bv));assert error<1e-4,(mode,error)
 report[mode]={'facial_timing_max_error':error,'frames':72}
(H/'export-roundtrip.json').write_text(json.dumps(report,indent=2));print('ROUNDTRIP_PASSED '+json.dumps(report))
