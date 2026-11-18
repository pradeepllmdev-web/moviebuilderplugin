"""Side-by-side check of what Unreal plays against what Blender built.
    python compare_unreal.py <movie_folder> [--scenes 5,7] [--frames 3]
For every scene: renders N frames in Blender (Workbench) and in the open Unreal editor (Movie Render Queue, draft, through the bridge) and writes
<export root>/<movie>/compare/scene_NN.png (Blender left, Unreal right, one row per frame)."""
import json,subprocess,sys,time
from pathlib import Path
from PIL import Image,ImageDraw
import quick_review,unreal_send as us
H=Path(__file__).resolve().parent
def pick(start,end,n):return [int(start+(end-start)*(i+.5)/n) for i in range(n)]
def unreal_frame(b,seq,f,out):
 b.command('render_movie',{'sequence_path':seq,'preset':'draft','resolution':[960,540],'format':'png','start_frame':f,'end_frame':f+1,'output_dir':str(out)});time.sleep(2)
 for _ in range(100):
  if b.get('/render_status').get('state')=='done':break
  time.sleep(2)
 got=sorted(Path(out).glob('*.png'));return got[-1] if got else None
def compare(movie,only=None,n=3):
 movie=Path(movie);rep=json.loads((movie/'report.json').read_text(encoding='utf-8'));b=us.Bridge();root=us.export_root()/movie.name;sheets=[]
 for r in rep['report']:
  if only and r['index'] not in only:continue
  if not r.get('file'):continue
  name='%s_%02d_%s'%(movie.name,r['index'],r['piece']);doc=json.loads((root/name/(name+'.ue.json')).read_text(encoding='utf-8'));fr=pick(doc['frame_start'],doc['frame_end'],n);cmp=root/'compare'/name;cmp.mkdir(parents=True,exist_ok=True)
  subprocess.run([quick_review.BLENDER,'-b',r['file'],'--python',str(H/'bl_frames.py'),'--',str(cmp),','.join(map(str,fr))],capture_output=True,timeout=900)
  seq=[a['path'] for a in b.get('/assets?path=/Game/Movie')['assets'] if a['path'].split('/')[-1]=='LS_'+name][0]
  rows=[]
  for f in fr:
   ue=unreal_frame(b,seq,f,cmp/('ue_%d'%f));bl=cmp/('blender_%04d.png'%f)
   if ue and bl.exists():rows.append((f,Image.open(bl).convert('RGB').resize((640,360)),Image.open(ue).convert('RGB').resize((640,360))))
  if rows:
   W=Image.new('RGB',(1280,360*len(rows)));d=ImageDraw.Draw(W)
   for i,(f,x,y) in enumerate(rows):W.paste(x,(0,i*360));W.paste(y,(640,i*360));d.text((6,i*360+4),'Blender f%d'%f,fill=(255,255,0));d.text((646,i*360+4),'Unreal',fill=(255,255,0))
   p=root/'compare'/('scene_%02d.png'%r['index']);W.save(p);sheets.append(str(p));print(p,flush=True)
 return sheets
if __name__=='__main__':
 a=sys.argv[1:];only=None;n=3
 if '--scenes' in a:i=a.index('--scenes');only={int(x) for x in a[i+1].split(',')};del a[i:i+2]
 if '--frames' in a:i=a.index('--frames');n=int(a[i+1]);del a[i:i+2]
 compare(a[0],only,n)
