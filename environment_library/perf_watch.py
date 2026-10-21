"""Watch a built film: opens <folder>/movie.blend in the Blender window as a sequencer preview (Workbench) with sound and subtitles and plays it.

  python perf_watch.py out/ember

The master is a timeline of title cards and the linked scene files (rebuild a scene and the master follows). The same file is Blender's startup script."""
import sys,os,subprocess
try:
 import bpy
except ImportError:
 bpy=None
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
def setup():
 s=bpy.context.scene;s.frame_set(s.frame_start);s.sync_mode='AUDIO_SYNC';s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=540
 for w in bpy.context.window_manager.windows:
  for a in w.screen.areas:
   if a.type=='VIEW_3D':a.type='SEQUENCE_EDITOR';a.spaces[0].view_type='SEQUENCER_PREVIEW'
   elif a.type=='TIMELINE':a.type='SEQUENCE_EDITOR';a.spaces[0].view_type='SEQUENCER'
  for a in w.screen.areas:
   if a.type=='SEQUENCE_EDITOR':
    r=next((r for r in a.regions if r.type=='WINDOW'),None)
    with bpy.context.temp_override(window=w,area=a,region=r):
     try:bpy.ops.sequencer.view_all();bpy.ops.sequencer.view_all_preview()
     except Exception:pass
  with bpy.context.temp_override(window=w):bpy.ops.screen.animation_play()
 return None
if bpy is not None:bpy.app.timers.register(setup,first_interval=1.5)
elif __name__=='__main__':
 folder=sys.argv[1] if len(sys.argv)>1 else '.';m=os.path.join(os.path.abspath(folder),'movie.blend')
 if not os.path.exists(m):sys.exit('no movie.blend in %s (build the film first)'%folder)
 subprocess.Popen([BLENDER,m,'--python',os.path.abspath(__file__)]);print('opened',m)
