"""Run with Blender --background --disable-autoexec --python this_file.
Loads assets internally; only small capability/production reports are emitted.
"""
import bpy,json,math,random,sys,wave
from pathlib import Path
from mathutils import Vector,Matrix,Euler
HERE=Path(__file__).parent.resolve();ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.verification/character-evaluation'))
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from movie_production.characters import RigController,load_profile,speech_commands
from rig_preview_helpers import studio
from facerig import visemes

plan=json.loads((HERE/'movie.json').read_text());evaluation=ROOT/'.verification/character-evaluation'
bpy.ops.wm.open_mainfile(filepath=str(evaluation/'snow-v4/Snow/snow_v4.2.blend'),load_ui=False,use_scripts=False)
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
snow=bpy.data.objects['RIG-Snow'];studio(snow,['Eye.L','Eye.R'],'Head','snow')
for obj in list(bpy.data.objects):
    if obj.type=='MESH' and obj.hide_render:bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(str(evaluation/'jacob-v1/Jacob/Jacob.blend'),link=False) as (source,target):
    target.objects=[name for name in source.objects if name=='Armature' or (name.startswith('Jacob') and not any(word in name.lower() for word in ('claymore','outline','christmas')))]
for obj in target.objects:
    if obj and obj.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(obj)
jacob=bpy.data.objects['Armature']
if jacob.animation_data:
    jacob.animation_data.action=None
    for track in jacob.animation_data.nla_tracks:track.mute=True
for bone in jacob.pose.bones:bone.matrix_basis=Matrix.Identity(4)
rigs={'snow':snow,'jacob':jacob};reports={}
for name,rig in rigs.items():
    rig.hide_set(False);rig.hide_render=False
    # Exclusion is explicit rather than trusting animated hide flags.
    for obj in list(bpy.data.objects):
        if obj.type=='MESH' and any(word in obj.name.lower() for word in ('claymore','christmashat','jacoboutline')):bpy.data.objects.remove(obj,do_unlink=True)
    meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers)]
    for obj in meshes:obj.hide_render=False;obj.hide_set(False)
    bpy.context.view_layer.update()
    points=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
    height=max(p.z for p in points)-min(p.z for p in points)
    rig.scale*=1.86/height;rig.location.x=-.72 if name=='snow' else .72
    bpy.context.view_layer.update()
    reports[name]={'profile':name,'skinned_meshes':len(meshes),'original_saved':False}

controllers={name:RigController(rig,load_profile(ROOT/'movie_production/profiles'/f'{name}.json'),1.86) for name,rig in rigs.items()}
bpy.context.view_layer.update()
# Calibrate Snow's rest arms from control/deform bone transforms, never geometry.
for side in ('L','R'):
    control=snow.pose.bones.get('FK-UpperArm.'+side);probe=snow.pose.bones.get('DEF-Wrist.'+side)
    if not control or not probe:continue
    best=(probe.head.z,None)
    for axis in range(3):
        for sign in (-1,1):
            rotation=[0,0,0];rotation[axis]=sign*1.20;control.rotation_euler=rotation;bpy.context.view_layer.update()
            if probe.head.z<best[0]:best=(probe.head.z,rotation)
    control.rotation_euler=best[1] or (0,0,0);bpy.context.view_layer.update()
    reports['snow'].setdefault('rest_arm_controls',[]).append({'bone':control.name,'rotation_radians':list(control.rotation_euler)})

scene=bpy.context.scene;scene.render.fps=24;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=384
audio_lines={name:[] for name in rigs}
for shot in plan['shots']:
    path=HERE/'audio'/f"line_{shot['id']}.wav"
    with wave.open(str(path),'rb') as wav:duration=wav.getnframes()/wav.getframerate()
    assert duration+.65<shot['duration'], 'Dialogue exceeds shot'
    audio_lines[shot['speaker']].append({'speaker':shot['speaker'],'text':shot['text'],'audio':str(path),'start':shot['start']+.35,'end':shot['start']+.5+duration,'manner':'talk','tone':'warm'})
for name,controller in controllers.items():
    vis,amp=visemes(audio_lines[name],384,24)
    for frame in range(1,385):
        t=(frame-1)/24;commands=speech_commands(vis,amp,frame-1)
        commands.update(blink=max(max(0,1-abs(t-centre)/.10) for centre in ([1.5,5.75,9.25,14.75] if name=='snow' else [2.25,6.5,10.75,15.25])),
                        smile=.4+.15*math.sin(t*.65),brow=.25+.18*math.sin(t*.9),gaze=.25*math.sin(t*.55),
                        head_yaw=.5*math.sin(t*.65+(0 if name=='snow' else 1)),head_nod=.4*math.sin(t*1.7)*max(.3,commands['jaw']))
        controller.key(frame,commands)
    reports[name]['capabilities']=controller.capabilities
    reports[name]['speech_active_frames']=sum(value>.03 for value in amp)

