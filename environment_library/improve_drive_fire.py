"""Isolated flame cards with animated noise, smoke and local light flicker."""
import unreal,json,math,random,traceback
from pathlib import Path
from unreal_bridge import vfx
D=Path(__file__).resolve().parent.parent/'samples/lion-drive-v2'
try:
 record=json.loads((D/'native.json').read_text());folder=record['level'].rsplit('/',1)[0];sequence=unreal.load_asset(record['sequence']);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('AnimatedFlameCards',folder,unreal.Material,unreal.MaterialFactoryNew())
 mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);mat.set_editor_property('two_sided',True)
 g=vfx._M(mat)
 code=vfx._SAMPLE+'''float2 uv=UV; float h=1-uv.y; float x=uv.x-.5;
float2 q=float2(x*2+Phase,h*2-T*1.3+Phase);
float n=NOISE(q).r*.65+NOISE(q*2.4+float2(.3,T*.2)).g*.35;
float sway=.08*sin(h*7-T*3+Phase);float radius=max(.015,.48*(1-h));
float edge=saturate((radius-abs(x+sway))/.14);
float tongues=saturate((n-(h*.52+.13))*4);
float alpha=edge*tongues*saturate(h*12)*saturate((1-h)*5)*.65;
float3 color=lerp(float3(1,.43,.035),float3(.75,.035,.004),h)*Intensity;
return float4(color,alpha);'''
 c=g.custom(code,[('Tex',g.node(unreal.MaterialExpressionTextureObject,texture=vfx._noise_texture())),('UV',g.node(unreal.MaterialExpressionTextureCoordinate)),('T',g.node(unreal.MaterialExpressionTime)),('Phase',g.scalar('Phase',0)),('Intensity',g.scalar('Intensity',3))])
 g.mel.connect_material_property(g.mask(c,'rgb'),'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);g.mel.connect_material_property(g.mask(c,'a'),'',unreal.MaterialProperty.MP_OPACITY);g.mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
 plane=unreal.load_asset('/Engine/BasicShapes/Plane.Plane');rng=random.Random(42);count=0
 for a in list(actors.get_all_level_actors()):
  label=a.get_actor_label()
  if not label.startswith('RoadsideFire_'):continue
  if isinstance(a,unreal.PointLight):
   comp=a.light_component;binding=sequence.add_possessable(comp);t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path('Intensity','Intensity');sec=t.add_section();sec.set_range(0,288)
   for f in range(0,288,3):sec.get_all_channels()[0].add_key(unreal.FrameNumber(f),160*(.75+.25*math.sin(f*.9+count)),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  if not isinstance(a,unreal.DynamicMeshActor) or not label.endswith('_Fire'):continue
  pos=a.get_actor_location();actors.destroy_actor(a);height=rng.uniform(300,560);width=rng.uniform(220,330)
  for layer in range(3):
   card=actors.spawn_actor_from_class(unreal.StaticMeshActor,pos+unreal.Vector(layer*13,layer*11,height*.5));card.set_actor_label(label+'_Card_'+str(layer));card.static_mesh_component.set_static_mesh(plane);card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);card.static_mesh_component.set_cast_shadow(False)
   card.set_actor_rotation(unreal.Rotator(pitch=0,yaw=layer*60+17,roll=90),False);card.set_actor_scale3d(unreal.Vector(width/100,height/100,1))
   mi=unreal.AssetToolsHelpers.get_asset_tools().create_asset('Flame_'+str(count),folder+'/Flames',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());unreal.MaterialEditingLibrary.set_material_instance_parent(mi,mat);unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi,'Phase',rng.uniform(0,20));card.static_mesh_component.set_material(0,mi);unreal.EditorAssetLibrary.save_loaded_asset(mi);count+=1
 unreal.EditorAssetLibrary.save_loaded_asset(sequence);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(0);unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(48)
 (D/'fire-check.json').write_text(json.dumps({'ok':True,'flame_cards':count,'smoke':'existing separate smoke plumes retained','lights':'keyframed flicker','type':'procedural animated material; no fluid simulation'},indent=2))
except Exception:(D/'fire-check.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()}))
