"""Reproducible scanned-asset river set; run from local Python with bridge 8520."""
import json, time, urllib.request, math, subprocess, sys
from pathlib import Path
from demo_client import command, BASE
from layout import compile_layout
H = Path(__file__).resolve().parent
name = 'RealisticRiver_' + time.strftime('%Y%m%d_%H%M%S')
layout = {'width_m':160,'depth_m':160,
          'rivers':[{'points':[[0,40],[20,43],[40,39],[60,37],[80,43],[100,38]],'width_m':9}],
          'paths':[], 'bridges':[],
          'forests':[{'center':[24,30],'radius_m':36,'density':1.0},
                     {'center':[76,28],'radius_m':40,'density':1.0},
                     {'center':[20,65],'radius_m':24,'density':.85},
                     {'center':[80,65],'radius_m':26,'density':.85}],
          'clear':[{'center':[50,58],'radius_m':5}],
          'camera':{'position':[47,53],'target':[57,37],'height_m':2.2,'target_height_m':1.4}}
recipe = {'id':name,'params':{'biome':'nordic_forest','terrain':'meadow','river':'none','mountains':False,
          'size':26000,'stage_radius':350,'density':1.0,'seed':73,'mood':'morning_fog','label':name},
          'layout':layout,'compiled_layout':compile_layout(layout)}
recipe['camera'] = recipe['compiled_layout']['camera']
D = H / 'demos' / name
D.mkdir(parents=True)
(D / 'recipe.json').write_text(json.dumps(recipe,indent=2))
(H / 'demos/build-request.json').write_text(json.dumps(recipe,indent=2))
command('console_command',{'command':'py '+str(H / 'build_demo_in_unreal.py').replace('\\','/')})
deadline = time.time()+300
while not (D/'build-result.json').exists():
    if (D/'error.txt').exists(): raise RuntimeError((D/'error.txt').read_text())
    if time.time()>deadline: raise TimeoutError('Editor still building; inspect before retrying')
    time.sleep(2)
shots = {'wide':([-2200,-2200,850],[300,1800,180]),
         'character_height':([-480,-480,220],[1120,2080,140]),
         'river_detail':([100,850,180],[1400,1950,80])}
def capture(location,target,path):
    dx,dy,dz = [b-a for a,b in zip(location,target)]
    command('set_camera',{'location':location,'rotation':[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]})
    time.sleep(2)
    with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:
        data=response.read()
    assert data.startswith(b'\x89PNG')
    path.write_bytes(data)
for shot,(location,target) in shots.items():
    capture(location,target,D/(shot+'.png'))
    print('Captured '+shot,flush=True)
(D/'preview.png').write_bytes((D/'character_height.png').read_bytes())
(H/'demos/latest-realistic-river.json').write_text(json.dumps({'id':name,'directory':str(D),'shots':shots},indent=2))
print('COMPLETE '+str(D),flush=True)
command('console_command',{'command':'py '+str(H / 'polish_realistic_river_unreal.py').replace('\\','/')})
polish_deadline=time.time()+120
while not json.loads((D/'build-result.json').read_text()).get('polish'):
    if time.time()>polish_deadline:raise TimeoutError('Polish is not complete; inspect editor before retrying')
    time.sleep(2)
subprocess.run([sys.executable,str(H/'capture_realistic_river.py')],check=True)
