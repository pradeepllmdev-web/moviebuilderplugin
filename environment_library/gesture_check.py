"""Blender script: what a gesture beat actually plays and how far it moves. Run on a built scene.blend:
blender -b scene.blend --python gesture_check.py -- <folder> <start_s> <end_s>  -> writes gesture-check.json"""
import bpy,json,sys
import numpy as np
D,start,end=sys.argv[sys.argv.index('--')+1:][:3];start,end=float(start),float(end);fps=24
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
strips=[(st.name,st.action.name if st.action else None,round(st.frame_start/fps,1),round(st.frame_end/fps,1)) for t in rig.animation_data.nla_tracks for st in t.strips] if rig.animation_data else []
inside=[x for x in strips if x[2]<end and x[3]>start]
bones={n:next(b for b in rig.pose.bones if b.name.endswith(n)) for n in ('Hips','Head','LeftHand','RightHand')}
def pos(frame):
 s.frame_set(frame);bpy.context.view_layer.update();hips=np.array(rig.matrix_world@bones['Hips'].head)*100
 return {n:np.array(rig.matrix_world@b.head)*100-(hips if n!='Hips' else 0) for n,b in bones.items()}
frames=list(range(round(start*fps)+1,round(end*fps)+1,3));rows=[pos(f) for f in frames]
travel={n:round(float(np.ptp(np.array([r[n] for r in rows]),axis=0).max()),1) for n in bones}
rest=pos(round(start*fps)+1)
clips=[x[1] or x[0] for x in inside];played=[c for c in clips if 'Idle' not in c]
report=dict(ok=bool(played) and max(travel.values())>5,clips=clips,travel_cm=travel,right_hand_peak_above_head_cm=round(float(max(r['RightHand'][2]-r['Head'][2] for r in rows)),1),left_hand_peak_above_head_cm=round(float(max(r['LeftHand'][2]-r['Head'][2] for r in rows)),1))
(open(D+'/gesture-check.json','w')).write(json.dumps(report))
