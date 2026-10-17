import bpy,json
from pathlib import Path
root=Path(r'C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin')
bpy.ops.wm.open_mainfile(filepath=str(root/'samples/the-last-lantern/the-last-lantern.blend'),load_ui=False,use_scripts=False)
r=bpy.data.objects['RIG-Snow']
print('ARM_CONTROLS',json.dumps([b.name for b in r.pose.bones if any(k in b.name.lower() for k in ('palm','hand','wrist','forearm','upperarm')) and b.name.endswith('.L')]),flush=True)
for n in ['UpperArm.L','FK-Shoulder.L','IK-M-UpperArm.L']:
 b=r.pose.bones.get(n)
 if b:print('CONTROL',n,'props',list(b.keys()),'constraints',[(c.type,c.name) for c in b.constraints],flush=True)
