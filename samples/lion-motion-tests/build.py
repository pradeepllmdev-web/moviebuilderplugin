"""Full-body diagnostic reel using existing recorded motion clips."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
P=Path('C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline');sys.path[:0]=[str(ROOT),str(P)]
from realistic_rig import retarget,bone_curves,strip_root_drift,normalize_heading,stride_speed
from facerig import visemes
from movie_production.characters import speech_commands
plan=json.loads((H/'plan.json').read_text());reports=[]
if '--' in sys.argv:plan=[p for p in plan if p['name']==sys.argv[sys.argv.index('--')+1]]
for spec in plan:
 name=spec['name'];out=H/name;out.mkdir(exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'samples/lion-open-mouth-meshy/talking-blink/lion-talking.blend'),use_scripts=False,load_ui=False)
 s=bpy.context.scene;s.frame_set(1);rig=next(o for o in s.objects if o.type=='ARMATURE')
 rig.animation_data_clear()
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 meshes=[o for o in s.objects if o.type=='MESH' and o.data.shape_keys]
 for o in meshes:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=0
 # Canonical names on this copy only. Explicit group rename preserves all bindings.
 mapping={b.name:'mixamorig:'+{'Spine02':'Spine','Spine01':'Spine1','Spine':'Spine2','neck':'Neck'}.get(b.name,b.name) for b in rig.data.bones}
 for old in mapping:rig.data.bones[old].name='TEMP_'+old
 for old,new in mapping.items():rig.data.bones['TEMP_'+old].name=new
 for o in s.objects:
  if o.type=='MESH':
   for g in o.vertex_groups:
    if g.name in mapping:g.name=mapping[g.name]
 clip='Talking' if name=='standing' else 'Mixamo_Walking' if name=='walking' else 'Mixamo_Running'
 with bpy.data.libraries.load(str(P/'assets/realistic/clips.blend'),link=False) as (src,dst):dst.actions=['clip|'+clip]
 assert dst.actions[0],clip
 action=retarget(dst.actions[0],rig,name+' full body');normalize_heading(action,rig)
 rest=json.loads(action['rest'])
 strip_root_drift(action,{k:Quaternion(q) for k,q in rest.items()},24,up=Vector((0,1,0))) if False else None
 # Retargeted hips drift is removed in target armature coordinates.
 strip_root_drift(action,{b.name:b.matrix_local.to_quaternion() for b in rig.data.bones},24,up=rig.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
 speed=0 if name=='standing' else stride_speed(rig,action)
 if name!='standing' and speed<.1:raise ValueError('No measurable stride speed')
 curves=bone_curves(action);f0,f1=action.frame_range;span=f1-f0
 count=round(spec['duration']*24);s.frame_start=1;s.frame_end=count;s.render.fps=24
 audio=Path(spec['audio']);vis,amp=visemes([{'text':spec['text'],'audio':str(audio),'start':.35,'end':spec['duration']-.3,'tone':'lively','manner':'talk'}],count,24)
 source=bpy.data.objects['char1'];head=rig.pose.bones['mixamorig:Head']
 # Facial accents are intentionally modest and localized to the brows.
 brow=source.shape_key_add(name='BrowLift',from_mix=False);basis=source.data.shape_keys.key_blocks['Basis'];w=source.matrix_world;inv=w.inverted()
 for v,b in zip(brow.data,basis.data):
  p=w@b.co;weight=math.exp(-((abs(p.x)-.085)/.045)**4-((p.z-1.465)/.025)**2) if p.y<-.25 else 0
  v.co=b.co+inv.to_3x3()@Vector((0,0,.006*weight))
 # World-space motion on an empty leaves the imported armature transform intact.
 root=bpy.data.objects.new('Actor path',None);s.collection.objects.link(root);world=rig.matrix_world.copy();rig.parent=root;rig.matrix_world=world
 radius=speed*spec['duration']/(2*math.pi) if name=='circle' else 0
 min_foot=10;foot_tracks={side:[] for side in ['Left','Right']};root_positions=[]
 # Bake motion and face into a new action; source clip is never modified externally.
 for f in range(1,count+1):
  t=(f-1)/24;sample=f0+(t*24)%span;s.frame_set(f)
  for b in rig.pose.bones:
   props=curves.get(b.name,{})
   b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion([c.evaluate(sample) for c in props['rotation_quaternion']]).normalized() if 'rotation_quaternion' in props else Quaternion()
   b.location=Vector([c.evaluate(sample) for c in props['location']]) if 'location' in props else Vector()
  # Mild conversational head attention on top of recorded body motion.
  ax=head.bone.matrix_local.to_quaternion().inverted()@Vector((0,1,0))
  head.rotation_quaternion=head.rotation_quaternion@Quaternion(ax,math.radians(3)*math.sin(t*1.8))
  for b in rig.pose.bones:
   b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  if name=='circle':
   angle=2*math.pi*t/spec['duration'];root.location=(radius*math.sin(angle),-radius*math.cos(angle),0);root.rotation_euler.z=angle+math.pi/2
   # Tangent is (cos(angle),sin(angle)); native forward is -Y.
  elif name!='standing':root.location=(speed*t,0,0);root.rotation_euler.z=math.pi/2
  root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
  command=speech_commands(vis,amp,f-1);jaw=min(.85,command['jaw']*.8)
  blink=max(max(0,1-abs(t-b)/.13) for b in [.8,2.9,5.2])
  for o in meshes:
   for k in o.data.shape_keys.key_blocks:
    if k.name=='JawOpen':k.value=jaw
    elif k.name=='LipSeal':k.value=1-jaw
    elif k.name.startswith('Blink'):k.value=blink
    else:continue
    k.keyframe_insert('value',frame=f)
  brow.value=.25+.25*math.sin(t*2.1);brow.keyframe_insert('value',frame=f)
  bpy.context.view_layer.update()
  for side in foot_tracks:
   p=rig.matrix_world@rig.pose.bones['mixamorig:'+side+'Foot'].head;foot_tracks[side].append(list(p));min_foot=min(min_foot,p.z)
  root_positions.append(list(root.location))
 # Align the lowest ankle to its rest foot clearance, retaining running flight.
 rest_clearance=min((rig.matrix_world@rig.data.bones['mixamorig:'+side+'Foot'].head_local).z for side in foot_tracks)
 vertical=rest_clearance-min_foot
 for f in range(1,count+1):s.frame_set(f);root.location.z+=vertical;root.keyframe_insert('location',frame=f)
 # Floor grid/track makes sliding and circular travel visible.
 gridmat=bpy.data.materials.new('Track markings');gridmat.diffuse_color=(.65,.7,.7,1)
 for y in range(-6,7):
  bpy.ops.mesh.primitive_cube_add(size=1,location=(speed*spec['duration']/2 if name!='circle' else 0,y,.002));line=bpy.context.object;line.scale=(max(12,speed*spec['duration']+4),.012,.003);line.data.materials.append(gridmat)
 if name=='circle':
  for rr in [radius-.45,radius+.45]:
   bpy.ops.mesh.primitive_torus_add(major_radius=rr,minor_radius=.015,major_segments=96,minor_segments=8,location=(0,0,.01));bpy.context.object.data.materials.append(gridmat)
 c=s.camera;c.animation_data_clear();c.data.lens=48
 for f in range(1,count+1):
  s.frame_set(f);target=root.location+Vector((0,0,1.0))
  if name=='standing':offset=Vector((0,-3.2,.2));target.z=1.18
  elif name=='circle':offset=Vector((0,-5,2.3))
  else:offset=Vector((2,-4.2,1.0))
  c.location=target+offset;c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.keyframe_insert('location',frame=f);c.keyframe_insert('rotation_euler',frame=f)
 s.render.resolution_x=512;s.render.resolution_y=512;s.cycles.samples=4;s.render.use_sequencer=False
 s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
 s.frame_set(min(count,60));s.render.filepath=str(out/'preview.png');bpy.ops.render.render(write_still=True)
 report={'name':name,'clip':clip,'frames':count,'fps':24,'speed_mps':speed,'circle_radius_m':radius,'vertical_correction_m':vertical,'audio':str(audio),'text':spec['text'],'duration':count/24,'root_travel_m':speed*(count-1)/24,'limitations':['prototype eyelid overlays','mouth corners need refinement','contact/stride diagnostics require visual review']}
 (out/'application.json').write_text(json.dumps(report,indent=2));reports.append(report)
 print('SECTION_READY',name,speed,flush=True)
(H/'reel.json').write_text(json.dumps(reports,indent=2))

