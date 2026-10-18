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

### Anchors (write where, not numbers)

`previs_anchors.py`: actors carry `at='door_front'` or `at=('inside_center','left')` instead of coordinates; DIRECTION names each place (`sets=[dict(name='hut', kind='village', origin_cm=[18000,0])]`, `shots={'title': dict(place='hut', framing='medium')}`). The resolver turns anchors into positions, facings (walkers face travel, talkers face each other, contact beats side by side with the measured spacing) and turns on automatic cameras. Anchors per place kind: forest (clearing, trail_start, trail_end, camp), river (south_bank, bridge_start, bridge_middle, bridge_end, north_bank), village (street, street_near, door_front, entrance, inside_center, inside_back, inside_near, seat_inside, counter, patio), mountains (path_start, stairs_bottom, stairs_top, summit). See `previs_story5.py` for a whole story written this way; `python quick_review.py previs --plan previs_story5:STORY --direction previs_story5:DIRECTION --strict`.

### Purposeful motion, big rooms, themed dressing

* **No movement without a purpose** (`stillness.py`, lint rule `purpose.gesture`): idle beats hold arms, hands, legs, feet and hips still (measured: hands move about 1 cm over a 4 s idle, feet and hips 0) while head, neck, eyes and blinks stay alive. A gesture beat (wave, nod, laugh, celebrate, ...) needs a line of dialogue or `purpose='...'`, otherwise the story check warns; use `idle` for listening. `natural=True` on a beat keeps the mocap idle.
* **Rooms** are 760 x 640 cm with 300 cm walls (`set_dressing.py`, anchors updated): inside_near / inside_center / inside_back / seat_inside sit in the clear acting zone.
* **Themed dressing** from `door_style` (`'cafe'`, `'bakery'`, anything else = home): furniture inside (counter, shelves with cups or bread, oven with fire, display case, bed, fireplace, bookshelf, tables with chairs, rug, hanging lamp) and outside (lamp posts with glow, flower boxes, barrels, crates, cart, sacks, woodpile, awning, sign, patio tables). Solid furniture becomes blocking footprints for the layout check and the camera solver. Outdoors: forest clearing (flowers, logs), river (dock, boat, reeds, signpost), mountains (campfire, tent, logs, signpost), village (market stall, hay bales).
* `previs_story7.py` (The Morning Bakery) is written with all of this.

### Fixes after story 7 (used by story 8, "A Friend's Visit")

* **Door**: the hand finds the handle (placed well inside the arm's reach), pushes the door 10 degrees with the arm following it (palm on the handle for the whole push, 5 cm worst), then the door swings on to 85 degrees by itself while the arm lets go. A brass handle is on the door. Hut, anchors and layout use the new door geometry (door centre 20.8 cm to the left of the opener, plane 47.5 cm ahead; `door_front` anchor is (21,-60) so the door is centred on x=0).
* **Floor**: the root height bobbed up to 5 cm with every step, which read as the floor changing; the root height of walking and standing shots is now smoothed over one second.
* **Teleporting**: `continuity.teleport` (error) when an actor ends a shot outside the room and starts the next inside it or the reverse; warning when they appear 2.2 m from where the previous shot left them. Add a shot of them walking through the doorway (anchors `doorway` and `room_entry`).
* **Seated direction**: `face='toward:<anchor>'` on an actor (a seated actor faces the middle of the room, the bench and table follow).
* **Handshake**: both actors turn 35 degrees toward each other (anchors do this), spacing from the wide end of the window (about 75 cm, head clearance 7 cm measured); both hands meet in front of the pair's mean facing. Hugs stay side by side.
* QA: the camera may follow actors through a doorway; a camera is only "against scenery" within 50 cm of a wall.

## Horse herd (aerial scene)

`horse_herd.py` builds an aerial herd of galloping horses over a green meadow in Blender from the CC0 Quaternius horse (`assets/quaternius_farm_animals_download/`, from "Farm Animals Animated by Quaternius", https://quaternius.itch.io/lowpoly-animated-animals, CC0, downloaded 2026-10-18; the zip and its extracted Blends/FBX/OBJ are not committed). The horse is already rigged (28 bones) with Idle, Walk, WalkSlow, Run, Jump and Death actions, so nothing is auto-rigged: each horse is a copy of the armature and mesh playing `Run` from an NLA strip (random phase, retimed to the ground speed), travelling along the herd heading with a sideways wander, with coats (white, grey, bay, black, chestnut, palomino) and foals as in the reference photo, plus a drone camera.

    blender -b --disable-autoexec --python horse_herd.py -- <Horse.blend> <out.blend> [horses=64] [seconds=12]

Also in the script: a meandering low-poly river with banks, rocks and pines, low-poly mountain ranges with snow caps ahead of the herd and beyond the river, five camera cuts bound to timeline markers (1 drone wide, 2 low alongside, 3 ahead looking back, 4 overhead, 5 river bank with mountains behind), and a soundtrack synthesised in the script with numpy (no downloads): hoof beats (70 horses x 4 hooves per stride, louder in the close shots), wind and river noise (river louder at the river bank), and a short Dm-Bb-F-C piece with arpeggios and a melody; three WAVs in `scenes/audio/` added as separate sound strips so each can be muted or rebalanced.

Result: `scenes/horse_herd.blend` (70 horses, 16 s, 384 frames). For any other un-rigged animal: Blender's Rigify quadruped metarig (manual fit) or an AI auto-rigger (Meshy, Tripo, Anything World) then retarget; Mixamo only rigs bipeds.

## Rider on a galloping horse

`rider_scene.py` (22 s, 7 camera cuts): Rowan stands beside the CC0 Quaternius horse, leaps into the saddle (an arc keyed from the horse's saddle position), then a Child Of constraint keeps him on the horse's torso bone while the horse goes idle, walk, gallop, jumps a fence and gallops on beside a river toward the mountains. Legs and arms are IK to stirrup and rein empties that follow the horse's bones (reins are rods stretched from his hands to the horse's mouth), he leans into the gallop, dust puffs appear at every hoof landing (found by sampling the hoof bones, 170 of them), and the soundtrack uses the real contact times for hoof beats, wind rising with speed and a music piece with a kick drum once the gallop starts.

    blender -b --disable-autoexec --python rider_scene.py -- <Horse.blend> <rider.blend> <out.blend> [seconds=22] [rowan|lion]

With `lion` the rider is Leo (use the `scene.blend` of any built lion shot as rider.blend, e.g. a `quick_review/shot1_wave_*` folder; result `scenes/rider_lion.blend`, white horse): the same IK seat with stirrups, knee poles, reins and lean tuned for his short legs and arms (`KINDS` in the script). The seat is solved by IK, not by the shared Sit clips: those are made for a bench and the lion's legs would hang straight down.

Cameras on markers: wide, walking out, chase from behind and above, low alongside, ahead looking back at the jump, drone toward the mountains, rider point of view (attached to Rowan's spine, looking over the horse's neck). Known limits: the legs are IK only (knees and feet can pass through the horse's flank), the mount is a leap with legs blending in, hands do not wrap the reins, dust puffs are low-poly spheres.
