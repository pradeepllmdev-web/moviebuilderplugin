"""Studio job: story (or a prompt) -> built scenes -> Unreal, in one go.

POST /api/story-to-unreal {prompt | story, minutes, dry_run, bridge_url}. Stages: write the story (story_writer, model optional), build the film scene by scene (build_movie.run), stop if any scene has audit issues or failed
(nothing is sent), then export and send every good scene through the UnrealBridge (unreal_send). The job holds the same build lock as every other Studio build, so a Blender build, an Unreal open and an Unreal send never overlap.
The job record carries the story text, the build report, what was sent and what was skipped, so a failure at any stage leaves the earlier results usable."""
import json,time
from pathlib import Path
import story_writer,build_movie,unreal_send,unreal_handoff
H=Path(__file__).resolve().parent
def worker(job,lock,prompt=None,story=None,minutes=8,bridge_url=None,dry_run=False,use_model=True):
 if story is None and not prompt:raise ValueError('Give a prompt or a story')
 if not lock.acquire(blocking=False):job.update(status='failed',error='Another build is running. Wait for it to finish.');return
 try:
  bridge=unreal_send.Bridge(bridge_url)            # validates the URL before any work starts
  if story is None:
   job['stage']='Writing the story';story,notes=story_writer.write_story(prompt,minutes,use_model);job['story_notes']=notes
  job['story']=story;out=H/'scenes'/('story_'+job['id'][:8]);job['stage']='Building scenes in Blender (one after another)'
  res=build_movie.run(story,str(out));job['report']=[dict(index=r['index'],piece=r['piece'],status=r['status'],audit=r['audit']) for r in res['report']];job['folder']=str(out)
  bad=[r for r in res['report'] if r['piece'] and (r['audit'] or not (r['status'].startswith('built') or r['status']=='reused'))]
  if bad:job.update(status='failed',error='scene %d (%s) has issues: %s. Nothing was sent to Unreal.'%(bad[0]['index'],bad[0]['piece'],(bad[0]['audit'] or [bad[0]['status']])[0]));return
  job['stage']='Sending to Unreal'
  sent=unreal_handoff.handoff(out,bridge,dry_run=dry_run,progress=lambda s:job.update(stage=s))
  job.update(status='complete',stage='In Unreal: open the Level Sequences listed in sent' if not dry_run else 'Dry run complete (nothing created in Unreal)',sent=sent['sent'],skipped=sent['skipped'])
 finally:lock.release()
