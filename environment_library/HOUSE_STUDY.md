# Continuous house set study

Built in the separate Unreal verification project; saved level path is recorded in `demos/ModernHouse_20261015_095225/build-result.json`. Existing levels and original repositories are preserved.

The single 8 × 6 × 3.2 metre layout contains dining furniture, built-in cupboards, shelves, pendant lights, a window opening and a 1 metre entrance opening. Interior and exterior cameras share the same geometry. The exterior includes a terrace and installed scanned plants. Windows intentionally have no glass yet. The layout is a single-room prototype, not a complete multi-room home.

Free CC0 material maps: Poly Haven Wood Floor Deck and Painted Plaster Wall. Download script, source URLs, hashes and local filenames are in `download_house_materials.py` and `assets/house-materials.json`. An initial ambientCG download returned HTTP 403; no files from that source were imported. The implemented downloader uses Poly Haven's public file host and does not require a live API integration. Six 2K maps were imported, with diffuse, roughness and DirectX normal connections. Texture repeat is fixed for this prototype rather than physically scaled per surface.

Run `build_house_unreal.py` inside the dedicated verification editor, then `capture_house.py` from local Python with bridge 8520 available and no other editor jobs running. The build verifies its project, uses unique asset/level folders, and writes its result only after save success. The builder includes the corrected practical-light intensity; `fix_house_lights_unreal.py` records the one-time repair of the initial study without overwriting its saved level.

Verification: inspected interior and exterior screenshots; corrected overbright practical lighting; saved the repaired level; Python compilation and showcase JavaScript syntax checks; gallery and static-file HTTP checks. No browser clickthrough or character interaction tests performed. The room uses simple procedural box geometry, so edges, furniture and sink remain visibly basic. It is an architectural starting point, not a Hollywood-quality finished set.

Next quality work: bevelled furniture and fixtures, believable window glazing, calibrated interior lighting, richer set dressing, additional rooms and adjoining street/café sets.
