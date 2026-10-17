# Activity templates

An activity (bench sitting, drinking, ...) is one entry in `activities.py`: its beats and clips, whether it is seated, planner text, how to recognise a request for it, duration limits and a short `test_beats` shot. Body-dependent geometry is never hard-coded: `body_measures.py` measures the evaluated body once (cached in `body_measures/<character>.json`) and the activity's module solves its layout from those numbers.

## Fast loop

| Command | Time | Tells you |
|---|---|---|
| `python quick_review.py activity drink --feasibility-only` | instant | whether this body can do it, with the solved layout (cup, table, hand target, nod) |
| `python quick_review.py activity drink --no-sheet` | ~12 s | one-shot Blender build of just that activity plus its checks |
| `python quick_review.py activity drink --frames 120,160` | ~15 s | adds a side-view sheet with table/cup proxies |
| `python -m unittest discover -s tests -p "test_*.py"` | 0.5 s | registry, planner rules and the layout math on a fixed measurement set |

Use Unreal (`quick_review.py movie`) only once, at the end.

## Adding an activity or a character

1. Add an entry to `ACTIVITIES` (beats, clips, planner text, request regex, `test_beats`). Seated beats play on `Sit_Idle` and are added to the seat family automatically.
2. If it depends on the body, add a module with `feasibility(measures)` (pure Python) and `apply(...)` (Blender pose); name it in `module`.
3. Run `activity <name> --feasibility-only` until the numbers are right, then the one-shot build.
4. New character: add a profile in `character_profiles.py`, then `python quick_review.py activity sit --character <name>` caches its measurements; the pre-check then works for every activity.

## Drink (lion)

The snout is ~52 cm ahead of the head pivot and the arm reaches ~47 cm, so a hand cannot lift a cup to the mouth. The cup stays on a low table, a hand rests beside it and the lion nods (Neck/Head, 25 degrees) until the muzzle meets the rim. Cup and table are fixed in space, so during a drink beat the body eases to its pose at the measurement frame (the seated idle clip sways ~15 cm). Checks: muzzle to rim under 6 cm, body not inside the table, hand reaches its target.

## Standing gestures (clip family)

wave, nod, shrug, think, bow, celebrate, laugh and hands_on_hips are one-line registry entries (`GESTURES` in `activities.py`) that play a clip straight from the shared library (`blendplugin-next/scene_pipeline/realistic_clips.py`, retargeted to the lion). No body solve, so adding one is: add the name to `GESTURES` with a request regex and a planner phrase, confirm the clip key exists in `CLIP_PREFERENCES`, run the batch check.

`python quick_review.py activity gestures` builds all of them in parallel (~25 s) and prints, per gesture, the clips actually played and how far the hands travel (`gesture_check.py`); a gesture that only plays idle fails. `sad` and `listen` are not offered because the lion has no clip for them (they fall back to Idle_3); laugh uses the shared agree-gesture clip.
