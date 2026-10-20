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
and if anything is mirrored or turned, fix it in `ue_loc` / `ue_rot_deg` in `unreal_bridge.py` (one place).
Not covered yet: material/emission animation, shape keys (jaw, lids), cloth and fur, per-clip root-motion settings, lighting and post-process look.
