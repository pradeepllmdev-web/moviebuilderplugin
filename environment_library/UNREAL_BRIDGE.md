# Unreal bridge (proof on one scene: the Boulder Trap)

Idea: do not rebuild scenes in Unreal by hand. Each built scene exports a description of itself; Unreal rebuilds it from that file with real assets, one placeholder at a time.

1. Export (Blender, headless): `blender -b scenes/ruins_scene.blend --python unreal_export.py -- scenes/unreal_export/ruins ruins`
   - `ruins.ue.json`: actors with per-frame transforms in Unreal axes and centimetres (keys already reduced), characters with their clip strips, IK targets, cameras with lens keys, lights, the cut list, audio strips.
   - FBX: `environment.fbx` (static meshes), `props.fbx` (animated props), `character_<tag>.fbx`, `anim_<clip>.fbx`.
2. Map placeholders to real assets in `unreal_asset_map.json` (`assets` and `animations`). Anything unmapped uses the proxy FBX mesh, so the scene always plays.
3. In the Unreal editor: `import unreal_import; unreal_import.run(r'<export>/ruins.ue.json', map_path=r'<repo>/environment_library/unreal_asset_map.json')` builds `/Game/Movie/LS_ruins` (transform tracks, skeletal animation sections, camera cuts, audio).
4. Without Unreal: `python unreal_import.py <export>/ruins.ue.json unreal_asset_map.json` is a dry run that prints what would be built.

Status: the exporter ran on the Boulder Trap (60 actors, 8 clip strips, 10 cuts, 6 audio strips; 678 frames reduced to 765 keys) and the dry-run importer and tests pass.
NOT yet verified: the Unreal API calls (written for UE 5.3+) and the axis conversion (location Y negated, rotation = roll, -pitch, -yaw) have not been run inside Unreal. Open the sequence in Unreal, check that Leo runs forward along the corridor with the boulder behind him,
and if anything is mirrored or turned, fix it in `ue_loc` / `ue_rot_deg` in `ue_common.py` (one place).
Not covered yet: material/emission animation, shape keys (jaw, lids), cloth and fur, per-clip root-motion settings, lighting and post-process look.

## One Studio job from story to Unreal (uses the UnrealBridge plugin)
`POST /api/story-to-unreal {prompt | story, minutes, dry_run, bridge_url}` runs: story_writer (if a prompt) > build_movie (scene by scene, audits) > stop if any scene fails its audit > for each good scene: export (`unreal_export.py`), `import_asset` the environment/prop FBX through the bridge, `apply_movie_scene`.
From a shell: `python unreal_send.py <movie_folder> [--bridge http://127.0.0.1:8500] [--dry-run] [--scenes 1,2]`.

