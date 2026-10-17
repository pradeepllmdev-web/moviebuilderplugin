import json,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'samples/echo-inspector';result=json.loads((D/'builder-result.json').read_text());file_id=result['render']['file_id'];source=H.parent.parent/'3dobjectnew/server/movie_files'/f'{file_id}.mp4'
out=H/'demos/EchoInspector';out.mkdir(exist_ok=True);target=out/'the-echo-inspector.mp4';shutil.copyfile(source,target)
subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True,capture_output=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(target)]))
assert abs(float(probe['format']['duration'])-16)<.1
assert any(s['codec_type']=='audio' for s in probe['streams'])
subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','3','-i',str(target),'-frames:v','1',str(out/'poster.png')],check=True)
plan=json.loads((D/'production-plan.json').read_text());vtt=['WEBVTT','']
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
for i,shot in enumerate(plan['contract']['shots']):
 for line in shot['lines']:vtt += [stamp(i*8+line['start'])+' --> '+stamp(i*8+line['end']),line['character']+': '+line['text'],'']
(out/'captions.vtt').write_text('\n'.join(vtt),encoding='utf-8')
manifest={'title':'The Echo Inspector','movie_id':36,'render_id':result['render']['id'],'duration':16,'width':640,'height':360,'full_decode_passed':True,'method':'3dobjectnew story/shot records → Blender performance → native Unreal rendering → Movie Builder assembly','video':'/demos/EchoInspector/the-echo-inspector.mp4','poster':'/demos/EchoInspector/poster.png','captions':'/demos/EchoInspector/captions.vtt','limitations':['Demo resolution; not a film-quality final.','Conversation blocking is restrained and both shots use similar framing.','Character material recovery was applied to this movie copy; generic material transfer still needs improvement.']}
(out/'movie.json').write_text(json.dumps(manifest,indent=2));print('Verified 16-second video and audio; full decode passed')
