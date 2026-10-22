# Handover: where the project stands (written at the end of a long session, October 2026)

Read this first in a new session, then `FILMS_README.md` (how to build and review), `PROMPT_PIPELINE.md` (prompt-driven flow) and `QUALITY_CHECKLIST.md` (every complaint and its check).

## What exists
* **Declarative film engine** (Blender 5.2, no Unreal needed to build): a film is a dict (`films/*.py` or `films/generated/*.json`); `perf_plan.py` plans it without Blender, `perf_scene.py` builds a scene in Blender, `perf_movie.py` builds a whole film, `render_film.py` renders an MP4 with sound, `review_pack.py` makes a one-page review of every shot.
* **Characters**: lions (old Mixamo rig), animals and dinosaurs (Quaternius, own actions + a procedural look/tail layer), and **people** on the Universal Animation Library skeleton (`assets/humanoid/ual_humanoid.blend`, 87 clips, committed). People: relaxed hands, clean clothing cuts, hair styles, idle variety and fidgets, base idle (no T-pose), narrow stance, carry walk, seated talking.
* **Films** (all in `films/`): pie_thief, silent_bell, lantern_run, storm_letter, wedding_cake, farm_egg (animals), village_clock_key (people, the current test film), generated/book_return (a 7 s scene written through the prompt path).
* **Process**: plan-only lint, build audits (collision, lip sync, eye line, foot slip, reach, framing, T-pose/frozen/overlap), story check (pacing causes, props that vanish, repeated lines, closing beat), `production_rules.json` (29 rules, prompt text per stage), `film_lint.py`, `film_from_story.py` (model writes the film as JSON; errors go back to it).
* 437 tests: `python -m pytest tests` from the repository root.

## How to resume
1. `cd environment_library`; Blender at `C:/Program Files/Blender Foundation/Blender 5.2/` (or set `BLENDER`).
2. Plan only (seconds): `python perf_movie.py films/village_clock_key.py scenes/movie_clock --plan-only`.
3. Build (minutes) then review: `python perf_movie.py films/<film>.py scenes/<folder>` and `python review_pack.py films/<film>.py scenes/<folder>` (open `review_pack.html`). Watch in Blender: `python dev_tools/play_scenes.py scenes/<folder>`.
4. A draft MP4 is the LAST step (10 to 20 minutes per film): `python render_film.py scenes/<folder> --draft`. The user said MP4s are only test videos until the process is good.

## The user's preferences (learned)
* Wants better videos through a better PROCESS (checks, prompts, rules), not one-off fixes; every complaint should become a guard (see QUALITY_CHECKLIST.md).
* MP4s last. Time (scene lengths) only needs to be approximate. Reviews by watching and with screenshots; complaints so far: T-pose, fists, stiff idles, running, funny celebration dance, weak dialogue, long dead walks, unclear story without sound.
* Long-term flow: **3dobjectnew** writes stories, character sheets, scenes and shots; **Blender** (this repo) builds animation and the low-poly world; **Unreal** builds the final movie from scenes with zero audit lines. This repo does not edit 3dobjectnew.

## Not in git (back these up: `python backup_assets.py <folder>`, about 2.1 GB)
`scenes/ship_assets` (the lion rig and clips, 790 MB; git ignores *.blend), the Quaternius animal/dinosaur downloads, the UAL downloads, `voices/` (Piper models and cached lines). The GitHub remote of this repository is gone (`origin/main: gone`): every commit is local only (the folder is synced by OneDrive). Create or fix a remote and push if you want an off-machine copy.
Also untracked and not mine: `body_measures/lion.json` (modified), `bl_frames.py`, `compare_unreal.py`, `make_stories.py`, `play_movie.py`, and the `scenes/movie_*` outputs (regenerable).

## Known gaps and next steps
1. People are still a plain mannequin (no shaped fingers, plain faces); more acting gestures (clap, hug, explain) are missing.
2. Animals only have walk, run, jump, idle, death (+ attack for dinosaurs).
3. The older films have long walks and story notes listed in their `review.md`; they were not restaged.
4. `film_from_story.generate` is tested only with a fake model. The existing `scene_ai` provider cannot import here (needs `sqlalchemy`, the 3dobjectnew server environment); set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` to try a real model. A second stage (build the scene in Blender, read its audit lines, feed them back) is not built; plan-only lint cannot see Blender-side audits such as arm reach.
5. Unreal export/import (`unreal_export.py`, `unreal_import.py`) has not been run inside Unreal in this work; Unreal editor must not be touched without the user's say.
6. Windows quirks: avoid bash heredocs with apostrophes (write scripts with the Write tool); no `sleep` polling; never chain `pytest | tail && git commit`.
