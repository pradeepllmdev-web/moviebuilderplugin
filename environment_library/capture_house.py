import json,math,time,urllib.request,argparse
from pathlib import Path
from demo_client import command,BASE
H=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--set',choices=['house','city','scale-check'],default='house');args=parser.parse_args()
manifest=H/('demos/latest-'+args.set+'.json')
deadline=time.time()+240
while not manifest.exists():
 if (H/('demos/'+args.set+'-error.txt')).exists():raise RuntimeError((H/('demos/'+args.set+'-error.txt')).read_text())
 if time.time()>deadline:raise TimeoutError('House build pending; inspect editor')
 time.sleep(2)
latest=json.loads(manifest.read_text());D=Path(latest['directory'])
for name,shot in latest['cameras'].items():
 location,target=shot['location'],shot['target'];dx,dy,dz=[b-a for a,b in zip(location,target)]
 command('set_camera',{'location':location,'rotation':[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]})
 time.sleep(5)
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
 assert data.startswith(b'\x89PNG')
 (D/(name+'.png')).write_bytes(data)
 print('Captured '+name,flush=True)
(D/'preview.png').write_bytes((D/({'house':'interior.png','city':'skyline.png','scale-check':'character_height.png'}[args.set])).read_bytes())
print('COMPLETE '+str(D),flush=True)
