import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
H=Path(__file__).resolve().parent.parent;D=H/'samples/lion-drive-v2'
bpy.ops.wm.open_mainfile(filepath=str(D/'car-source.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'shadow' not in o.name and 'glass' not in o.name]
body=next(o for o in objects if o.name=='car_body_car_body_0')
corners=[body.matrix_world@Vector(v) for v in body.bound_box];length=max(v.y for v in corners)-min(v.y for v in corners);scale=4.6/length
center=Vector(((max(v.x for v in corners)+min(v.x for v in corners))/2,(max(v.y for v in corners)+min(v.y for v in corners))/2,min(v.z for v in corners)))
conversion=Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Scale(scale,4)@Matrix.Translation(-center)
for o in objects:
 world=o.matrix_world.copy();o.parent=None;o.data.transform(conversion@world);o.matrix_world=Matrix.Identity(4)
groups={'Body':[o for o in objects if 'wheel' not in o.name]}
for code in ('BL','BR','FL','FR'):groups['Wheel_'+code]=[o for o in objects if 'wheel_'+code in o.name]
records=[]
for name,parts in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name
 corners=[Vector(v) for v in o.bound_box];lo=Vector(tuple(min(v[i] for v in corners) for i in range(3)));hi=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
 pivot=(lo+hi)*.5 if name!='Body' else Vector((0,0,0));o.data.transform(Matrix.Translation(-pivot));o.location=(0,0,0)
 bpy.ops.export_scene.fbx(filepath=str(D/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',path_mode='COPY',embed_textures=True,bake_anim=False)
 records.append({'name':name,'file':name+'.fbx','pivot_m':list(pivot),'radius_m':float((hi.z-lo.z)/2) if name!='Body' else None})
(D/'car-export.json').write_text(json.dumps({'parts':records,'length_m':4.6,'credit':'Fictional supercar - V12 Goblin by ollitei, CC Attribution','source':'https://sketchfab.com/3d-models/none-0a20e49ad5774d778567cb5c3f345786','modifications':'normalized scale; separated wheels; glass removed for driver visibility'},indent=2))
