import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'movie_jobs/952bbdad5b6f43d9b8f65066b839a95f';m=json.loads((D/'ready.json').read_text())
for report in [m['master']]+[s['report'] for s in m['shots']]:unreal.EditorAssetLibrary.save_directory(report['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
if unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():raise RuntimeError('Unrelated unsaved changes')
for shot in m['shots']:
 unreal.EditorLoadingAndSavingUtils.load_map(shot['report']['level']);(H/'demos/scene-active.json').write_text(json.dumps({'id':shot['scene_id']}));source=H/'setup_prompt_scene_unreal.py';exec(compile(source.read_text(),str(source),'exec'),{'__file__':str(source)})
