import json,math,time,urllib.request
from pathlib import Path
from demo_client import command,BASE
H=Path(__file__).resolve().parent
latest=json.loads((H/'demos/latest-modular.json').read_text());D=Path(latest['directory'])
for name,shot in latest['cameras'].items():
 p,t=shot['location'],shot['target'];dx,dy,dz=[b-a for a,b in zip(p,t)]
 command('set_camera',{'location':p,'rotation':[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]})
 time.sleep(4)
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as r:data=r.read()
 if not data.startswith(b'\x89PNG'):raise RuntimeError('Invalid screenshot')
 (D/(name+'.png')).write_bytes(data)
(D/'preview.png').write_bytes((D/'overview.png').read_bytes())
print(D)
