import bpy,json,sys,math
from pathlib import Path
root=Path(__file__).parent.resolve()
performance='--performance' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(root/('the-last-lantern-performance.blend' if performance else 'the-last-lantern-body.blend')),load_ui=False,use_scripts=False)
report={}
for name,rig_name,probes in [('snow','RIG-Snow',['DEF-Wrist.L','DEF-Wrist.R']),('jacob','Armature',['DEF-HAND.L','DEF-HAND.R'])]:
    rig=bpy.data.objects[rig_name];previous=None;maximum=0;worst=0;previous_rotations=None;max_rotation=0
    for frame in range(1,385):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        points=[(rig.matrix_world@rig.pose.bones[bone].matrix).translation.copy() for bone in probes]
        rotations=[rig.pose.bones[bone].matrix.to_quaternion().normalized() for bone in probes]
        if previous_rotations:max_rotation=max(max_rotation,max(math.degrees(2*math.acos(min(1,abs(a.dot(b))))) for a,b in zip(rotations,previous_rotations)))
        if previous:
            change=max((a-b).length for a,b in zip(points,previous))
            if change>maximum:maximum=change;worst=frame
        previous=points
        previous_rotations=rotations
    report[name]={'maximum_hand_step_metres':maximum,'frame':worst,'maximum_hand_rotation_step_degrees':max_rotation}
    print('CONTINUITY_ACTOR',name,json.dumps(report[name]),flush=True)
    assert maximum<.18,'Possible retarget pop: '+name
report['passed']=True
(root/('performance-continuity.json' if performance else 'body-continuity.json')).write_text(json.dumps(report,indent=2));print('CONTINUITY',json.dumps(report),flush=True)
