"""Create new offline dialogue and scene-specific story plans for existing sets."""
import json,sys,wave,math
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import speech_visemes,talk_animation
river=json.loads((H/'demos/latest-realistic-river.json').read_text())['id']
house=json.loads((H/'demos/latest-house.json').read_text())['id']
city=json.loads((H/'demos/latest-city.json').read_text())['id']
collection={i['biome']:i['id'] for i in json.loads((H/'demos/environment-collection.json').read_text())}
stories=[
 ('river','The Floating Crown',river+'/character_height.png','reach', [('cat','Your crown is floating away!'),('lion','Then today, I rule the river!')]),
 ('pine','The Echo Detective','ForestMist/preview.png','listen',[('lion','Someone keeps copying my roar.'),('cat','That mountain has excellent manners!')]),
 ('woodland','The Tiny Giant',collection['beech_woods']+'/preview.png','crouch',[('cat','Careful! A beetle is crossing.'),('lion','Even kings can wait.')]),
 ('meadow','The Backwards Race',collection['meadow']+'/preview.png','run',[('lion','This race has one rule: backwards!'),('cat','Finally, a race with hindsight!')]),
 ('highland','The Brave First Step',collection['rocky_highland']+'/preview.png','balance',[('cat','That path looks rather narrow.'),('lion','Small steps. We cross together.')]),
 ('house','The Secret Recipe',house+'/interior.png','stir',[('lion','My soup needs one secret ingredient.'),('cat','A smaller spoonful of courage?')]),
 ('city','The Cloud Inspectors',city+'/skyline.png','look_up',[('cat','Our office is above the clouds!'),('lion','Good. No one can rain on us.')]),
 ('industrial','The Rhythm Factory','FreeKit_city_kit_industrial/preview.png','dance',[('lion','The factory has lost its rhythm.'),('cat','Then let us give it a beat!')]),
 ('suburban','The Surprise Delivery','FreeKit_city_kit_suburban/preview.png','wave',[('cat','Special delivery: one enormous smile!'),('lion','Perfect. Leave it with the neighbours!')]),
]
manifest=[]
for key,title,background,action,dialogue in stories:
 D=H/'demos/CharacterStories'/key;D.mkdir(parents=True,exist_ok=True)
 lines=[];parts=[];start=.6
 for i,(actor,text) in enumerate(dialogue):
  v=speech_visemes.sapi_speak(text,D/('line-'+str(i+1)),'Microsoft Zira Desktop' if actor=='cat' else 'Microsoft David Desktop',1)
  tr=talk_animation.build_track(v['visemes'],v['duration'],emotion='warm',intensity=1.05)
  lines.append(dict(actor=actor,text=text,start=start,duration=v['duration'],track=tr))
  with wave.open(str(v['wav'])) as stream:rate=stream.getframerate();parts.append((start,stream.readframes(stream.getnframes())))
  start+=v['duration']+.4
 duration=math.ceil((start+1)*12)/12;data=bytearray(round(duration*rate)*2)
 for start,raw in parts:
  offset=round(start*rate)*2;data[offset:offset+len(raw)]=raw
 with wave.open(str(D/'dialogue.wav'),'wb') as stream:
  stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(rate);stream.writeframes(data)
 plan=dict(id=key,title=title,action=action,background=str(H/'demos'/background),duration=duration,fps=12,lines=lines,
           method='Blender character performance composited over a still Unreal set view; previs, not in-engine interaction')
 (D/'plan.json').write_text(json.dumps(plan,indent=2))
 manifest.append(dict(id=key,title=title,action=action,duration=duration,video='/demos/CharacterStories/'+key+'/movie.mp4',
                      poster='/demos/CharacterStories/'+key+'/poster.png'))
 print(key+': dialogue ready, '+str(round(duration,2))+' seconds',flush=True)
(H/'demos/CharacterStories/manifest.json').write_text(json.dumps(manifest,indent=2))
