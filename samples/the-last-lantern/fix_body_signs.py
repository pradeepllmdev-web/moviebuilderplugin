"""Repair equivalent quaternion signs, then rerender nearby interpolation frames."""
import bpy,sys,json
from pathlib import Path
from mathutils import Quaternion
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/blendplugin-next/scene_pipeline')
from realistic_rig import bone_curves
root=Path(__file__).parent.resolve();repo=root.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-body.blend'),load_ui=False,use_scripts=False)
seams=[]
for name,rig_name in [('snow','RIG-Snow'),('jacob','Armature')]:
    rig=bpy.data.objects[rig_name];curves=bone_curves(rig.animation_data.action)
    profile=json.loads((repo/'movie_production/profiles'/f'{name}-body.json').read_text())
    for bone in profile['mapping'].values():
        cs=curves[bone]['rotation_quaternion'];previous=None;original_previous=None
        for i in range(len(cs[0].keyframe_points)):
            q=Quaternion([c.keyframe_points[i].co.y for c in cs]).normalized();original=q.copy()
            if original_previous is not None and original_previous.dot(original)<0:seams.append(round(cs[0].keyframe_points[i].co.x))
            if previous is not None and previous.dot(q)<0:
                for c in cs:
                    point=c.keyframe_points[i];point.co.y*=-1
                q.negate()
            previous=q;original_previous=original
        for c in cs:
            for point in c.keyframe_points:point.handle_left_type='AUTO';point.handle_right_type='AUTO'
            c.update()
frames=sorted({f for centre in seams for f in range(max(1,centre-6),min(384,centre+6)+1)})
bpy.ops.wm.save_as_mainfile(filepath=str(root/'the-last-lantern-body.blend'))
(root/'body-sign-repair.json').write_text(json.dumps({'seams':seams,'rerendered_frames':frames,'reason':'equivalent quaternion signs must stay continuous for component interpolation'},indent=2))
for frame in frames:
    bpy.context.scene.frame_set(frame);bpy.context.scene.render.filepath=str(root/'body-frames'/f'frame_{frame:04}.png');bpy.ops.render.render(write_still=True)
print('BODY_SEAMS_REPAIRED',len(frames),flush=True)
