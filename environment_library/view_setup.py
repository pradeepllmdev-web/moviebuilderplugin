"""Blender GUI startup for quick_review --open: frame the lion, hide helper clutter, add bench/table proxies, play.
blender scene.blend --python view_setup.py -- <folder>"""
import bpy,json,os,sys
args=sys.argv[sys.argv.index('--')+1:];D=args[0];MODE=args[1] if len(args)>1 else 'single'
def proxies():
 s=bpy.context.scene
 def box(name,size,location,color):
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.scale=size;o.location=location
  m=bpy.data.materials.new(name);m.diffuse_color=color;o.data.materials.append(m)
 if os.path.exists(D+'/seat.json') and os.path.exists(D+'/route.json'):
  seat=json.load(open(D+'/seat.json'));route=json.load(open(D+'/route.json'));at=route[seat['frame']]['location_cm']
  box('Proxy_bench',(.7,.32,seat['top_cm']/100),(seat['lateral_cm']/100,-(seat['forward_cm']-3)/100,seat['top_cm']/200),(.35,.22,.1,1))
 if os.path.exists(D+'/drink.json'):
  d=json.load(open(D+'/drink.json'));tb=d['table'];top=tb['top_cm']/100;th=tb['thickness_cm']/100
  box('Proxy_table',(tb['size_cm'][0]/100,tb['size_cm'][1]/100,th),(tb['center'][0]/100,tb['center'][1]/100,top-th/2),(.5,.3,.15,1))
  c=d['cup'];bpy.ops.mesh.primitive_cylinder_add(radius=c['radius_cm']/100,depth=c['height_cm']/100,location=[v/100 for v in d['cup_cm']]);bpy.context.object.name='Proxy_cup'
def captions():
 """movie mode: burned-in subtitles (speaker and line), the scene goal at the top and the character names, following whichever camera is active, so a scene can be understood with the sound off"""
 import math
 blend=bpy.data.filepath;pj=blend+'.plan.json';sj=blend.replace('.blend','.spec.json')
 if not os.path.exists(pj):return
 plan=json.load(open(pj));spec=json.load(open(sj)) if os.path.exists(sj) else {};cj=os.path.join(D,'cast.json');names={}
 if os.path.exists(cj):
  ch=json.load(open(cj))['characters'];recs=ch.values() if isinstance(ch,dict) else ch
  names={r.get('id'):(r.get('name') or r.get('id')) for r in recs}
 s=bpy.context.scene
 def mk(name,color,size):
  cu=bpy.data.curves.new(name,'FONT');cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';o=bpy.data.objects.new(name,cu);s.collection.objects.link(o)
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);o.data.materials.append(m);return o
 sh=mk('CapShadow',(0,0,0),.036);cap=mk('Caption',(1,1,1),.036);goal=mk('Goal',(1,.85,.2),.03);goal.data.align_x='LEFT'
 goal.data.body=spec.get('objective') or spec.get('title') or ''
 lines=plan['lines']
 def wrap(t):
  if len(t)<=46:return t
  mid=len(t)//2;i=min((k for k,ch_ in enumerate(t) if ch_==' '),key=lambda k:abs(k-mid),default=mid);return t[:i]+chr(10)+t[i+1:]
 def update(scn,*a):
  cam=scn.camera
  if cam is None:return
  t=(scn.frame_current-scn.frame_start)/scn.render.fps;txt=''
  for L in lines:
   if L['t0']-.1<=t<=L['t1']+.5:txt='%s: %s'%(names.get(L['speaker'],L['speaker']).upper(),L['text'])
  k=36./max(10.,cam.data.lens)/.9
  for o in (sh,cap,goal):
   if o.parent is not cam:o.parent=cam;o.matrix_parent_inverse=type(o.matrix_world)()
   o.scale=(k,k,k)
  cap.data.body=sh.data.body=wrap(txt);cap.location=(0,-.205*k,-1);sh.location=(.0016*k,-.2066*k,-1.001);goal.location=(-.41*k,.22*k,-1);cap.hide_viewport=sh.hide_viewport=(txt=='')
 bpy.app.handlers.frame_change_post.append(update);update(s)
def setup():
 s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
 for o in s.objects:
  if o.type=='EMPTY' or o.type=='LIGHT' or (o.type=='CAMERA' and MODE!='movie'):o.hide_set(True)   # the movie view looks through the scene's camera, so it must stay visible
  if MODE=='single' and o.type=='MESH' and o.parent is None and not any(m.type=='ARMATURE' for m in o.modifiers) and not o.name.startswith('Proxy'):o.hide_set(True)
 proxies();s.frame_set(1)
 if MODE=='movie':
  s.sync_mode='AUDIO_SYNC'    # a viewport slower than 24 fps drops frames to stay with the sound, instead of letting lips drift away from the voice
  if os.environ.get('CAPTIONS')=='1':captions()    # subtitles are off unless asked for
 for window in bpy.context.window_manager.windows:
  for area in window.screen.areas:
   if area.type=='VIEW_3D':
    space=area.spaces[0];space.overlay.show_relationship_lines=False;space.overlay.show_bones=False;space.shading.type='SOLID';space.shading.color_type='TEXTURE';space.clip_end=300;space.overlay.show_floor=True
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=window,area=area,region=region,scene=s):
     bpy.ops.object.select_all(action='DESELECT')
     for o in s.objects:
      if o.type=='MESH' and not o.hide_get() and o.name!='Ground' and MODE=='single':o.select_set(True)
     if MODE=='movie':
      space.region_3d.view_perspective='CAMERA';space.overlay.show_floor=False;space.overlay.show_extras=False;space.overlay.show_cursor=False
     else:
      bpy.ops.view3d.view_axis(type='BACK' if MODE=='gallery' else 'RIGHT')
      if MODE=='gallery':
       for o in s.objects:o.select_set(o.type=='ARMATURE')
      bpy.ops.view3d.view_selected(use_all_regions=False)
     bpy.ops.object.select_all(action='DESELECT')
  bpy.ops.screen.animation_play()
 return None
bpy.app.timers.register(setup,first_interval=1.5)
