"""Create a fictional city study with a 600 m landmark; no downloaded models."""
import unreal,json,time,random,traceback,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from scale_policy import POLICY
try:
 if 'LatestSceneVerification' not in unreal.Paths.get_project_file_path():raise RuntimeError('Wrong project')
 name='SkyscraperCity_'+time.strftime('%Y%m%d_%H%M%S');folder='/Game/EnvironmentAssets/CityStudies/'+name
 tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
 def material(label,color,rough=.6,metal=0):
  mat=tools.create_asset(label,folder,unreal.Material,unreal.MaterialFactoryNew())
  c=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);c.constant=unreal.LinearColor(*color,1)
  mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR)
  for prop,value in [(unreal.MaterialProperty.MP_ROUGHNESS,rough),(unreal.MaterialProperty.MP_METALLIC,metal)]:
   n=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);n.r=value;mel.connect_material_property(n,'',prop)
  mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);return mat
 mats={'road':material('Asphalt',[.035,.04,.045],.88),'walk':material('Paving',[.32,.33,.32],.85),
       'white':material('Paint',[.8,.79,.66]),'roof':material('Roof',[.12,.13,.14]),
       'stone':material('Stone',[.35,.33,.29]),'glass':material('Facade',[.065,.13,.19],.22,.65)}
 mat=mats['glass']
 worldpos=mel.create_material_expression(mat,unreal.MaterialExpressionWorldPosition)
 custom=mel.create_material_expression(mat,unreal.MaterialExpressionCustom)
 custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
 inp=unreal.CustomInput();inp.set_editor_property('input_name','W');custom.set_editor_property('inputs',[inp])
 custom.set_editor_property('code','float u=frac((W.x+W.y)/180.0); float v=frac(W.z/380.0); float win=step(0.08,u)*step(u,0.92)*step(0.12,v)*step(v,0.91); float tint=0.8+0.2*frac(sin(floor((W.x+W.y)/180.0)*12.7+floor(W.z/380.0)*78.1)*43758.5); return lerp(float3(0.23,0.25,0.27),float3(0.045,0.105,0.16)*tint,win);')
 custom.set_editor_property('code',custom.get_editor_property('code').replace('380.0',str(float(POLICY['architecture_cm']['office_floor']))))
 mel.connect_material_expressions(worldpos,'',custom,'W');mel.connect_material_property(custom,'',unreal.MaterialProperty.MP_BASE_COLOR)
 mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube');count=0
 def box(label,loc,size,material):
  global count
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label)
  a.static_mesh_component.set_static_mesh(cube);a.static_mesh_component.set_material(0,mats[material])
  a.set_actor_scale3d(unreal.Vector(*[s/100 for s in size]));count+=1;return a
 box('CityGround',(0,0,-70),(600000,600000,100),'road')
 rng=random.Random(117);buildings=[]
 for i in range(5):
  for j in range(5):
   x,y=(i-2)*10000+5000,(j-2)*10000+5000
   landmark=i==2 and j==2
   height=60000 if landmark else rng.randrange(8000,26000,POLICY['architecture_cm']['office_floor'])
   width=6000 if landmark else rng.randrange(3000,5100,100)
   depth=width if landmark else rng.randrange(3000,5100,100)
   box('BlockPavement',(x,y,-5),(7800,7800,30),'walk')
   box('BuildingPodium',(x,y,550),(width+600,depth+600,1100),'stone')
   if landmark:
    for k,(ratio,z,h) in enumerate([(1,1100,24000),(.8,25100,16000),(.6,41100,10000),(.4,51100,6900)]):
     box('LandmarkSetback_'+str(k),(x,y,z+h/2),(width*ratio,depth*ratio,h),'glass')
    box('LandmarkSpire',(x,y,59000),(100,100,2000),'roof')
   else:
    box('Tower',(x,y,(height+1100)/2),(width,depth,height-1100),'glass')
    box('RoofCap',(x,y,height+30),(width+60,depth+60,60),'roof')
    box('RoofPlant',(x+width*.15,y,height+230),(width*.35,depth*.3,400),'roof')
   buildings.append(dict(location_cm=[x,y,0],height_m=height/100,width_m=width/100,landmark=landmark))
 # Road markings remain on corridors between pavement blocks.
 for lane in range(-2,4):
  p=lane*10000
  for t in range(-23000,32000,1800):
   box('LaneMark_NS',(p,t,-13),(18,700,2),'white')
   box('LaneMark_EW',(t,p,-13),(700,18,2),'white')
  for t in range(-20000,30001,10000):
   for k in range(7):
    box('Crosswalk',(p-600+k*200,t+1300,-12),(100,600,2),'white')
 # Repeated street furniture at pedestrian scale.
 for x in [-10000,0,10000]:
  for y in range(-18000,28000,4000):
   box('StreetlightPole',(x+1400,y,500),(16,16,1000),'roof')
   box('StreetlightArm',(x+1220,y,995),(370,30,25),'roof')
 from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
 from unreal_bridge.moods import handle_apply_mood
 handle_add_clouds({});handle_add_post_process({});handle_apply_mood({'mood':'blockbuster','weather':False,'sun_azimuth':130})
 cameras={'skyline':{'location':[-65000,-85000,40000],'target':[3000,4000,22000]},
          'street':{'location':[0,-16000,180],'target':[5000,5000,21000]}}
 for label,shot in cameras.items():
  loc=unreal.Vector(*shot['location']);rot=unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*shot['target']))
  camera=actors.spawn_actor_from_class(unreal.CineCameraActor,loc,rot);camera.set_actor_label('CityCamera_'+label)
 shot=cameras['skyline'];loc=unreal.Vector(*shot['location'])
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(loc,unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*shot['target'])),unreal.Name())
 path='/Game/EnvironmentDemos/'+name;assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
 D=H/'demos'/name;D.mkdir(exist_ok=True)
 report=dict(level=path,biome='skyscraper_city',warnings=[],buildings=buildings,architectural_pieces=count,cameras=cameras,
  limitations=['Procedural opaque reflective facades, not individual furnished interiors','No traffic or crowds','Roads and façades need production detail'])
 (D/'build-result.json').write_text(json.dumps(report,indent=2))
 (H/'demos/latest-city.json').write_text(json.dumps(dict(id=name,directory=str(D),cameras=cameras),indent=2))
except Exception:
 (H/'demos/city-error.txt').write_text(traceback.format_exc());raise
