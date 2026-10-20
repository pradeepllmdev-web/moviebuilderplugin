# Movie building flow: architecture

## The flow
```
prompt or story text
  -> prompt_router.route()            which engine answers: story | set_piece | shot | environment
  -> story_writer.write_story()       (story engine only) scene list from a model, or offline from the catalogue
  -> story_plan.plan()                paragraphs -> scene types, parameters, lengths, continuity warnings
  -> build_movie.run()                scenes built one after another (own Blender process each), audits collected, reuse by key
       -> set_pieces.build()          one scene: <id>_scene.py on scene_base, environment from the shared bank
  -> assemble_movie.py                linked-scene master + report.md
  -> unreal_export.py                 scene description JSON + FBX (per scene)
  -> unreal_import.py                 Level Sequence in Unreal, real assets via the asset map (guarded)
```

## Layers and who owns what
| layer | files | rule |
|---|---|---|
| Scene library | `*_scene.py`, `scene_base.py`, `scene_kit.py` | one file per scene type; creative decisions only in the scene; shared scaffolding in `scene_base` |
| Environments | `locations.py` (generation 1), `world2_locations.py` (generation 2), `bank/` | built once, hashed by builder source and constants, loaded by every scene |
| Registry | `set_pieces.py`, `story_plan.py`, `story_writer.SENT` | a scene type exists when it is in `SET_PIECES`; `register_piece.py` / `scaffold_scene.py` add it everywhere |
| Language models | `llm.py` | the only module that talks to a model; pluggable, cached, always has an offline fallback |
| Routing | `prompt_router.py`, `studio_server.py` (`/api/route`, `/api/story-write`) | new pipeline where it applies, old builders elsewhere, `PROMPT_ENGINE=legacy` rolls back |
| Unreal | `ue_common.py`, `unreal_export.py`, `unreal_import.py`, `unreal_asset_map.json` | the scene is described, not rebuilt by hand; placeholders swapped for real assets by id |
| Gate | `verify_all_scenes.py`, `tests/`, the audit lines inside every scene | nothing is "done" until its audit says so |

Other repositories keep their roles: `3dobjectnew` owns movie records, scheduling and final assembly; `unrealplugin-next` owns native Unreal scene construction and its editor bridge; `blendplugin` owns the
Blender scene pipeline for shot-by-shot human scenes; `automatedmoviebuilder` owns the ComfyUI media service. This repo changes none of them. The integration points are data files (`.ue.json`, story text, `report.json`).

## Principles every scene follows (from the project's lessons)
1. Measure, then schedule: derive times from planners (hop windows, release solvers, pursuit tuning), never hand-tune.
2. Everything that appears is visible for the whole film; animate instead of hiding (only short-lived effects, named `Dust*`/`Spark*`/`Splash*`/`Steam*`, may scale to nothing).
3. Every claim in a scene's docstring has an audit line; a scene with audit issues does not enter a movie.
4. Scenes are built strictly one after another; shared environments are built once.
5. Children of scaled parents get local coordinates (or the parent is an unscaled empty).

## Everyday tasks
- Add a scene type: `python scaffold_scene.py <id> "<Title>" "<keywords>"`, replace the template mechanic, write the audit, `python set_pieces.py --write-docs`, add a sentence to `story_writer.SENT` (a test checks it selects its own scene), run `python verify_all_scenes.py --only <id>`.
- Make a film from an idea: `python story_writer.py 8 "your idea"` > `story.txt`, edit it, `python build_movie.py story.txt out_folder`.
- Check everything: `python -m unittest discover -s tests` (fast) and `python verify_all_scenes.py --fast` (builds the library).
- Use a different model provider: set `LLM_PROVIDER` (`scene_ai`, `anthropic`, `none`) or `llm.register_provider(name, fn)`; plans are cached in `analysis_cache/`.
- Send a scene to Unreal: see `UNREAL_BRIDGE.md`; the importer refuses to run unless the verification project is open with nothing unsaved and never overwrites an existing sequence.

## Declarative performance films (second route)
Besides the 28 bespoke set pieces there is a data-driven route: a cast registry (`cast_registry.py`: species looks, accessories, gaits, voices on the single lion rig), scene specs written with `perf_dsl.py`, compiled and audited by `perf_plan.py` (no Blender), shot by `perf_camera.py`, played by `perf_scene.py`, built into films by `perf_movie.py` (`films/`). See `PERFORMANCE_ENGINE.md`; it does not touch the set-piece registry or the Unreal bridge.

## Known gaps (honest list)
- Characters are one lion rig with clips; no finger poses, face acting beyond lip sync, fur or cloth. Environments are blocked-in geometry. The Unreal bridge exists to replace both with real assets.
- Only 27 scene types; a prompt outside them falls back to the old single-shot builder.
- The Unreal importer and the axis conversion have not been run inside Unreal yet.
- Scene lengths are 20-70 s each; a 12-minute film needs about 15-20 scenes, so long films need more scene types or longer scenes.
