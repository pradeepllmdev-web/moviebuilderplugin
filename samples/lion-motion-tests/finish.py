import json,subprocess
from pathlib import Path
import imageio_ffmpeg
H=Path(__file__).resolve().parent;ff=imageio_ffmpeg.get_ffmpeg_exe();names=['standing','walking','running','circle'];reports=[]
for name in names:
 D=H/name;p=json.loads((D/'application.json').read_text());assert len(list((D/'frames').glob('frame_*.png')))==p['frames']
 output=D/(name+'.mp4')
 subprocess.run([ff,'-y','-v','error','-framerate','24','-i',str(D/'frames/frame_%04d.png'),'-i',p['audio'],'-filter_complex','[1:a]adelay=350|350,apad[a]','-map','0:v','-map','[a]','-t',str(p['duration']),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],check=True)
 reports.append(p)
(H/'concat.txt').write_text('\n'.join("file '"+name+'/'+name+".mp4'" for name in names))
def stamp(t):
 h=int(t//3600);m=int(t%3600//60);sec=t%60;return f'{h}:{m:02d}:{sec:05.2f}'
head='''[Script Info]
ScriptType: v4.00+
PlayResX: 512
PlayResY: 512
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial,22,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,15,15,16,1
Style: Speech,Arial,17,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,20,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
t=0;events=[]
labels=['1. Standing and speaking','2. Walking and speaking','3. Running and speaking','4. Circular race run and speaking']
for i,p in enumerate(reports):
 end=t+p['duration'];events.append(f'Dialogue: 0,{stamp(t)},{stamp(end)},Title,,0,0,0,,{labels[i]}')
 events.append(f'Dialogue: 0,{stamp(t+.35)},{stamp(end-.2)},Speech,,0,0,0,,{p["text"]}');t=end
(H/'sections.ass').write_text(head+'\n'.join(events),encoding='utf-8')
output=H/'lion-animation-test-reel.mp4'
subprocess.run([ff,'-y','-v','error','-f','concat','-safe','0','-i','concat.txt','-vf','subtitles=sections.ass','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],cwd=H,check=True)
subprocess.run([ff,'-v','error','-i',str(output),'-f','null','-'],check=True)
(H/'delivery.json').write_text(json.dumps({'duration':t,'sections':reports,'full_decode_passed':True,'production_approved':False},indent=2));print('REEL_READY',round(t,2),flush=True)
