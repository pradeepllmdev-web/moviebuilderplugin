import unreal,json
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene'
queue=unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).get_queue()
(D/'queue.json').write_text(json.dumps([{'name':j.job_name,'sequence':str(j.sequence)} for j in queue.get_jobs()],indent=2))
