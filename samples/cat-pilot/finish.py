import subprocess,json
from pathlib import Path
import imageio_ffmpeg
H=Path(__file__).resolve().parent;ff=imageio_ffmpeg.get_ffmpeg_exe()
assert len(list((H/'frames').glob('*.png')))==192
(H/'labels.ass').write_text('''[Script Info]
ScriptType: v4.00+
PlayResX: 512
PlayResY: 512
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,15,15,18,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Free Cat Pilot: Walk + blink
Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,Run + blink
Dialogue: 0,0:00:06.00,0:00:08.00,Default,,0,0,0,,Cheer - no speech rig included
''')
out=H/'cat-pilot-preview.mp4'
subprocess.run([ff,'-y','-v','error','-framerate','24','-i','frames/%04d.png','-vf','subtitles=labels.ass','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(out)],cwd=H,check=True)
subprocess.run([ff,'-v','error','-i',str(out),'-f','null','-'],check=True);print('Preview encoded and decoded successfully')
