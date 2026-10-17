"""Scrub a generated master already opened by the pipeline, without switching levels."""
import json,re,unreal
from pathlib import Path
H=Path(__file__).resolve().parent
request=json.loads((H/'movie-review-request.json').read_text());movie_id=request['movie_id'];frame=request['frame']
if not re.fullmatch('[a-f0-9]{32}',movie_id) or isinstance(frame,bool) or not isinstance(frame,int) or not 0<=frame<=2160:raise ValueError('Invalid review request')
D=H/'movie_jobs'/movie_id;movie=json.loads((D/'ready.json').read_text());master=movie['master']
lib=unreal.LevelSequenceEditorBlueprintLibrary;lib.pause();lib.open_level_sequence(unreal.load_asset(master['sequence']));lib.set_lock_camera_cut_to_viewport(True);lib.set_current_time(frame)
(D/'review-confirmation.json').write_text(json.dumps({'movie_id':movie_id,'frame':frame,'ok':True}))
