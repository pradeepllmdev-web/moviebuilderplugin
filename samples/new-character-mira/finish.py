import json,subprocess
from pathlib import Path
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;frames=list((HERE/'frames').glob('frame_*.png'))
if len(frames)!=144:raise ValueError('Expected 144 rendered frames')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg,'-y','-v','error','-framerate','24','-i',str(HERE/'frames/frame_%04d.png'),
    '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'mira-body-audition.mp4')],check=True)
subprocess.run([ffmpeg,'-v','error','-i',str(HERE/'mira-body-audition.mp4'),'-f','null','-'],check=True)
print('Six-second body audition encoded and decoded successfully.')
