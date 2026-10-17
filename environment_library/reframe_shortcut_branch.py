import unreal,json,sys,importlib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import branch_event_unreal;importlib.reload(branch_event_unreal)
D=H/'movie_jobs/fdaf2ce0f965410a9db3561a8c58dd6e';movie=json.loads((D/'ready.json').read_text());item=movie['shots'][2];plan=json.loads((H/'scene_jobs'/item['scene_id']/'plan.json').read_text())
results=[]
for path in [item['report']['sequence'],movie['master']['sequence'].rsplit('/',1)[0]+'/Shot_3']:
 sequence=unreal.load_asset(path);results.append(branch_event_unreal.frame_camera(sequence,plan['events'],120));unreal.EditorAssetLibrary.save_loaded_asset(sequence)
(D/'branch-framing-check.json').write_text(json.dumps({'ok':True,'camera_tracks_updated':results}))
