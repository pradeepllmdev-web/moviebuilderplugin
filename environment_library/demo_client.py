"""Local bridge client. Never retries a mutating command automatically."""
import json,urllib.request,argparse,time
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'demos'
import os
from urllib.parse import urlsplit
settings=json.loads((H/'local_settings.json').read_text()) if (H/'local_settings.json').is_file() else {}
BASE=os.environ.get('MOVIE_UNREAL_URL',settings.get('unreal_url','http://127.0.0.1:8520')).rstrip('/')
parsed=urlsplit(BASE)
if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:raise ValueError('Unreal bridge URL must be a local HTTP origin')
def command(name,params):
 req=urllib.request.Request(BASE+'/',json.dumps({'command':name,'params':params}).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','snapshot','camera']);p.add_argument('id');p.add_argument('--recipe');args=p.parse_args()
 if args.action=='build':
  request=json.loads(Path(args.recipe).read_text()) if args.recipe else next(r for r in json.loads((H/'demo_requests.json').read_text()) if r['id']==args.id)
  if request['id']!=args.id:raise ValueError('Recipe ID does not match requested environment')
  D.mkdir(exist_ok=True);(D/'build-request.json').write_text(json.dumps(request,indent=2))
  result=command('console_command',{'command':'py '+str(H/'build_demo_in_unreal.py').replace('\\','/')});print(json.dumps(result))
 elif args.action=='snapshot':
  path=D/args.id;path.mkdir(exist_ok=True)
  with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=45) as response:data=response.read()
  if not data.startswith(b'\x89PNG'):raise RuntimeError('Bridge did not return a PNG: '+data[:200].decode(errors='replace'))
  (path/'preview.png').write_bytes(data);print('Saved '+str(path/'preview.png'))
 else:
  request=next(r for r in json.loads((H/'demo_requests.json').read_text()) if r['id']==args.id);camera=request['camera'];x,y,z=camera['location'];tx,ty,tz=camera['target']
  import math
  dx,dy,dz=tx-x,ty-y,tz-z;rotation=[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]
  print(json.dumps(command('set_camera',{'location':[x,y,z],'rotation':rotation})))
