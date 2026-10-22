"""Final render of a built film to one MP4 with sound (EEVEE frames, graded; every scene's tracks mixed; a title card with the scene's goal; loudness-normalised).

    python render_film.py out_folder                      full quality (1280x720, 24 samples)
    python render_film.py out_folder --draft              960x540, 8 samples: about half the time
    python render_film.py out_folder --scenes 2,3         only those scenes (the others keep their last render)
    python render_film.py out_folder --no-cards           no title cards

out_folder is a folder written by perf_movie.py (report.json, scene_NN_id.blend, audio_<id>/ tracks). Needs ffmpeg on the PATH. The result is out_folder/<film id>.mp4; per-scene clips are kept in out_folder/render/ so a re-render of one scene is cheap.
Pure helpers (ffmpeg command lines) are importable and tested without Blender."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
FONT='C\\:/Windows/Fonts/arial.ttf'
def ffmpeg():
 p=shutil.which('ffmpeg')
 if not p:raise SystemExit('ffmpeg not found on the PATH')
 return p
def esc(t):
 """text for ffmpeg drawtext"""
 return t.replace('\\','\\\\').replace("'",'\u2019').replace(':','\\:').replace('%','\\%')
def scene_cmd(frames,audio_files,out,fps=24,title='',goal='',cards=True,seconds=None):
 """ffmpeg command line for one scene: frames + the mixed tracks (+ a title card for the first 3.5 s)"""
 cmd=[ffmpeg(),'-y','-framerate',str(fps),'-i',str(Path(frames)/'f_%04d.png')]
 for a in audio_files:cmd+=['-i',str(a)]
 vf=[]
 if cards and (title or goal):
  fade="alpha='if(lt(t,3),1,max(0,1-(t-3)/.5))'"
  if title:vf.append("drawtext=fontfile='%s':text='%s':fontcolor=0xFFF2B3:fontsize=h/12:x=(w-text_w)/2:y=h*0.14:box=1:boxcolor=black@0.45:boxborderw=14:%s:enable='lt(t,3.5)'"%(FONT,esc(title),fade))
  if goal:vf.append("drawtext=fontfile='%s':text='%s':fontcolor=white:fontsize=h/20:x=(w-text_w)/2:y=h*0.26:box=1:boxcolor=black@0.45:boxborderw=10:%s:enable='lt(t,3.5)'"%(FONT,esc(goal),fade))
 if vf:cmd+=['-vf',','.join(vf)]
 if audio_files:
  n=len(audio_files);cmd+=['-filter_complex',''.join('[%d:a]'%(i+1) for i in range(n))+'amix=inputs=%d:normalize=0:dropout_transition=0,alimiter=limit=0.95[a]'%n,'-map','0:v','-map','[a]']
 cmd+=['-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium','-c:a','aac','-b:a','192k','-r',str(fps)]
 if seconds:cmd+=['-t','%.3f'%seconds]
 return cmd+[str(out)]
def final_cmd(listfile,out):
 """concatenate the scene clips and normalise the loudness of the whole film"""
 return [ffmpeg(),'-y','-f','concat','-safe','0','-i',str(listfile),'-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k',str(out)]
def render(out,draft=False,scenes=None,cards=True,echo=True):
 out=Path(out).resolve();rep=json.loads((out/'report.json').read_text(encoding='utf-8'));film=rep.get('film') or 'film';rd=out/'render';rd.mkdir(exist_ok=True)
 W,Hh,smp=(960,540,8) if draft else (1280,720,24);clips=[];t0=time.time()
 for r in rep['records']:
  i=r['index'];name='scene_%02d_%s'%(i,r['id']);blend=Path(r['file']) if r.get('file') else out/(name+'.blend');clip=rd/(name+'.mp4')
  if scenes and i not in scenes and clip.exists():clips.append(clip);continue
  if scenes and i not in scenes:continue
  fr=rd/('frames_%02d'%i)
  if fr.exists():shutil.rmtree(fr)
  if echo:print('scene %02d %s: rendering frames'%(i,r['id']),flush=True)
  p=subprocess.run([BLENDER,'-b',str(blend),'--python',str(H/'render_scene_frames.py'),'--',str(fr),str(W),str(Hh),str(smp)],capture_output=True,text=True,errors='ignore')
  if not any(fr.glob('f_*.png')):print('  render failed:',p.stdout[-400:]);continue
  spec=json.loads((out/(name+'.spec.json')).read_text(encoding='utf-8')) if (out/(name+'.spec.json')).exists() else {}
  audio=sorted((out/('audio_'+r['id'])).glob('*.wav'))
  subprocess.run(scene_cmd(fr,audio,clip,24,spec.get('title',''),spec.get('objective',''),cards,seconds=r.get('seconds')),capture_output=True)
  if clip.exists():
   clips.append(clip);shutil.rmtree(fr,ignore_errors=True)
   if echo:print('  %s done (%.0f s elapsed)'%(clip.name,time.time()-t0),flush=True)
 if not clips:return None
 lst=rd/'clips.txt';lst.write_text(''.join("file '%s'\n"%str(c).replace('\\','/') for c in clips),encoding='utf-8');final=out/(film+'.mp4')
 subprocess.run(final_cmd(lst,final),capture_output=True)
 if echo:print('film:',final if final.exists() else 'FAILED')
 return final if final.exists() else None
if __name__=='__main__':
 a=sys.argv[1:]
 if not a:print(__doc__);sys.exit(1)
 sc=None
 if '--scenes' in a:i=a.index('--scenes');sc=set(int(x) for x in a[i+1].split(','));del a[i:i+2]
 render(a[0],'--draft' in a,sc,'--no-cards' not in a)
