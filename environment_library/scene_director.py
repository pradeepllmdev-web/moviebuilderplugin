"""Small directing pass when the general story planner omits requested cues."""
import json,os

async def complete_controls(plan,prompt,scene_ai,validate_plan,require_controls):
 try:return require_controls(plan,prompt)
 except ValueError:pass
 shots=plan.get('shots',[plan]);timeline=[]
 for i,s in enumerate(shots):
  actors=s.get('actors') or [{'character':s['character'],'segments':s['segments']}]
  timeline.append({'shot':i,'actors':[{'character':a['character'],'segments':[{'index':j,'duration':g['duration'],'action':g['action']} for j,g in enumerate(a['segments'])]} for a in actors]})
 system='''Return ONLY JSON {"events":[{"shot":0,"type":"twig_snap","time":2}],"looks":[{"shot":0,"actor":"cat","segment":1,"yaw":-25,"pitch":3,"emotion":"alert"}]}. Add the head attention and twig snap expressly requested in the user's scene. Use only supplied shot/actor/segment indices. yaw -35..35, pitch -8..8. emotion neutral|alert|curious|reassuring. Twig event time is local to its shot and must fit the shot duration. Nonzero head turns are required when requested; keep them restrained. Use an empty events array when no snap is requested. When the user asks for eye contact or looking at each other, add look_at:"partner" to both stationary idle/talk actor cues. Do not use partner targets on walking/running. Do not change dialogue, durations, root movement or cast. No other fields or code.'''
 system+=' For an expressly requested falling branch, add branch_fall event with time, duration 0.4..2, position_cm:[x,y] and length_cm:40..140 on a stationary shot; keep its landing site clear of both characters.'
 system+=' When a wind gust is explicitly requested, add an event with type wind_gust, time and duration 0.3..6; omit unrelated sound events. A supplied shared 3D target can use look_at:point and target_cm:[x,y,z] on both stationary actors.'
 metadata=await scene_ai._call_openai_json(system,prompt+'\nExisting timeline: '+json.dumps(timeline,separators=(',',':')),os.environ.get('OPENAI_API_KEY',''),None)
 from pathlib import Path
 import uuid
 reports=Path(__file__).resolve().parent/'director_reports';reports.mkdir(exist_ok=True);(reports/(uuid.uuid4().hex+'.json')).write_text(json.dumps(metadata))
 apply_controls(plan,metadata)
 return require_controls(validate_plan(plan),prompt)

def apply_controls(plan,metadata):
 shots=plan.get('shots',[plan])
 def shot(index):
  if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(shots):raise ValueError('Director returned an invalid shot index')
  return shots[index]
 looks=metadata.get('looks',[]);events=metadata.get('events',[])
 if not isinstance(looks,list) or not isinstance(events,list) or len(looks)>48 or len(events)>8:raise ValueError('Too many director cues')
 for cue in looks:
  s=shot(cue['shot']);actors=s.get('actors') or [{'character':s['character'],'segments':s['segments']}];a=next((a for a in actors if a['character']==cue['actor']),None);index=cue['segment']
  if a is None or isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(a['segments']):raise ValueError('Director returned an invalid actor or segment')
  a['segments'][index].update(look_yaw_deg=cue.get('yaw',a['segments'][index].get('look_yaw_deg',0)),look_pitch_deg=cue.get('pitch',a['segments'][index].get('look_pitch_deg',0)),emotion=cue.get('emotion','neutral'))
  if 'look_at' in cue:a['segments'][index]['look_at']=cue['look_at']
  if 'target_cm' in cue:a['segments'][index]['look_target_cm']=cue['target_cm']
 for cue in events:
  s=shot(cue['shot']);event={'type':cue['type'],'time':cue['time']};existing=s.setdefault('events',[])
  for field in ['duration','position_cm','length_cm']:
   if field in cue:event[field]=cue[field]
  if event not in existing:existing.append(event)
 return plan
