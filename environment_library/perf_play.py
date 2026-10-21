"""Open a built film's scene files in Blender one after another, each playing through its camera cuts, then closing it before the next.

  python perf_play.py <build folder> [first scene number] [last scene number]

Each scene opens in its own Blender window (3D view through the active camera, Workbench shading, sound on) and plays for its length; the window is closed and the next scene opens. The same file is Blender's startup script."""
import json,os,subprocess,sys,time,glob
try:
 import bpy
except ImportError:
 bpy=None
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
def _try(f):
 try:f()
 except Exception as e:print('perf_play:',e)
def setup():
 s=bpy.context.scene;_try(lambda:s.frame_set(s.frame_start));s.render.engine='BLENDER_WORKBENCH'
 s.display.shading.type='SOLID';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE'
 for w in bpy.context.window_manager.windows:
  for a in w.screen.areas:
   if a.type=='VIEW_3D':
    sp=a.spaces[0]
    def shade(sp=sp):
     sp.shading.type='SOLID';sp.shading.light='STUDIO';sp.shading.color_type='TEXTURE';sp.shading.show_cavity=False;sp.shading.use_dof=False
    _try(shade);_try(lambda sp=sp:setattr(sp.region_3d,'view_perspective','CAMERA'));_try(lambda sp=sp:setattr(sp.overlay,'show_overlays',False))
  def play(w=w):
   with bpy.context.temp_override(window=w):bpy.ops.screen.animation_play()
  _try(play)
 return None
if bpy is not None:bpy.app.timers.register(setup,first_interval=1.5)
elif __name__=='__main__':
 a=sys.argv[1:]
 if not a:sys.exit(__doc__)
 folder=os.path.abspath(a[0]);first=int(a[1]) if len(a)>1 else 1;last=int(a[2]) if len(a)>2 else 999
 files=sorted(glob.glob(os.path.join(folder,'scene_*.blend')))
 for k,f in enumerate(files,1):
  if k<first or k>last:continue
  pj=f+'.plan.json';sec=json.load(open(pj))['seconds'] if os.path.exists(pj) else 45
  print('scene %d: %s (%.0f s)'%(k,os.path.basename(f),sec),flush=True)
  p=subprocess.Popen([BLENDER,f,'--python',os.path.abspath(__file__)]);time.sleep(sec+4);p.terminate()
  try:p.wait(10)
  except Exception:p.kill()
