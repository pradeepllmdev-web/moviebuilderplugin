"""Open each scene of a built film in the Blender viewer, one after another (camera cuts, voices, music), for watching without a render.

    python dev_tools/play_scenes.py scenes/movie_clock

Reads <folder>/report.json (written by perf_movie.py) and plays exactly the scenes of the latest build in order, so old scene files left in the folder are never played."""
import json,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H))
import previs
folder=Path(sys.argv[1]).resolve()
for i,r in enumerate(json.loads((folder/'report.json').read_text(encoding='utf-8'))['records'],1):
 f=Path(r['file']);secs=r.get('seconds') or 40;print('scene %d: %s (%.0f s)'%(i,f.name,secs),flush=True)
 previs.open_viewer(f,folder,'movie');time.sleep(secs+4)
