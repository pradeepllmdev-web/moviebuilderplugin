import subprocess,json,argparse
from pathlib import Path
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE);parser.add_argument('--name',default='rowan')
args=parser.parse_args();HERE=args.directory.resolve()
if len(list((HERE/'frames').glob('frame_*.png')))!=144:raise ValueError('Expected 144 frames')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();output=HERE/(args.name+'-talking-audition.mp4')
subprocess.run([ffmpeg,'-y','-v','error','-framerate','24','-i',str(HERE/'frames/frame_%04d.png'),
    '-i',str(ROOT/'samples/the-last-lantern/audio/line_2.wav'),'-filter_complex','[1:a]adelay=750|750,apad[a]',
    '-map','0:v','-map','[a]','-t','6','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac',
    '-movflags','+faststart',str(output)],check=True)
subprocess.run([ffmpeg,'-v','error','-i',str(output),'-f','null','-'],check=True)
(HERE/'delivery.json').write_text(json.dumps({'duration_seconds':6,'frames':144,'fps':24,'resolution':[768,768],
    'audio':'local Windows voice from existing fixture','full_decode_passed':True},indent=2))
print('Six-second talking audition encoded and decoded successfully.')
