import json,subprocess,argparse
from pathlib import Path
import imageio_ffmpeg
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE);args=parser.parse_args();HERE=args.directory.resolve()
plan=json.loads((HERE/'application.json').read_text())
if len(list((HERE/'frames').glob('frame_*.png')))!=plan['frames']:raise ValueError('Missing rendered frames')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();output=HERE/'lion-talking-audition.mp4'
delay=str(round(plan['audio_start']*1000))
subprocess.run([ffmpeg,'-y','-v','error','-framerate',str(plan['fps']),'-i',str(HERE/'frames/frame_%04d.png'),
    '-i',plan['audio'],'-filter_complex','[1:a]adelay='+delay+'|'+delay+',apad[a]',
    '-map','0:v','-map','[a]','-t','8','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],check=True)
subprocess.run([ffmpeg,'-v','error','-i',str(output),'-f','null','-'],check=True)
(HERE/'delivery.json').write_text(json.dumps({'duration':8,'frames':192,'fps':24,'voice':plan['audio'],'full_decode_passed':True},indent=2))
print('Eight-second talking lion audition encoded and decoded successfully.')
