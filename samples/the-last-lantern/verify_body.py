import bpy,json,math,sys
from pathlib import Path
root=Path(__file__).parent.resolve();frames=(1,37,73,133,181,229,277,325,384)
configs={'snow':('RIG-Snow','Jaw','DEF-Wrist.L','DEF-Wrist.R'),'jacob':('Armature','CTRL-JAW','DEF-HAND.L','DEF-HAND.R')}
def sample(path):
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False);result={}
    for name,(rig_name,jaw,left,right) in configs.items():
        rig=bpy.data.objects[rig_name];result[name]={}
        missing={left,right}-set(rig.pose.bones.keys())
        if missing:raise ValueError('Missing body QA probes: '+str(missing))
        for frame in frames:
            bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();b=rig.pose.bones[jaw]
            q=(b.rotation_quaternion if b.rotation_mode=='QUATERNION' else b.rotation_euler.to_quaternion()).copy()
            feet={b.name:(rig.matrix_world@b.matrix).translation.copy() for b in rig.pose.bones if b.bone.use_deform and 'foot' in b.name.lower()}
            result[name][frame]={'jaw':q,'hands':[(rig.matrix_world@rig.pose.bones[n].matrix).translation.copy() for n in (left,right)],'feet':feet,'root':rig.matrix_world.copy()}
    return result
attention='--attention' in sys.argv
performance='--performance' in sys.argv
old=sample(root/('the-last-lantern-attention.blend' if performance else 'the-last-lantern-body.blend' if attention else 'the-last-lantern.blend'));new=sample(root/('the-last-lantern-performance.blend' if performance else 'the-last-lantern-attention.blend' if attention else 'the-last-lantern-body.blend'));report={}
for name in configs:
    jaw_error=max(2*math.acos(min(1,abs(old[name][f]['jaw'].dot(new[name][f]['jaw'])))) for f in frames)
    motion=max((new[name][f]['hands'][i]-new[name][frames[0]]['hands'][i]).length for f in frames for i in range(2))
    change=max((new[name][f]['hands'][i]-old[name][f]['hands'][i]).length for f in frames for i in range(2))
    foot_error=max(((new[name][f]['feet'][bone]-position).length for f in frames for bone,position in old[name][f]['feet'].items()),default=0)
    root_error=max((new[name][f]['root'].translation-old[name][f]['root'].translation).length for f in frames)
    assert jaw_error<.001,'Facial control changed'
    assert motion>.015,'No effective retargeted hand motion'
    if attention:assert change<.001,'Attention pass changed body gesture'
    else:assert change>.03,'No effective retargeted hand motion'
    assert foot_error<.001 and root_error<.001,'Feet or root moved'
    report[name]={'jaw_control_difference_degrees':math.degrees(jaw_error),'hand_motion_metres':motion,'hand_change_from_previous_metres':change,'foot_probes':len(old[name][1]['feet']),'foot_position_difference_metres':foot_error,'root_position_difference_metres':root_error}
report['passed']=True
(root/('performance-preservation.json' if performance else 'attention-preservation.json' if attention else 'body-verification.json')).write_text(json.dumps(report,indent=2));print('BODY_VERIFIED',json.dumps(report),flush=True)
