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

## Test every activity at once (Blender only)

`python quick_review.py activity all` builds sit, drink and every gesture in parallel Blender processes (~75 s for 30) and prints one `PASS`/`FAIL` line each: build, motion safety, foot drift, plus the activity's own check (gesture clip played and hands/head moved; drink muzzle-to-rim, hand reach and body-in-table). `activity gestures` runs only the clip-driven ones; `activity <name> --frames 40,80,120` adds a side sheet for one.

Clip activities: wave, nod, shrug, think, bow, celebrate, laugh, hands_on_hips, look_around, phone, pick_up, open_door, push, kick, punch, dodge, startle, block, hit_react, fall_back, get_up, kneel, crawl, lie_down, sleep, headache, stunned, argue. They play the library clip only: pick_up, open_door and phone have no prop yet (a hand-contact prop pass is the next layer), and lie_down/sleep/fall_back/get_up/crawl move the body to the floor, so judge them in Unreal. Not offered, no lion clip: sad, listen, point, cry.

## One template, several characters

Test on one character, then run the same check on the others: `python quick_review.py activity gestures --character rowan` (or `cat`). Clip activities need nothing character-specific (clips come from the shared library and are retargeted per rig), so all 27 gesture/clip activities pass on lion, cat and rowan. Each registry entry lists `characters`; others show `SKIP ... not calibrated`. Seat activities (sit, drink) are lion-only for now: they need that character's seated measurements (`activity sit --character X`, which also needs the sit clips retargeted to that rig) and the planner still enforces lion for the seat workflow. To add a character to an activity: run it, and if it passes add the name to that entry's `characters`.

Prompts: 3dobjectnew only proxies to the studio server (port 8521), so planner text, validation, the unsupported-motion rule and `/api/scene-capabilities` (`activity_catalog`) are all defined here and apply to every client after a server restart.

## Many at once, and a movie, in Blender only

| Command | What you get |
|---|---|
| `python quick_review.py activity all` | build + check all 34 activities in parallel (~3 min), one PASS/FAIL line each; also writes the gallery scene |
| `python quick_review.py gallery all` | same, then opens ONE Blender window with every activity side by side, labelled and playing (use `gallery wave,kick,hug` for a subset; `--no-open` to skip the window) |
| `python quick_review.py previs --plan previs_samples:STORY` | a whole movie plan as ONE low-poly Blender scene: actors per shot, a camera per shot (cuts are bound timeline markers), flat ground and trees; opens Blender |
| `python quick_review.py previs --plan previs_samples:STORY --render --no-open` | also renders `previs.mp4` (workbench, 640x360; ~1 min for 30 s) next to `previs.blend` |

Files: `previs.py` (driver: builds every actor in parallel, merges), `previs_merge.py` (Blender script: appends each actor's scene, parents it to a slot placed like Unreal places it, shifts its animation to the shot's start frame, hides it outside the shot, adds ground/trees/cameras), `previs_samples.py` (example plans: copy it to write your own). Any movie plan that `movie_prompt.validate` accepts works, including two-actor shots; the textures of the character blend files carry over.

New activities in this batch: pick_up (cup from a side table, arm IK), open_door (hinged door fitted to the hand), carry_walk (cup held at the hip while walking), climb_stairs (root follows three steps, root lifted so no foot sinks), handshake and hug (two actors, auto-facing, hands meet at a shared point; `pair_check` compares both actors). Contact beats are written once in `contact_actions.py`; all geometry comes from the evaluated body of each actor.

Known limits: props and stairs exist in Blender only (no Unreal prop yet); stairs do not plant feet with IK; the hug puts hands on the partner's sides, not a full wrap; handshake spacing 25..72 cm and hug 25..46 cm for the lion's reach.

`python quick_review.py reel [all|a,b,c] [--render]` plays ONE activity at a time on one timeline, 5 seconds (120 frames) each, one fixed camera, a caption and a timeline marker per slot (Marker menu: jump to next/previous). `library.json` next to the .blend lists every activity with its slot frames and the built actor folders, so a movie can pick clips from it later; `--render` writes `previs.mp4`.

## Story previs (Blender only, no render)

`python quick_review.py previs --plan previs_story:STORY --direction previs_story:DIRECTION` builds the sample story "Leo and the Missing Cup" (12 shots, ~78 s) as one `previs.blend` and opens it in the camera view. No mp4 is rendered unless you add `--render`. Actors walk their routes, each shot has its own camera (some with dolly moves), dialogue shows as subtitles and plays as audio strips, and low-poly sets (forest, river with bridge, village, mountain steps, mountain backdrop; `previs_sets.py`) sit 60 m apart. Bench, table, cup and stairs are added automatically from each actor's build. The plan limits (positions within 6 m, 40 s per shot) still apply per shot, but the movie-level 6-shot limit does not. Copy `previs_story.py` to write another story; `DIRECTION` holds the previs-only extras (sets, each shot's place and camera).

More stories (same format as previs_story.py): `previs_story2` (Storm at the Mountain Hut), `previs_story3` (The Lion Cafe: new `cafe` set with awning, counter, tables and chairs), `previs_story4` (The Lost Cub: paw-print trail and a cub prop via `DIRECTION['props']`, optionally visible only in named shots with `only_in`). Run: `python quick_review.py previs --plan previs_story3:STORY --direction previs_story3:DIRECTION`. Available low-poly sets: forest, river (with bridge), village (houses, well, fence), mountains, cafe, plus a mountain backdrop; props: bench/table/cup/stairs/crate/door/cub/paw prints/spheres/boxes/cylinders.

## Building a story: the automatic pipeline

Order a director works in, each step automatic (`quick_review.py previs --plan m:STORY --direction m:DIRECTION [--strict] [--keep-open]`):

1. **Environment and props** (`story_layout.scenery`, `previs_sets.py`): sets per place; door huts, benches, tables, stairs and story props are permanent scenery for every shot at their place.
2. **Paths** (`story_layout.segment_paths`): where each actor stands and walks, shot by shot (walks go +Y; `offset_cm` moves a shot inside its place).
3. **Blocking** (`story_layout`, `story_lint`): actors inside walls, water, stairs or each other, cuts between places without travel, actors that vanish, dialogue about things that are not there. Errors stop a `--strict` run.
4. **Facing** (`story_layout`): walkers face their travel, talkers face their partner, contact beats are side by side, nobody faces the camera by accident.
5. **Build**, then **camera and collision QA with real geometry** (`previs_qa.py`, Blender ray casts): candidate cameras around the actors are scored (actors in frame and well sized, nothing between lens and faces, not against a wall, same room as the actors, faces visible) and the winner is saved into `previs.blend`; body points inside walls are reported. Set `auto_camera=True` in DIRECTION to use `story_camera.py` for the first guess.

Output lists `story check`, per-shot `PASS`, and `camera and collision QA` with what is left for a human.
