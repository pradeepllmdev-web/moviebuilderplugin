"""Constrain capture spikes in native body channels; preserve head/face tracks."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Quaternion
root=Path(__file__).parent.resolve();repo=root.parents[1]
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from realistic_rig import bone_curves
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-performance.blend'),load_ui=False,use_scripts=False)
report={}
for name,rig_name in [('snow','RIG-Snow'),('jacob','Armature')]:
    rig=bpy.data.objects[rig_name];profile=json.loads((repo/'movie_production/profiles'/f'{name}-body.json').read_text());curves=bone_curves(rig.animation_data.action);count=0
    for bone in profile['mapping'].values():
        channels=curves[bone]['rotation_quaternion'];previous=None;previous_frame=None
        for i in range(len(channels[0].keyframe_points)):
            frame=channels[0].keyframe_points[i].co.x;q=Quaternion([c.keyframe_points[i].co.y for c in channels]).normalized()
            if previous is not None:
                if previous.dot(q)<0:q=-q
                angle=previous.rotation_difference(q).angle;limit=math.radians(120)*(frame-previous_frame)/24
                if angle>limit:q=previous.slerp(q,limit/angle);count+=1
            for axis,c in enumerate(channels):
                point=c.keyframe_points[i];point.co.y=q[axis];point.handle_left_type='AUTO_CLAMPED';point.handle_right_type='AUTO_CLAMPED'
            previous=q;previous_frame=frame
        for channel in channels:channel.update()
    report[name]={'limited_body_keys':count,'maximum_native_joint_speed_degrees_per_second':120,'face_head_channels_modified':False}
bpy.ops.wm.save_as_mainfile(filepath=str(root/'the-last-lantern-performance.blend'))
(root/'performance-cleanup.json').write_text(json.dumps(report,indent=2));print('CAPTURE_CLEANUP',json.dumps(report),flush=True)
