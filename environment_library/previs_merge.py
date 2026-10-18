"""Blender script: merge built actor scenes into one low-poly previs scene (gallery or movie).

blender -b --python previs_merge.py -- spec.json

spec: {out, mode: 'gallery'|'movie', fps, render: bool, width, height,
       shots: [{start, length, label, camera: {pos_cm, target_cm, lens}|null,
                actors: [{folder, position_cm, yaw}]}],
       trees: bool}
Every actor's scene.blend is appended (rig, body, props), parented to a slot empty placed like Unreal places the
actor (yaw 0 faces +Y, so the rig, which faces -Y, turns by yaw+180), its animation shifted to the shot's start frame
and hidden outside the shot. A flat ground, simple trees, a camera per shot (movie, with cuts as bound markers) and a
workbench mp4 render make a quick previs; textures come from the source scenes."""
import bpy,json,math,random,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
spec=json.load(open(sys.argv[sys.argv.index('--')+1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;fps=spec.get('fps',24);scene.render.fps=fps
def link(o):
 if o.name not in scene.collection.objects:scene.collection.objects.link(o)
def curves(action):
 """F-curves of an action on any Blender version (5.x moved them into layered channelbags)."""
 if hasattr(action,'fcurves'):return list(action.fcurves)
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
def shift(action,offset,done):
 if action is None or action.name in done:return
 done.add(action.name)
 for fc in curves(action):
  for kp in fc.keyframe_points:kp.co.x+=offset;kp.handle_left.x+=offset;kp.handle_right.x+=offset
def hide_outside(obj,start,end):
 for prop in ('hide_viewport','hide_render'):
  setattr(obj,prop,True);obj.keyframe_insert(prop,frame=max(0,start-1))
  setattr(obj,prop,False);obj.keyframe_insert(prop,frame=start)
  setattr(obj,prop,True);obj.keyframe_insert(prop,frame=end+1)
 if obj.animation_data and obj.animation_data.action:
  for fc in curves(obj.animation_data.action):
   if fc.data_path in ('hide_viewport','hide_render'):
    for kp in fc.keyframe_points:kp.interpolation='CONSTANT'
def add_actor(actor,start,length,index,slot_offset=(0,0),src_start=1):
 before=set(bpy.data.objects)
 with bpy.data.libraries.load(actor['folder']+'/scene.blend',link=False) as (src,dst):dst.objects=list(src.objects)
 new=[o for o in bpy.data.objects if o not in before]
 for o in list(new):
  # Drop helpers and anything the source scene kept hidden (reference meshes, rig shapes): hiding them again would show them.
  if o.type in ('CAMERA','LIGHT') or o.name.startswith(('Ball hold','Drink hand')) or o.hide_render or (o.type=='MESH' and o.hide_viewport):bpy.data.objects.remove(o);new.remove(o)
 root=bpy.data.objects.new('Slot_%d'%index,None);link(root)
 px,py=actor['position_cm'];root.location=((px+slot_offset[0])/100,(py+slot_offset[1])/100,0);root.rotation_euler=(0,0,math.radians(actor['yaw']+180))
 if spec.get('use_routes'):   # root motion: the build keeps the rig at the origin and writes where it goes per frame
  rows=json.load(open(actor['folder']+'/route.json'));shift_f=start-src_start
  for row in rows[::2]+[rows[-1]]:
   fr=row['frame']+1+shift_f
   if fr<start-1 or fr>start+length:continue
   root.location=((px+slot_offset[0]+row['location_cm'][0])/100,(py+slot_offset[1]+row['location_cm'][1])/100,row['location_cm'][2]/100);root.rotation_euler=(0,0,math.radians(row['yaw']+180))
   root.keyframe_insert('location',frame=fr);root.keyframe_insert('rotation_euler',frame=fr)
  for fc in curves(root.animation_data.action):
   for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 done=set()
 for o in new:
  link(o)
  if o.parent is None:o.parent=root
  if o.type=='EMPTY' and not o.children:o.hide_viewport=True
  shift(o.animation_data.action if o.animation_data else None,start-src_start,done)
  if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:shift(o.data.shape_keys.animation_data.action,start-src_start,done)
  if o.animation_data:
   for track in o.animation_data.nla_tracks:o.animation_data.nla_tracks.remove(track)
  hide_outside(o,start,start+length-1)
 return new
def low_poly_world(extent_m,trees):
 bpy.ops.mesh.primitive_plane_add(size=extent_m*2);ground=bpy.context.object;ground.name='Ground'
 m=bpy.data.materials.new('Ground');m.diffuse_color=(.22,.38,.16,1);ground.data.materials.append(m)
 if trees:
  rnd=random.Random(7);trunk=bpy.data.materials.new('Trunk');trunk.diffuse_color=(.3,.18,.08,1);leaf=bpy.data.materials.new('Leaf');leaf.diffuse_color=(.1,.3,.12,1)
  for i in range(26):
   a=rnd.uniform(0,6.283);r=rnd.uniform(9,extent_m*.9);x,y=math.cos(a)*r,math.sin(a)*r;h=rnd.uniform(3,6)
   bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.2,depth=h*.4,location=(x,y,h*.2));t=bpy.context.object;t.data.materials.append(trunk)
   bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=1.4,depth=h,location=(x,y,h*.4+h*.5));c=bpy.context.object;c.data.materials.append(leaf)
 scene.world=bpy.data.worlds.new('Sky');scene.world.color=(.55,.72,.9)
 scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
def label(text,x,y,z=2.1):
 bpy.ops.object.text_add(location=(x,y,z),rotation=(math.radians(90),0,math.radians(180)));o=bpy.context.object;o.data.body=text;o.data.size=.16;o.data.align_x='CENTER'
 m=bpy.data.materials.new('Label');m.diffuse_color=(1,1,.2,1);o.data.materials.append(m)
frame_end=1
if spec['mode']=='gallery':
 cols=spec.get('columns',8);gap=spec.get('gap_cm',300);index=0
 for k,shot in enumerate(spec['shots']):
  col,row=k%cols,k//cols;ox,oy=(col-(cols-1)/2)*gap,-row*gap
  for actor in shot['actors']:
   add_actor(actor,1,shot['length'],index,(ox,oy));index+=1
  label(shot['label'],ox/100,oy/100+.0)
  frame_end=max(frame_end,shot['length'])
 low_poly_world(max(14,cols*gap/200+3),False)
else:
 cams=[];index=0
 for k,shot in enumerate(spec['shots']):
  for actor in shot['actors']:
   add_actor(actor,shot['start'],shot['length'],index,(0,0),shot.get('src_start',1));index+=1
  frame_end=max(frame_end,shot['start']+shot['length']-1)
  if spec.get('captions'):
   px,py=shot['actors'][0]['position_cm'];bpy.ops.object.text_add(location=(px/100,py/100,2.3),rotation=(math.radians(90),0,math.radians(180)+math.atan2(-220,420)*-1));cap=bpy.context.object;cap.data.body=shot.get('label','');cap.data.size=.22;cap.data.align_x='CENTER';mm=bpy.data.materials.new('Cap');mm.diffuse_color=(1,1,.2,1);cap.data.materials.append(mm);hide_outside(cap,shot['start'],shot['start']+shot['length']-1)
  c=shot.get('camera') if not spec.get('camera') else None
  if spec.get('camera'):marker=scene.timeline_markers.new(shot.get('label','shot%d'%k),frame=shot['start'])
  if c:
   data=bpy.data.cameras.new('Cam%d'%k);data.lens=c['lens'];cam=bpy.data.objects.new('Cam%d'%k,data);link(cam);cam.location=[v/100 for v in c['pos_cm']]
   aim=bpy.data.objects.new('Aim%d'%k,None);link(aim);aim.location=[v/100 for v in c['target_cm']];aim.hide_viewport=True
   con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
   if c.get('to_pos_cm'):   # camera move: linear dolly over the shot
    end=shot['start']+shot['length']-1;cam.keyframe_insert('location',frame=shot['start']);cam.location=[v/100 for v in c['to_pos_cm']];cam.keyframe_insert('location',frame=end)
    aim.keyframe_insert('location',frame=shot['start']);aim.location=[v/100 for v in c.get('to_target_cm',c['target_cm'])];aim.keyframe_insert('location',frame=end)
    for obj in (cam,aim):
     for fc in curves(obj.animation_data.action):
      for kp in fc.keyframe_points:kp.interpolation='LINEAR'
   marker=scene.timeline_markers.new(shot.get('label','shot%d'%k),frame=shot['start']);marker.camera=cam;cams.append(cam)
   for line in shot.get('lines',[]):   # dialogue: subtitle under the camera + audio strip
    f1=shot['start']+round(line['start_s']*fps);f2=shot['start']+round(line['end_s']*fps)
    bpy.ops.object.text_add(location=(0,-.36,-1.5),rotation=(0,0,0));sub_=bpy.context.object;sub_.data.body=line['speaker']+': '+line['text'];sub_.data.size=.075;sub_.data.align_x='CENTER';sub_.parent=cam
    sub_.data.materials.append(bpy.data.materials.new('Sub'));sub_.data.materials[0].diffuse_color=(1,1,.85,1);hide_outside(sub_,f1,f2)
    if line.get('audio'):
     se=scene.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
     strips.new_sound('line%d_%d'%(k,f1),line['audio'],1+(index%3),f1)
 if cams:scene.camera=cams[0]
 if spec.get('camera'):
  c=spec['camera'];data=bpy.data.cameras.new('ReelCam');data.lens=c['lens'];cam=bpy.data.objects.new('ReelCam',data);link(cam);cam.location=[v/100 for v in c['pos_cm']]
  aim=bpy.data.objects.new('ReelAim',None);link(aim);aim.location=[v/100 for v in c['target_cm']];aim.hide_viewport=True
  con=cam.constraints.new('TRACK_TO');con.target=aim;con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y';scene.camera=cam
 if spec.get('sets'):
  import previs_sets;previs_sets.build(scene,spec['sets'],spec.get('props',[]))
 else:low_poly_world(24,spec.get('trees',True))
scene.frame_start=1;scene.frame_end=frame_end;scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=spec['out']+'.blend')
if spec.get('render') and spec['mode']=='movie':
 r=scene.render;r.engine='BLENDER_WORKBENCH';r.resolution_x=spec.get('width',640);r.resolution_y=spec.get('height',360);r.resolution_percentage=100
 r.image_settings.media_type='VIDEO' if hasattr(r.image_settings,'media_type') else None;r.image_settings.file_format='FFMPEG';r.ffmpeg.format='MPEG4';r.ffmpeg.codec='H264';r.ffmpeg.constant_rate_factor='MEDIUM';r.filepath=spec['out']+'.mp4';r.ffmpeg.audio_codec='AAC';r.ffmpeg.audio_bitrate=128
 scene.display.shading.color_type='TEXTURE';scene.display.shading.show_object_outline=False
 bpy.ops.render.render(animation=True)
print('PREVIS_DONE',frame_end,spec['out'])
