"""Invoked inside Unreal; build one request into a NEW saved demo level."""
import unreal,json,traceback,time
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/environment_library/demos')
request=json.loads((H/'build-request.json').read_text());name=request['id'];D=H/name;D.mkdir(exist_ok=True)
try:
 from unreal_bridge.realworld import handle_add_real_world
 from unreal_bridge.environment import handle_add_clouds,handle_add_post_process
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
 handle_add_post_process({});handle_add_clouds({})
 params=dict(request['params']);layout=request.get('compiled_layout')
 if layout:
  params['size']=max(params.get('size',22000),layout['width_cm'],layout['depth_cm']);params['clear']=params.get('clear',[])+layout['clear']
  if layout['rivers']:params['river']='none'
 result=handle_add_real_world(params)
 if layout:
  from unreal_bridge.water import handle_add_river
  from unreal_bridge.props import handle_add_path,handle_add_bridge
  from unreal_bridge.forest import handle_add_forest
  from unreal_bridge.core import _find_actor_by_label,_actor_subsystem
  built={'rivers':[],'paths':[],'bridges':[],'forests':[],'clear':layout['clear']}
  for i,river in enumerate(layout['rivers']):
   built['rivers'].append(handle_add_river({**river,'depth':100,'bank':1200,'label':name+'_LayoutRiver_'+str(i)}))
  if layout['forests']:
   from unreal_bridge.realworld import scan_library,REAL_BIOMES,_pick
   original=_find_actor_by_label(params['label']+'_Forest')
   if original:_actor_subsystem().destroy_actor(original)
   result['actors']=[a for a in result['actors'] if a!=params['label']+'_Forest']
   library=scan_library();layers=[];ground_layers=[]
   for layer in REAL_BIOMES[params['biome']]['layers']:
    picks=_pick(library,layer['kind'],layer.get('prefer'),layer.get('strict'))
    if not picks:continue
    meshes=[m for e in picks for m in e['meshes'][:6]]
    resolved={**{k:v for k,v in layer.items() if k in ('density','scale','sink','align','in_clear','species')},'meshes':meshes}
    if layer['kind']=='tree':layers.append(resolved)
    else:
     if layer.get('near'):resolved['within']=[0,0,layer['near']]
     ground_layers.append(resolved)
   if ground_layers:
    cover_label=name+'_GroundCover';cover=handle_add_forest({'layers':ground_layers,'center':[0,0],'size':params['size'],'density':params['density'],'seed':params['seed'],'clear':params.get('clear',[]),'label':cover_label});result['actors'].append(cover_label);built['ground_cover']=cover
   for i,region in enumerate(layout['forests']):
    label=name+'_ForestRegion_'+str(i);center=region['center'];radius=region['radius']
    local_layers=[{**layer,'within':[*center,radius]} for layer in layers]
    built['forests'].append(handle_add_forest({'layers':local_layers,'center':center,'size':radius*2,'density':region['density'],'seed':params['seed']+i,'clear':params.get('clear',[]),'label':label}));result['actors'].append(label)
  elif layout['rivers']:
   # Regrow the existing scatter after carving, respecting the new water.
   built['forests'].append(handle_add_forest({'label':params['label']+'_Forest'}))
  for i,path in enumerate(layout['paths']):built['paths'].append(handle_add_path({**path,'clear_trees':True,'label':name+'_LayoutPath_'+str(i)}))
  for i,bridge in enumerate(layout['bridges']):built['bridges'].append(handle_add_bridge({**bridge,'river':name+'_LayoutRiver_'+str(bridge['river']),'label':name+'_LayoutBridge_'+str(i)}))
  result['layout']=built
 if request.get('detail_layers'):
  from unreal_bridge.realworld import scan_library, _pick
  from unreal_bridge.forest import handle_add_forest
  library=scan_library();layers=[]
  for detail in request['detail_layers']:
   picks=_pick(library,detail['kind'],None,None)
   meshes=[m for entry in picks for m in entry['meshes'][:6]]
   if meshes:layers.append({**{k:v for k,v in detail.items() if k!='kind'},'meshes':meshes})
  result['camera_detail']=handle_add_forest({'layers':layers,'center':request['camera']['location'][:2],
   'size':12000,'density':1,'seed':params['seed']+100,'clumping':.7,'clearings':.03,'label':name+'_CameraDetail'})
 location=unreal.Vector(*request['camera']['location']);target=unreal.Vector(*request['camera']['target']);rotation=unreal.MathLibrary.find_look_at_rotation(location,target)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_level_viewport_camera_info(location,rotation,unreal.Name())
 camera=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CineCameraActor,location,rotation);camera.set_actor_label('EnvironmentPreviewCamera')
 comp=camera.get_cine_camera_component();comp.set_editor_property('current_focal_length',28.0)
 path='/Game/EnvironmentDemos/'+name;counter=1
 while unreal.EditorAssetLibrary.does_asset_exist(path):counter+=1;path='/Game/EnvironmentDemos/'+name+'_v'+str(counter)
 assert unreal.EditorLoadingAndSavingUtils.save_map(world,path),'Level save failed'
 result.update(level=path,camera=request['camera'],reference_image=request.get('reference_image'),finished_at=time.time())
 (D/'build-result.json').write_text(json.dumps(result,indent=2));unreal.log('ENVIRONMENT_BUILT '+name)
except Exception:
 (D/'error.txt').write_text(traceback.format_exc());raise
