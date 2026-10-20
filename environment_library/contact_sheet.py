"""Contact sheet of a built scene: renders stills with Blender (Workbench, no video) and joins them into one labelled PNG.

python contact_sheet.py <scene.blend> <out.png> [N=12] [columns=3] [width=480]
Needs Pillow. Used by perf_movie for every scene and by hand to review weak frames."""
import json,subprocess,sys,tempfile,os
from pathlib import Path
H=Path(__file__).resolve().parent
BLENDER=os.environ.get('BLENDER','C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
def render(blend,out_png,n=12,cols=3,width=480):
 from PIL import Image,ImageDraw
 d=Path(tempfile.mkdtemp(prefix='sheet_'))
 r=subprocess.run([BLENDER,'-b',str(blend),'--python',str(H/'contact_frames.py'),'--',str(d),str(n),str(width)],capture_output=True,text=True,errors='ignore')
 if not (d/'frames.json').exists():raise RuntimeError('contact frames failed: '+r.stdout[-400:]+r.stderr[-400:])
 meta=json.loads((d/'frames.json').read_text());ims=[Image.open(d/('f_%02d_%d.png'%(m['index'],m['frame']))).convert('RGB') for m in meta]
 w,h=ims[0].size;rows=(len(ims)+cols-1)//cols;sheet=Image.new('RGB',(w*cols,h*rows),(20,20,24));dr=ImageDraw.Draw(sheet)
 for k,(im,m) in enumerate(zip(ims,meta)):
  x,y=(k%cols)*w,(k//cols)*h;sheet.paste(im,(x,y));dr.rectangle([x,y,x+w,y+16],fill=(0,0,0));dr.text((x+4,y+2),'%.1fs  %s'%(m['time'],m['cut'][:48]),fill=(255,255,255))
 sheet.save(out_png);return meta
if __name__=='__main__':
 a=sys.argv[1:]
 if len(a)<2:print(__doc__);sys.exit(1)
 render(a[0],a[1],int(a[2]) if len(a)>2 else 12,int(a[3]) if len(a)>3 else 3,int(a[4]) if len(a)>4 else 480);print('wrote',a[1])