Unreal side (one-time): in `unrealplugin-next` the command `apply_movie_scene` was added (new file `UnrealBridge/Content/Python/unreal_bridge/movie_scene.py`, registered in `commands.py`). Those edits are NOT committed there, because that repo already
had uncommitted changes of yours; review and commit them yourself. Before starting the editor set `MOVIEBUILDER_ENV_LIB=<this folder>` (and optionally `MOVIEBUILDER_EXPORT_ROOT`). The bridge reads only `<name>.ue.json` files below the export root and never overwrites an existing sequence.
The pure helper module is `ue_common.py` (not `unreal_bridge.py`, which would collide with the plugin's own package name).
Tested here: the whole path against a fake local bridge (real Blender export of the Boulder Trap, real HTTP client, command order). Not tested: the commands inside a live editor.
Characters: the bridge's cast and animation library own the real character assets; map `LeoRoot` and the clip names in `unreal_asset_map.json` to your imported lion and animations (see the earlier steps), or import them with the bridge's own `import_cast`.

## The handoff commands (Blender stays the source, Unreal does environment and the final render)

```
python unreal_handoff.py <movie_folder>                 # export + check + import + exposure, cached and parallel, one summary
python unreal_handoff.py <movie_folder> --check-only    # export and check, nothing is sent (no editor needed)
python unreal_handoff.py swap <name> <asset> [--scene swamp] [--scale 1.2] [--no-fit]   # use a real Unreal asset for a prop
python unreal_handoff.py swap --env <scene> <asset> [--scale s]                           # a real environment for a whole scene
python unreal_render.py <movie_folder> [--preset final|draft] [--size 1920x1080] [--first N]   # PNG frames + audio, no mp4
```
(`unreal_send.py <movie_folder>` is the same as `unreal_handoff.py`.) In Git Bash set `MSYS_NO_PATHCONV=1` before passing `/Game/...` paths.

**Handoff.** Per scene: *export* (headless Blender; skipped when the .blend hash, the exporter code and the scene's swapped names are unchanged; `--jobs 2` exports run ahead while Unreal imports the previous scene) -> *check* (`unreal_check.py`: missing
meshes, unresolved characters, missing animation files, missing/silent audio; a scene with errors is not sent unless `--send-anyway`) -> *import* (skipped when export, the scene's slice of `unreal_asset_map.json` and the importer are unchanged and the sequence is
still in the editor) -> *exposure* (one apply, three draft frames measured, the bias set in place and remembered, so a re-import reuses it without rendering; pin it with `scenes.<s>.look.exposure`) -> *verify* (the editor's `<scene>.import.json` against the export).
State: `<export root>/<movie>/handoff_state.json`; summary: `handoff_summary.txt` (also printed in full). `--force` redoes everything, `--recalibrate` measures again, `--dry-run` only counts.

**Environment swap (`unreal_asset_map.json`).** `assets` (placeholder id, e.g. `Boulder`), `props` (exact object name, wins over `assets`) and `scenes.<scene|glob|piece>` with its own `props`/`assets`/`animations`/`environment`/`look`. An entry is an asset path or
`{asset, scale, fit:false, offset, rotation}`; by default the real asset is scaled to the size of the Blender placeholder. Swapped objects are kept out of the joined environment mesh by the exporter, so even a static boulder can be replaced alone. Editing the map
re-imports only the scenes it concerns; nothing is lost on a re-send because the map lives outside the export and the importer rebuilds from it every time. `scenes.<s>.environment` replaces the whole low-poly environment (static mesh or Blueprint, e.g. a level piece that also carries its own sky).

**Look.** The exporter writes Blender's world colour/strength and sun (`look` in the .ue.json). The importer lights each scene by its own lights: the sun and points as exported (the sun no longer drives the sky), a scene sky light in the world colour, and every mesh and light of the scene on
lighting channel 1 so the level's shared `Env_Sun` (channel 0) no longer lights it. Tune per scene with `scenes.<s>.look = {isolate, sun_scale, sky_scale, sky_color, exposure, exposure_target}`. Not covered: the visible sky background and fog are still the level's; give a scene its own with an environment swap.

**Final render.** `unreal_render.py` renders each scene's Level Sequence through Movie Render Queue (bridge `render_movie`, PNG), renumbers the frames into one run `frames/frame_000001.png ...` and mixes the Blender audio strips into `audio/movie.wav` (+ one wav per scene) in Python, so
there is no encoder in the loop; `render.json` has fps, size and where each scene starts. Finished scenes are skipped when it is started again. `--first N` makes a quick proof of the whole movie.

**One scene, and the contract.** `python unreal_handoff.py scene <scene.blend> <scene_name>` (in code `unreal_handoff.handoff_scene(blend, name, bridge)`) is the unit the movie flow calls: export, check, import, exposure, all cached. The scene package (`<scene>.ue.json` with `format_version`, FBX files, audio files)
is the contract between Blender and Unreal or any other tool; the importer refuses a newer version (`ue_common.FORMAT_VERSION`; a package without the field is version 1). Performance (animation, cameras, timing, audio) comes only from the package, so a re-send never loses it; Unreal-side look work survives
when it lives in the asset map (swaps, `look`) or in actors that are not tagged `moviebuilder:<scene>` (only tagged actors are rebuilt).
Characters are defined once: `<export root>/character_registry.json` remembers the skeletal mesh and each clip by content hash, so the same Leo or the same clip is not imported again, in this movie or the next. Upgrade a character by name through `assets` (e.g. `LeoRoot`) and `animations` in the asset map.
Scenes sit at `NN` km along +Y (scene 1 at 1 km), clear of the level's own sky sphere/water/post-process at the origin. `python unreal_handoff.py clean <movie_name>` removes a movie's scenes from the editor (tagged actors and sequences only); a layout change leaves scenes of an earlier layout behind until they are re-sent or cleaned.
