"""Stationary acting challenge, using installed assets and local speech."""
import json,uuid,threading
from pathlib import Path
from movie_prompt import worker
H=Path(__file__).resolve().parent
def actor(character,action,duration,text='',emotion='neutral'):
 return dict(character=character,position_cm=[-120,0] if character=='rowan' else [120,0],segments=[dict(action=action,duration=duration,dialogue=text,emotion=emotion,look_at='partner')])
def shot(title,camera,focus,duration,rowan='',lion='',emotion='neutral',events=None):
 return dict(version=1,title=title,environment='forest',mood='morning_fog',camera=camera,focus=focus,actors=[actor('rowan','talk' if rowan else 'idle',duration,rowan,emotion),actor('lion','talk' if lion else 'idle',duration,lion,'reassuring')],unsupported=[],notes=[],events=events or [])
plan=dict(version=1,title='The Forest Wakes - Polished Conversation',unsupported=[],shots=[shot('A sound in the trees','medium','both',3,emotion='alert',events=[dict(type='twig_snap',time=1)]),shot('Rowan hears it','reaction','rowan',4,rowan='Did you hear that?',emotion='curious'),shot('Leo reassures him','close','lion',4,lion='Just the forest waking up.',emotion='reassuring')])
job=dict(id=uuid.uuid4().hex,status='running');(H/'forest-conversation-job.json').write_text(json.dumps(job))
worker(job,threading.Lock(),plan=plan)
if job['status']=='complete':(H/'conversation-active.txt').write_text(job['id'])
(H/'forest-conversation-job.json').write_text(json.dumps(job,indent=2))
