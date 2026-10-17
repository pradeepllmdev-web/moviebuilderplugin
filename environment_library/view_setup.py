"""Blender GUI startup for quick_review --open: frame the lion, hide helper clutter, add bench/table proxies, play.
blender scene.blend --python view_setup.py -- <folder>"""
import bpy,json,os,sys
D=sys.argv[sys.argv.index('--')+1]
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
def setup():
 s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
 for o in s.objects:
  if o.type=='EMPTY' or o.type=='CAMERA' or o.type=='LIGHT':o.hide_set(True)
  if o.type=='MESH' and o.parent is None and not any(m.type=='ARMATURE' for m in o.modifiers) and not o.name.startswith('Proxy'):o.hide_set(True)
 proxies();s.frame_set(1)
 for window in bpy.context.window_manager.windows:
  for area in window.screen.areas:
   if area.type=='VIEW_3D':
    space=area.spaces[0];space.overlay.show_relationship_lines=False;space.overlay.show_bones=False;space.shading.type='SOLID';space.shading.color_type='TEXTURE';space.clip_end=100;space.overlay.show_floor=True
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=window,area=area,region=region,scene=s):
     bpy.ops.object.select_all(action='DESELECT')
     for o in s.objects:
      if o.type=='MESH' and not o.hide_get():o.select_set(True)
     bpy.ops.view3d.view_axis(type='RIGHT');bpy.ops.view3d.view_selected(use_all_regions=False)
     bpy.ops.object.select_all(action='DESELECT')
  bpy.ops.screen.animation_play()
 return None
bpy.app.timers.register(setup,first_interval=1.5)
