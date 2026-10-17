import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'movie_jobs'/(H/'conversation-active.txt').read_text().strip();movie=json.loads((D/'ready.json').read_text())
for report in [movie['master']]+[shot['report'] for shot in movie['shots']]:unreal.EditorAssetLibrary.save_directory(report['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages():raise RuntimeError('Unrelated unsaved changes; stopped')
for item in movie['shots']:
 if not unreal.EditorLoadingAndSavingUtils.load_map(item['report']['level']):raise RuntimeError('Cannot open generated shot')
 (H/'demos/scene-active.json').write_text(json.dumps({'id':item['scene_id']}))
 source=H/'setup_prompt_scene_unreal.py';exec(compile(source.read_text(),str(source),'exec'),{'__file__':str(source)})
 result=json.loads((H/'scene_jobs'/item['scene_id']/'ready.json').read_text())
 if not result['ok']:raise RuntimeError(result['error'])
(D/'framing-check.json').write_text(json.dumps({'ok':True,'close_camera_distance_cm':184,'rowan_camera_target_height_cm':145}))
