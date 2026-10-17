"""Mix original local score, generated speech, captions and asset credits."""
import json,math,subprocess,wave,sys
from pathlib import Path
import numpy as np
import imageio_ffmpeg
HERE=Path(__file__).parent.resolve();plan=json.loads((HERE/'movie.json').read_text());ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
performance='--performance' in sys.argv
fps=plan['fps'];duration=plan['duration']+(3 if performance else 2)
attention='--attention' in sys.argv or performance;body='--body' in sys.argv or attention;frame_folder=HERE/('performance-frames' if performance else 'attention-frames' if attention else 'body-frames' if body else 'frames')
assert len(list(frame_folder.glob('frame_*.png')))==plan['duration']*fps
rate=48000;t=np.arange(rate*duration)/rate;music=np.zeros_like(t)
for start,notes in [(0,[146.83,174.61,220]),(4,[130.81,164.81,196]),(8,[116.54,146.83,174.61]),(12,[130.81,164.81,196]),(16,[146.83,174.61,220])]:
    elapsed=t-start;gate=(elapsed>=0)&(elapsed<4);envelope=np.minimum(1,np.maximum(0,elapsed)/.8)*np.minimum(1,np.maximum(0,4-elapsed)/1.2)
    for frequency in notes:music+=gate*envelope*.012*np.sin(2*np.pi*frequency*t)
music*=np.minimum(1,t/1.5)*np.minimum(1,(duration-t)/1.5)
stereo=np.column_stack((music,music*.96));pcm=(np.clip(stereo,-1,1)*32767).astype('<i2')
with wave.open(str(HERE/'audio/score.wav'),'wb') as wav:
    wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(pcm.tobytes())
def timestamp(value):
    return f'0:{int(value)//60:02}:{int(value)%60:02}.{round((value-int(value))*100):02}'
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 960
PlayResY: 540
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dialogue,Arial,23,&H00FFFFFF,&H00FFFFFF,&H00101010,&H60000000,0,0,0,0,100,100,0,0,1,1.5,1,2,25,25,25,1
Style: Title,Arial,32,&H00FFFFFF,&H00FFFFFF,&H00101010,&H60000000,0,0,0,0,100,100,1,0,1,1,1,8,25,25,25,1
Style: Credit,Arial,19,&H00FFFFFF,&H00FFFFFF,&H00101010,&H60000000,0,0,0,0,100,100,0,0,1,1,1,2,25,25,35,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
events=['Dialogue: 0,0:00:00.00,0:00:02.00,Title,,0,0,0,,The Last Lantern']
inputs=['-framerate',str(fps),'-start_number','1','-i',str(frame_folder/'frame_%04d.png')]
filters=[];audio=[]
for index,shot in enumerate(plan['shots'],1):
    inputs+=['-i',str(HERE/'audio'/f"line_{shot['id']}.wav")]
    start=shot['start']+.5;delay=round(start*1000)
    filters.append(f'[{index}:a]adelay={delay}:all=1,apad[a{index}]');audio.append(f'[a{index}]')
    events.append(f"Dialogue: 0,{timestamp(start)},{timestamp(shot['start']+3.65)},Dialogue,,0,0,0,,{shot['text']}")
inputs+=['-i',str(HERE/'audio/score.wav')];audio.append('[5:a]')
filters.append(''.join(audio)+'amix=inputs=5:normalize=0,alimiter=limit=0.9[a]')
events.append('Dialogue: 0,0:00:16.00,'+timestamp(duration)+',Credit,,0,0,0,,Snow Rig © Blender Foundation | studio.blender.org | CC BY\\NJacob by jupifox | jupifox.itch.io | CC BY 4.0\\NAnimation, staging and materials modified · Local speech and original demo score'+('\\NMotion references: Kindel Media, Gustavo Fring, Tima Miroshnichenko / Pexels' if performance else ''))
(HERE/'captions.ass').write_text(header+'\n'.join(events)+'\n',encoding='utf-8')
output=HERE/('the-last-lantern-performance.mp4' if performance else 'the-last-lantern-attention.mp4' if attention else 'the-last-lantern-body.mp4' if body else 'the-last-lantern.mp4')
subprocess.run([ffmpeg,'-y','-hide_banner','-loglevel','error',*inputs,'-filter_complex',';'.join(filters),'-map','0:v','-map','[a]','-vf',f"tpad=stop_mode=clone:stop_duration={duration-plan['duration']},subtitles=captions.ass",'-t',str(duration),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)],cwd=HERE,check=True)
check=subprocess.run([ffmpeg,'-hide_banner','-i',str(output),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True,check=True)
assert '960x540' in check.stderr and '24 fps' in check.stderr and f'00:00:{duration:02}.00' in check.stderr
(HERE/('delivery-performance-report.json' if performance else 'delivery-attention-report.json' if attention else 'delivery-body-report.json' if body else 'delivery-report.json')).write_text(json.dumps({'movie':str(output),'rendered_frames':384,'fps':24,'resolution':[960,540],'story_seconds':16,'credits_seconds':duration-16,'duration_seconds':duration,'audio_video_decode_passed':True,'voices':'installed Windows speech, generated locally','music':'original procedural demo score','characters':['Snow','Jacob'],'engine':'Blender','original_assets_saved':False,'recorded_body_clips':body,'conversation_attention':attention,'typed_video_performance_capture':performance},indent=2))
print('MOVIE_READY',str(output))
