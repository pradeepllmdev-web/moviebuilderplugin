"""Blender GUI startup for a linked-scene master: sequencer preview (Workbench, solid) with the strips framed, then play. blender movie.blend --python movie_view_setup.py"""
import bpy
def setup():
 s=bpy.context.scene;s.frame_set(s.frame_start);s.sync_mode='AUDIO_SYNC';s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=540
 for w in bpy.context.window_manager.windows:
  for a in w.screen.areas:
   if a.type=='VIEW_3D':a.type='SEQUENCE_EDITOR';a.spaces[0].view_type='SEQUENCER_PREVIEW'
   elif a.type=='TIMELINE':a.type='SEQUENCE_EDITOR';a.spaces[0].view_type='SEQUENCER'
  for a in w.screen.areas:
   if a.type=='SEQUENCE_EDITOR':
    sp=a.spaces[0]
    try:sp.shading.type='SOLID'
    except Exception:pass
    r=next((r for r in a.regions if r.type=='WINDOW'),None)
    with bpy.context.temp_override(window=w,area=a,region=r):
     try:bpy.ops.sequencer.view_all();bpy.ops.sequencer.view_all_preview()
     except Exception:pass
  with bpy.context.temp_override(window=w):bpy.ops.screen.animation_play()
 return None
bpy.app.timers.register(setup,first_interval=1.5)
