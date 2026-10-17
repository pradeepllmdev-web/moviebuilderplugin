"""Author reusable carry/walk/idle/recoil/help clips on the existing rigs."""
import bpy,json,sys,time,math
from pathlib import Path
from mathutils import Vector,Quaternion
H=Path(__file__).resolve().parent;D=H/'delivery_scene';D.mkdir(exist_ok=True)
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from realistic_rig import retarget,normalize_heading,strip_root_drift,stride_speed,bone_curves
from contact import _solve
from footlock import lock_feet
from export_performance import export
source='C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline/assets/realistic/clips.blend'
package=D/('actions_'+time.strftime('%Y%m%d_%H%M%S'));package.mkdir()
entries=[]
states=[('cat_walk','cat','Walking',True),('cat_idle','cat','Idle_3',True),('cat_recoil','cat','Hit_Reaction',False),
        ('lion_idle','lion','Idle_3',False),('lion_walk','lion','Walking',False),('lion_help','lion','Step_Push',False)]
for state,name,clipname,carry in states:
 bpy.ops.wm.open_mainfile(filepath=str(H/'demos/CharacterStories/meadow/performance.blend'),use_scripts=False,load_ui=False)
 s=bpy.context.scene;s.frame_set(1);s.render.fps=24
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE')
 root.animation_data_clear();root.location.x=0;root.location.y=0;root.rotation_euler.z=0
 rig.animation_data_clear()
 with bpy.data.libraries.load(source,link=False) as (src,dst):dst.actions=['clip|'+clipname]
 clip=retarget(dst.actions[0],rig,state);normalize_heading(clip,rig)
 strip_root_drift(clip,{b.name:b.matrix_local.to_quaternion() for b in rig.data.bones},24,up=rig.matrix_world.to_3x3().inverted()@Vector((0,0,1)))
 speed=stride_speed(rig,clip) if clipname=='Walking' else 0
 curves=bone_curves(clip);f0,f1=clip.frame_range;count=max(24,round(f1-f0)+1);s.frame_start=1;s.frame_end=count
 rig.animation_data_clear();meshes=[o for o in rig.children_recursive if o.type=='MESH' and o.data.shape_keys]
 for o in meshes:o.data.shape_keys.animation_data_clear()
 for frame in range(1,count+1):
  s.frame_set(frame);at=f0+(frame-1)
  for b in rig.pose.bones:
   c=curves.get(b.name,{});b.rotation_mode='QUATERNION'
   if 'rotation_quaternion' in c:b.rotation_quaternion=Quaternion([v.evaluate(at) for v in c['rotation_quaternion']]).normalized()
   if 'location' in c:b.location=Vector([v.evaluate(at) for v in c['location']])
  bpy.context.view_layer.update()
  if carry:
   chest=rig.matrix_world@rig.pose.bones['mixamorig:Spine2'].head
   center=chest+Vector((0,-.34,-.17))
   for side,sign in [('Left',-1),('Right',1)]:_solve(rig,side,center+Vector((sign*.18,0,-.04)),1)
  for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
  if speed:
   root.location.y=-speed*(frame-1)/24;root.keyframe_insert('location',frame=frame)
  for o in meshes:
   for key in o.data.shape_keys.key_blocks:
    key.value=1 if key.name in ('JawClose','LipSeal') else 0
    key.keyframe_insert('value',frame=frame)
 # Blender evaluates its active action above NLA. Put the base pose on an NLA
 # strip so the new foot-lock layer is actually evaluated instead of masked.
 if speed:
  base=rig.animation_data.action;rig.animation_data.action=None
  track=rig.animation_data.nla_tracks.new();strip=track.strips.new('Delivery base',1,base)
  if hasattr(strip,'action_slot'):strip.action_slot=base.slots[0]
 feet=lock_feet(rig,1,count,24) if speed else {}
 # The virtual travel is used only to solve foot plants. Unreal supplies actual movement.
 root.animation_data_clear();root.location.y=0
 out=package/state
 export(out,{'actors':[{'name':state}]},catalog={state:{'armature':rig.name}})
 entries.append({'state':state,'character':name,'clip':clipname,'carry_ik':carry,'native_speed_cm_s':speed*100,
                 'frames':count,'fps':24,'directory':str(out),'foot_lock_report':feet})
 print('EXPORTED '+state+'; speed '+str(round(speed*100,1))+' cm/s',flush=True)
(D/'actions.json').write_text(json.dumps({'directory':str(package),'states':entries},indent=2))
