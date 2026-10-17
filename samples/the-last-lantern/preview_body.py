import bpy,json,sys
from pathlib import Path
root=Path(__file__).parent.resolve();sys.path.insert(0,str(root.parents[1]))
from movie_production.catalog import resolve_character
bpy.ops.wm.open_mainfile(filepath=str(root/'the-last-lantern-body.blend'),load_ui=False,use_scripts=False)
report={name:{'source_clips':['clip|Talking','clip|Listen'],'body_controls':list(resolve_character(name)['body']['mapping'].values()),'frames':384,'root_and_feet_keyed':False,'face_controls_keyed':False} for name in ('snow','jacob')}
(root/'body-report.json').write_text(json.dumps(report,indent=2))
for frame in (37,133,229,325):
    bpy.context.scene.frame_set(frame);bpy.context.scene.render.filepath=str(root/f'body-preview-{frame}.png');bpy.ops.render.render(write_still=True)
print('BODY_PREVIEWS_READY',flush=True)
