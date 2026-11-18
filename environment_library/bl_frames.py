"""Blender side of compare_unreal.py: render still frames of a built scene with the Workbench engine.
    blender -b scene.blend --python bl_frames.py -- <out_dir> <frame,frame,...>"""
import bpy,sys,os
out,frames=sys.argv[sys.argv.index('--')+1:][:2];frames=[int(x) for x in frames.split(',')]
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x,sc.render.resolution_y=960,540;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
os.makedirs(out,exist_ok=True)
for f in frames:
 sc.frame_set(f);sc.render.filepath=os.path.join(out,'blender_%04d.png'%f);bpy.ops.render.render(write_still=True)
