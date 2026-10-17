import bpy,json
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');m=json.loads((H/'environment_library/movie_jobs/940944df98d34181912600bb1644fa09/ready.json').read_text());d=H/'environment_library/scene_jobs'/m['shots'][0]['scene_id'];bpy.ops.wm.open_mainfile(filepath=str(d/'actor_0/scene.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rows=[{'name':b.name,'deform':b.use_deform,'parent':b.parent.name if b.parent else None} for b in rig.data.bones if 'head' in b.name.lower()]
q=[]
for f in [1,48,96]:
 bpy.context.scene.frame_set(f);bpy.context.view_layer.update();q.append({'frame':f,'head_rotation':list(next(b for b in rig.pose.bones if b.name.endswith('Head')).rotation_quaternion)})
weights={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers):continue
 heights=[(o.matrix_world@v.co).z for v in o.data.vertices]
 if not heights:continue
 cutoff=min(heights)+(max(heights)-min(heights))*.78
 for v,z in zip(o.data.vertices,heights):
  if z<cutoff:continue
  for group in v.groups:
   name=o.vertex_groups[group.group].name;weights[name]=weights.get(name,0)+group.weight
(H/'environment_library/partner-head-controls.json').write_text(json.dumps({'heads':rows,'samples':q,'upper_mesh_weight_totals':sorted(weights.items(),key=lambda x:x[1],reverse=True)[:5]}))
