"""Build a continuous interior/exterior house study in the verification project."""
import unreal,json,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 name='ModernHouse_'+time.strftime('%Y%m%d_%H%M%S')
 folder='/Game/EnvironmentAssets/HouseStudies/'+name
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
 def material(name,color,rough=.65):
  mat=tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
  c=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
  c.constant=unreal.LinearColor(*color,1)
  mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
  r=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);r.r=rough
  mel.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
  return mat
 mats={'trim':material('M_Trim',[.025,.03,.035],.35),'cabinet':material('M_Cabinet',[.25,.31,.25]),
       'stone':material('M_Stone',[.15,.16,.16],.42),'fabric':material('M_Fabric',[.65,.57,.43]),
       'white':material('M_White',[.76,.74,.69]),'ground':material('M_Ground',[.14,.16,.11])}
 for source in json.loads((H/'assets/house-materials.json').read_text()):
  mat=tools.create_asset('M_'+source['id'],folder,unreal.Material,unreal.MaterialFactoryNew())
  uv=mel.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate)
  uv.u_tiling=4;uv.v_tiling=3
  for file in source['files']:
   task=unreal.AssetImportTask();task.filename=file['path'];task.destination_path=folder+'/Textures';task.automated=True;task.save=True
   tools.import_asset_tasks([task]);texture=unreal.load_asset(task.imported_object_paths[0])
   role=file['role']
   if role!='diff':texture.set_editor_property('srgb',False)
   if role=='nor_dx':texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
   unreal.EditorAssetLibrary.save_loaded_asset(texture)
   sample=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
   sample.texture=texture
   if role=='nor_dx':sample.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
   elif role=='rough':sample.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
   mel.connect_material_expressions(uv,'',sample,'Coordinates')
   prop={'diff':unreal.MaterialProperty.MP_BASE_COLOR,'rough':unreal.MaterialProperty.MP_ROUGHNESS,'nor_dx':unreal.MaterialProperty.MP_NORMAL}[role]
   mel.connect_material_property(sample,'RGB' if role!='rough' else 'R',prop)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
  mats['wood' if source['id']=='wood_floor_deck' else 'plaster']=mat
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube')
 count=0
 def box(label,loc,size,mat):
  global count
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label)
  a.static_mesh_component.set_static_mesh(cube);a.static_mesh_component.set_material(0,mats[mat])
  a.set_actor_scale3d(unreal.Vector(*[n/100 for n in size]));count+=1
  return a
 box('Ground',(0,0,-35),(40000,40000,30),'ground')
 box('InteriorFloor',(0,0,-5),(800,600,10),'wood')
 box('Terrace',(0,-500,-10),(1000,400,20),'wood')
 box('BackWall',(0,310,160),(840,20,320),'plaster')
 box('WestWall',(-410,0,160),(20,600,320),'plaster')
 box('EastWall',(410,0,160),(20,600,320),'plaster')
 # Front wall segments leave a large window and an open entrance.
 for label,x,width in [('FrontWest',-350,100),('FrontDivider',200,100),('FrontEast',375,50)]:
  box(label,(x,-310,160),(width,20,320),'plaster')
 box('WindowSillWall',(-75,-310,40),(450,20,80),'plaster')
 box('FrontHeader',(0,-310,295),(800,20,50),'plaster')
 box('Roof',(0,0,330),(900,720,20),'white')
 for x in [-300,-150,0,150]:box('WindowMullion',(x,-310,175),(5,10,190),'trim')
 for z in [80,270]:box('WindowFrame',(-75,-310,z),(455,12,5),'trim')
 for x in [-400,400]:box('SideSkirting',(x,0,7),(3,600,14),'white')
 box('BackSkirting',(0,296,7),(800,3,14),'white')
 # Built-in kitchen, worktop, sink inset and cupboard divisions.
 box('KitchenCabinet',(0,260,45),(550,65,90),'cabinet')
 box('KitchenCounter',(0,260,94),(570,75,8),'stone')
 for x in [-220,-110,0,110,220]:box('CabinetHandle',(x,224,73),(35,3,2),'trim')
 for x in [-165,-55,55,165]:box('CabinetJoint',(x,226,44),(1,1,82),'trim')
 box('SinkBasin',(-140,260,99),(65,42,2),'trim')
 box('TapStem',(-140,284,112),(3,3,27),'trim')
 box('TapSpout',(-140,277,124),(3,16,3),'trim')
 for z in [170,225]:
  box('FloatingShelf',(40,282,z),(380,32,5),'wood')
 for i in range(12):box('Book',(-110+i*13,273,190),(9,18,31+(i%3)*3),'cabinet' if i%2 else 'white')
 box('DiningTable',(0,-20,77),(200,90,6),'wood')
 for x in [-80,80]:
  for y in [-48,8]:box('TableLeg',(x,y,37),(6,6,74),'trim')
 for y in [-100,60]:
  box('DiningBench',(0,y,44),(190,36,7),'wood')
  for x in [-75,75]:box('BenchLeg',(x,y,20),(6,28,40),'trim')
 box('Rug',(0,-20,1),(290,260,1),'fabric')
 # Pendant shades and practical warm lighting.
 for x in [-65,65]:
  box('PendantCable',(x,-20,270),(1,1,100),'trim')
  shade=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,-20,220))
  shade.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder.Cylinder'))
  shade.static_mesh_component.set_material(0,mats['trim']);shade.set_actor_scale3d(unreal.Vector(.38,.38,.12))
  lamp=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,-20,205))
  lamp.light_component.set_editor_property('intensity',1.5)
  lamp.light_component.set_editor_property('attenuation_radius',550)
  lamp.light_component.set_editor_property('use_temperature',True);lamp.light_component.set_editor_property('temperature',3200)
 from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
 from unreal_bridge.moods import handle_apply_mood
 handle_add_post_process({});handle_add_clouds({});handle_apply_mood({'mood':'blockbuster','weather':False,'sun_azimuth':280})
 from unreal_bridge.realworld import scan_library
 from unreal_bridge.forest import handle_add_forest
 lib=scan_library()
 layers=[]
 for kind,density,scale in [('tree',.8,[.65,1]),('grass',160,[.8,1.3]),('rock',.15,[.4,.8])]:
  meshes=[m for e in lib.get(kind,[]) for m in e['meshes'][:4]]
  if meshes:layers.append({'meshes':meshes,'density':density,'scale':scale,'within':[0,0,6500]})
 planting=handle_add_forest({'layers':layers,'size':14000,'seed':111,'density':1,'clear':[[0,0,900]],'label':'HouseLandscape'})
 cameras={'interior':{'location':[-280,-210,165],'target':[90,150,125]},
          'exterior':{'location':[1200,-1600,500],'target':[0,-50,140]}}
 for key,shot in cameras.items():
  location=unreal.Vector(*shot['location']);rotation=unreal.MathLibrary.find_look_at_rotation(location,unreal.Vector(*shot['target']))
  camera=actors.spawn_actor_from_class(unreal.CineCameraActor,location,rotation);camera.set_actor_label('HouseCamera_'+key)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*cameras['interior']['location']),
  unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*cameras['interior']['location']),unreal.Vector(*cameras['interior']['target'])),unreal.Name())
 path='/Game/EnvironmentDemos/'+name
 assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
 D=H/'demos'/name;D.mkdir(exist_ok=True)
 report=dict(level=path,biome='modern_house',warnings=[],architectural_pieces=count,cameras=cameras,
             floorplan_cm={'width':800,'depth':600,'height':320,'entrance_x':[250,350]},planting=planting)
 (D/'build-result.json').write_text(json.dumps(report,indent=2))
 (H/'demos/latest-house.json').write_text(json.dumps({'id':name,'directory':str(D),'cameras':cameras},indent=2))
except Exception:
 (H/'demos/house-error.txt').write_text(traceback.format_exc());raise
