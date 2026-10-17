"""Sequential local render/encode runner; never invokes paid services."""
import subprocess,json,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;blender='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
items=json.loads((H/'demos/CharacterStories/manifest.json').read_text())
for item in ([] if '--assemble-only' in sys.argv else items):
 key=item['id'];D=H/'demos/CharacterStories'/key
 if '--finish-only' not in sys.argv:
  with (D/'render.log').open('w') as log:
   subprocess.run([blender,'-b','-t','6','--python',str(H/'render_character_story.py'),'--',key],stdout=log,stderr=subprocess.STDOUT,check=True)
 if not (D/'render-complete.json').exists():raise RuntimeError(key+': Blender did not write completion report')
 subprocess.run([sys.executable,str(H/'finish_character_story.py'),key],check=True)
 print('COMPLETED '+key,flush=True)
ff=__import__('imageio_ffmpeg').get_ffmpeg_exe();folder=H/'demos/CharacterStories'
(folder/'montage-list.txt').write_text('\n'.join("file '"+item['id']+"/movie.mp4'" for item in items))
subprocess.run([ff,'-y','-f','concat','-safe','0','-i',str(folder/'montage-list.txt'),'-c','copy','-movflags','+faststart',str(folder/'all-stories.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([ff,'-v','error','-i',str(folder/'all-stories.mp4'),'-f','null','-'],check=True)
(folder/'complete.json').write_text(json.dumps({'clips':len(items),'full_decode_passed':True,'finished_at':time.time()},indent=2))
print('ALL NINE STORIES COMPLETE',flush=True)
