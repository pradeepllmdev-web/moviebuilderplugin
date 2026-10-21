"""Blender script: render contact-sheet stills of a scene (Workbench, no video): the middle of every camera cut, at most N frames spread over the scene.

blender -b <scene.blend> --python contact_frames.py -- <out_dir> [N=12] [width=480]

Writes <out_dir>/f_<index>_<frame>.png and frames.json (index, frame, time, cut name). contact_sheet.py joins them into one labelled image."""
import bpy,sys,os,json
a=sys.argv[sys.argv.index('--')+1:];out=a[0];N=int(a[1]) if len(a)>1 else 12;W=int(a[2]) if len(a)>2 else 480
os.makedirs(out,exist_ok=True);sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x=W;sc.render.resolution_y=int(W*9/16);sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
marks=sorted([m for m in sc.timeline_markers if m.camera],key=lambda m:m.frame);ends=[m.frame for m in marks[1:]]+[sc.frame_end]
fr=[(m,(m.frame+e)//2) for m,e in zip(marks,ends)]
if len(fr)>N:fr=[fr[round(i*(len(fr)-1)/(N-1))] for i in range(N)]
meta=[]
for i,(m,f) in enumerate(fr):
 sc.frame_set(f);sc.camera=m.camera;sc.render.filepath=os.path.join(out,'f_%02d_%d.png'%(i,f));bpy.ops.render.render(write_still=True);meta.append(dict(index=i,frame=f,time=(f-1)/sc.render.fps,cut=m.name))
json.dump(meta,open(os.path.join(out,'frames.json'),'w'),indent=1);print('CONTACT_DONE',len(meta))
