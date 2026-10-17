import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(H/'front-setup.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');o=next(o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==r for m in o.modifiers));w=o.matrix_world;inv=w.inverted()
o.shape_key_add(name='Basis',from_mix=False);basis=o.data.shape_keys.key_blocks['Basis'];key=o.shape_key_add(name='JawClose',from_mix=False)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
pivot=Vector((0,-.37,.51));rot=Matrix.Rotation(math.radians(-22),3,'X')
for v,b in zip(key.data,basis.data):
 p=w@b.co;weight=smooth((.17-abs(p.x))/.075)*smooth((-.35-p.y)/.09)*smooth((.495-p.z)/.03)*smooth((p.z-.29)/.09)
 v.co=b.co+inv.to_3x3()@((pivot+rot@(p-pivot)-p)*weight)
key.value=0
for name in ['MouthRound','MouthWide','Smile']:
 k=o.shape_key_add(name=name,from_mix=False)
 for v,b in zip(k.data,basis.data):
  p=w@b.co;weight=math.exp(-(p.x/.12)**4-((p.z-.50)/.035)**2)*smooth((-.40-p.y)/.10)
  if p.z>.54:weight=0
  d=Vector((-.12*p.x,-.003,0)) if name=='MouthRound' else Vector((.10*p.x,0,0)) if name=='MouthWide' else Vector((0,0,.006*min(1,abs(p.x)/.08)))
  v.co=b.co+inv.to_3x3()@(d*weight)
 k.value=0
s.render.engine='CYCLES';s.cycles.samples=8
for name,close in [('mouth-open',0),('mouth-half',.5),('mouth-closed',1)]:
 key.value=close;s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
key.value=1;bpy.ops.wm.save_as_mainfile(filepath=str(H/'jaw-test.blend'))
protected=[i for i,b in enumerate(basis.data) if (w@b.co).z>.54];error=max((key.data[i].co-basis.data[i].co).length for i in protected);assert error<1e-7
(H/'jaw-verification.json').write_text(json.dumps({'upper_face_error_m':error,'fresh_geometry_only':True,'source_anatomy_preserved':True,'status':'pose-review-required','eyes':'not yet rigged'},indent=2));print('JAW_POSES_READY')

