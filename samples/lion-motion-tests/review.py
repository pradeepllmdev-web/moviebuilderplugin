from pathlib import Path
import imageio_ffmpeg,subprocess
H=Path('samples/lion-motion-tests');f=imageio_ffmpeg.get_ffmpeg_exe()
for i,t in enumerate([3,10,17,25]):
 subprocess.run([f,'-y','-v','error','-ss',str(t),'-i',str(H/'lion-animation-test-reel.mp4'),'-frames:v','1',str(H/f'review-{i}.png')],check=True)
