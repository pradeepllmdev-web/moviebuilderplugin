import bpy,json,math,random
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
H=Path(__file__).resolve().parent;ROOT=H.parents[1];plan=json.loads((H/'plan.json').read_text());fps=24;count=round(plan['duration']*fps)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'samples/lion-open-mouth-meshy/talking-blink/lion-talking.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene
def actor_objects(objects):
 rig=next(o for o in objects if o.type=='ARMATURE')
 keep=[rig]
 for o in objects:
  if o.type=='MESH' and (o in rig.children_recursive or any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)):keep.append(o)
 return rig,keep
lion,lo=actor_objects(list(s.objects))
for o in list(s.objects):
 if o not in lo:bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(ROOT/'samples/amber-open-mouth-v2/fresh-talking.blend'),link=False) as (src,dst):dst.objects=src.objects
cat,co=actor_objects([o for o in dst.objects if o])
for o in co:s.collection.objects.link(o)
actors={}
for name,rig,objects,x,height in [('lion',lion,lo,-.85,1.85),('cat',cat,co,.85,1.5)]:
 s.frame_set(1);bpy.context.view_layer.update()
 pts=[o.matrix_world@Vector(p) for o in objects if o.type=='MESH' for p in o.bound_box];low=min(p.z for p in pts);high=max(p.z for p in pts);cx=(min(p.x for p in pts)+max(p.x for p in pts))/2
 root=bpy.data.objects.new(name+' placement',None);s.collection.objects.link(root)
 for o in objects:
  if o.parent not in objects:w=o.matrix_world.copy();o.parent=root;o.matrix_world=w
 scale=height/(high-low);root.scale=(scale,)*3;root.location=(x-cx*scale,0,-low*scale)
 # Preserve existing body performance in a new baked action, looping gently.
 end=max(2,int(rig.animation_data.action.frame_range[1])) if rig.animation_data and rig.animation_data.action else 192
 poses=[]
 for f in range(count):
  s.frame_set(1+(f%max(1,end-1)));poses.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 rig.animation_data_clear()
 for o in objects:
  if o.type=='MESH' and o.data.shape_keys:o.data.shape_keys.animation_data_clear()
 actors[name]=(rig,objects,poses)
for f in range(1,count+1):
 t=(f-1)/fps;s.frame_set(f)
 for name,(rig,objects,poses) in actors.items():
  for b in rig.pose.bones:
   b.matrix_basis=poses[f-1][b.name];b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None)
  jaw=roundness=wide=0
  if line:
   tr=line['track'];idx=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*fps)));w=tr['weights'];jaw=w['jawOpen'][idx]*.7;roundness=w.get('mouthPucker',[0]*tr['frames'])[idx]*.5;wide=w.get('mouthWide',[0]*tr['frames'])[idx]*.5
  blink=max(0,1-abs((t+(0 if name=='lion' else .9))%3.8-1.6)/.13)
  for o in objects:
   if o.type!='MESH' or not o.data.shape_keys:continue
   for k in o.data.shape_keys.key_blocks:
    if k.name=='JawOpen':k.value=jaw
    elif k.name in ['JawClose','LipSeal']:k.value=1-jaw
    elif k.name.startswith('Blink'):k.value=blink
    elif k.name=='MouthRound':k.value=roundness
    elif k.name=='MouthWide':k.value=wide
    elif k.name=='Smile':k.value=.08
    else:continue
    k.keyframe_insert('value',frame=f)
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;return m
ground=mat('Forest earth',(.055,.075,.045));bark=mat('Bark',(.07,.045,.025));leaf=mat('Pine foliage',(.025,.09,.045));stone=mat('Stone',(.12,.15,.13))
def cube(name,loc,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);return o
cube('Forest floor',(0,3,-.08),(30,30,.15),ground)
random.seed(22)
for i in range(26):
 x=random.uniform(-8,8);y=random.uniform(2,12);h=random.uniform(3,6)
 bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=.12,depth=h,location=(x,y,h/2));bpy.context.object.data.materials.append(bark)
 for z,radius in [(h*.55,1.1),(h*.75,.85),(h*.92,.5)]:
  bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=radius,depth=1.8,location=(x,y,z));bpy.context.object.data.materials.append(leaf)
for i in range(16):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.1,.3),location=(random.uniform(-5,5),random.uniform(.8,6),.06));bpy.context.object.scale.z=.5;bpy.context.object.data.materials.append(stone)
metal=mat('Lantern bronze',(.18,.1,.025));glow=mat('Lantern light',(1,.5,.08));glow.use_nodes=True;bs=glow.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.32,.035,1);bs.inputs['Emission Strength'].default_value=4
cube('Lantern pedestal',(0,.35,.23),(.45,.4,.46),stone)
cube('Lantern base',(0,.35,.49),(.23,.22,.035),metal);cube('Lantern flame',(0,.35,.62),(.1,.1,.2),glow);cube('Lantern roof',(0,.35,.76),(.26,.25,.045),metal)
for x in [-.1,.1]:
 for y in [.25,.45]:cube('Lantern frame',(x,y,.62),(.02,.02,.25),metal)
def light(name,kind,loc,energy,color,size=3):
 d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=color
 if kind=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();return o
light('Soft moon key','AREA',(-3,-4,5),450,(.65,.78,1),5);light('Warm fill','AREA',(3,-2,3),220,(1,.72,.4),4);light('Moon rim','AREA',(0,4,5),650,(.45,.65,1),4);light('Lantern pool','POINT',(0,.35,.7),35,(1,.35,.06))
s.world.color=(.025,.035,.055)
shots=[(1,(3,-7,3),(0,.5,1),45,'Establishing forest'),(round(plan['lines'][0]['start']*fps)+1,(2.8,-4,2),(.65,0,1.1),52,'Amber asks'),(round(plan['lines'][1]['start']*fps)+1,(-2.7,-4,2),(-.7,0,1.25),52,'Leo finds light'),(round(plan['lines'][2]['start']*fps)+1,(2.5,-3.8,1.9),(.7,0,1.05),55,'Amber doubts'),(round(plan['lines'][3]['start']*fps)+1,(0,-5.8,2.35),(0,0,.95),48,'Together long shot')]
for f,pos,target,lens,name in shots:
 d=bpy.data.cameras.new(name);d.lens=lens;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();marker=s.timeline_markers.new(name,frame=f);marker.camera=o
s.camera=s.timeline_markers[0].camera;s.frame_start=1;s.frame_end=count;s.render.fps=fps;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.use_sequencer=False;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'the-last-light.blend'))
(H/'render.json').write_text(json.dumps({'frames':count,'fps':fps,'shots':[{'frame':a,'name':e} for a,b,c,d,e in shots],'limitations':['Existing prototype facial rigs','Body clips loop; no new walking or object contacts','Procedural Blender environment, not Unreal final render']},indent=2))
D=H/'frames';D.mkdir(exist_ok=True)
for f in range(1,count+1):
 s.frame_set(f);s.render.filepath=str(D/f'{f-1:05d}.png');bpy.ops.render.render(write_still=True)
print('STORY_RENDER_COMPLETE')
