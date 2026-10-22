"""Blender script: render one EEVEE still of a built scene at a time, through the scene's own camera cut.

    blender -b scene_03_found.blend --python dev_tools/still_at.py -- <seconds> <out.png>"""
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:];t=float(a[0]);out=a[1];s=bpy.context.scene;f=int(s.frame_start+t*s.render.fps)
marks=sorted((m for m in s.timeline_markers if m.camera),key=lambda m:m.frame);s.camera=[m for m in marks if m.frame<=f][-1].camera;s.frame_set(f)
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=960;s.render.resolution_y=540;s.render.filepath=out;bpy.ops.render.render(write_still=True);print('OK',out)
