"""Create a real 3D scale comparison with existing characters and centimetre geometry."""
import unreal,json,time,sys,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from scale_policy import POLICY,pack_conversion,grounded_location,building_height
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 name='ScaleCheck_'+time.strftime('%Y%m%d_%H%M%S');folder='/Game/EnvironmentAssets/ScaleChecks/'+name
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
 def material(label,color):
  mat=tools.create_asset(label,folder,unreal.Material,unreal.MaterialFactoryNew())
  c=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(*color,1)
  mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR);mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);return mat
 mats={'ground':material('Ground',[.12,.14,.16]),'frame':material('Frame',[.25,.15,.07]),
       'ruler':material('Ruler',[.6,.03,.025]),'white':material('White',[.7,.7,.7]),'building':material('Building',[.15,.24,.3])}
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
 def box(label,loc,size,mat):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label)
  a.static_mesh_component.set_static_mesh(cube);a.static_mesh_component.set_material(0,mats[mat]);a.set_actor_scale3d(unreal.Vector(*[v/100 for v in size]));return a
 box('Ground',(0,0,-15),(30000,30000,30),'ground')
 metrics=[]
 data=json.loads((H/'physics_lab/import.json').read_text())
 for entry,x in zip(data['characters'],[-200,-20]):
  part=max(entry['parts'],key=lambda p:p['extent'][2]);target=POLICY['characters_cm'][entry['name']];factor=target/(part['extent'][2]*2)
  offset=grounded_location(part['origin'],part['extent'],factor)
  actor=actors.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(x+offset[0],offset[1],offset[2]));actor.set_actor_label(entry['name']+'_'+str(target)+'cm')
  actor.set_actor_scale3d(unreal.Vector(factor,factor,factor));comp=actor.skeletal_mesh_component
  actor.set_actor_rotation(unreal.Rotator(yaw=180),False)
  comp.set_skeletal_mesh_asset(unreal.load_asset(part['mesh']))
  comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE);comp.override_animation_data(unreal.load_asset(part['animation']),False,False,0,1)
  comp.set_update_animation_in_editor(True)
  metrics.append({'name':entry['name'],'height_cm':target,'uniform_scale':factor})
 arch=POLICY['architecture_cm'];w,h=arch['door_width'],arch['door_height'];x=180
 for px in [x-w/2-5,x+w/2+5]:box('DoorJamb',(px,0,h/2),(10,15,h),'frame')
 box('DoorLintel',(x,0,h+5),(w+20,15,10),'frame')
 for i in range(10):box('Ruler_'+str(i*20),( -360,0,i*20+10),(12,15,20),'ruler' if i%2 else 'white')
 box('DiningTableTop',(390,100,72),(160,90,6),'frame')
 for px in [330,450]:
  for py in [70,130]:box('TableLeg',(px,py,35),(6,6,70),'frame')
 packs=json.loads((H/'assets/unreal-import.json').read_text())['packs'];pack=next(p for p in packs if p['name']=='furniture-kit')
 conversion=pack_conversion(pack);chair=next(m for m in pack['meshes'] if m['path'].split('.')[-1]=='chair')
 mesh=unreal.load_asset(chair['path']);bounds=mesh.get_bounds();factor=conversion['uniform_scale'];off=grounded_location(list(bounds.origin.to_tuple()),list(bounds.box_extent.to_tuple()),factor)
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(540+off[0],off[1],off[2]));a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(unreal.Vector(factor,factor,factor));a.set_actor_label('ReferenceChair_90cmOverall')
 building_h=building_height(3,'residential',90)
 box('ThreeStoreyBuilding',(850,1700,building_h/2),(900,700,building_h),'building')
 for floor in range(3):
  for column in range(4):box('BuildingWindow',(520+column*210,1348,100+floor*300),(120,4,150),'white')
 from unreal_bridge.realworld import scan_library
 lib=scan_library();trees=lib.get('tree',[]);tree=next((e for e in trees if e.get('group')=='broadleaf'),trees[0] if trees else None)
 tree_height=None
 if tree:
  asset=unreal.load_asset(tree['meshes'][0]);bounds=asset.get_imported_bounds() if isinstance(asset,unreal.SkeletalMesh) else asset.get_bounds()
  off=grounded_location(list(bounds.origin.to_tuple()),list(bounds.box_extent.to_tuple()))
  cls=unreal.SkeletalMeshActor if isinstance(asset,unreal.SkeletalMesh) else unreal.StaticMeshActor
  a=actors.spawn_actor_from_class(cls,unreal.Vector(-850+off[0],1600+off[1],off[2]));a.set_actor_label('NativeScaleTree')
  if isinstance(asset,unreal.SkeletalMesh):a.skeletal_mesh_component.set_skeletal_mesh_asset(asset)
  else:a.static_mesh_component.set_static_mesh(asset)
  tree_height=bounds.box_extent.z*2
 from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
 from unreal_bridge.moods import handle_apply_mood
 handle_add_clouds({});handle_add_post_process({});handle_apply_mood({'mood':'blockbuster','weather':False})
 cameras={'character_height':{'location':[80,-650,165],'target':[80,80,115]},
          'wide':{'location':[0,-2800,650],'target':[0,700,650]}}
 shot=cameras['character_height'];loc=unreal.Vector(*shot['location'])
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(loc,unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*shot['target'])),unreal.Name())
 path='/Game/EnvironmentDemos/'+name;assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
 D=H/'demos'/name;D.mkdir(exist_ok=True)
 report={'level':path,'biome':'scale_check','warnings':[],'characters':metrics,'door_opening_cm':[w,h],'ruler_cm':200,'table_top_cm':75,
         'chair_overall_cm':90,'building_height_cm':building_h,'tree_native_height_cm':tree_height,'cameras':cameras,
         'limitations':['Bounds-based normalization does not author seat/handle anchors','Static pose check; runtime foot IK remains pending']}
 (D/'build-result.json').write_text(json.dumps(report,indent=2))
 (H/'demos/latest-scale-check.json').write_text(json.dumps({'id':name,'directory':str(D),'cameras':cameras},indent=2))
except Exception:(H/'demos/scale-error.txt').write_text(traceback.format_exc());raise
