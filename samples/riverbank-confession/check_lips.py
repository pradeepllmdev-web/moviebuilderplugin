import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent;p=json.loads((H/'plan.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(H/'no-shortcuts.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene
for name in ('cat','lion'):
 options=[]
 for line in [l for l in p['lines'] if l['actor']==name]:
  tr=line['track'];valid=[(v,i) for i,v in enumerate(tr['weights']['mouthClose']) if tr['lead']<=i/24<tr['lead']+line['duration']];value,i=max(valid);options.append((value,i,line))
 value,i,line=max(options,key=lambda item:item[0]);tr=line['track']
 frame=round((line['start']+i/24-tr['lead'])*24)+1;s.frame_set(frame);s.render.filepath=str(H/('lip-press-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print(name,'frame',frame,'lip_press',round(value,3))
