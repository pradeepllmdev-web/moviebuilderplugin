# Living eyes

Set `eye_life: true` on a lion shot. `eye_life.py` keys the lion's existing `BlinkL`/`BlinkR` lid morphs and `GazeLeft`/`GazeRight`/`GazeDown`:

- Blinks just before each spoken line and when head attention shifts by 12° or more, plus idle blinks every 2.5–5.5 s, at least 1.2 s apart. Each blink closes over 3 frames, holds 1 and opens over 5.
- Small gaze darts every 0.8–2.2 s; on a head turn the eyes move 3 frames before the head.
- Timing is seeded by the shot title, so rebuilds match. `eye-life-check.json` lists blink frames.

## Why blinks were broken in Unreal, and the fix

Unreal reported the exported FBX bind pose invalid ("rebind using the time zero pose"). It then rebinds skinning to the first animation frame, which garbled morph targets (the lid blink landed on the mouth, the old "blink deformed the body") and would reverse any added bones.

`blendplugin-next/scene_pipeline/export_performance.py` now leads every character FBX with one true rest-pose frame and marks it `rest_frame: 1` in the manifest. `unrealplugin-next` (`performance_production.py`, `blender_transfer.py`) skips that frame: the animation section starts one frame in and facial curves are baked one frame later, so timing is unchanged. The verification project's plugin copy (`verification/LatestSceneProject/Plugins/UnrealBridge`) is a separate copy and must be synced and reloaded after bridge changes.

The lid meshes' normals point inward when closed, so the job copy flips them (`flip_normals`); otherwise the one-sided lid material hides the blink.

## Checking

`python quick_review.py shot 1 --plan test_eye_movie:PLAN --view face` renders head-following close-ups of open and fully closed frames in Blender (~15 s). `python quick_review.py movie --plan test_eye_movie:PLAN --frames 68,74,138,144` checks the same moments in Unreal. `tests/test_eye_life.py` covers the timing rules.

Known gap: the `close` camera crops the lion's face near the bottom of frame.
