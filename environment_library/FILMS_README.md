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
* If a build crashes on JSON, an interrupted run left a half-written `scene_NN_*.meta.json` or `report.json`: delete it and rerun.
* If lip sync reports "0 mouth shapes", a cached voice in `voices/cache` is silent: delete the silent wavs and rerun.
* People reach between about shoulder height minus 0.5 m and the shoulder: put props on pedestals of 0.9-1.1 m. A character can start a scene holding a prop with `at(id, x, y, holds='key')`.
* People only run or jog when the film says `gait='run'` or `'brisk'`.
* Tests: `python -m pytest tests` from the repository root.
