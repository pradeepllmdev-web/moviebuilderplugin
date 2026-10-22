# Rebuilding the films

Needs: Blender 5.2 (set `BLENDER` if it is not in `C:/Program Files/Blender Foundation/Blender 5.2/`), ffmpeg on the PATH, Python with numpy and the Piper voice models in `voices/*.onnx`.

## One-time assets (not in git)
* People: download the CC0 Universal Animation Library 1 and 2 (Standard) into `assets/ual1_download/extracted` and `assets/ual2_download/extracted`, then
  `blender -b --factory-startup --python build_humanoid_library.py` (writes `assets/humanoid/ual_humanoid.blend`).
* Animals and dinosaurs: the Quaternius packs in `assets/quaternius_farm_animals_download` and `assets/quaternius_dinosaurs_download`.

## Build a film
    python perf_movie.py films/<film>.py scenes/<folder>            plan, voices, scenes, contact sheets, movie.blend, storyboard.md, review.md
    python perf_movie.py films/<film>.py scenes/<folder> --plan-only
    python perf_movie.py ... --scenes 3,4 --force                   only those scenes
    python render_film.py scenes/<folder> --draft                   MP4 with sound (drop --draft for 1280x720)

Films: pie_thief, silent_bell, lantern_run, storm_letter, wedding_cake, farm_egg, village_clock_key (people).

## Things learned
* Interrupted builds recover by themselves: metadata files are written atomically and a damaged one just means that scene is built again; silent or truncated cached voices are deleted and synthesised again.
* `review.md` (written with every build) includes a story check: walks that arrive at nothing, props that vanish between scenes, repeated lines, a late first line.
* People reach between about shoulder height minus 0.5 m and the shoulder: put props on pedestals of 0.9-1.1 m. A character can start a scene holding a prop with `at(id, x, y, holds='key')`.
* People only run or jog when the film says `gait='run'` or `'brisk'`.
* Tests: `python -m pytest tests` from the repository root.

## Open-movie practices applied (Blender Studio films: Big Buck Bunny, Sintel, Glass Half, Sprite Fright ...)
* **Storyboard, then animatic, then blocking, then polish**: every build writes `storyboard.md` (a purpose for every shot) and contact sheets before any full render; `render_film.py --draft` is the animatic-quality pass. Voice recordings set the timing (as when Glass Half re-edited its animatic after the voice session).
* **Setups and payoffs, and a closing beat** (Big Buck Bunny): `review.md` flags props that are set up and never used, props that vanish between scenes, and a film that does not end on a small joke or a warm line.
* **Live-action reference for acting** (Glass Half): people play captured motion (Universal Animation Library) rather than invented poses.
* **Principles of animation**: anticipation before a walk starts and follow-through when it stops (the upper body carries on and settles), overlapping action from the head and neck lagging the body, ease in and out on every camera move, secondary action from idle fidgets, weight shifts and tail sway.

## The workflow (cheap checks first, the slow render last)
1. **Write the film** (`films/<name>.py`): one goal per scene, setups with payoffs, a closing beat. Run `python perf_movie.py films/<name>.py scenes/<folder> --plan-only`: a few seconds, finds spec errors and prints the plan; `review.md` lists the story notes (walks to nowhere, dead time, props that vanish, repeated lines).
2. **Build** (`perf_movie.py ...`, a few minutes): every scene is audited (collisions, lip sync, eye lines, foot slip, reach, framing, poses, T-pose, frozen people). Fix every AUDIT line before anything else.
3. **Review pack** (`python review_pack.py films/<name>.py scenes/<folder>`, about 20 seconds): `review_pack.html` shows every shot with its purpose, the lines and the audit results on one page. Look at it before watching anything.
4. **Note what is wrong** and add the guard: `QUALITY_CHECKLIST.md` lists every complaint so far and the check that now catches it; `tests/test_quality_checklist.py` fails if a guard is removed. A complaint that no check can catch goes in the "Manual" rows.
5. **Only then render** (`render_film.py --draft`, 10 to 20 minutes per film) for the sound and the motion that stills cannot show.
