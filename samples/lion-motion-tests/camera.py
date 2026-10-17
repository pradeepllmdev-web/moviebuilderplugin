import bpy,sys
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;name=sys.argv[sys.argv.index('--')+1];D=H/name
bpy.ops.wm.open_mainfile(filepath=str(D/'scene.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;c=s.camera;root=bpy.data.objects['Actor path']
for f in range(1,s.frame_end+1):
 s.frame_set(f);target=root.location+Vector((0,0,1));offset=Vector((0,-5,2.3)) if name=='circle' else Vector((2,-4.2,1))
 c.location=target+offset;c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.keyframe_insert('location',frame=f);c.keyframe_insert('rotation_euler',frame=f)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
