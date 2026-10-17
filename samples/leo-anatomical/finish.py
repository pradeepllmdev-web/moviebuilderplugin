import json,subprocess
from pathlib import Path
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;plan=json.loads((HERE/'application.json').read_text())
if len(list((HERE/'frames').glob('frame_*.png')))!=192:raise ValueError('Missing frames')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();output=HERE/'leo-talking-audition.mp4'
subprocess.run([ffmpeg,'-y','-v','error','-framerate','24','-i',str(HERE/'frames/frame_%04d.png'),'-i',plan['audio'],
    '-filter_complex','[1:a]adelay=550|550,apad[a]','-map','0:v','-map','[a]','-t','8','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],check=True)
subprocess.run([ffmpeg,'-v','error','-i',str(output),'-f','null','-'],check=True)
print('Eight-second anatomical lion audition encoded and decoded successfully.')
