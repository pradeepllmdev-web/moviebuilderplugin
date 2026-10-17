import math,time,urllib.request
from pathlib import Path
from demo_client import command,BASE
D=Path(__file__).resolve().parent/'demos/PromptSet_963e753662ed'
for name,p,t in [('preview',[7200,-6500,4000],[1500,1000,150]),('furniture',[2300,-2300,260],[1400,-1200,45])]:
 dx,dy,dz=[b-a for a,b in zip(p,t)];command('set_camera',{'location':p,'rotation':[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]});time.sleep(3)
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as r:data=r.read()
 assert data.startswith(b'\x89PNG');(D/(name+'.png')).write_bytes(data)
print('Overview and furniture detail captured')
