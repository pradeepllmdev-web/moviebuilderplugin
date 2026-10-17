"""Generic full-body demo, recorded/library clip plus speech; geometry remains internal."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from character_workflow_performance import speech_envelope,VERSION
args=json.loads(sys.argv[sys.argv.index('--')+1]);track=json.loads(Path(args['track']).read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=args['glb'])
s=bpy.context.scene;rigs=[o for o in s.objects if o.type=='ARMATURE']
if len(rigs)!=1:raise ValueError('Demo expects one biped skeleton')
rig=rigs[0];mode=args['mode'];stationary=mode in ('standing','scene');want='walk' if mode=='walking' else 'run' if mode in ('running','circle') else 'talk'
choices=[a for a in bpy.data.actions if want in a.name.lower() and not any(x in a.name.lower() for x in ('stop','start','back','jump')) and any(slot.target_id_type=='OBJECT' for slot in a.slots)]
choices.sort(key=lambda a:(a.name.lower()!=want,len(a.name)))
if not stationary and not choices:raise ValueError('No '+want+' animation clip is available; review the rig')
action=choices[0] if choices else None
for o in s.objects:
 if o.animation_data:
  o.animation_data.action=None
  for t in o.animation_data.nla_tracks:t.mute=True
 if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:o.data.shape_keys.animation_data_clear()
if action:
 ad=rig.animation_data_create();ad.action=action
 if action.slots:ad.action_slot=next(slot for slot in action.slots if slot.target_id_type=='OBJECT')
# A native quiet clip supplies an arm-down baseline where possible. Otherwise
# hold the first native talking pose rather than drifting toward a T pose.
idle=next((a for a in bpy.data.actions if any(n in a.name.lower() for n in ('idle','listen')) and any(slot.target_id_type=='OBJECT' for slot in a.slots)),None)
ad=rig.animation_data_create();ad.action=idle or action
if ad.action and ad.action.slots:ad.action_slot=next(slot for slot in ad.action.slots if slot.target_id_type=='OBJECT')
s.frame_set(int(ad.action.frame_range[0]) if ad.action else 1);bpy.context.view_layer.update()
quiet={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
ad.action=action
if action and action.slots:ad.action_slot=next(slot for slot in action.slots if slot.target_id_type=='OBJECT')
envelope=speech_envelope(track['weights']['jawOpen'],track['fps'],args.get('gesture_strength',.18))
keyed=[(o,o.data.shape_keys.key_blocks) for o in s.objects if o.type=='MESH' and o.data.shape_keys]
points=[o.matrix_world@Vector(p) for o,_ in keyed for p in o.bound_box]
if not points:raise ValueError('No facial mesh to render')
low=min(p.z for p in points);high=max(p.z for p in points);height=high-low
center=Vector(((min(p.x for p in points)+max(p.x for p in points))/2,(min(p.y for p in points)+max(p.y for p in points))/2,low))
root=bpy.data.objects.new('Demo path',None);s.collection.objects.link(root);world=rig.matrix_world.copy();rig.parent=root;rig.matrix_world=world
bpy.ops.mesh.primitive_plane_add(size=100,location=(center.x,center.y,low-.01));floor=bpy.context.object
mat=bpy.data.materials.new('Studio floor');mat.diffuse_color=(.16,.2,.23,1);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=mat.diffuse_color;floor.data.materials.append(mat)
if mode=='circle':
 for radius in (1.15,1.85):
  bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.015,major_segments=96,minor_segments=8,location=(0,0,low));bpy.context.object.name='Track line'
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.lens=50;s.camera=cam
for loc,power in [((2,-4,5),450),((-3,-2,3),300),((0,3,4),400)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.size=4;light.rotation_euler=(center+Vector((0,0,height*.6))-light.location).to_track_quat('-Z','Y').to_euler()
s.world=bpy.data.worlds.new('Demo world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.25,.3,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.4
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=args.get('size',512);s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
D=Path(args['frames_dir']);D.mkdir(parents=True,exist_ok=True);duration=track['frames']/track['fps'];front=-1 if args.get('front',1)>0 else 1
if mode=='scene':
 s.render.resolution_x=768;s.render.resolution_y=432
 def material(name,color):
  m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);return m
 bark=material('Tree bark',(.07,.04,.02));foliage=material('Forest canopy',(.035,.12,.06))
 import random
 random.seed(18)
 for i in range(16):
  x=center.x+random.uniform(-4,4)*height;y=center.y-front*random.uniform(1.2,5)*height
  bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=height*.07,depth=height*2.4,location=(x,y,low+height*1.2));bpy.context.object.data.materials.append(bark)
  bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=height*.65,depth=height*1.5,location=(x,y,low+height*2));bpy.context.object.data.materials.append(foliage)
 # A warm path light gives the sample a distinct scene context.
 lamp=center+Vector((height*.6,front*height*.25,height*.35))
 metal=material('Lantern metal',(.16,.09,.025));glow=material('Lantern glow',(1,.5,.08));bs=glow.node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=(1,.3,.035,1);bs.inputs['Emission Strength'].default_value=4
 def cube(name,loc,scale,mat):
  bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 cube('Path stone',lamp-Vector((0,0,height*.2)),(height*.22,height*.2,height*.3),bark)
 cube('Lantern flame',lamp,(height*.07,height*.07,height*.12),glow)
 for z in (-.075,.075):cube('Lantern cap',lamp+Vector((0,0,height*z)),(height*.15,height*.15,height*.02),metal)
 for x in (-.06,.06):
  for y in (-.06,.06):cube('Lantern corner',lamp+Vector((height*x,height*y,0)),(height*.01,height*.01,height*.15),metal)
 bpy.ops.object.light_add(type='POINT',location=lamp);bpy.context.object.data.energy=height*20;bpy.context.object.data.color=(1,.55,.18)
head=next((b for b in rig.pose.bones if b.name.split(':')[-1].lower()=='head'),None)
head_axis=head.bone.matrix_local.to_quaternion().inverted()@(rig.matrix_world.to_3x3().inverted()@Vector((0,0,1))) if head else None
# Bake the actual demo, including facial controls and quiet pauses, into a
# separate editable scene. Do not mutate the model's source animation clips.
poses=[]
for i in range(track['frames']):
 if action:
  f0,f1=action.frame_range;s.frame_set(int(f0+i%max(1,int(f1-f0))))
 poses.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
ad.action=None
s.frame_start=1;s.frame_end=track['frames'];s.render.fps=track['fps']
max_step=0.;previous=None
for i in range(track['frames']):
 t=i/track['fps']
 s.frame_set(i+1)
 for b in rig.pose.bones:
  if stationary:
   loc,q,scale=quiet[b.name].decompose();_,target,_=poses[i][b.name].decompose()
   role=b.name.split(':')[-1].lower()
   upper=any(part in role for part in ('spine','chest','neck','head','shoulder','arm','hand'))
   b.matrix_basis=Matrix.LocRotScale(loc,q.slerp(target,envelope[i] if upper else 0),scale)
  else:b.matrix_basis=poses[i][b.name]
  b.rotation_mode='QUATERNION'
 if head and stationary:
  head.rotation_quaternion=head.rotation_quaternion@Quaternion(head_axis,math.radians(3)*math.sin(t*.75))
 for b in rig.pose.bones:
  b.keyframe_insert('rotation_quaternion',frame=i+1);b.keyframe_insert('location',frame=i+1);b.keyframe_insert('scale',frame=i+1)
 for name,values in track['weights'].items():
  for o,keys in keyed:
   if name in keys:keys[name].value=float(values[i]);keys[name].keyframe_insert('value',frame=i+1)
 if mode=='circle':
  theta=2*math.pi*t/duration;root.location=(1.5*math.sin(theta),-1.5*math.cos(theta),0);root.rotation_euler.z=theta+math.pi/2+(math.pi if front>0 else 0)
 elif not stationary:root.location.x=t*(.6 if mode=='walking' else 1.2);root.rotation_euler.z=math.pi/2+(math.pi if front>0 else 0)
 root.keyframe_insert('location',frame=i+1);root.keyframe_insert('rotation_euler',frame=i+1)
 target=center+root.location+Vector((0,0,height*.52));offset=Vector((height*1.3 if not stationary else 0,front*height*(2.1 if stationary else 3.2),height*.25))
 if mode=='scene':
  # Full-body opening and ending, with a closer dialogue view in between.
  close=.23*duration<t<.72*duration
  target=center+Vector((0,0,height*(.78 if close else .52)));offset=Vector((height*.25*math.sin(t*.15),front*height*(1.7 if close else 2.9),height*.12))
 cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=i+1);cam.keyframe_insert('rotation_euler',frame=i+1)
 bpy.context.view_layer.update()
 hands=[rig.matrix_world@b.head for b in rig.pose.bones if b.name.split(':')[-1] in ('LeftHand','RightHand')]
 if previous and len(previous)==len(hands):max_step=max(max_step,max((a-b).length for a,b in zip(hands,previous)))
 previous=hands
 s.render.filepath=str(D/f'{i:05d}.png');bpy.ops.render.render(write_still=True)
 if i in (0,max(0,track['frames']//2),track['frames']-1):
  import shutil
  shutil.copy2(D/f'{i:05d}.png',D.parent/f'review-{i:05d}.png')
bpy.ops.wm.save_as_mainfile(filepath=str(D.parent/'demo.blend'))
if stationary:
 bpy.ops.object.select_all(action='DESELECT')
 for o in [root,rig,*rig.children_recursive]:
  if o.type in ('EMPTY','ARMATURE','MESH'):o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(D.parent/'performance.glb'),export_format='GLB',use_selection=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_force_sampling=True,export_frame_range=True)
print('RESULT '+json.dumps({'frames':track['frames'],'clip':action.name if action else None,'quiet_clip':idle.name if idle else 'held native pose','mode':mode,'performance_version':VERSION,'gesture_strength':args.get('gesture_strength',.18),'max_hand_step':max_step,'foot_contacts_verified':False,'visual_review_required':True}))

