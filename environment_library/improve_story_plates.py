import json,time,urllib.request
from pathlib import Path
from demo_client import command,BASE
H=Path(__file__).resolve().parent
collection={i['biome']:i for i in json.loads((H/'demos/environment-collection.json').read_text())}
city=json.loads((H/'demos/latest-city.json').read_text())
jobs=[('highland',collection['rocky_highland']['level'],[-1500,-2300,180],[1000,5000,130],True),
      ('city',json.loads((Path(city['directory'])/'build-result.json').read_text())['level'],[0,-16000,160],[4500,5000,130],False),
      ('industrial',json.loads((H/'demos/FreeKit_city_kit_industrial/build-result.json').read_text())['level'],[0,-2100,170],[0,1500,120],False),
      ('suburban',json.loads((H/'demos/FreeKit_city_kit_suburban/build-result.json').read_text())['level'],[0,-2100,170],[0,1500,120],False)]
for key,level,location,target,ground in jobs:
 D=H/'demos/CharacterStories'/key
 (H/'demos/CharacterStories/plate-request.json').write_text(json.dumps(dict(level=level,location=location,target=target,ground_camera=ground)))
 command('console_command',{'command':'py '+str(H/'set_story_plate_unreal.py').replace('\\','/')})
 time.sleep(4)
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
 assert data.startswith(b'\x89PNG')
 (D/'background.png').write_bytes(data)
 p=json.loads((D/'plan.json').read_text());p['background']=str(D/'background.png');(D/'plan.json').write_text(json.dumps(p,indent=2))
 print('Character-height background ready: '+key,flush=True)
