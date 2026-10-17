"""Composite explicitly labelled previs and encode/fully decode each demo."""
import json,sys,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
H=Path(__file__).resolve().parent;key=sys.argv[1];D=H/'demos/CharacterStories'/key
p=json.loads((D/'plan.json').read_text());r=json.loads((D/'render-complete.json').read_text())
F=D/'frames';F.mkdir(exist_ok=True);W,HH=768,432
background=Image.open(p['background']).convert('RGBA').resize((W,HH),Image.Resampling.LANCZOS)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
for i in range(r['frames']):
 path=D/'alpha-frames'/f'{i:05d}.png';assert path.exists(),path
 character=Image.open(path).convert('RGBA');assert character.size==(W,HH)
 image=background.copy()
 # Soft graphic contact hints, not physically simulated Unreal shadows.
 shadow=Image.new('RGBA',(W,HH));draw=ImageDraw.Draw(shadow)
 for x in [260,515]:draw.ellipse((x-45,345,x+45,360),fill=(0,0,0,60))
 image=Image.alpha_composite(image,shadow.filter(ImageFilter.GaussianBlur(8)))
 image=Image.alpha_composite(image,character)
 overlay=Image.new('RGBA',(W,HH));draw=ImageDraw.Draw(overlay)
 draw.rectangle((0,0,W,46),fill=(8,15,20,160));draw.text((16,7),p['title'],font=font,fill='white')
 draw.text((16,29),'Blender + Unreal composite scene preview',font=small,fill=(200,215,222))
 t=i/r['fps'];line=next((l for l in p['lines'] if l['start']<=t<l['start']+l['duration']),None)
 if line:
  caption=('Leo: ' if line['actor']=='lion' else 'Amber: ')+line['text']
  draw.rectangle((0,392,W,HH),fill=(0,0,0,180));width=draw.textlength(caption,font=font)
  draw.text(((W-width)/2,402),caption,font=font,fill='white')
 image=Image.alpha_composite(image,overlay).convert('RGB');image.save(F/f'{i:05d}.png')
 if i==min(18,r['frames']-1):image.save(D/'poster.png')
with wave.open(str(D/'dialogue.wav')) as stream:
 rate=stream.getframerate();voice=np.frombuffer(stream.readframes(stream.getnframes()),dtype='<i2').astype(float)/32768
N=round(r['frames']/r['fps']*rate);voice=np.pad(voice,(0,max(0,N-len(voice))))[:N];t=np.arange(N)/rate
music=np.zeros(N)
for hz in ([130.81,164.81,196] if key not in ('highland','pine') else [130.81,155.56,196]):
 music+=.004*np.sin(t*2*np.pi*hz)*(1-np.exp(-t*2))*np.minimum(1,np.maximum(0,(N/rate-t)/.7))
with wave.open(str(D/'soundtrack.wav'),'wb') as stream:
 stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(rate);stream.writeframes((np.clip(voice+music,-.98,.98)*32767).astype('<i2').tobytes())
ff=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff,'-y','-framerate',str(r['fps']),'-i',str(F/'%05d.png'),'-i',str(D/'soundtrack.wav'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-c:a','aac','-shortest','-movflags','+faststart',str(D/'movie.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run([ff,'-v','error','-i',str(D/'movie.mp4'),'-f','null','-'],check=True)
delivery=dict(id=key,title=p['title'],action=p['action'],frames=r['frames'],fps=r['fps'],duration=r['frames']/r['fps'],full_decode_passed=True,
 method=p['method'],limitations=['Still Unreal background plate; Blender foreground composite','No in-engine contact, occlusion or physically matched shadows','12 fps previs; facial rig approximations remain'])
(D/'delivery.json').write_text(json.dumps(delivery,indent=2));print('DELIVERED '+key,flush=True)
