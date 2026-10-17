import bpy,json
from pathlib import Path
p=Path(r'C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/samples/the-last-lantern')
bpy.ops.wm.open_mainfile(filepath=str(p/'the-last-lantern.blend'),load_ui=False,use_scripts=False)
r=bpy.data.objects['RIG-Snow']
print('PROPERTIES',json.dumps({'rig':list(r.keys()),'bones':{b.name:{k:str(b[k])[:80] for k in b.keys() if any(w in k.lower() for w in ('ik','fk','arm'))} for b in r.pose.bones if any(any(w in k.lower() for w in ('ik','fk','arm')) for k in b.keys())}}),flush=True)
