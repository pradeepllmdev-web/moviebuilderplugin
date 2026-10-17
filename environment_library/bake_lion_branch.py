"""Bake a branch to evaluated hand contact, retaining an editable Sequencer track."""
import unreal,json,math,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-branch';record=json.loads((D/'native.json').read_text())
lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();sequence=unreal.load_asset(record['sequence'])
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lion=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Performance_Leo')
comp=lion.get_component_by_class(unreal.SkeletalMeshComponent)
names=[comp.get_bone_name(i) for i in range(comp.get_num_bones())]
left=next(n for n in names if str(n).lower().endswith('lefthand'));right=next(n for n in names if str(n).lower().endswith('righthand'))
rows=[];state={'frame':0,'wait':0};token=None;lib.set_current_time(0)
def finish():
 pickup=min(range(100,205),key=lambda i:min(rows[i]['left'][2],rows[i]['right'][2]))
 release=min(range(350,408),key=lambda i:min(rows[i]['left'][2],rows[i]['right'][2]))
 grip='left' if rows[pickup]['left'][2]<rows[pickup]['right'][2] else 'right'
 for frame,row in enumerate(rows):
  blend=1. if 216<=frame<336 else 0.
  row['mid']=[a*(1-blend)+b*blend for a,b in zip(row[grip],row['mid'])]
 for old in actors.get_all_level_actors():
  if old.get_actor_label()=='Story_FallenBranch':actors.destroy_actor(old)
 cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder.Cylinder')
 branch=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0));branch.set_actor_label('Story_FallenBranch')
 component=branch.static_mesh_component;component.set_static_mesh(cylinder);component.set_mobility(unreal.ComponentMobility.MOVABLE)
 folder=record['level'].rsplit('/',1)[0]
 material=unreal.load_asset(folder+'/BranchWood') or unreal.AssetToolsHelpers.get_asset_tools().create_asset('BranchWood',folder,unreal.Material,unreal.MaterialFactoryNew())
 color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-200,0)
 color.set_editor_property('constant',unreal.LinearColor(.12,.047,.014,1));unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
 unreal.MaterialEditingLibrary.recompile_material(material);component.set_material(0,material);unreal.EditorAssetLibrary.save_loaded_asset(material)
 binding=sequence.add_possessable(branch);section=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();section.set_range(0,480);channels=section.get_all_channels()
 ground_start=unreal.Vector(rows[pickup]['mid'][0],rows[pickup]['mid'][1],8)
 ground_end=unreal.Vector(rows[release]['mid'][0],rows[release]['mid'][1],8)
 previous=None;max_gap=0
 for frame,row in enumerate(rows):
  mid=unreal.Vector(*row['mid']);direction=unreal.Vector(*row['axis']);length=110;direction=unreal.Vector(1,0,0)
  if frame<pickup-6:pos=ground_start;direction=unreal.Vector(1,0,0)
  elif frame<pickup:
   alpha=(frame-(pickup-6))/6;pos=ground_start*(1-alpha)+mid*alpha
  elif frame<=release:pos=mid
  else:
   alpha=min(1,(frame-release)/10);alpha=alpha*alpha*(3-2*alpha)
   pos=unreal.Vector(*rows[release]['mid'])*(1-alpha)+ground_end*alpha
  rot=unreal.MathLibrary.make_rot_from_z(direction);rotation=[rot.roll,rot.pitch,rot.yaw]
  if previous:rotation=[v+360*round((p-v)/360) for v,p in zip(rotation,previous)]
  previous=rotation
  for channel,value in zip(channels,[pos.x,pos.y,pos.z]+rotation+[.11,.11,length/100]):channel.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  if pickup<=frame<=release:max_gap=max(max_gap,(pos-mid).length())
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
 (D/'contact-check.json').write_text(json.dumps({'ok':True,'frames_sampled':len(rows),'pickup_frame':pickup,'release_frame':release,'branch_center_to_hand_midpoint_max_cm':max_gap,'settling':'keyframed; no rigid-body simulation','hand_grip':'single-hand pickup and lowering; two-hand carry; finger grip needs visual review'},indent=2))
 lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(pickup)
def tick(dt):
 global token
 try:
  state['wait']+=1
  if state['wait']<2:return
  state['wait']=0;l=comp.get_socket_location(left);r=comp.get_socket_location(right);mid=(l+r)*.5;axis=r-l
  rows.append(dict(mid=[mid.x,mid.y,mid.z],left=[l.x,l.y,l.z],right=[r.x,r.y,r.z],axis=[axis.x,axis.y,axis.z],span=axis.length()))
  state['frame']+=1
  if state['frame']==480:
   unreal.unregister_slate_post_tick_callback(token);finish();return
  lib.set_current_time(state['frame'])
 except Exception:
  unreal.unregister_slate_post_tick_callback(token);(D/'contact-check.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
token=unreal.register_slate_post_tick_callback(tick)
