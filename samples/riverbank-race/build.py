"""Existing characters, separately retargeted running clips, procedural river set."""
import bpy,json,math,random,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
H=Path(__file__).resolve().parent;ROOT=H.parents[1];P=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline');sys.path.insert(0,str(P))
from realistic_rig import retarget,bone_curves,normalize_heading,strip_root_drift,stride_speed
plan=json.loads((H/'plan.json').read_text());fps=24;count=round(plan['duration']*fps)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'samples/lion-open-mouth-meshy/talking-blink/lion-talking.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;s.render.fps=fps
def actor(objects):
 r=next(o for o in objects if o.type=='ARMATURE');return r,[r]+[o for o in objects if o.type=='MESH' and (o in r.children_recursive or any(m.type=='ARMATURE' and m.object==r for m in o.modifiers))]
lion,lo=actor(list(s.objects))
for o in list(s.objects):
 if o not in lo:bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(ROOT/'samples/amber-open-mouth-v2/fresh-talking.blend'),link=False) as (src,dst):dst.objects=src.objects
cat,co=actor([o for o in dst.objects if o])
for o in co:s.collection.objects.link(o)
with bpy.data.libraries.load(str(P/'assets/realistic/clips.blend'),link=False) as (src,dst):dst.actions=['clip|Mixamo_Running','clip|Listen']
running,idle=dst.actions;actors={};reports={}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def sample(curves,b,f):
 p=curves.get(b.name,{})
 q=Quaternion([c.evaluate(f) for c in p['rotation_quaternion']]).normalized() if 'rotation_quaternion' in p else Quaternion()
 loc=Vector([c.evaluate(f) for c in p['location']]) if 'location' in p else Vector()
 return loc,q
