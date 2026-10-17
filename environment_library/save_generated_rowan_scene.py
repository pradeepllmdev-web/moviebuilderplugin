import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent
movie=json.loads((H/'movie_jobs/a9b0f57d182e4e709ff9d9e420bbc717/ready.json').read_text())
for data in [movie['master']]+[shot['report'] for shot in movie['shots']]:
 unreal.EditorAssetLibrary.save_directory(data['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
(H/'rowan-dirty-check.json').write_text(json.dumps({'dirty':[p.get_path_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())]}))



