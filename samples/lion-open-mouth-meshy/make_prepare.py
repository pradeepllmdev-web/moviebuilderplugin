from pathlib import Path
p=Path('samples/lion-open-mouth-meshy/jaw_fit.py')
t=p.read_text();t=t[:t.index('# Identical jaw timing')]
t=t.replace("H=Path(__file__).resolve().parent","BASE=Path(__file__).resolve().parent;H=BASE/'talking';H.mkdir(exist_ok=True)").replace("str(H/'face-fit.blend')","str(BASE/'face-fit.blend')").replace(".x)<.095 and -.535",".x)<.075 and -.535")
t+='''
seal=o.shape_key_add(name='LipSeal')
for v in seal.data:
 p=w@v.co
 if p.z<=z+1e-5:
  weight=smooth((.15-abs(p.x))/.045)*smooth((-.43-p.y)/.05)*smooth((p.z-1.10)/.08)
  v.co=inv@(p+Vector((0,0,.028*weight)))
# Diagnostic poses before building the full performance.
for frame,value in [(1,0),(12,1)]:
 for a in [o]+added:
  a.data.shape_keys.key_blocks['JawOpen'].value=value
 seal.value=1-value
 bpy.context.view_layer.update();s.render.filepath=str(H/('closed.png' if frame==1 else 'open.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(H/'mouth-ready.blend'))
'''
Path('samples/lion-open-mouth-meshy/prepare_talking.py').write_text(t)
