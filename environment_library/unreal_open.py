"""Only open levels already recorded by this studio; never accept executable commands."""
import json,re
from pathlib import Path
H=Path(__file__).resolve().parent

def known_levels():
 levels=set()
 def visit(value):
  if isinstance(value,dict):
   level=value.get('level')
   if isinstance(level,str) and re.fullmatch(r'/Game/EnvironmentDemos/[A-Za-z0-9_]+',level):levels.add(level)
   for child in value.values():visit(child)
  elif isinstance(value,list):
   for child in value:visit(child)
 paths=list((H/'demos').glob('*/build-result.json'))+list((H/'demos').glob('*.json'))+[H/'delivery_scene/sequence.json']
 for p in paths:
  try:visit(json.loads(p.read_text(encoding='utf-8-sig')))
  except (OSError,ValueError):continue
 return levels

def resolve_open(body):
 if body.get('scene')=='movie-master':
  key=body.get('movie_id','')
  if not re.fullmatch(r'[a-f0-9]{32}',key):raise ValueError('Invalid movie ID')
  data=json.loads((H/'movie_jobs'/key/'ready.json').read_text()).get('master',{})
  if not data.get('ok') or not re.fullmatch(r'/Game/StudioMovies/[a-f0-9]{32}/MasterLevel',data.get('level','')) or data.get('sequence')!=data['level'].rsplit('/',1)[0]+'/Master':raise ValueError('No valid saved master for this movie')
  return {'level':data['level'],'sequence':data['sequence']}
 if body.get('scene')=='prompt-scene':
  key=body.get('scene_id','')
  if not re.fullmatch(r'[a-f0-9]{32}',key):raise ValueError('Invalid scene ID')
  data=json.loads((H/'scene_jobs'/key/'ready.json').read_text())
  if not data.get('ok') or not re.fullmatch(r'/Game/StudioProduction/[a-f0-9]+/Level',data['level']) or data['sequence']!=data['level'].rsplit('/',1)[0]+'/Performance':raise ValueError('Invalid saved scene')
  return {'level':data['level'],'sequence':data['sequence']}
 if body.get('scene') in ('lion-run-mouth','lion-run-blink','lion-forest','lion-branch','lion-grip','lion-drive','lion-drive-v2','lion-climb','lion-scramble','lion-jump'):
  folder={'lion-run-blink':'lion-run-blink','lion-run-mouth':'lion-run-lipsync','lion-forest':'lion-forest-adventure','lion-branch':'lion-branch','lion-grip':'lion-grip-ik','lion-drive':'lion-fire-drive','lion-drive-v2':'lion-drive-v2','lion-climb':'lion-climb','lion-scramble':'lion-scramble','lion-jump':'lion-jump'}[body['scene']]
  data=json.loads((H.parent/'samples'/folder/'native.json').read_text())
  level=data['level'];sequence=data['sequence']
  if not re.fullmatch(r'/Game/StudioProduction/[a-f0-9]+/Level',level) or sequence!=level.rsplit('/',1)[0]+'/Performance':raise ValueError('Invalid saved lion test')
  return {'level':level,'sequence':sequence}
 if body.get('scene')=='lion-trial':
  data=json.loads((H.parent/'samples/lion-single-run/native.json').read_text())
  level=data['level'];sequence=data['sequence']
  if not re.fullmatch(r'/Game/StudioProduction/[a-f0-9]+/Level',level) or sequence!=level.rsplit('/',1)[0]+'/Performance':raise ValueError('Invalid saved lion trial')
  return {'level':level,'sequence':sequence}
 if body.get('scene')=='echo-inspector':
  shot_id=body.get('shot_id')
  data=json.loads((H.parent/'samples/echo-inspector/job-status.json').read_text())
  shot=next((s for s in data['result']['shots'] if s['shot_id']==shot_id),None)
  if not shot:raise ValueError('Choose a saved Echo Inspector shot')
  level=shot['native_scene']
  if not re.fullmatch(r'/Game/StudioProduction/[a-f0-9]+/Level',level):raise ValueError('Invalid saved scene')
  return {'level':level,'sequence':level.rsplit('/',1)[0]+'/Performance'}
 if body.get('scene')=='delivery':
  data=json.loads((H/'delivery_scene/sequence.json').read_text());return {'level':data['level'],'sequence':data['sequence']}
 level=body.get('level')
 if level not in known_levels():raise ValueError('Choose a saved environment from this studio')
 return {'level':level}

PROJECT=H.parent.parent/'unrealplugin-next/verification/LatestSceneProject'
def level_file(body):
 spec=resolve_open(body)
 content=(PROJECT/'Content').resolve()
 path=(content/(spec['level'].removeprefix('/Game/')+'.umap')).resolve()
 if not path.is_relative_to(content) or not path.is_file():raise ValueError('Saved Unreal level file is missing')
 return path

def open_folder(body):
 import os
 path=level_file(body)
 os.startfile(str(path.parent))
 return {'ok':True,'folder':str(path.parent),'filename':path.name}
