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
