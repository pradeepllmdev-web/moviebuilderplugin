"""Play a built movie scene by scene: opens each scene file in turn in the Blender viewer (closing the previous one) and waits for its length.
python play_movie.py scenes/movie_full [first_scene_number]"""
import json,subprocess,sys,time,pathlib
import previs
def seconds(blend,qr):
 p=subprocess.run([qr.BLENDER,'-b',str(blend),'--python-expr','import bpy;s=bpy.context.scene;print("LEN",(s.frame_end-s.frame_start+1)/s.render.fps)'],capture_output=True,text=True)
 return next(float(l.split()[1]) for l in p.stdout.splitlines() if l.startswith('LEN'))
def main(folder,first=1):
 folder=pathlib.Path(folder).resolve();plan=json.load(open(folder/'plan.json'));qr=previs._qr();cache=folder/'durations.json'
 dur=json.load(open(cache)) if cache.exists() else {}
 for i,sc in enumerate(plan['scenes'],1):
  f=pathlib.Path(sc['file'])
  if f.name not in dur:dur[f.name]=seconds(f,qr);json.dump(dur,open(cache,'w'))
 for i,sc in enumerate(plan['scenes'],1):
  if i<first:continue
  f=pathlib.Path(sc['file']);print('scene %d: %s (%.0f s)'%(i,sc['title'],dur[f.name]),flush=True)
  previs.open_viewer(f,folder,'movie');time.sleep(dur[f.name]+4)
if __name__=='__main__':main(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 1)
