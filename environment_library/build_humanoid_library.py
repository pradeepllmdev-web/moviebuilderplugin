"""Build the humanoid library: one mannequin (Universal Animation Library rig, CC0) with BOTH libraries' animations and a material slot per body region, saved as assets/humanoid/ual_humanoid.blend.

    blender -b --factory-startup --python build_humanoid_library.py

Input (downloaded, CC0): assets/ual1_download/extracted (Animation Library [Standard], FBX) and assets/ual2_download/extracted (Universal Animation Library 2 [Standard], GLB). Both use the same 65-bone rig (root, pelvis, spine_01-03, neck_01, Head, clavicle/upperarm/lowerarm/hand, fingers, thigh/calf/foot/ball).
The mannequin's faces are split into material slots by the bone that moves them most: 0 skin (head, neck, hands), 1 shirt (torso above the waist and arms), 2 trousers (pelvis and legs), 3 shoes (feet). Every action is kept with a fake user under a short name (Walk_Loop, Idle_Talking_Loop, ...)."""
import bpy,os,glob,re,json
H=os.path.dirname(os.path.abspath(__file__));A=os.path.join(H,'assets')
u2=glob.glob(os.path.join(A,'ual2_download','extracted','*','Unreal-Godot','UAL2_Standard.glb'))[0]
u1=glob.glob(os.path.join(A,'ual1_download','extracted','*','Unreal Engine','AL_Standard.fbx'))[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=u2)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.data.objects if o.type=='MESH' and o.name=='Mannequin')
for o in list(bpy.data.objects):
 if o not in (arm,mesh):bpy.data.objects.remove(o)
names2={a.name for a in bpy.data.actions}
before=set(a.name for a in bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=u1)
for o in list(bpy.data.objects):
 if o not in (arm,mesh):bpy.data.objects.remove(o)
out={}
for a in list(bpy.data.actions):
 short=re.sub(r'^Rig\|Rig\|','',a.name)
 if short in('A_TPose',) and a.name!='A_TPose' and short in {x.name for x in bpy.data.actions}:bpy.data.actions.remove(a);continue
 if short!=a.name and short in {x.name for x in bpy.data.actions if x is not a}:short='U1_'+short
 a.name=short;a.use_fake_user=True;out[short]=int(a.frame_range[1]-a.frame_range[0])+1
# regions of the mannequin
names={g.index:g.name for g in mesh.vertex_groups};me=mesh.data
def region(v_groups,z):
 if not v_groups:return 0
 g=names[max(v_groups,key=lambda x:x.weight).group].lower()
 if any(k in g for k in('head','neck','hand','index','middle','pinky','ring','thumb')):return 0
 if any(k in g for k in('foot','ball','toe')):return 3
 if any(k in g for k in('thigh','calf')):return 2
 if 'pelvis' in g:return 2 if z<.98 else 1
 return 1
for m in list(me.materials):pass
me.materials.clear()
for nm,col in (('skin',(.9,.7,.55)),('shirt',(.3,.5,.8)),('trousers',(.25,.28,.4)),('shoes',(.2,.12,.08))):
 m=bpy.data.materials.new('H_'+nm);m.diffuse_color=(*col,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 if b:b.inputs['Base Color'].default_value=(*col,1);b.inputs['Roughness'].default_value=.7
 me.materials.append(m)
# clean colour boundaries: cut the mesh on exact planes (wrist, neck, waist, ankle) of the T-pose, then colour each face by where it lies
import bmesh
bm=bmesh.new();bm.from_mesh(me)
for co,no in (((.745,0,0),(1,0,0)),((-.745,0,0),(1,0,0)),((0,0,1.50),(0,0,1)),((0,0,.95),(0,0,1)),((0,0,.10),(0,0,1))):
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=co,plane_no=no)
def region_of(c):
 if abs(c.x)>.745 or (c.z>1.50 and abs(c.x)<.14):return 0      # hands, head and neck
 if c.z<.10:return 3                         # shoes
 if c.z<.95 and abs(c.x)<.5:return 2          # trousers
 return 1                                    # shirt (torso and arms)
for f in bm.faces:f.material_index=region_of(f.calc_center_median());f.smooth=True
bm.to_mesh(me);bm.free()
zs=[v.co.z for v in me.vertices]
mesh.parent=arm
bpy.context.view_layer.update()
rest=dict(height=max(zs)-min(zs),zmin=min(zs),dims=tuple(mesh.dimensions))
bones={b.name:tuple(round(x,3) for x in b.head_local) for b in arm.data.bones if b.name in('root','pelvis','foot_l','ball_l','Head','hand_l','spine_03','neck_01')}
os.makedirs(os.path.join(A,'humanoid'),exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A,'humanoid','ual_humanoid.blend'))
json.dump(dict(actions=out,rest=rest,bones=bones),open(os.path.join(A,'humanoid','ual_humanoid.json'),'w'),indent=1)
print('LIB',len(out),'actions',rest,bones)
