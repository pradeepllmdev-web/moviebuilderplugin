import unreal,json,math,random,traceback
from pathlib import Path
D=Path(__file__).resolve().parent.parent/'samples/lion-climb'
try:
 record=json.loads((D/'native.json').read_text());sequence=unreal.load_asset(record['sequence']);folder=record['level'].rsplit('/',1)[0];route=json.loads((D/'route.json').read_text());actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause()
 material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('CliffRock',folder,unreal.Material,unreal.MaterialFactoryNew());mel=unreal.MaterialEditingLibrary
 color=mel.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,0);color.set_editor_property('constant',unreal.LinearColor(.19,.16,.12,1));mel.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
 rough=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-300,100);rough.set_editor_property('r',.95);mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(material);unreal.EditorAssetLibrary.save_loaded_asset(material)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube.Cube');sphere=unreal.load_asset('/Engine/BasicShapes/Sphere.Sphere')
 def rock(label,pos,scale,mesh):
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*pos));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_material(0,material);return a
 rock('ClimbingFace',[0,110,175],[2.4,1.3,3.5],cube);rock('UpperLedge',[0,85,345],[3.,1.8,.22],cube)
 rng=random.Random(73)
 for i in range(28):
  x=rng.choice([-1,1])*rng.uniform(65,145);rock('CliffEdge_'+str(i),[x,85,rng.uniform(0,330)],[rng.uniform(.3,.7),rng.uniform(.5,1.),rng.uniform(.4,.9)],sphere)
 for i,(x,y,z) in enumerate(route['holds']):rock('RockHold_'+str(i),[x*100,-y*100+7,z*100-4],[.22,.22,.12],sphere)
 def transform(binding):
  sec=binding.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,240);return sec.get_all_channels()
 lion_binding=next(b for b in sequence.get_bindings() if b.get_name()=='Performance_Leo');cc=transform(lion_binding)
 camera_binding=next(b for b in sequence.get_bindings() if b.get_name()=='Transferred_Camera')
 for t in list(camera_binding.get_tracks()):
  if isinstance(t,unreal.MovieScene3DTransformTrack):camera_binding.remove_track(t)
 camera=transform(camera_binding)
 for row in route['root']:
  f=row['frame'];z=row['z']*100
  for c,v in zip(cc,[0,0,z,0,0,0,1,1,1]):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  pos=unreal.Vector(320,-440,z+230) if f<96 else unreal.Vector(250,-90,z+140) if f<192 else unreal.Vector(190,-150,z+180)
  target=unreal.Vector(0,22,z+100);rot=unreal.MathLibrary.make_rot_from_x(target-pos)
  for c,v in zip(camera,[pos.x,pos.y,pos.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):c.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for a in actors.get_all_level_actors():
  if isinstance(a,unreal.DirectionalLight):a.light_component.set_editor_property('intensity',7);a.set_actor_rotation(unreal.Rotator(pitch=-35,yaw=135,roll=0),False)
  if isinstance(a,unreal.SkyLight):a.light_component.set_editor_property('intensity',2.5)
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();lib.set_current_time(1);lib.set_current_time(48);lib.set_lock_camera_cut_to_viewport(True)
 (D/'cliff-ready.json').write_text(json.dumps({'ok':True,'duration':10,'ascent_m':1.6,'holds':len(route['holds']),'views':['wide','side contact','upper section'],'limitations':'Adapted ladder motion and joint IK; finger grip and summit transition not implemented'},indent=2))
except Exception:(D/'cliff-ready.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
