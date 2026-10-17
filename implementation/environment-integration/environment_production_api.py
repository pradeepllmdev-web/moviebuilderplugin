"""3dobjectnew entry point for the local Unreal environment production service."""
from pathlib import Path
import json,re,uuid
import httpx
from fastapi import APIRouter,HTTPException,Response
from pydantic import BaseModel,Field
router=APIRouter(prefix='/api/environment-production',tags=['environment-production'])
SERVICE='http://127.0.0.1:8521'
STORE=Path(__file__).parent/'environment_production'
class PlanRequest(BaseModel):
 prompt:str=Field(min_length=5,max_length=4000)
 image:str|None=Field(default=None,max_length=17000000)
class BuildRequest(BaseModel):
 plan:dict
async def remote(method,path,body=None):
 try:
  async with httpx.AsyncClient(timeout=30) as client:r=await client.request(method,SERVICE+path,json=body)
 except httpx.HTTPError:raise HTTPException(503,'Environment service is offline. Start Environment Studio on port 8521.')
 if r.status_code>=400:
  try:detail=r.json().get('error','Environment request failed')
  except ValueError:detail='Environment request failed'
  raise HTTPException(r.status_code,detail)
 return r
@router.post('/plan')
async def plan(request:PlanRequest):
 return (await remote('POST','/api/prompt-plan',request.model_dump(exclude_none=True))).json()
@router.post('/build')
async def build(request:BuildRequest):
 return (await remote('POST','/api/prompt-build',request.model_dump())).json()
@router.get('/jobs/{job_id}')
async def job(job_id:str):
 if not re.fullmatch('[a-f0-9]{32}',job_id):raise HTTPException(400,'Invalid job ID')
 data=(await remote('GET','/api/jobs/'+job_id)).json()
 if data.get('status') in ('ready','complete'):
  STORE.mkdir(exist_ok=True);(STORE/(job_id+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
 return data
@router.get('/saved')
async def saved():
 data=(await remote('GET','/api/demos')).json()
 return [item for item in data if item['id'].startswith('PromptSet_')]
@router.get('/media/{set_id}/{filename}')
async def media(set_id:str,filename:str):
 if not re.fullmatch('PromptSet_[a-f0-9]{12}',set_id) or filename not in ('preview.png','plan.json','build-result.json'):raise HTTPException(400,'Invalid environment file')
 r=await remote('GET','/demos/'+set_id+'/'+filename)
 return Response(content=r.content,media_type='image/png' if filename.endswith('.png') else 'application/json')
