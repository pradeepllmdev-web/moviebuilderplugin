"""Create distinct scanned-asset set studies in new levels, then capture previews."""
import json, time, math, urllib.request
from pathlib import Path
from demo_client import command, BASE
H=Path(__file__).resolve().parent
stamp=time.strftime('%Y%m%d_%H%M%S')
presets=[
 ('BeechSanctuary','Broadleaf woodland','beech_woods','meadow',False,'blockbuster',1.15,24000,250,91,[-850,-1100,210],[550,1800,260]),
 ('OpenMeadow','Open countryside','meadow','meadow',False,'blockbuster',1.35,30000,350,92,[-1800,-2200,240],[500,8000,200]),
 ('HighlandPass','Rocky highland pass','rocky_highland','valley',True,'overcast_drizzle',1.15,36000,400,93,[-4500,-6000,3500],[1000,10000,1800]),
]
items=[]
for key,title,biome,terrain,mountains,mood,density,size,stage,seed,location,target in presets:
 name=key+'_'+stamp
 D=H/'demos'/name;D.mkdir(parents=True)
 recipe={'id':name,'params':dict(biome=biome,terrain=terrain,river='none',mountains=mountains,mood=mood,
         density=density,size=size,stage_radius=stage,seed=seed,label=name),
         'camera':{'location':location,'target':target}}
 recipe['detail_layers']=[{'kind':'grass','density':300 if biome=='meadow' else 140,'scale':[.8,1.35],
                          'within':[*location[:2],4500],'in_clear':True},
                         {'kind':'fern','density':24 if biome=='beech_woods' else 3,'scale':[.7,1.25],
                          'within':[*location[:2],4000]}]
 (D/'recipe.json').write_text(json.dumps(recipe,indent=2))
 (H/'demos/build-request.json').write_text(json.dumps(recipe,indent=2))
 command('console_command',{'command':'py '+str(H/'build_demo_in_unreal.py').replace('\\','/')})
 deadline=time.time()+300
 while not (D/'build-result.json').exists():
  if (D/'error.txt').exists():raise RuntimeError((D/'error.txt').read_text())
  if time.time()>deadline:raise TimeoutError('Editor still working; inspect before retrying')
  time.sleep(2)
 time.sleep(4)
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
 assert data.startswith(b'\x89PNG')
 (D/'preview.png').write_bytes(data)
 report=json.loads((D/'build-result.json').read_text())
 items.append(dict(id=name,title=title,biome=biome,level=report['level'],preview='/demos/'+name+'/preview.png',warnings=report['warnings']))
 (H/'demos/environment-collection.json').write_text(json.dumps(items,indent=2))
 print(title+': saved '+report['level']+'; warnings='+str(report['warnings']),flush=True)
print('COMPLETE: three saved environments and previews',flush=True)
