# Full movie workflow

In the studio: Create scene → Movie prompt. Choose a saved environment or describe one, enter the story, plan and review the shots, then click **Build full movie and website draft**. In 3dobjectnew, use Movie Studio's equivalent full-movie button. Existing editable-shot builds and separate rendering remain available.

The pipeline creates unique shot copies, checks body tracks, changing speech jaw curves, missing facial targets, dialogue duration, route QA and available bone-discontinuity/eye-material reports; it then creates a continuous spawnable-shot Unreal master, mixes local speech/effects/original music and renders a decoded website draft. Checks are shown on the saved movie. Saved movies also have a finish action and master-open button. An exclusive reentrant build lock prevents other editor mutations from interleaving with the full run. Child-stage completion cannot prematurely finish the public job.

Continuous masters currently require one shared environment and mood. Camera cropping, natural gait, pupil contact and facial appeal still need visual review. Bone checks flag extreme control jumps or scale changes, not every bad anatomical pose. Older scenes lacking new reports receive explicit warnings. Unsaved unrelated Unreal changes block level switching. Original films and source environments are preserved.

## End-to-end verification

**The River Secret**, movie `f637d0d2d5d34f2692ae7163e2ba88d6`, was planned and produced through the main app's public APIs: `/movie/plan` → `/movie/pipeline`. The eight-second, two-shot Rowan/Leo story uses the installed `RealisticRiver_20261015_093641` forest set with detailed conifers, ground cover and rocks. No new download or Meshy call was required. Both render frames were inspected, full decode passed, and the website video reported duration 8, readyState 4 and no media error. The master and quality checks are saved with the movie.

The planner initially returned a valid saved-set ID in `environment` rather than `environment_id`. Validation now normalizes only IDs that resolve to an installed saved set, preserving its exact Unreal level. Unknown values remain errors. This has a regression test.

51 targeted Python tests, the JavaScript syntax check and the main application's TypeScript check passed. Source model geometry was processed only locally; no geometry arrays were retrieved into the conversation.
