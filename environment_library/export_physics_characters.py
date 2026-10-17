"""Export the existing animals, sampling animation internally without geometry logs."""
import bpy,json,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from export_performance import export
bpy.ops.wm.open_mainfile(filepath=str(H/'demos/CharacterStories/meadow/performance.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;s.frame_set(1)
catalog={};checks=[]
for name in ['lion','cat']:
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE')
 root.animation_data_clear();root.location.x=0;root.location.y=0;root.rotation_euler.z=0
 catalog[name]={'armature':rig.name}
 checks.append({'name':name,'required_foot_bones_present':all('mixamorig:'+side+'Foot' in rig.pose.bones for side in ['Left','Right'])})
out=H/'physics_lab'/('package_'+time.strftime('%Y%m%d_%H%M%S'))
export(out,{'actors':[{'name':'lion'},{'name':'cat'}]},combine_meshes=False,catalog=catalog)
(H/'physics_lab/latest-package.json').write_text(json.dumps({'directory':str(out),'checks':checks},indent=2))
print('PHYSICS_CHARACTER_EXPORT_COMPLETE; two characters; foot bone checks '+str(all(c['required_foot_bones_present'] for c in checks)))
