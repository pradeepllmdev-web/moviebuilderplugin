"""Diagnostic ankle plant correction; does not certify sole/toe rolling."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;D=H/sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False,load_ui=False)
assert 'contact_correction' not in json.loads((D/'application.json').read_text()),'Rebuild section before applying plant correction again'
s=bpy.context.scene;r=next(o for o in s.objects if o.type=='ARMATURE');root=bpy.data.objects['Actor path'];samples=[]
for f in range(1,s.frame_end+1):
 s.frame_set(f);bpy.context.view_layer.update();samples.append((root.location.copy(),[(r.matrix_world@r.pose.bones['mixamorig:'+side+'Foot'].head).copy() for side in ['Left','Right']]))
minimum=min(p.z for _,feet in samples for p in feet);threshold=minimum+.025
correction=Vector();active=None;anchor=None;used=0
for f,(position,feet) in enumerate(samples,1):
 candidate=min(range(2),key=lambda i:feet[i].z)
 if feet[candidate].z>threshold:active=None
 else:
  current=feet[candidate]+correction
  if candidate!=active:anchor=current.copy();active=candidate
  else:
   shift=anchor-current;shift.z=0
   # Bound per-frame correction, avoiding a touchdown snap.
   if shift.length>.07:shift*=.07/shift.length
   correction+=shift;used+=1
 s.frame_set(f);root.location=position+correction;root.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
p=json.loads((D/'application.json').read_text());p['contact_correction']={'plant_frames':used,'final_path_offset_m':correction.length,'method':'low ankle contact lock in world XY; flight unchanged','limitation':'toe roll and exact circular lap closure still require review'};(D/'application.json').write_text(json.dumps(p,indent=2))
s.frame_set(60);s.render.filepath=str(D/'preview.png');bpy.ops.render.render(write_still=True)

