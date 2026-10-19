# A long story to one film (sequential, nothing built in parallel)

    python build_movie.py story.txt out_folder [--hero-tint 1.0,0.85,0.7] [--force]

1. `story_plan.plan(text)` splits the story into scenes (blank lines or `Scene 3:` lines), routes each to a set piece (`set_pieces.match`), reads the time of day from its words
   (dawn, day, dusk, night, overcast) and estimates its length. Warnings: night and day back to back, the same set piece twice in a row, a scene with no set piece, missing assets.
2. `build_movie.py` builds the scenes strictly one after another with `set_pieces.build(piece, out, seconds, params)`. `params` travel in the environment variable `SCENE_PARAMS`
   (`scene_params.py`: `time_of_day`, `hero_tint`, `title`; invalid values are ignored). The storm scenes (ship, cliff) keep their own sky.
3. Every scene file `scene_NN_<piece>.blend` has a `.json` next to it with the key of its piece, parameters and length and its audit lines. A rerun reuses scenes whose key did not change
   and rebuilds only the changed or failed ones (`--force` rebuilds everything).
4. `assemble_movie.py` links the good scene files into `movie.blend` (a sequencer timeline of scene strips with a 2 s title card before each, the sound strips of every scene copied
   with their offset). The scene files stay the single source of truth: rebuild one scene and the master follows. Open the master in the Video Editing workspace; the 3D viewport
   shows one scene at a time.
5. `report.md` and `report.json` list for every scene: built, reused, missing assets or failed, its audit lines, and the continuity warnings.

Limits: scenes that match no set piece are listed as `shots` and are not in the master (build them with the shot-by-shot planner `movie_prompt.py`); only the lion rig is available as
hero (tint changes its colour); a 10 minute film is about 10 scenes and builds in roughly 15 to 25 minutes in sequence, much less when most scenes are reused.

## Shared things, built once

* **Locations** (`locations.py`): the mountain village and the citadel are built once into `bank/<id>_<state>_<hash>.blend` and appended by every scene that uses them (`locations.load`);
  the hash of the module invalidates the cache when a location changes, `set_pieces.build` creates missing bank files first. A scene state (`intact`, `buried`, `breached`) is the
  parameter `location_state`; `story_plan` carries damage from scene to scene (an avalanche buries the village for the scenes after it) and warns when a set piece cannot show it.
* **Characters and clips** (`scenes/ship_assets`, from `build_ship_assets.py`): built once, loaded by every scene.
* Next candidates for the bank: props that travel between scenes (cub, egg, knife, banner) and the remaining environments (river canyon, plains, arena).
