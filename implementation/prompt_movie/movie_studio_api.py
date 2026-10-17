"""Main application proxy for the local, versioned scene/movie production service."""
import re
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from environment_production_api import remote
router=APIRouter(prefix='/api/movie-studio',tags=['movie-studio'])
class Prompt(BaseModel):
 prompt:str=Field(min_length=5,max_length=4000)
class Plan(BaseModel):
 plan:dict
class Pipeline(Plan):
 render:bool=True
class Open(BaseModel):
 scene_id:str
@router.post('/scene/plan')
async def scene_plan(body:Prompt):return (await remote('POST','/api/scene-plan',body.model_dump())).json()
@router.post('/scene/build')
async def scene_build(body:Plan):return (await remote('POST','/api/scene-build',body.model_dump())).json()
@router.post('/movie/plan')
async def movie_plan(body:Prompt):return (await remote('POST','/api/movie-plan',body.model_dump())).json()
@router.post('/movie/build')
async def movie_build(body:Plan):return (await remote('POST','/api/movie-build',body.model_dump())).json()
@router.get('/jobs/{key}')
async def job(key:str):
 if not re.fullmatch('[a-f0-9]{32}',key):raise HTTPException(400,'Invalid job ID')
 return (await remote('GET','/api/jobs/'+key)).json()
@router.get('/scenes')
async def scenes():return (await remote('GET','/api/scenes')).json()
@router.get('/movies')
async def movies():return (await remote('GET','/api/movies')).json()
@router.get('/capabilities')
async def capabilities():return (await remote('GET','/api/scene-capabilities')).json()
@router.post('/open')
async def open_scene(body:Open):return (await remote('POST','/api/open-unreal',{'scene':'prompt-scene','scene_id':body.scene_id})).json()
class Render(BaseModel):
 movie_id:str
 quality:str='draft'
@router.post('/render')
async def render(body:Render):return (await remote('POST','/api/movie-render',body.model_dump())).json()
@router.get('/media/{key}')
async def media(key:str):
 if not re.fullmatch('[a-f0-9]{32}',key):raise HTTPException(400,'Invalid movie ID')
 r=await remote('GET','/movie_jobs/'+key+'/movie.mp4')
 return Response(r.content,media_type='video/mp4')

@router.post('/movie/pipeline')
async def movie_pipeline(body:Pipeline):return (await remote('POST','/api/movie-pipeline',body.model_dump())).json()
@router.post('/movie/finish')
async def movie_finish(body:Render):return (await remote('POST','/api/movie-finish',body.model_dump())).json()
@router.post('/open-master')
async def open_master(body:Render):return (await remote('POST','/api/open-unreal',{'scene':'movie-master','movie_id':body.movie_id})).json()
