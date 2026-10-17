import sys,json,shutil,time
from pathlib import Path
H=Path(__file__).resolve().parent.parent;D=H/'samples/echo-inspector';D.mkdir(exist_ok=True)
server=H.parent/'3dobjectnew/server';sys.path.insert(0,str(server))
import movie_db as m
from speech_visemes import sapi_speak
shots=[('The complaint', [('Amber','Leo, the mountain keeps copying me.'),('Leo','Then ask it for rent.')]),('The verdict',[('Amber','Rent!'),('Leo','A silent tenant. Perfect.')])]
with m.SessionLocal() as db:
 movie=m.Movie(name='The Echo Inspector',description='A sixteen-second comedy: Amber complains about a mountain echo; Leo invents a rental agreement. Native Blender performance rendered in Unreal.');db.add(movie);db.flush()
 story=m.MovieStory(movie_id=movie.id,content='At a mountain crossroads, Amber hears her voice echo. Leo advises charging rent. Amber demands payment from the mountain. Its silence convinces Leo they have found the perfect tenant.',status='approved');db.add(story)
 scene=m.MovieScene(movie_id=movie.id,order_index=0,name='A mountain with excellent manners',general_story=story.content);db.add(scene);db.flush()
 cast={}
 for name in ('Leo','Amber'):
  char=db.query(m.CharacterMetadata).filter_by(name=name).first()
  if not char:char=m.CharacterMetadata(name=name,description='Lion' if name=='Leo' else 'Cat');db.add(char);db.flush()
  cast[name]=char;db.add(m.MovieCharacter(movie_id=movie.id,character_id=char.id,role='Lead'));db.add(m.SceneCharacter(movie_scene_id=scene.id,character_id=char.id))
 for i,(title,lines) in enumerate(shots):
  shot=m.MovieSceneShot(movie_scene_id=scene.id,order_index=i,name=title,duration_seconds=8,action_description='Two friends exchange a playful complaint and a dry joke. Restrained listening and expressive speech.',camera_direction='Conversation two-shot with a gentle cinematic framing.');db.add(shot);db.flush()
  for j,(name,text) in enumerate(lines):
   voice='Microsoft David Desktop' if name=='Leo' else 'Microsoft Zira Desktop'
   speech=sapi_speak(text,D/f'shot-{i+1}-line-{j+1}',voice,1)
   filename=f'echo-inspector-{movie.id}-{i+1}-{j+1}.wav';shutil.copyfile(speech['wav'],server/'movie_files'/filename)
   file=m.FileMetadata(filename=filename,kind='audio',mime_type='audio/wav');db.add(file);db.flush()
   db.add(m.SceneDialogueLine(movie_scene_shot_id=shot.id,character_id=cast[name].id,order_index=j,text=text,status='approved',file_id=file.id,voice_used='Windows SAPI / '+voice))
 db.commit();manifest=dict(movie_id=movie.id,scene_id=scene.id,title=movie.name,duration=16,bindings={'Leo':'DemoLeo','Amber':'DemoAmber'},source_level='/Game/EnvironmentDemos/PromptSet_75c53dbd326e')
(D/'movie.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
