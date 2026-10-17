"""Blender-only character performance; emit no model geometry to logs."""
import bpy,json,math,sys,time
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent;ROOT=H.parent
args=sys.argv[sys.argv.index('--')+1:];key=args[0];test='--test' in args
D=H/'demos/CharacterStories'/key;plan=json.loads((D/'plan.json').read_text());fps=12;frames=round(plan['duration']*fps)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'samples/riverbank-confession/no-shortcuts.blend'),use_scripts=False,load_ui=False)
s=bpy.context.scene;s.frame_set(s.frame_end)
actors={};keep=set()
for name,x in [('lion',-.95),('cat',.95)]:
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE')
 objects=list(root.children_recursive);keep.update([root]+objects)
 held={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones}
 rig.animation_data_clear();root.animation_data_clear();root.location.x=x;root.location.y=0
 meshes=[o for o in objects if o.type=='MESH' and o.data.shape_keys]
 for o in meshes:o.data.shape_keys.animation_data_clear()
 actors[name]=(root,rig,held,meshes)
for o in list(s.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def rotate(rig,bone,axis,angle):
 b=rig.pose.bones.get('mixamorig:'+bone)
 if b:
  local=b.bone.matrix_local.to_quaternion().inverted()@(rig.matrix_world.to_3x3().inverted()@Vector(axis))
  b.rotation_quaternion=b.rotation_quaternion@Quaternion(local.normalized(),math.radians(angle))
# Retarget a genuine running clip for the backwards race, rather than moving a frozen pose.
run_curves={};run_span={}
if plan['action']=='run':
 sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
 from realistic_rig import retarget,normalize_heading,strip_root_drift,bone_curves
 source=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend')
 with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.actions=['clip|Mixamo_Running']
 for name,(root,rig,held,meshes) in actors.items():
  clip=retarget(dst.actions[0],rig,name+' backwards race');normalize_heading(clip,rig)
  strip_root_drift(clip,{b.name:b.matrix_local.to_quaternion() for b in rig.data.bones},24,up=rig.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
  run_curves[name]=bone_curves(clip);run_span[name]=tuple(clip.frame_range);rig.animation_data_clear()
for f in range(1,frames+1):
 t=(f-1)/fps;s.frame_set(f)
 for name,(root,rig,held,meshes) in actors.items():
  sign=1 if name=='lion' else -1;phase=0 if name=='lion' else .8
  for b in rig.pose.bones:
   b.rotation_mode='QUATERNION';b.location=held[b.name][0];b.rotation_quaternion=held[b.name][1]
  line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None)
  active=bool(line);beat=math.sin(t*2+phase);pulse=smooth((t-.3)/.7)*(1-smooth((t-(plan['duration']-1))/.7))
  root.location.x=(-.95 if name=='lion' else .95);root.location.y=0
  # Head orientation responds to the partner, delivery and the chosen action.
  rotate(rig,'Head',(0,0,1),sign*(7+5*math.sin(t*.8+phase)))
  rotate(rig,'Head',(1,0,0),(-12 if plan['action']=='look_up' else 3)+(2 if active else .5)*beat)
  rotate(rig,'Spine2',(1,0,0),.6*math.sin(t*1.7+phase))
  action=plan['action']
  if action=='run':
   f0,f1=run_span[name];at=f0+(t*24*1.2+phase*15)%(f1-f0)
   for b in rig.pose.bones:
    curves=run_curves[name].get(b.name,{})
    if 'rotation_quaternion' in curves:
     q=Quaternion([c.evaluate(at) for c in curves['rotation_quaternion']]).normalized();b.rotation_quaternion=b.rotation_quaternion.slerp(q,.8*pulse)
   root.location.x+=.28*math.sin(t*.65+phase);root.location.y=.2*math.sin(t*.65+phase)
  elif action=='reach':
   rotate(rig,'RightArm',(0,1,0),-sign*38*pulse);rotate(rig,'RightForeArm',(0,0,1),25*pulse)
   rotate(rig,'Spine2',(1,0,0),8*pulse if name=='lion' else 0)
  elif action=='listen':
   rotate(rig,'Head',(0,1,0),sign*12*pulse)
   if name=='lion':rotate(rig,'LeftArm',(0,1,0),35*pulse);rotate(rig,'LeftForeArm',(0,0,1),-45*pulse)
  elif action=='crouch':
   rotate(rig,'Spine2',(1,0,0),14*pulse);rotate(rig,'Head',(1,0,0),12*pulse)
   rotate(rig,'RightArm',(0,1,0),-30*pulse);rotate(rig,'RightForeArm',(0,0,1),25*pulse)
  elif action=='balance':
   rotate(rig,'LeftArm',(0,1,0),28*pulse);rotate(rig,'RightArm',(0,1,0),-28*pulse)
   rotate(rig,'Spine2',(0,1,0),4*math.sin(t*1.5+phase)*pulse)
  elif action=='stir':
   rotate(rig,'RightArm',(0,1,0),-25*pulse);rotate(rig,'RightForeArm',(0,0,1),(32+10*beat)*pulse)
   rotate(rig,'RightHand',(1,0,0),16*math.cos(t*3+phase)*pulse)
  elif action=='look_up':
   if name=='cat':rotate(rig,'LeftArm',(0,1,0),48*pulse);rotate(rig,'LeftForeArm',(1,0,0),20*pulse)
  elif action=='dance':
   rotate(rig,'Spine2',(0,1,0),7*beat*pulse)
   rotate(rig,'LeftArm',(0,1,0),(25+15*beat)*pulse);rotate(rig,'RightArm',(0,1,0),(-25+15*beat)*pulse)
  elif action=='wave':
   rotate(rig,'LeftArm',(0,1,0),65*pulse);rotate(rig,'LeftForeArm',(0,0,1),25*math.sin(t*4+phase)*pulse)
  for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  root.keyframe_insert('location',frame=f)
  jaw=roundness=wide=press=bite=0
  if line:
   track=line['track'];i=min(track['frames']-1,max(0,round((t-line['start']+track['lead'])*24)));w=track['weights']
   jaw=min(.85,w['jawOpen'][i]);roundness=w['mouthPucker'][i];wide=w['mouthWide'][i];press=w['mouthClose'][i];bite=w['lowerLipBite'][i]
  blink=max(0,1-abs((t+phase)%3.1-1.3)/.14)
  for o in meshes:
   for k in o.data.shape_keys.key_blocks:
    value=0
    if k.name=='JawOpen':value=jaw
    elif k.name in ('JawClose','LipSeal'):value=1-jaw
    elif k.name.startswith('Blink'):value=blink
    elif k.name in ('MouthRound','Round'):value=roundness*.6
    elif k.name in ('MouthWide','Wide'):value=wide*.6
    elif k.name=='LipPress':value=press
    elif k.name=='LowerLipBite':value=bite
    elif k.name.startswith('ActingBrow'):value=.12+.15*int(active)
    elif k.name in ('Smile','WarmSmile'):value=.15
    elif k.name=='GazeLeft':value=.3 if name=='cat' else 0
    elif k.name=='GazeRight':value=.3 if name=='lion' else 0
    k.value=value;k.keyframe_insert('value',frame=f)
def area(name,pos,energy,color,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.size=size
 o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
def propmat(name,color,metal=0):
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True
 bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Metallic'].default_value=metal;bsdf.inputs['Roughness'].default_value=.4
 return mat
gold=propmat('Crown gold',(.8,.42,.045),.7);dark=propmat('Prop dark',(.035,.06,.065));red=propmat('Parcel coral',(.65,.12,.055))
if key=='river':
 bpy.ops.mesh.primitive_torus_add(major_radius=.19,minor_radius=.025,location=(0,-.1,.58));prop=bpy.context.object;prop.name='Floating crown';prop.data.materials.append(gold)
 for f in range(1,frames+1):
  t=(f-1)/fps;prop.location.x=.45*math.sin(t*.6);prop.location.z=.58+.04*math.sin(t*2);prop.keyframe_insert('location',frame=f)
elif key=='woodland':
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.09,location=(0,-.7,.07));prop=bpy.context.object;prop.scale=(1,.65,.6);prop.data.materials.append(dark)
 for f in range(1,frames+1):prop.location.x=-.5+(f-1)/max(1,frames-1);prop.keyframe_insert('location',frame=f)
elif key in ('house','industrial'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.22 if key=='house' else .32,depth=.22 if key=='house' else .6,location=(0,-.25,.72 if key=='house' else .3));bpy.context.object.data.materials.append(dark)
 if key=='house':
  for pos,size in [((0,-.25,.59),(.65,.5,.08)),((-.22,-.25,.29),(.06,.4,.58)),((.22,-.25,.29),(.06,.4,.58))]:
   bpy.ops.mesh.primitive_cube_add(size=1,location=pos);bpy.context.object.scale=size;bpy.context.object.data.materials.append(dark)
elif key=='suburban':
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.2,.22));bpy.context.object.scale=(.38,.3,.35);bpy.context.object.data.materials.append(red)
area('Soft key',(-3,-4,5),450,(1,.91,.8),5);area('Fill',(3,-2,3),200,(.75,.85,1),4);area('Rim',(0,3,4),450,(1,.9,.7),3)
data=bpy.data.cameras.new('PrevisCamera');cam=bpy.data.objects.new('PrevisCamera',data);s.collection.objects.link(cam);s.camera=cam
cam.location=(0,-7,2.5);cam.rotation_euler=(Vector((0,0,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=5.5
s.render.engine='BLENDER_EEVEE'
s.render.resolution_x=768;s.render.resolution_y=432;s.render.resolution_percentage=100;s.render.fps=fps
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.frame_start=1;s.frame_end=frames;s.view_settings.exposure=0
if s.world:s.world.color=(.12,.12,.12)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'performance.blend'))
F=D/'alpha-frames';F.mkdir(exist_ok=True)
if test:
 s.frame_set(min(frames,18));s.render.filepath=str(D/'test-alpha.png');bpy.ops.render.render(write_still=True)
else:
 start=time.time()
 for f in range(1,frames+1):
  s.frame_set(f);s.render.filepath=str(F/f'{f-1:05d}.png');bpy.ops.render.render(write_still=True)
 (D/'render-complete.json').write_text(json.dumps(dict(frames=frames,fps=fps,seconds=time.time()-start,action=plan['action'])))
print('STORY_RENDER_COMPLETE '+key,flush=True)
