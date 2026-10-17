import sys,json
from pathlib import Path
sys.path.insert(0,'environment_library')
from verify_prompt_flow import request,wait
h=Path('environment_library')
prompt='Create The Lantern Road, a quiet woodland stop in bright morning mist, mood morning_fog. Two small buildings beside one straight road: a ranger hut and a travellers shelter, represented by supported modular buildings. Use one road tile only, straight at cell [0,0] yaw0. Building southwest corners [-1800,-400] and [1000,-400], each width_tiles3 depth_tiles3. Three spruce trees far away at [-3500,-1500], [-3500,1500] and [3500,1500]. Add two rocks at [3500,-1500] and [4500,-1500]. Use installed catalogue IDs and report unsupported architectural details.'
planned=wait(request('/api/prompt-plan',{'prompt':prompt}))
(h/'demos/creative-prompt-plan.json').write_text(json.dumps({'prompt':prompt,'plan':planned['plan']},indent=2))
print('PLAN READY',flush=True)
done=wait(request('/api/prompt-build',{'plan':planned['plan']}))
(h/'demos/creative-prompt-result.json').write_text(json.dumps(done,indent=2))
print(done['preview'],flush=True)
print(json.dumps(done['report']['warnings']),flush=True)



