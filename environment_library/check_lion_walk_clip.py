import bpy,sys,json
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent.parent/'blendplugin-next/scene_pipeline'))
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'samples/lion-grip-ik/scene.blend'),use_scripts=False)
from realistic_rig import shared_clips,choose_variant,HIPS,video_clip
import realistic_clips
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
realistic_clips.STYLE='adult' if (rig.matrix_world@rig.data.bones[HIPS].head_local).z/1.85>.42 else 'stylized'
realistic_clips.BODY='creature'
choice=choose_variant('walk',{},shared_clips(),0);video=video_clip('walk')
(H/'lion-walk-clip.json').write_text(json.dumps({'style':realistic_clips.STYLE,'choice':choice,'video_override':video}))
