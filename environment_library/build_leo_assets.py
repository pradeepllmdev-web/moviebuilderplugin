"""Build the lion animations the dinosaur scene needs (walk, run, pick up, sit) with the normal pipeline and copy each scene.blend to scenes/dino_assets/.
python build_leo_assets.py"""
import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import previs,scene_prompt
from concurrent.futures import ThreadPoolExecutor
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
PLANS={'walk':[beat('walk',4,distance_cm=300)],'run':[beat('run',2,distance_cm=600)],'pick':[beat('idle',2),beat('pick_up',5,purpose='takes the egg'),beat('idle',2)],'sit':[beat('idle',2),beat('sit_down',3),beat('sit',3)]}
def one(item):
 name,segments=item
 shot=dict(version=1,title='leo '+name,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='golden_hour',lookdev='soft_portrait',camera='full',unsupported=[],notes=[],actors=[dict(character='lion',position_cm=[0,0],segments=segments)])
 shot=scene_prompt.validate(shot);single=previs.actor_inputs(shot)[0];folder,ok,detail=previs.build_actor(single,'dino_'+name,2)
 return name,folder,ok,detail
out=Path(__file__).resolve().parent/'scenes'/'dino_assets';out.mkdir(parents=True,exist_ok=True)
with ThreadPoolExecutor(4) as pool:
 for name,folder,ok,detail in pool.map(one,PLANS.items()):
  print(name,'ok' if ok else 'FAIL',detail[:120])
  if (folder/'scene.blend').exists():shutil.copy(folder/'scene.blend',out/f'leo_{name}.blend');shutil.copy(folder/'route.json',out/f'leo_{name}_route.json')
