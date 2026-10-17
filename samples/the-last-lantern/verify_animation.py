"""Control animation checks on the saved sample, without mesh inspection."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).parent.resolve()
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern.blend'),load_ui=False,use_scripts=False)
scene=bpy.context.scene;report={}
for name,rig_name,jaw_name,blink_name,blink_axis in [('snow','RIG-Snow','Jaw','MSTR-Eyelid_Upper.L',1),('jacob','Armature','CTRL-JAW','CTRL-EYE-BLINK.L',2)]:
    rig=bpy.data.objects[rig_name];jaw=[];blink=[]
    for frame in range(1,385):
        scene.frame_set(frame)
        bone=rig.pose.bones[jaw_name]
        rotation=bone.rotation_quaternion if bone.rotation_mode=='QUATERNION' else bone.rotation_euler.to_quaternion()
        jaw.append(2*math.acos(min(1,abs(rotation.normalized().w))))
        blink.append(abs(rig.pose.bones[blink_name].location[blink_axis]))
    assert sum(value>.005 for value in jaw)>12, 'No speech animation: '+name
    assert max(blink)>.018, 'No full blink control: '+name
    assert jaw[0]<.001 and jaw[-1]<.001, 'Jaw not neutral at clip boundaries: '+name
    report[name]={'jaw_active_frames':sum(value>.005 for value in jaw),'max_jaw_degrees':math.degrees(max(jaw)),'max_blink_control':max(blink),'jaw_neutral_at_clip_boundaries':True}
assert len([marker for marker in scene.timeline_markers if marker.camera])==4
report['camera_cuts']=4;report['passed']=True
(root/'animation-verification.json').write_text(json.dumps(report,indent=2));print('ANIMATION_VERIFIED',json.dumps(report),flush=True)
