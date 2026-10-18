"""Build the lion animations the Storm Ship scene needs with the normal pipeline; each scene.blend goes to scenes/ship_assets/leo_<name>.blend with its baked action renamed leo_<name>.
python build_ship_assets.py [names]   (default: all; the cliff scene needs 'pick')"""
import sys,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import previs,scene_prompt,quick_review
from concurrent.futures import ThreadPoolExecutor
def beat(action,duration,dialogue='',**extra):return dict(action=action,duration=duration,dialogue=dialogue,**extra)
PLANS={'look':[beat('idle',2),beat('look_around',4)],'run':[beat('run',2,distance_cm=600)],'climb':[beat('climb_stairs',4)],'cut':[beat('punch',3)],'fall':[beat('fall_back',3)],
 'hit':[beat('hit_react',3)],'getup':[beat('get_up',3)],'dodge':[beat('dodge',3)],'punch':[beat('punch',3)],'cele':[beat('celebrate',5)],'idle':[beat('idle',4)],'pick':[beat('pick_up',5,purpose='lifts the cub onto his back')],'jump':[beat('jump',3,gap_cm=40)],'block':[beat('block',3)],'bow':[beat('bow',3)],'kick':[beat('kick',3)]}
RENAME="import bpy;r=next(o for o in bpy.data.objects if o.type=='ARMATURE' and o.animation_data and o.animation_data.action);r.animation_data.action.name='leo_%s';bpy.ops.wm.save_mainfile()"
def one(item):
 name,segments=item
 shot=dict(version=1,title='leo '+name,environment='forest',environment_id='RealisticRiver_20261015_093641',mood='golden_hour',lookdev='soft_portrait',camera='full',unsupported=[],notes=[],actors=[dict(character='lion',position_cm=[0,0],segments=segments)])
 shot=scene_prompt.validate(shot);single=previs.actor_inputs(shot)[0];folder,ok,detail=previs.build_actor(single,'ship_'+name,2)
 return name,folder,ok,detail
out=Path(__file__).resolve().parent/'scenes'/'ship_assets';out.mkdir(parents=True,exist_ok=True)
wanted=[a for a in sys.argv[1:] if a in PLANS] or list(PLANS)
with ThreadPoolExecutor(4) as pool:
 for name,folder,ok,detail in pool.map(one,[(k,PLANS[k]) for k in wanted]):
  print(name,'ok' if ok else 'FAIL',detail[:140])
  if (folder/'scene.blend').exists():
   dest=out/f'leo_{name}.blend';shutil.copy(folder/'scene.blend',dest);shutil.copy(folder/'route.json',out/f'leo_{name}_route.json')
   subprocess.call([quick_review.BLENDER,'-b',str(dest),'--python-expr',RENAME%name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
