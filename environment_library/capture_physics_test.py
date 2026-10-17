"""Capture live Unreal viewport frames alongside genuine simulation telemetry."""
import json,time,urllib.request,subprocess
from pathlib import Path
from demo_client import command,BASE
import imageio_ffmpeg
H=Path(__file__).resolve().parent;D=H/'physics_lab';F=D/'live-frames';F.mkdir(exist_ok=True)
command('console_command',{'command':'py '+str(H/'run_physics_test_unreal.py').replace('\\','/')})
start=time.time();index=0;times=[]
while time.time()-start<19:
 with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:data=response.read()
 if not data.startswith(b'\x89PNG'):raise RuntimeError('Missing viewport screenshot')
 (F/f'{index:04d}.png').write_bytes(data);times.append(time.time()-start);index+=1
 time.sleep(.3)
 if index%10==0:print('Captured '+str(index)+' live frames',flush=True)
fps=(index-1)/max(times[-1]-times[0],.01)
ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-y','-framerate',str(fps),'-i',str(F/'%04d.png'),'-frames:v',str(index),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(D/'physics-test.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([ff,'-v','error','-i',str(D/'physics-test.mp4'),'-f','null','-'],check=True)
(D/'capture.json').write_text(json.dumps({'frames':index,'timestamps_wall_seconds':times,'playback_fps':fps,'full_decode_passed':True,'method':'Live Unreal viewport capture; variable screenshot timing'},indent=2))
print('LIVE_PHYSICS_PREVIEW_COMPLETE',flush=True)