def material(name,color,roughness=.8,emission=0):
    result=bpy.data.materials.new(name);result.use_nodes=True;bsdf=result.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=roughness
    if emission:bsdf.inputs['Emission Color'].default_value=(*color,1);bsdf.inputs['Emission Strength'].default_value=emission
    return result
ground_mat=material('Lantern Moss',(.025,.075,.045));bark=material('Lantern Bark',(.08,.045,.025));leaf=material('Lantern Canopy',(.018,.085,.04));rock=material('Lantern Stone',(.11,.15,.13));gold=material('Lantern Glow',(1,.40,.07),emission=5)
def primitive(kind,name,location,scale,mat):
    if kind=='cone':bpy.ops.mesh.primitive_cone_add(vertices=9,radius1=1,radius2=.12,depth=2,location=location)
    elif kind=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=1,depth=2,location=location)
    elif kind=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=location)
    else:bpy.ops.mesh.primitive_cube_add(size=2,location=location)
    obj=bpy.context.object;obj.name=name;obj.scale=scale;obj.data.materials.append(mat);return obj
primitive('cube','Crossing Ground',(0,0,-.1),(20,20,.1),ground_mat)
random.seed(24)
for index in range(42):
    x=random.uniform(-11,11);y=random.uniform(2,14);h=random.uniform(3,6)
    primitive('cylinder',f'Forest Trunk {index}',(x,y,h/2),(.12,.12,h/2),bark)
    primitive('cone',f'Forest Canopy {index}',(x,y,h),(.9,.9,1.7),leaf)
for index in range(13):
    x=random.uniform(-5,5);y=random.uniform(1,8)
    primitive('sphere',f'Crossing Stone {index}',(x,y,.12),(.3,.22,.15),rock)
primitive('cylinder','Lantern Post',(0,1,1.15),(.035,.035,1.15),bark)
primitive('sphere','Last Lantern',(0,1,2.35),(.13,.13,.19),gold)
world=bpy.data.worlds.new('Lantern Evening');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.12,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
for obj in scene.objects:
    if obj.type=='LIGHT':obj.hide_render=True
def light(name,location,energy,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location;obj.rotation_euler=(Vector((0,0,1.4))-obj.location).to_track_quat('-Z','Y').to_euler()
light('Lantern Soft Key',(-3,-4,5),650,(.75,.85,1),5)
light('Lantern Warm Fill',(3,-2,3),450,(1,.65,.35),4)
light('Lantern Rim',(0,3,5),950,(.4,.65,1),4)
data=bpy.data.lights.new('Lantern Practical','POINT');data.energy=45;data.color=(1,.35,.08);data.shadow_soft_size=.3
obj=bpy.data.objects.new('Lantern Practical',data);scene.collection.objects.link(obj);obj.location=(0,1,2.35)

for obj in scene.objects:
    if obj.type=='CAMERA':obj.hide_render=True
cameras={}
for shot in plan['shots']:
    data=bpy.data.cameras.new(f"Shot {shot['id']}");obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);data.lens=58;data.sensor_width=36
    if shot['camera']=='two_shot':position=Vector((0,-6.4,1.8));target=Vector((0,0,1.14));data.lens=52
    else:
        x=-.72 if shot['speaker']=='snow' else .72;position=Vector((x,-3.0,1.75));target=Vector((x,0,1.50));data.lens=70
    for frame,factor in [(shot['start']*24+1,1),(int((shot['start']+4)*24),.95)]:
        obj.location=target+(position-target)*factor;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
        obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_euler',frame=frame)
    marker=scene.timeline_markers.new(f"Cut {shot['id']}",frame=shot['start']*24+1);marker.camera=obj;cameras[shot['id']]=obj
scene.camera=cameras[1]
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
if hasattr(scene.render.image_settings,'media_type'):scene.render.image_settings.media_type='IMAGE'
scene.render.use_motion_blur=False;scene.view_settings.view_transform='AgX'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'the-last-lantern.blend'))
(HERE/'production-report.json').write_text(json.dumps(reports,indent=2))
frames_dir=HERE/'frames';frames_dir.mkdir(exist_ok=True)
if '--stills' in sys.argv:
    for frame in (37,133,229,325):
        scene.frame_set(frame);scene.render.filepath=str(HERE/f'preview-{frame}.png');bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath=str(frames_dir/'frame_');bpy.ops.render.render(animation=True)
print('SAMPLE_COMPLETE',json.dumps(reports),flush=True)
