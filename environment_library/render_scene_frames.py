"""Render one built scene file to PNG frames with EEVEE (run inside Blender: blender -b scene.blend --python render_scene_frames.py -- <frames_dir> <width> <height> <samples> [first last]).
A graded finish: filmic-style view transform (already set by the scene), a soft bloom and a vignette in the compositor when the build of Blender allows it."""
import bpy,sys,os
a=sys.argv[sys.argv.index('--')+1:];out=a[0];W=int(a[1]);H=int(a[2]);samples=int(a[3]);first=int(a[4]) if len(a)>4 else None;last=int(a[5]) if len(a)>5 else None
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
try:
 sc.eevee.taa_render_samples=samples;sc.eevee.use_raytracing=False;sc.eevee.use_shadows=True
except Exception as e:print('eevee settings',e)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.use_motion_blur=False
if first is not None:sc.frame_start=first
if last is not None:sc.frame_end=min(sc.frame_end,last)
def finish():
 """a soft bloom and a vignette in the compositor (Blender 5.x node names: inputs are sockets, the group output is the composite)"""
 ng=bpy.data.node_groups.new('Finish','CompositorNodeTree');N=ng.nodes;L=ng.links
 ng.interface.new_socket('Image',in_out='OUTPUT',socket_type='NodeSocketColor')
 rl=N.new('CompositorNodeRLayers');gl=N.new('CompositorNodeGlare');out=N.new('NodeGroupOutput')
 for k,v in (('Type','Fog Glow'),('Threshold',1.2),('Strength',.35),('Quality','Medium')):
  try:gl.inputs[k].default_value=v
  except Exception as e:print('glare',k,e)
 L.new(rl.outputs['Image'],gl.inputs['Image']);last=gl.outputs['Image']
 try:
  el=N.new('CompositorNodeEllipseMask');bl=N.new('CompositorNodeBlur');mx=N.new('ShaderNodeMix');mx.data_type='RGBA';mx.blend_type='MULTIPLY'
  for k,v in (('Size',(.95,.9)),('Position',(.5,.5))):
   try:el.inputs[k].default_value=v
   except Exception as e:print('ellipse',k,e)
  for k,v in (('Size',(140.,140.)),('Type','Gaussian')):
   try:bl.inputs[k].default_value=v
   except Exception as e:print('blur',k,e)
  mx.inputs[0].default_value=.5;L.new(el.outputs['Mask'],bl.inputs['Image']);L.new(last,mx.inputs[6]);L.new(bl.outputs['Image'],mx.inputs[7]);last=mx.outputs[2]
 except Exception as e:print('vignette skipped',e)
 L.new(last,out.inputs[0]);sc.compositing_node_group=ng
try:finish()
except Exception as e:print('compositor skipped',e)
os.makedirs(out,exist_ok=True);sc.render.filepath=os.path.join(out,'f_')
bpy.ops.render.render(animation=True);print('RENDERED',sc.frame_start,sc.frame_end)
