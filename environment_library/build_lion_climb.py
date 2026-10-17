import sys,json,subprocess,time,uuid
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'samples/lion-climb';PLUGIN=H.parent.parent/'blendplugin-next/scene_pipeline'
sys.path.insert(0,str(H))
from demo_client import command
def status(stage):print(stage,flush=True)
blender='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
def run(args,log):
 with (D/log).open('w') as stream:subprocess.run(args,cwd=PLUGIN,stdout=stream,stderr=subprocess.STDOUT,check=True)
status('Building rock-climbing contact test')
run([blender,'-b','-t','6','--python-exit-code','1','-P',str(H/'build_lion_climb_blender.py'),'--',str(D),'--render','none'],'build.log')
status('Exporting body, face, camera and dialogue performance')
run([blender,'-b',str(D/'scene.blend'),'--python-exit-code','1','-P',str(PLUGIN/'export_performance.py'),'--','--out',str(D/'performance-v3'),'--plan',str(D/'scene.json'),'--combine-meshes'],'export.log')
status('Importing editable performance into Unreal')
request_id=uuid.uuid4().hex
result=command('production_import_performance',dict(request_id=request_id,package=str(D/'performance-v3'),environment='mountains',mood='golden_hour',source_level=None))['result']
deadline=time.monotonic()+900
while result.get('state') in ('pending','building') and time.monotonic()<deadline:
 time.sleep(2);result=command('production_result',dict(request_id=request_id))['result']
if result.get('state')!='done':raise RuntimeError(str(result))
(D/'native.json').write_text(json.dumps(result,indent=2));status('Unreal sequence built; ready for material and playback checks')



