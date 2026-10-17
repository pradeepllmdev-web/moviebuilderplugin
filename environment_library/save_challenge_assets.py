import unreal,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;key=json.loads((H/'challenge-save-request.json').read_text())['movie_id']
if not re.fullmatch('[a-f0-9]{32}',key):raise ValueError('Invalid movie')
m=json.loads((H/'movie_jobs'/key/'ready.json').read_text())
for report in [m['master']]+[shot['report'] for shot in m['shots']]:unreal.EditorAssetLibrary.save_directory(report['level'].rsplit('/',1)[0],only_if_is_dirty=True,recursive=True)