for name,r,objects,lane,height,duration in [('lion',lion,lo,.65,1.85,8.3),('cat',cat,co,-.65,1.5,7.7)]:
 r.animation_data_clear()
 for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
 for o in objects:
  if o.type=='MESH' and o.data.shape_keys:
   o.data.shape_keys.animation_data_clear()
   for k in o.data.shape_keys.key_blocks:k.value=1 if k.name in ('JawClose','LipSeal') else 0
 mapping={b.name:'mixamorig:'+{'Spine02':'Spine','Spine01':'Spine1','Spine':'Spine2','neck':'Neck'}.get(b.name,b.name) for b in r.data.bones}
 for old in mapping:r.data.bones[old].name='TEMP_'+old
 for old,new in mapping.items():r.data.bones['TEMP_'+old].name=new
 for o in objects:
  if o.type=='MESH':
   for g in o.vertex_groups:
    if g.name in mapping:g.name=mapping[g.name]
 bpy.context.view_layer.update();pts=[o.matrix_world@Vector(p) for o in objects if o.type=='MESH' for p in o.bound_box];low=min(p.z for p in pts);high=max(p.z for p in pts);cx=(min(p.x for p in pts)+max(p.x for p in pts))/2;cy=(min(p.y for p in pts)+max(p.y for p in pts))/2
 root=bpy.data.objects.new(name+' race path',None);s.collection.objects.link(root)
 for o in objects:
  if o.parent not in objects:w=o.matrix_world.copy();o.parent=root;o.matrix_world=w
 scale=height/(high-low);root.scale=(scale,)*3;origin=Vector((-cx*scale,lane-cy*scale,-low*scale));root.location=origin;bpy.context.view_layer.update()
 run=retarget(running,r,name+' running');normalize_heading(run,r)
 strip_root_drift(run,{b.name:b.matrix_local.to_quaternion() for b in r.data.bones},24,up=r.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
 quiet=retarget(idle,r,name+' quiet ready');normalize_heading(quiet,r)
 native_speed=stride_speed(r,run);assert native_speed>.1,(name,native_speed)
 rc=bone_curves(run);ic=bone_curves(quiet);f0,f1=run.frame_range;span=f1-f0
 r.animation_data_clear();head=r.pose.bones['mixamorig:Head'];axis=head.bone.matrix_local.to_quaternion().inverted()@(r.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
 feet=[]
 for frame in range(1,count+1):
  t=(frame-1)/fps;s.frame_set(frame);p=max(0,min(1,(t-3.8)/duration));distance=16*smooth(p);weight=smooth((t-3.8)/.45)*(1-smooth((t-(3.8+duration-.6))/.6));phase=f0+(distance/native_speed*fps+(0 if name=='lion' else span*.3))%span
  for b in r.pose.bones:
   il,iq=sample(ic,b,quiet.frame_range[0]+6);rl,rq=sample(rc,b,phase);b.rotation_mode='QUATERNION';b.rotation_quaternion=iq.slerp(rq,weight);b.location=il.lerp(rl,weight)
  head.rotation_quaternion=head.rotation_quaternion@Quaternion(axis,math.radians(3)*math.sin(t*1.3+(0 if name=='lion' else 1)))
  for b in r.pose.bones:b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
  root.location=origin+Vector((distance,0,0));root.rotation_euler.z=math.pi/2*smooth((t-3.45)/.5)*(1-smooth((t-(3.8+duration))/.7));root.keyframe_insert('location',frame=frame);root.keyframe_insert('rotation_euler',frame=frame)
  line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None);jaw=roundness=wide=0
  if line:
   tr=line['track'];i=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*fps)));jaw=tr['weights']['jawOpen'][i]*.7;roundness=tr['weights'].get('mouthPucker',[0]*tr['frames'])[i]*.5;wide=tr['weights'].get('mouthWide',[0]*tr['frames'])[i]*.5
  blink=max(0,1-abs((t+(0 if name=='lion' else 1))%3.7-1.7)/.12)
  for o in objects:
   if o.type!='MESH' or not o.data.shape_keys:continue
   for k in o.data.shape_keys.key_blocks:
    if k.name=='JawOpen':k.value=jaw
    elif k.name in ('JawClose','LipSeal'):k.value=1-jaw
    elif k.name.startswith('Blink'):k.value=blink
    elif k.name=='MouthRound':k.value=roundness
    elif k.name=='MouthWide':k.value=wide
    elif k.name=='Smile':k.value=.1
    else:continue
    k.keyframe_insert('value',frame=frame)
  bpy.context.view_layer.update();feet.extend((r.matrix_world@r.pose.bones['mixamorig:'+side+'Foot'].head).z for side in ('Left','Right'))
 correction=height*.045-min(feet)
 for frame in range(1,count+1):s.frame_set(frame);root.location.z+=correction;root.keyframe_insert('location',frame=frame)
 actors[name]=(r,root,height);reports[name]={'native_stride_speed':native_speed,'finish_time':3.8+duration,'travel_m':16,'vertical_correction':correction}
def mat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.8;return m
grass=mat('Spring grass',(.13,.27,.065));sand=mat('Riverbank trail',(.36,.25,.13));wood=mat('Bridge cedar',(.22,.095,.035));bark=mat('Tree bark',(.12,.065,.025));leaves=mat('Willow canopy',(.12,.31,.075));rock=mat('River stones',(.24,.27,.22));white=mat('Finish chalk',(.85,.8,.6));red=mat('Coral flags',(.75,.075,.035))
def cube(name,loc,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);return o
cube('Near riverbank',(8,-5,-.2),(70,14,.4),grass);cube('Far riverbank',(8,15,-.2),(70,14,.4),grass);cube('Sandy race trail',(8,0,.008),(30,2.9,.025),sand)
water=mat('Flowing river',(.035,.24,.32));bs=water.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.22;bs.inputs['Metallic'].default_value=.25
noise=water.node_tree.nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=2
bump=water.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.07;water.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);water.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
noise.inputs['W'].default_value=0;noise.inputs['W'].keyframe_insert('default_value',frame=1);noise.inputs['W'].default_value=3;noise.inputs['W'].keyframe_insert('default_value',frame=count)
cube('River',(8,5,-.075),(80,6,.025),water)
# Bridge is the goal landmark; the race stays safely on the near bank.
for i in range(25):cube('Bridge plank',(17,1.9+i*.25,.16),(2,.23,.16),wood)
for x in (16.05,17.95):
 cube('Bridge handrail',(x,5,1),( .09,6.7,.09),wood)
 for y in (1.9,4,6,8):cube('Bridge post',(x,y,.6),(.13,.13,1.2),wood)
