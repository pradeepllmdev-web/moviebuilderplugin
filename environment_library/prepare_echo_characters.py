import bpy,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin')
bpy.ops.wm.open_mainfile(filepath=str(H/'environment_library/demos/CharacterStories/meadow/performance.blend'),use_scripts=False,load_ui=False)
D=H/'samples/echo-inspector';D.mkdir(exist_ok=True)
entries={}
for name,label in [('lion','DemoLeo'),('cat','DemoAmber')]:
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE')
 rig.animation_data_clear()
 for o in rig.children_recursive:
  if o.type=='MESH' and o.data.shape_keys:
   o.data.shape_keys.animation_data_clear()
   for k in o.data.shape_keys.key_blocks:k.value=0
 rig.parent=None;rig.location.x=0;rig.location.y=0;rig.location.z=0
 if 'mixamorig:Hips' not in rig.data.bones:raise RuntimeError('Unexpected rig naming')
 rig['rig_version']=2
 collection=bpy.data.collections.new(label)
 for obj in [rig,*rig.children_recursive]:collection.objects.link(obj)
 path=D/(label+'.blend');bpy.data.libraries.write(str(path),{collection},fake_user=True)
 entries[label]=dict(asset_type='rigged_realistic',asset_path=str(path),collection=label,armature=rig.name,species=name,height_m=1.85 if name=='lion' else 1.5,rig_version=2,color=[.5,.5,.5])
(D/'catalog-entries.json').write_text(json.dumps(entries,indent=2));print('Prepared two character collections; no mesh data emitted')
