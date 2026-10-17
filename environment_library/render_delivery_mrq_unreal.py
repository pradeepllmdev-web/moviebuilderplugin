"""Render deterministic baked live performance through Unreal Movie Render Queue."""
import unreal,json,traceback,time
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene'
try:
 report=json.loads((D/'sequence.json').read_text());assert report['ok']
 subsystem=unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
 if subsystem.is_rendering():raise RuntimeError('Another Movie Render Queue job is active')
 queue=subsystem.get_queue()
 # Do not remove the user's queued jobs; require a clean dedicated editor queue.
 jobs=list(queue.get_jobs())
 if jobs:
  if len(jobs)!=1 or jobs[0].job_name!='DeliveryMishap':raise RuntimeError('Dedicated editor render queue contains another job')
  job=jobs[0]
 else:job=queue.allocate_new_job(unreal.MoviePipelineExecutorJob);job.job_name='DeliveryMishap'
 job.sequence=unreal.SoftObjectPath(report['sequence'])
 job.map=unreal.SoftObjectPath(report['level']+'.'+report['level'].split('/')[-1])
 config=job.get_configuration();output=config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
 output_directory=D/('mrq-frames-'+time.strftime('%H%M%S'))
 output.output_directory=unreal.DirectoryPath(str(output_directory))
 output.file_name_format='{frame_number}';output.output_resolution=unreal.IntPoint(960,540)
 output.use_custom_frame_rate=True;output.output_frame_rate=unreal.FrameRate(24,1)
 output.use_custom_playback_range=True;output.custom_start_frame=0;output.custom_end_frame=report['frames']
 config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
 config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
 config.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
 aa=config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
 aa.spatial_sample_count=1;aa.temporal_sample_count=1;aa.engine_warm_up_count=16;aa.render_warm_up_count=16
 executor=unreal.MoviePipelinePIEExecutor()
 def done(executor,success):
  (D/'mrq-result.json').write_text(json.dumps({'success':success,'finished_at':time.time(),'frames_expected':report['frames'],'resolution':[960,540],'fps':24,'directory':str(output_directory)},indent=2))
 executor.on_executor_finished_delegate.add_callable(done)
 subsystem.render_queue_with_executor_instance(executor)
 (D/'mrq-start.json').write_text(json.dumps({'started_at':time.time(),'job':job.job_name,'directory':str(output_directory)},indent=2))
except Exception:(D/'mrq-error.txt').write_text(traceback.format_exc());raise