for x in (0,16):cube('Race line',(x,0,.035),(.09,2.8,.014),white)
for y in (-1.5,1.5):
 cube('Finish pole',(16,y,1.2),(.06,.06,2.4),wood);cube('Finish pennant',(16,y+.22,2.18),(.035,.44,.22),red)
random.seed(56)
for i in range(30):
 x=random.uniform(-10,35);y=random.choice([random.uniform(9,17),random.uniform(-16,-12)]);h=random.uniform(3,5.5)
 bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=.13,depth=h,location=(x,y,h/2));bpy.context.object.data.materials.append(bark)
 for z,scale in [(h*.9,(1.3,1.2,1.1)),(h*.7,(1.4,1.4,1.0))]:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z));bpy.context.object.scale=scale;bpy.context.object.data.materials.append(leaves)
for i in range(65):
 x=random.uniform(-10,32);y=random.choice([random.uniform(1.7,2.2),random.uniform(8,8.5)])
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.1,.28),location=(x,y,.03));bpy.context.object.scale=(1.3,1,.6);bpy.context.object.data.materials.append(rock)
for x in range(-3,24,2):
 for y in (-2,1.7):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.045,location=(x+.2,y,.12));bpy.context.object.data.materials.append(red)
def light(name,kind,loc,energy,color,size=5):
 d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=color
 if kind=='AREA':d.size=size
 o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((8,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
light('Afternoon sun','SUN',(-5,-8,12),2.5,(1,.84,.62));light('Sky fill','AREA',(8,-3,6),1600,(.72,.85,1),12)
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.48,.68,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
d=bpy.data.cameras.new('Race camera');d.lens=42;cam=bpy.data.objects.new('Race camera',d);s.collection.objects.link(cam);s.camera=cam
shots=[]
for frame in range(1,count+1):
 t=(frame-1)/fps;s.frame_set(frame);mid=(actors['lion'][1].location+actors['cat'][1].location)/2;mid.z=1
 if t<3.8:pos=Vector((3,-6.5,3));target=Vector((.4,.4,1));label='Starting line'
 elif t<6:pos=mid+Vector((-3.8,-6.8,3.8));target=mid+Vector((1,1,0));label='River tracking wide'
 elif t<10.2:pos=mid+Vector((3.5,-5.8,1.65));target=mid+Vector((.3,.4,.05));label='Side race tracking'
 elif t<13:pos=Vector((20,-7,3.8));target=Vector((14.7,.7,1));label='Bridge finish wide'
 else:pos=Vector((18.8,-6.7,2.8));target=Vector((16,.3,1));label='Finish reaction'
 if not shots or shots[-1]['name']!=label:shots.append({'frame':frame,'name':label})
 cam.location=pos;cam.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_euler',frame=frame)
s.frame_start=1;s.frame_end=count;s.render.fps=fps;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.use_sequencer=False;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=.1
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(H/'riverbank-race.blend'))
(H/'application.json').write_text(json.dumps({'frames':count,'fps':fps,'actors':reports,'shots':shots,'meshy_calls':0,'limitations':['Prototype facial rigs and fur','Foot/toe contact needs visual review','No water interaction simulation']},indent=2))
for f,name in [(24,'start'),(168,'race'),(350,'finish')]:
 s.frame_set(f);s.render.filepath=str(H/(name+'.png'));bpy.ops.render.render(write_still=True)
print('RACE_SCENE_READY '+json.dumps(reports))
