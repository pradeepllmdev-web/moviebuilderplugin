"""Three real AI prompts, sequential Unreal builds, persistent success/failure evidence."""
import json,urllib.request,time
from pathlib import Path
H=Path(__file__).resolve().parent;BASE='http://127.0.0.1:8000/api/environment-production'
def request(path,body=None):
 req=urllib.request.Request(BASE+path,json.dumps(body).encode() if body else None,{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
def wait(job):
 end=time.monotonic()+400
 while time.monotonic()<end:
  data=request('/jobs/'+job['id'])
  if data['status']=='failed':raise RuntimeError(data['error'])
  if data['status'] in ('ready','complete'):return data
  time.sleep(2)
 raise TimeoutError('Environment job timed out')
tests=[
 ('ForestOutpost','A quiet forest ranger outpost at morning fog. One small cabin at [1000,1000], width_tiles3 depth_tiles2. No road tiles. Four silver birch or beech trees spaced widely at [-5000,-3500], [-5000,3500], [5000,3500], [5000,-3500], scale0.6. Two mossy rocks at [-3000,0] and [4000,0], scale0.5. No mountains. Use only installed assets and supported construction.'),
 ('MountainVillage','A remote mountain village under soft overcast daylight, mood overcast_drizzle. Two small houses at [-1800,-400] and [1000,-400], width_tiles3 depth_tiles3. One straight road tile cell[0,0], yaw0. Three spruce trees spaced at [-4000,-2500], [-4000,2500], [4000,2500], scale0.6. A mountain behind at +Y, height_cm35000 size_cm180000 distance_cm150000 side_deg90. Use supported construction only.'),
 ('RoadsideSettlement','A sunny roadside settlement, mood blockbuster. Three modular buildings: southwest corners [-2400,-1000], [1400,-1000], [1400,1000], each width_tiles3 depth_tiles3. Straight north south road exactly three tiles: cells[0,-1],[0,0],[0,1], all yaw0. Three broadleaf beech trees spaced at [-5000,-3500], [-5000,3500], [5000,3500], scale0.5. Two Nordic rocks at [-3500,0] and [4500,-3000], scale0.5. No mountains. Do not add vehicles or unsupported props.')]
results=[]
for name,prompt in tests:
 row={'name':name,'prompt':prompt,'status':'planning'};results.append(row)
 try:
  planned=wait(request('/plan',{'prompt':prompt}));row['plan']=planned['plan'];print(name+': PLAN READY',flush=True)
  done=wait(request('/build',{'plan':row['plan']}));row.update(status='complete',preview=done['preview'],report=done['report']);print(name+': '+done['report']['level'],flush=True)
 except Exception as e:row.update(status='failed',error=str(e));print(name+': FAILED '+str(e),flush=True)
 (H/'demos/prompt-comparison.json').write_text(json.dumps(results,indent=2))
print('Finished '+str(sum(r['status']=='complete' for r in results))+'/3 builds',flush=True)
