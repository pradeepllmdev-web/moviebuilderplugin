import bpy,sys,json,math
from pathlib import Path
H=Path(__file__).resolve().parent;name=sys.argv[sys.argv.index('--')+1];D=H/name
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');root=bpy.data.objects['Actor path'];points={side:[] for side in ['Left','Right']};jaw=[];blink=[]
for f in range(1,s.frame_end+1):
 s.frame_set(f);bpy.context.view_layer.update()
 for side in points:points[side].append((r.matrix_world@r.pose.bones['mixamorig:'+side+'Foot'].head).copy())
 jaw.append(bpy.data.objects['char1'].data.shape_keys.key_blocks['JawOpen'].value)
 blink.append(bpy.data.objects['Lid L'].data.shape_keys.key_blocks['BlinkL'].value)
assert max(jaw)>.1 and min(jaw)<.01
assert max(blink)>.6
assert all(math.isfinite(v) for values in points.values() for p in values for v in p)
step=max((b-a).length for values in points.values() for a,b in zip(values,values[1:]));assert step<.35,'Foot discontinuity'
slip=[]
for values in points.values():
 zs=sorted(p.z for p in values);threshold=zs[len(zs)//5]+.012
 for a,b in zip(values,values[1:]):
  if max(a.z,b.z)<threshold and abs(a.z-b.z)<.012:slip.append((b-a).to_2d().length*24)
slip.sort();report={'frames':s.frame_end,'jaw_range':[min(jaw),max(jaw)],'blink_peak':max(blink),'max_foot_step_m':step,'estimated_low_foot_sliding_mps_median':slip[len(slip)//2] if slip else None,'estimated_low_foot_sliding_mps_max':max(slip) if slip else None,'contact_measurement':'ankle-height heuristic; not sole contact certification','status':'diagnostic preview; not perfect-model certification'}
(D/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
