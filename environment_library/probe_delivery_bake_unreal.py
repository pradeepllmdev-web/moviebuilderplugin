import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene';data=json.loads((D/'import.json').read_text())
anim=unreal.load_asset(data['states']['cat_idle']['animation']);controller=anim.get_editor_property('controller')
methods=['set_number_of_frames','set_frame_rate','set_bone_track_keys','add_bone_curve']
report={'controller':{name:hasattr(controller,name) for name in methods},
 'get_bone_pose_for_time':hasattr(unreal.AnimationLibrary,'get_bone_pose_for_time')}
if report['get_bone_pose_for_time']:
 try:
  pose=unreal.AnimationLibrary.get_bone_pose_for_time(anim,unreal.Name('mixamorig_Hips'),0,False)
  report['pose_read_ok']=isinstance(pose,unreal.Transform)
 except Exception as error:report['pose_error']=str(error)
(D/'bake-api.json').write_text(json.dumps(report,indent=2))
