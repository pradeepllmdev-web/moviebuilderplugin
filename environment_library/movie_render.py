"""Explicit draft/final rendering of reviewed shots, then local audio/movie assembly."""
import json,re,time,urllib.request,subprocess,shutil,sys,wave,math
from pathlib import Path
from demo_client import command,BASE
H=Path(__file__).resolve().parent

def ffmpeg():
 path=shutil.which('ffmpeg')
 if path:return path
 import imageio_ffmpeg
 return imageio_ffmpeg.get_ffmpeg_exe()

def soundtrack(movie,folder):
 import numpy as np
 rate=24000;durations=[s['report']['duration'] for s in movie['shots']];length=sum(durations);n=round(length*rate);voice=np.zeros(n,dtype=np.float32);fx=np.zeros(n,dtype=np.float32);offset=0;random=np.random.default_rng(42)
 for item,duration in zip(movie['shots'],durations):
  p=json.loads((H/'scene_jobs'/item['scene_id']/'scene.json').read_text())
  for line in p.get('lines',[]):
   with wave.open(line['audio']) as w:
    if w.getsampwidth()!=2:raise ValueError('Dialogue requires 16-bit PCM')
    samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768;channels=w.getnchannels();source_rate=w.getframerate()
   if channels>1:samples=samples.reshape(-1,channels).mean(axis=1)
   samples=np.interp(np.arange(round(len(samples)*rate/source_rate))*source_rate/rate,np.arange(len(samples)),samples)
   at=round((offset+line['start'])*rate);end=min(n,at+len(samples));voice[at:end]+=samples[:end-at]
  for actor in p['actors']:
   for g in actor['segments']:
    if g['action']=='box_bump':
     at=round((offset+g['start']+g['duration']/2)*rate);count=min(round(.12*rate),n-at);fx[at:at+count]+=random.normal(0,1,count)*np.exp(-np.arange(count)/(rate*.025))*.12
    if g['action'] not in ['walk','run','box_carry']:continue
    step=.5 if g['action'] in ['walk','box_carry'] else .33
    for t in np.arange(g['start']+.1,g['end'],step):
     size=round(.06*rate);at=round((offset+t)*rate);count=min(size,n-at);pulse=random.normal(0,1,count)*np.exp(-np.arange(count)/(rate*.012))*.05;fx[at:at+count]+=pulse
  for event in p.get('events',[]):
   if event['type']=='box_contact':
    at=round((offset+event['time'])*rate);count=min(round(.12*rate),n-at);fx[at:at+count]+=random.normal(0,1,count)*np.exp(-np.arange(count)/(rate*.025))*.12;continue
   if event['type']=='wind_gust':
    at=round((offset+event['time'])*rate);count=min(round(event.get('duration',2)*rate),n-at)
    noise=random.normal(0,1,count);noise=np.convolve(noise,np.ones(64)/64,mode='same');phase=np.arange(count)/max(1,count-1);gust=noise*np.sin(np.pi*phase)**2*.45
    fx[at:at+count]+=gust
    continue
   if event['type'] not in ['twig_snap','branch_fall']:continue
   at=round((offset+event['time']+(event.get('duration',1) if event['type']=='branch_fall' else 0))*rate)
   for delay,gain in [(0,.18),(.018,.12),(.052,.07)]:
    start=at+round(delay*rate);count=min(round(.07*rate),n-start)
    if count>0:
     burst=random.normal(0,1,count);burst-=np.concatenate(([0],burst[:-1]))*.8;fx[start:start+count]+=burst*np.exp(-np.arange(count)/(rate*.009))*gain
  offset+=duration
 t=np.arange(n)/rate;music=np.zeros(n,dtype=np.float32)
 for start in np.arange(0,length,4):
  chord=[130.81,164.81,196] if int(start/4)%2==0 else [110,146.83,174.61];mask=(t>=start)&(t<start+4);phase=t[mask]-start;envelope=np.minimum(phase/.4,1)*np.minimum((4-phase)/.8,1)
  for freq in chord:music[mask]+=np.sin(2*np.pi*freq*phase)*envelope*.012
 # Duck the original procedural score below speech and limit the final mix.
 block=max(1,rate//20);energy=np.maximum.reduceat(np.abs(voice),np.arange(0,n,block));duck=np.repeat(np.where(energy>.02,.3,1),block)[:n];mix=voice*.85+fx+music*duck;mix*=np.minimum(t/.2,1)*np.minimum((length-t)/.3,1);peak=float(np.max(np.abs(mix)))
 if peak>.94:mix*=.94/peak
 with wave.open(str(folder/'soundtrack.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((mix*32767).astype(np.int16).tobytes())
 return {'duration':length,'peak':min(peak,.94),'music':'original procedural score','effects':'procedural footsteps; not surface-specific'}

def worker(job,lock,movie_id,quality='draft'):
 try:
  if not re.fullmatch(r'[a-f0-9]{32}',movie_id) or quality not in ['draft','final']:raise ValueError('Invalid movie or quality')
  D=H/'movie_jobs'/movie_id;movie=json.loads((D/'ready.json').read_text())
  if not lock.acquire(blocking=False):raise RuntimeError('Unreal is busy. Wait before rendering.')
  try:
   clips=[]
   for i,item in enumerate(movie['shots']):
    job['stage']='Rendering shot '+str(i+1)+' of '+str(len(movie['shots']));r=item['report'];key=uuid_hex();output=H/'demos'/('open-result-'+key+'.json');(H/'demos/open-request.json').write_text(json.dumps({'id':key,'level':r['level'],'sequence':r['sequence']}));command('console_command',{'command':'py '+str(H/'open_saved_unreal.py').replace('\\','/')});deadline=time.monotonic()+90
    while not output.exists():
     if time.monotonic()>deadline:raise TimeoutError('Unreal did not confirm shot opening')
     time.sleep(.5)
    opened=json.loads(output.read_text())
    if not opened['ok']:raise RuntimeError(opened['error'])
    folder=D/('render_'+job['id']+'_'+str(i));folder.mkdir();reply=command('render_scene',dict(sequence_path=r['sequence'],quality=quality,resolution=[640,360] if quality=='draft' else [1920,1080],sound=False,container='mp4',output_dir=str(folder),name='shot',look=True))
    if reply.get('status')!='ok':raise RuntimeError(str(reply))
    deadline=time.monotonic()+3600
    while True:
     with urllib.request.urlopen(BASE+'/render_status',timeout=30) as response:state=json.load(response)
     if state.get('sequence_path')!=r['sequence']:raise RuntimeError('Another render replaced this job')
     if state.get('clip_error') or state.get('state')=='failed':raise RuntimeError(state.get('clip_error') or 'Unreal rendering failed')
     clip=(state.get('clip') or {}).get('clip')
     if clip:
      path=Path(clip).resolve()
      if not path.is_relative_to(folder.resolve()) or not path.is_file():raise RuntimeError('Invalid rendered clip path')
      clips.append(path);break
     if time.monotonic()>deadline:raise TimeoutError('Render timed out. Inspect Unreal before retrying')
     time.sleep(2)
   job['stage']='Mixing dialogue, original music and footsteps';audio=soundtrack(movie,D);concat=D/'clips.txt';concat.write_text(''.join("file '"+str(p).replace('\\','/').replace("'","'\\''")+"'\n" for p in clips),encoding='utf-8')
   versioned=D/('movie-'+job['id']+'.mp4')
   command_line=[ffmpeg(),'-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-i',str(D/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart','-t',str(audio['duration']),str(versioned)]
   job['stage']='Assembling and decoding movie preview'
   subprocess.run(command_line,check=True,timeout=600,capture_output=True);subprocess.run([ffmpeg(),'-v','error','-i',str(versioned),'-f','null','-'],check=True,timeout=180,capture_output=True)
   shutil.copy2(versioned,D/'movie.mp4');shutil.copy2(D/'soundtrack.wav',D/('soundtrack-'+job['id']+'.wav'));movie.setdefault('render_history',[]).append({'job_id':job['id'],'quality':quality,'file':versioned.name})
   movie.update(rendered=True,audio=audio,quality=quality);(D/'ready.json').write_text(json.dumps(movie,indent=2));job.update(status='complete',stage='Movie preview assembled and decode checked',movie_id=movie_id,report=movie)
  finally:lock.release()
 except Exception as e:job.update(status='failed',error=str(e)[:1500])

def uuid_hex():
 import uuid
 return uuid.uuid4().hex
