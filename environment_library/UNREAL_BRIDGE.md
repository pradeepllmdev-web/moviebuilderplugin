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
