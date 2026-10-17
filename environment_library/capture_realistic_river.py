"""Capture three inspection views and a short editor camera-move preview."""
import json,time,math,urllib.request,subprocess
from pathlib import Path
from demo_client import command, BASE
H=Path(__file__).resolve().parent
latest=json.loads((H/'demos/latest-realistic-river.json').read_text())
D=Path(latest['directory'])
def capture(location,target,path,settle=.25):
    dx,dy,dz=[b-a for a,b in zip(location,target)]
    command('set_camera',{'location':location,'rotation':[math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0]})
    time.sleep(settle)
    with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
    assert data.startswith(b'\x89PNG')
    path.write_bytes(data)
for name,(location,target) in latest['shots'].items():
    capture(location,target,D/(name+'.png'),2)
    print('Checked view: '+name,flush=True)
(D/'preview.png').write_bytes((D/'character_height.png').read_bytes())
frames=D/'camera-frames';frames.mkdir(exist_ok=True)
for i in range(48):
    t=i/47;s=t*t*(3-2*t)
    capture([-1100+1400*s,-650+500*s,260],[900,2100,160],frames/(f'{i:04}.png'))
    if i%12==0:print('Camera preview frames: '+str(i+1)+'/48',flush=True)
import imageio_ffmpeg
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-framerate','12','-i',str(frames/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18',str(D/'camera-study.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(D/'camera-study.mp4'),'-f','null','-'],check=True)
print('PASS: three views and decoded 4-second camera study',flush=True)
